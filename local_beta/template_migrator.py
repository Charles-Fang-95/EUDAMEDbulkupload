from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .build_unified_template import DATA_START_ROW, build_workbook
from .constants import EXPORT_DIR, TOOL_DIR, VENDOR_LIB
from .template_schema import ENTRY_SHEETS, RELATED_SHEETS, TEMPLATE_VERSION, columns_for_entry_sheet

if str(VENDOR_LIB) not in sys.path:
    sys.path.insert(0, str(VENDOR_LIB))
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import openpyxl  # type: ignore


LEGACY_RELATED_SHEET_MAP = {
    "Market Information": "Market Info",
    "Package Information": "Package Info",
}

RELATED_SHEET_ALIASES = {
    "Market Info": ["Market Info", "Market Information"],
    "Package Info": ["Package Info", "Package Information"],
    "Critical Warnings": ["Critical Warnings"],
    "Storage Conditions": ["Storage Conditions"],
    "CMR Substances": ["CMR Substances"],
    "Trade Names": ["Trade Names"],
    "Device Certificates": ["Device Certificates"],
    "Clinical Sizes": ["Clinical Sizes"],
    "Annex XVI Purposes": ["Annex XVI Purposes"],
}

PACKAGE_HEADER_ALIASES = {
    "Package Level": "Local - Package Level",
    "Package Type": "Local - Package Type",
}

MAIN_HEADER_ALIASES = {
    "Basic - Kit (IVDR)": "Basic - Is it a Kit",
    "Kit (IVDR)": "Basic - Is it a Kit",
}


