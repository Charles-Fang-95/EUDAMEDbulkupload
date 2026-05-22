#!/usr/bin/env python3
"""Check EUDAMED official technical documents against the pinned local manifest.

This script is intentionally stdlib-only so it can run in GitHub Actions without
installing project dependencies. It reports changes; it never modifies source
code or user templates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT_DIR / "official_docs" / "official_sources_manifest.json"
TECHNICAL_DOCUMENTATION_URL = "https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html"
USER_AGENT = "eudamed-bulkupload-official-docs-check/1.0"

SOURCE_QUERIES = {
    "xsd_schemas": ("xsd", "schemas"),
    "data_dictionary": ("data", "dictionary"),
    "business_rules": ("business", "rules"),
    "services_definition": ("services", "definition"),
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict] = []
        self._current_href = ""
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        self._current_href = attrs_dict.get("href", "")
        self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_href:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._current_href:
            self.links.append({"href": self._current_href, "text": " ".join("".join(self._text_parts).split())})
            self._current_href = ""
            self._text_parts = []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="official-update-report", help="Directory for JSON and Markdown reports.")
    parser.add_argument(
        "--local-baseline-only",
        action="store_true",
        help="Do not use the network; report the currently pinned manifest only. Useful for local smoke tests.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()

    if args.local_baseline_only:
        report = baseline_report(manifest)
    else:
        report = check_remote(manifest)

    write_reports(report, output_dir)
    return 0


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"sources": {}, "enum_baseline": {}, "expected_xsd_version": ""}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def baseline_report(manifest: dict) -> dict:
    return {
        "changed": False,
        "mode": "local-baseline-only",
        "expected_xsd_version": manifest.get("expected_xsd_version", ""),
        "sources": {
            key: {
                "label": item.get("label", key),
                "status": "baseline",
                "sha256": item.get("sha256", ""),
                "size": item.get("size", 0),
            }
            for key, item in (manifest.get("sources") or {}).items()
        },
        "enums": manifest.get("enum_baseline", {}),
        "errors": [],
    }


def check_remote(manifest: dict) -> dict:
    report = {
        "changed": False,
        "mode": "remote",
        "expected_xsd_version": manifest.get("expected_xsd_version", ""),
        "sources": {},
        "enums": {},
        "errors": [],
    }
    try:
        html = fetch_text(TECHNICAL_DOCUMENTATION_URL)
    except Exception as exc:  # noqa: BLE001 - report, do not crash the scheduled workflow.
        report["errors"].append(f"Cannot fetch technical documentation page: {exc}")
        report["changed"] = True
        return report

    links = extract_links(html, TECHNICAL_DOCUMENTATION_URL)
    selected = select_source_links(links)
    baseline_sources = manifest.get("sources") or {}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        xsd_file = None
        for key, baseline in baseline_sources.items():
            url = selected.get(key, "")
            item = {
                "label": baseline.get("label", key),
                "url": url,
                "status": "missing-link" if not url else "ok",
                "baseline_sha256": baseline.get("sha256", ""),
                "baseline_size": baseline.get("size", 0),
            }
            if not url:
                report["changed"] = True
                report["sources"][key] = item
                continue
            try:
                data = fetch_bytes(url)
            except Exception as exc:  # noqa: BLE001
                item["status"] = "download-error"
                item["error"] = str(exc)
                report["changed"] = True
                report["sources"][key] = item
                continue
            sha = hashlib.sha256(data).hexdigest()
            item["sha256"] = sha
            item["size"] = len(data)
            item["changed"] = sha != baseline.get("sha256") or len(data) != baseline.get("size")
            if item["changed"]:
                item["status"] = "changed"
                report["changed"] = True
            if key == "xsd_schemas":
                xsd_file = tmp_dir / "xsd_schemas.zip"
                xsd_file.write_bytes(data)
            report["sources"][key] = item

        if xsd_file and xsd_file.exists():
            report["enums"] = inspect_xsd_zip(xsd_file)
            baseline_enums = manifest.get("enum_baseline") or {}
            for enum_name, value in report["enums"].items():
                if enum_name.endswith("_count") and baseline_enums.get(enum_name) != value:
                    report["changed"] = True
                    report["enums"][f"{enum_name}_changed"] = True
            if report["enums"].get("xsd_version") != manifest.get("expected_xsd_version"):
                report["changed"] = True
                report["enums"]["xsd_version_changed"] = True

    return report


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def extract_links(html: str, base_url: str) -> list[dict]:
    parser = LinkParser()
    parser.feed(html)
    links = []
    for link in parser.links:
        href = urllib.parse.urljoin(base_url, link["href"])
        links.append({"href": href, "text": link["text"]})
    return links


def select_source_links(links: list[dict]) -> dict[str, str]:
    selected: dict[str, str] = {}
    for key, keywords in SOURCE_QUERIES.items():
        for link in links:
            haystack = f"{link.get('text', '')} {urllib.parse.unquote(link.get('href', ''))}".lower()
            if all(keyword in haystack for keyword in keywords):
                selected[key] = link["href"]
                break
    return selected


def inspect_xsd_zip(zip_path: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(tmp_dir)
        files = list(tmp_dir.rglob("*.xsd"))
        report = {
            "xsd_file_count": len(files),
            "xsd_version": fixed_version(find_file(files, "MessageType.xsd")),
            "language_count": enum_count(find_file(files, "LanguageSpecificNameType.xsd"), "LanguageEnum"),
            "country_count": enum_count(find_file(files, "CountryEnum.xsd"), "EUCountryWithSpecialEnum"),
            "issuing_entity_count": enum_count(find_file(files, "UDIDIType.xsd"), "IssuingEntityTypeEnum"),
            "storage_condition_count": enum_count(find_file(files, "CommonDeviceType.xsd"), "StorageHandlingConditionEnum"),
            "critical_warning_count": enum_count(find_file(files, "CommonDeviceType.xsd"), "CriticalWarningEnum"),
        }
        return report


def find_file(files: list[Path], filename: str) -> Path | None:
    matches = [path for path in files if path.name == filename]
    if not matches:
        return None
    return sorted(matches, key=lambda path: len(path.parts))[0]


def fixed_version(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r'fixed="([^"]+)"', text)
    return match.group(1) if match else ""


def enum_count(path: Path | None, type_name: str) -> int:
    if not path or not path.exists():
        return 0
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return 0
    restriction = root.find(f".//xs:simpleType[@name='{type_name}']/xs:restriction", ns)
    if restriction is None:
        return 0
    return len([enum for enum in restriction.findall("xs:enumeration", ns) if enum.attrib.get("value")])


def write_reports(report: dict, output_dir: Path) -> None:
    (output_dir / "official_update_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "official_update_report.md").write_text(markdown_report(report), encoding="utf-8")


def markdown_report(report: dict) -> str:
    lines = [
        "# EUDAMED Official Documentation Check",
        "",
        f"- Mode: `{report.get('mode', '')}`",
        f"- Changed: `{bool(report.get('changed'))}`",
        f"- Expected XSD version: `{report.get('expected_xsd_version', '')}`",
        "",
        "## Sources",
        "",
        "| Key | Status | Size | SHA-256 | URL |",
        "|---|---:|---:|---|---|",
    ]
    for key, item in (report.get("sources") or {}).items():
        lines.append(
            "| {key} | {status} | {size} | `{sha}` | {url} |".format(
                key=key,
                status=item.get("status", ""),
                size=item.get("size", item.get("baseline_size", "")),
                sha=item.get("sha256", item.get("baseline_sha256", "")),
                url=item.get("url", ""),
            )
        )
    lines += ["", "## XSD / Enum Snapshot", "", "| Item | Value |", "|---|---:|"]
    for key, value in (report.get("enums") or {}).items():
        lines.append(f"| {key} | `{value}` |")
    if report.get("errors"):
        lines += ["", "## Errors", ""]
        lines.extend(f"- {error}" for error in report["errors"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
