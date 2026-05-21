import re
import urllib.error
import urllib.request

from .constants import LOCAL_MESSAGE_XSD, SCHEMA_VERSION, TECHNICAL_DOCUMENTATION_URL

VERSION_RE = r"([0-9]+\.[0-9]+\.[0-9]+)"


def get_tool_xsd_version() -> str:
    return get_local_xsd_version() or SCHEMA_VERSION


def get_local_xsd_version() -> str:
    if not LOCAL_MESSAGE_XSD.exists():
        return ""
    text = LOCAL_MESSAGE_XSD.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r'name="version"[^>]*fixed="' + VERSION_RE + r'"', text)
    return match.group(1) if match else ""


def get_official_xsd_version(timeout: int = 8) -> tuple[str, str]:
    try:
        with urllib.request.urlopen(TECHNICAL_DOCUMENTATION_URL, timeout=timeout) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except (OSError, urllib.error.URLError) as exc:
        return "", f"无法访问官方技术文档页：{exc}"

    version = _extract_xsd_version(html)
    if version:
        return version, ""
    return "", "已访问官方技术文档页，但没有识别到 XSD schemas 版本。"


def build_xsd_version_report(check_online: bool = True) -> dict:
    tool_version = get_tool_xsd_version()
    local_version = get_local_xsd_version()
    official_version, error = get_official_xsd_version() if check_online else ("", "")
    reference_version = official_version or local_version

    status = "unknown"
    if reference_version:
        status = "ok" if tool_version == reference_version else "mismatch"
    elif local_version:
        status = "ok" if tool_version == local_version else "mismatch"

    return {
        "tool_version": tool_version,
        "local_xsd_version": local_version,
        "official_xsd_version": official_version,
        "official_url": TECHNICAL_DOCUMENTATION_URL,
        "status": status,
        "error": error,
    }


def _extract_xsd_version(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)

    xsd_match = re.search(r"XSD schemas.{0,250}?v\s*" + VERSION_RE, text, re.IGNORECASE)
    if xsd_match:
        return xsd_match.group(1)

    nearby_match = re.search(r"XSD.{0,250}?" + VERSION_RE, text, re.IGNORECASE)
    return nearby_match.group(1) if nearby_match else ""