def migrate_workbook(source_path: Path, output_dir: Path = EXPORT_DIR) -> dict:
    """Copy known EUDAMED template data into the current generated template.

    The migrator only auto-copies fields it can match by current header, legacy
    header, or stable field name. Unknown customer columns are reported instead
    of guessed.
    """
    if source_path.suffix.lower() != ".xlsx":
        return {
            "ok": False,
            "errors": ["目前迁移工具只支持 .xlsx。旧 .xls 请先用 Excel/WPS 另存为 .xlsx。"],
            "warnings": [],
            "output_filename": "",
            "report": {},
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    source = openpyxl.load_workbook(source_path, data_only=True)
    target = build_workbook()
    report = {
        "source_file": source_path.name,
        "source_sheets": list(source.sheetnames),
        "mode": "unknown",
        "copied_rows": defaultdict(int),
        "unmapped_headers": defaultdict(list),
        "warnings": [],
    }

    if any(sheet in source.sheetnames for sheet in ENTRY_SHEETS):
        report["mode"] = "current_unified_template"
        _copy_unified_sheets(source, target, report)
    elif "Basic UDI-DI" in source.sheetnames and "UDI-DI" in source.sheetnames:
        report["mode"] = "legacy_split_template"
        _copy_legacy_split_sheets(source, target, report)
    else:
        report["warnings"].append("未识别到 MDR_MDD / IVDR_IVDD 或旧版 Basic UDI-DI + UDI-DI sheet；未自动搬迁数据。")

    _copy_related_sheets(source, target, report)
    _add_report_sheet(target, report)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"MIGRATED_EUDAMED_Template_{TEMPLATE_VERSION}_{timestamp}.xlsx"
    target.save(output_path)
    return {
        "ok": True,
        "errors": [],
        "warnings": list(report["warnings"]),
        "output_filename": output_path.name,
        "report": _serializable_report(report),
    }


def _copy_unified_sheets(source, target, report: dict):
    for sheet_name in ENTRY_SHEETS:
        if sheet_name not in source.sheetnames:
            continue
        rows = _read_rows(source[sheet_name])
        target_headers = _headers(target[sheet_name])
        source_headers = _headers(source[sheet_name])
        header_map = _header_map(source_headers, target_headers, extra_aliases=MAIN_HEADER_ALIASES)
        _record_unmapped(report, sheet_name, source_headers, header_map)
        target_row = DATA_START_ROW
        for row in rows:
            if not _has_data(row):
                continue
            _write_row(target[sheet_name], target_headers, target_row, row, header_map)
            _append_old_udi_detail_rows(target, row, report)
            target_row += 1
            report["copied_rows"][sheet_name] += 1


def _copy_legacy_split_sheets(source, target, report: dict):
    basic_rows = _read_rows(source["Basic UDI-DI"])
    udi_rows = _read_rows(source["UDI-DI"])
    basics = {}
    for row in basic_rows:
        code = str(_get_by_alias(row, "Basic UDI-DI Code") or "").strip()
        if code:
            basics[code] = row

    target_next_rows = {sheet: DATA_START_ROW for sheet in ENTRY_SHEETS}
    for udi in udi_rows:
        udi_code = str(_get_by_alias(udi, "UDI-DI Code") or "").strip()
        if not udi_code:
            continue
        parent = str(_get_by_alias(udi, "Parent Basic UDI-DI") or "").strip()
        basic = basics.get(parent, {})
        legislation = str(_get_by_alias(basic, "Applicable Legislation") or "").upper()
        target_sheet = "IVDR_IVDD" if legislation in {"IVDR", "IVDD"} else "MDR_MDD"
        target_headers = _headers(target[target_sheet])
        combined = _legacy_combined_row(basic, udi)
        _write_by_field(target[target_sheet], target_headers, target_next_rows[target_sheet], combined)
        _append_old_udi_detail_rows(target, udi, report)
        target_next_rows[target_sheet] += 1
        report["copied_rows"][target_sheet] += 1

    source_headers = _headers(source["Basic UDI-DI"]) + _headers(source["UDI-DI"])
    matched = set(_legacy_field_map().keys()) | {"Parent Basic UDI-DI"}
    report["unmapped_headers"]["Legacy Basic/UDI"] = [
        header for header in source_headers if header and _canonical(header) not in {_canonical(item) for item in matched}
    ]


def _copy_related_sheets(source, target, report: dict):
    for target_sheet, aliases in RELATED_SHEET_ALIASES.items():
        source_sheet = next((name for name in aliases if name in source.sheetnames), "")
        if not source_sheet:
            continue
        rows = _read_rows(source[source_sheet])
        target_headers = _headers(target[target_sheet])
        source_headers = _headers(source[source_sheet])
        header_map = _header_map(source_headers, target_headers, extra_aliases=PACKAGE_HEADER_ALIASES)
        _record_unmapped(report, source_sheet, source_headers, header_map)
        target_row = DATA_START_ROW
        for row in rows:
            if not _has_data(row):
                continue
            _write_row(target[target_sheet], target_headers, target_row, row, header_map)
            target_row += 1
            report["copied_rows"][target_sheet] += 1


def _read_rows(ws) -> list[dict]:
    headers = _headers(ws)
    rows = []
    for row_idx in range(DATA_START_ROW, ws.max_row + 1):
        row = {}
        for col_idx, header in enumerate(headers, start=1):
            if header:
                row[header] = ws.cell(row_idx, col_idx).value
        if _has_data(row):
            rows.append(row)
    return rows


def _headers(ws) -> list[str]:
    return [str(cell.value or "").strip() for cell in ws[1]]


def _header_map(source_headers: list[str], target_headers: list[str], extra_aliases: dict | None = None) -> dict:
    extra_aliases = extra_aliases or {}
    target_by_key = {_canonical(header): header for header in target_headers if header}
    mapping = {}
    for source_header in source_headers:
        if not source_header:
            continue
        target_header = extra_aliases.get(source_header, source_header)
        key = _canonical(target_header)
        if key in target_by_key:
            mapping[source_header] = target_by_key[key]
    return mapping


def _write_row(ws, target_headers: list[str], target_row: int, row: dict, header_map: dict):
    target_index = {header: idx for idx, header in enumerate(target_headers, start=1)}
    for source_header, target_header in header_map.items():
        if target_header in target_index:
            ws.cell(target_row, target_index[target_header]).value = row.get(source_header)


def _write_by_field(ws, target_headers: list[str], target_row: int, field_values: dict):
    target_index = {header: idx for idx, header in enumerate(target_headers, start=1)}
    field_to_header = {item["field"]: item["header"] for item in columns_for_entry_sheet(ws.title)}
    for field, value in field_values.items():
        header = field_to_header.get(field)
        if header in target_index:
            ws.cell(target_row, target_index[header]).value = value


def _legacy_combined_row(basic: dict, udi: dict) -> dict:
    mapped = {}
    field_map = _legacy_field_map()
    for header, value in basic.items():
        field = field_map.get(_canonical(header))
        if field:
            mapped[field] = value
    for header, value in udi.items():
        field = field_map.get(_canonical(header))
        if field:
            mapped[field] = value
    parent = _get_by_alias(udi, "Parent Basic UDI-DI")
    if parent:
        mapped["Basic UDI-DI Code"] = parent
    return mapped


def _legacy_field_map() -> dict:
    fields = {}
    for item in columns_for_entry_sheet("MDR_MDD") + columns_for_entry_sheet("IVDR_IVDD"):
        fields[_canonical(item["field"])] = item["field"]
        fields[_canonical(item["header"])] = item["field"]
    aliases = {
        "Device Name/Model": "Device Name/Model",
        "Device Name/Model*": "Device Name/Model",
        "Parent Basic UDI-DI": "Basic UDI-DI Code",
    }
    for source, field in aliases.items():
        fields[_canonical(source)] = field
    return fields


def _append_old_udi_detail_rows(target, source_row: dict, report: dict):
    udi_code = str(_get_by_alias(source_row, "UDI-DI Code") or "").strip()
    if not udi_code:
        return

    old_size_value = _get_by_alias(source_row, "Clinical Size Value")
    old_size_unit = _get_by_alias(source_row, "Clinical Size Unit")
    if old_size_value not in (None, "") or old_size_unit not in (None, ""):
        _append_related_row(
            target["Clinical Sizes"],
            {
                "UDI-DI Code*": udi_code,
                "Precision*": "Value",
                "Value": old_size_value,
                "Measure Unit": old_size_unit,
            },
        )
        report["copied_rows"]["Clinical Sizes"] += 1
        report["warnings"].append(
            f"UDI-DI {udi_code} 的旧 Clinical Size Value/Unit 已迁移到 Clinical Sizes sheet；请补充 Clinical Size Type，并确认 Measure Unit 使用 v2.6 下拉值。"
        )

    old_annex = _get_by_alias(source_row, "Purpose Other Than Medical")
    if _truthy(old_annex):
        _append_related_row(
            target["Annex XVI Purposes"],
            {
                "UDI-DI Code*": udi_code,
            },
        )
        report["copied_rows"]["Annex XVI Purposes"] += 1
        report["warnings"].append(
            f"UDI-DI {udi_code} 的旧 Purpose Other Than Medical=TRUE 无法自动判断 Annex XVI 具体类型；请在 Annex XVI Purposes sheet 选择 Non-Medical Device Type。"
        )


def _append_related_row(ws, values_by_header: dict):
    headers = _headers(ws)
    target_index = {header: idx for idx, header in enumerate(headers, start=1)}
    row_idx = _next_data_row(ws)
    for header, value in values_by_header.items():
        if header in target_index:
            ws.cell(row_idx, target_index[header]).value = value


def _next_data_row(ws) -> int:
    for row_idx in range(DATA_START_ROW, ws.max_row + 2):
        values = [ws.cell(row_idx, col_idx).value for col_idx in range(1, ws.max_column + 1)]
        if not any(value not in (None, "") for value in values):
            return row_idx
    return ws.max_row + 1


def _truthy(value) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "YES", "1", "Y"}


def _get_by_alias(row: dict, field: str):
    key = _canonical(field)
    for header, value in row.items():
        if _canonical(header) == key:
            return value
    return None


def _record_unmapped(report: dict, sheet_name: str, source_headers: list[str], header_map: dict):
    mapped = set(header_map)
    unmapped = [header for header in source_headers if header and header not in mapped]
    if unmapped:
        report["unmapped_headers"][sheet_name].extend(unmapped)


def _has_data(row: dict) -> bool:
    return any(value not in (None, "") for value in row.values())


def _canonical(value: str) -> str:
    text = str(value or "").replace("*", "")
    text = re.sub(r"^(basic|udi|local)\s*-\s*", "", text, flags=re.IGNORECASE)
    text = text.replace("UDI DI", "UDI-DI")
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _add_report_sheet(wb, report: dict):
    ws = wb.create_sheet("Migration Report", 0)
    ws.append(["Item", "Value"])
    ws.append(["Source file", report["source_file"]])
    ws.append(["Detected mode", report["mode"]])
    ws.append(["Source sheets", ", ".join(report["source_sheets"])])
    ws.append([])
    ws.append(["Copied sheet", "Rows"])
    for sheet, count in sorted(report["copied_rows"].items()):
        ws.append([sheet, count])
    ws.append([])
    ws.append(["Unmapped source sheet", "Headers"])
    for sheet, headers in sorted(report["unmapped_headers"].items()):
        ws.append([sheet, ", ".join(headers)])
    ws.append([])
    ws.append(["Warnings"])
    for warning in report["warnings"]:
        ws.append([warning])
    for col in ("A", "B"):
        ws.column_dimensions[col].width = 48


def _serializable_report(report: dict) -> dict:
    return {
        "source_file": report["source_file"],
        "source_sheets": report["source_sheets"],
        "mode": report["mode"],
        "copied_rows": dict(report["copied_rows"]),
        "unmapped_headers": {key: list(value) for key, value in report["unmapped_headers"].items()},
        "warnings": list(report["warnings"]),
    }
