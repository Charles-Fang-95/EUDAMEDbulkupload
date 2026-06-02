#!/usr/bin/env python3

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL_LIB = ROOT / "EUDAMED_TOOL_v2" / "lib"
if str(TOOL_LIB) not in sys.path:
    sys.path.insert(0, str(TOOL_LIB))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import openpyxl  # type: ignore
from openpyxl.styles import Alignment, Border, Font, PatternFill, Protection, Side  # type: ignore
from openpyxl.utils import get_column_letter  # type: ignore
from openpyxl.worksheet.datavalidation import DataValidation  # type: ignore

try:
    from .template_schema import (
        ALL_COLUMNS,
        ENTRY_SHEETS,
        ENUM_SOURCES,
        RELATED_SHEETS,
        TEMPLATE_VERSION,
        columns_for_entry_sheet,
    )
except ImportError:
    from local_beta.template_schema import (
        ALL_COLUMNS,
        ENTRY_SHEETS,
        ENUM_SOURCES,
        RELATED_SHEETS,
        TEMPLATE_VERSION,
        columns_for_entry_sheet,
    )


OUTPUTS = [
    ROOT / f"EUDAMED_Template_{TEMPLATE_VERSION}.xlsx",
    ROOT / "EUDAMED_TOOL_v2" / "templates" / f"EUDAMED_Template_{TEMPLATE_VERSION}.xlsx",
]
MAX_DATA_ROWS = 1000
DATA_START_ROW = 4
PROTECTION_PASSWORD = "eudamed"

GROUP_FILLS = {
    "Meta": "D9E8FB",
    "Basic": "DFF2E1",
    "UDI": "FFF0C7",
    "Related": "F8DEE0",
}
REQUIREMENT_FILLS = {
    "required": "F8D7DA",
    "conditional": "FFF3CD",
    "optional": "EAF4EA",
}

HEADER_FONT = Font(name="Arial", bold=True, color="1F1F1F")
REQUIRED_HEADER_FONT = Font(name="Arial", bold=True, color="8A1C1C")
CONDITIONAL_HEADER_FONT = Font(name="Arial", bold=True, color="7A4D00")
HELP_TITLE = Font(name="宋体", bold=True, size=14)
HELP_HEAD = Font(name="宋体", bold=True, color="1F1F1F")
CHINESE_FONT = Font(name="宋体")
ENGLISH_FONT = Font(name="Arial")
THIN = Side(style="thin", color="C8BEAC")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
UNLOCKED = Protection(locked=False)
HIGH_RISK_TEXT_TOKENS = (
    "UDI-DI Code",
    "Basic UDI-DI Code",
    "Package UDI-DI Code",
    "DM DI Code",
    "Unit of Use DI Code",
    "Secondary UDI-DI Code",
    "Reference Number",
    "SRN",
    "EMDN Code",
    "Nomenclature Code",
    "CAS Code",
    "EC Code",
    "Current Version",
)


def build_workbook():
    wb = openpyxl.Workbook()
    first = wb.active
    first.title = "MDR_MDD"

    _build_entry_sheet(first, "MDR_MDD")
    _build_entry_sheet(wb.create_sheet("IVDR_IVDD"), "IVDR_IVDD")
    for sheet_name, spec in RELATED_SHEETS.items():
        _build_related_sheet(wb.create_sheet(sheet_name), sheet_name, spec["columns"])

    _build_how_to_use(wb.create_sheet("How to Use"))
    _build_glossary(wb.create_sheet("Glossary"))
    _build_critical_warning_glossary(wb.create_sheet("Critical Warning Glossary"))
    enums = wb.create_sheet("Enumerations")
    _build_enums(enums)
    enums.sheet_state = "hidden"
    return wb


def _build_entry_sheet(ws, sheet_name: str):
    _build_table_sheet(ws, columns_for_entry_sheet(sheet_name))
    ws.sheet_view.showGridLines = True


def _build_related_sheet(ws, sheet_name: str, columns: list[dict]):
    _build_table_sheet(ws, columns)


def _build_table_sheet(ws, columns: list[dict]):
    for col_idx, item in enumerate(columns, start=1):
        header = ws.cell(1, col_idx, item["header"])
        header.font = _header_font(item)
        header.fill = PatternFill("solid", fgColor=GROUP_FILLS[item["group"]])
        header.alignment = WRAP
        header.border = BOX

        description = ws.cell(2, col_idx, _description_line(item))
        description.font = CHINESE_FONT
        description.fill = PatternFill("solid", fgColor=REQUIREMENT_FILLS[item["requirement"]])
        description.alignment = WRAP
        description.border = BOX

        example = ws.cell(3, col_idx, item["example"])
        example.font = ENGLISH_FONT
        example.fill = PatternFill("solid", fgColor="F3F8E8")
        example.alignment = WRAP
        example.border = BOX

        width_base = max(len(item["header"]), len(str(item["example"] or "")))
        ws.column_dimensions[get_column_letter(col_idx)].width = max(14, min(42, width_base * 0.95))

    for row_idx, height in ((1, 42), (2, 84), (3, 50)):
        ws.row_dimensions[row_idx].height = height

    last_col = get_column_letter(len(columns))
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A1:{last_col}1"
    _unlock_data_area(ws, len(columns))
    _format_data_area(ws, len(columns))
    _add_data_validations(ws, columns)
    _protect_sheet(ws)


def _description_line(item: dict) -> str:
    required = {"required": "必填", "conditional": "条件必填", "optional": "可选"}[item["requirement"]]
    fmt = f"；格式：{item['format']}" if item["format"] else ""
    description = str(item["description"] or "")
    if description.startswith(f"{required}：") or description.startswith(f"{required}/"):
        return f"{description}{fmt}"
    return f"{required}。{description}{fmt}"


def _header_font(item: dict):
    if item["requirement"] == "required":
        return REQUIRED_HEADER_FONT
    if item["requirement"] == "conditional":
        return CONDITIONAL_HEADER_FONT
    return HEADER_FONT


def _unlock_data_area(ws, column_count: int):
    for row in ws.iter_rows(min_row=DATA_START_ROW, max_row=MAX_DATA_ROWS, min_col=1, max_col=column_count):
        for cell in row:
            cell.protection = UNLOCKED


def _format_data_area(ws, column_count: int):
    for row in ws.iter_rows(min_row=DATA_START_ROW, max_row=MAX_DATA_ROWS, min_col=1, max_col=column_count):
        for cell in row:
            cell.font = ENGLISH_FONT
            cell.number_format = "@"


def _protect_sheet(ws):
    ws.protection.sheet = True
    ws.protection.password = PROTECTION_PASSWORD
    ws.protection.selectLockedCells = False
    ws.protection.selectUnlockedCells = False
    ws.protection.autoFilter = False
    ws.protection.sort = False
    ws.protection.formatColumns = False


def _build_enums(ws):
    for col_idx, (name, values) in enumerate(ENUM_SOURCES.items(), start=1):
        ws.cell(1, col_idx, name)
        ws.cell(1, col_idx).font = HEADER_FONT
        ws.column_dimensions[get_column_letter(col_idx)].width = 44 if name in {"storage_condition", "critical_warning"} else 18
        for row_idx, value in enumerate(values, start=2):
            ws.cell(row_idx, col_idx, value)
            ws.cell(row_idx, col_idx).font = ENGLISH_FONT


def _build_how_to_use(ws):
    lines = [
        (f"EUDAMED Template {TEMPLATE_VERSION} - How to Use", HELP_TITLE),
        ("1. 选择法规 sheet", HELP_HEAD),
        ("MDR/MDD 产品填写 MDR_MDD；IVDR/IVDD 产品填写 IVDR_IVDD。正式数据从第 4 行开始。", None),
        ("2. 三行表头", HELP_HEAD),
        ("第 1 行是程序识别字段名；第 2 行是中文说明；第 3 行是示例。前三行已锁定，请不要修改。", None),
        ("3. 推荐维护方式", HELP_HEAD),
        ("Excel template 是主维护文件；本地网页端用于批量导入、校验、筛选、选择 service 和导出 XML。", None),
        ("网页端数据库是工作库/导出历史库，不建议长期绕过 Excel 直接维护唯一数据源。", None),
        ("4. 一个 UDI-DI 一行", HELP_HEAD),
        ("一个 Basic UDI-DI 下有多个 UDI-DI 时，在主表重复填写 Basic 列，并逐行填写不同 UDI-DI。", None),
        ("5. 明细 sheet", HELP_HEAD),
        ("Trade Names、Market Info、Package Info、Device Certificates、Critical Warnings、Storage Conditions、CMR Substances 使用独立列填写，不再使用 | 分隔符。", None),
        ("Package Info 不是所有产品都要填：只有存在 container package / 多层包装 DI 时才填写；没有包装层级时整张 Package Info sheet 可留空。", None),
        ("Market Info 属于 UDI-DI 层，不属于 BUDI 层；独立 Update market information service 后续实现。", None),
        ("同一 UDI-DI 可以有多个 made available 国家，但 Originally Placed on Market 必须且只能有一个 TRUE，其它国家填写 FALSE。", None),
        ("国家/市场信息填报错误时，应优先通过 EUDAMED update/create new version 纠正，不应默认删除 UDI-DI 重新注册。", None),
        ("只有当 UDI-DI、器械身份或 Basic UDI-DI 关联本身错误，且无法通过更新纠正时，才考虑 discard/逻辑删除并重新注册。", None),
        ("6. UDI/GTIN/Reference 文本格式", HELP_HEAD),
        ("UDI-DI、Basic UDI-DI、Package UDI-DI、Reference、SRN、EMDN/Nomenclature 等字段必须按文本维护。", None),
        ("不要使用数字格式保存这些编码，避免 Excel/WPS 自动改成科学计数法或丢失前导 0。", None),
        ("7. 多语言 Trade Name", HELP_HEAD),
        ("主表 Trade Name 是快捷列；同一 UDI-DI 有多个商品名或多语言时，请在 Trade Names sheet 中逐行填写。", None),
        ("Trade Name 的 Language 可选 ANY，表示该商品名不限定具体语言；ANY 不会自动翻译，也不代表只能填写一个商品名。", None),
        ("如果同一 UDI-DI 有不同语言或多个商品名，可在 Trade Names sheet 填多行；能确定语言时建议选择具体语言代码。", None),
        ("8. Reference Number", HELP_HEAD),
        ("UDI - Reference Number* 是 EUDAMED XML 必填字段。没有内部 reference/catalogue number 时，请先与客户确认可提交的 reference。", None),
        ("9. Storage / Critical Warning 枚举", HELP_HEAD),
        ("下拉值采用 CODE - English label。程序导入时会自动取 CODE 输出 XML。SHC099 / CW999 为 OTHER，必须填写说明并选择具体语言。", None),
        ("Critical Warning Glossary sheet 提供完整官方 CW 枚举，便于按说明书或标签查找对应 warning。", None),
        ("10. Package Info 多层包装", HELP_HEAD),
        ("Package Info 每一行表示“一个 Package DI 包含一个 child DI”。child 可为主 UDI-DI，也可为同组下一级 Package DI。", None),
        ("如果填写 Package Info 行，UDI-DI Code、Package UDI-DI Code、Package Issuing Entity、Quantity per Package 为条件必填。", None),
        ("Contains DI Code 留空时兼容旧填法，默认 child 为主 UDI-DI；Local - Package Level / Type 只作本地辅助说明，不输出到 XML。", None),
        ("11. 上传 service", HELP_HEAD),
        ("新建 Basic + 多个 UDI-DI 使用 DEVICE.POST；已有 Basic 追加 UDI-DI 使用 UDI_DI.POST。新上传时可随 UDI-DI 一起输出 container package。", None),
        ("MDR/IVDR 会按 Regulation Device XML 输出；MDD/AIMDD/IVDD 会按 Legacy Device / EUDI XML 输出。", None),
        ("AIMDD 的 Risk Class 通常选择 AIMDD；IVDD 可选择 IVD Annex II List A/B、IVD Self Testing 或 IVD General。", None),
        ("12. 特殊下拉值", HELP_HEAD),
        ("国家代码请使用官方 XSD 代码：希腊是 EL，不是 GR。", None),
        ("Issuing Entity 的 EUDAMED 通常用于 EUDAMED DI 等 legacy 场景；普通 UDI 请按实际发码机构选择 GS1/HIBCC/ICCBBA/IFA。", None),
        ("IFA 是官方 issuing entity 选项之一；是否适用以客户实际发码机构为准。", None),
        ("13. Device Certificates", HELP_HEAD),
        ("触发 MDR Art. 29(3) / IVDR Art. 26(2) 或 legacy 指令证书场景时，请在 Device Certificates sheet 逐行填写 product certificate 信息。", None),
        ("证书信息会输出到 Basic UDI-DI 的 deviceCertificateLinks；PR/SPP 证书结构暂未实现。", None),
        ("14. 当前不输出字段", HELP_HEAD),
        ("eIFU URL、Public Email、Clinical Size、Product Designer、Purpose Other Than Medical 等字段正在做官方字段映射审计；未确认前不会静默写入 XML。", None),
        ("15. 更新 service", HELP_HEAD),
        ("Basic_UDI.PATCH 需要在主表 B 列 Basic - Current Version 填写 EUDAMED 网页中的当前 Basic 版本号。", None),
        ("UDI_DI.PATCH 需要在主表 UDI 区域的 UDI - Current Version 列填写 EUDAMED 网页中的当前 UDI-DI 版本号。", None),
        ("独立 Update container package service 暂未开放；独立 Update market information service 后续实现。", None),
        ("16. Basic Model", HELP_HEAD),
        ("如果 EUDAMED 中 Model 不适用于 BUDI，请只填 Basic - Device Name*，并留空 Basic - Device Model。", None),
        ("17. WPS / Excel 兼容说明", HELP_HEAD),
        ("模板为无宏 .xlsx，理论上可在 WPS 中填写；实际兼容性以后续用户测试为准。导入时系统会提示疑似自动格式化风险。", None),
        ("18. 字体和锁定", HELP_HEAD),
        ("英文/代码/枚举值使用 Arial；中文说明使用宋体。前三行已锁定，正式填写从第 4 行开始。", None),
    ]
    row = 1
    for text, font in lines:
        cell = ws.cell(row, 1, text)
        cell.alignment = WRAP
        cell.font = font or CHINESE_FONT
        row += 1
    ws.column_dimensions["A"].width = 120


def _build_glossary(ws):
    headers = ["Group", "Column", "Requirement", "Target", "Applies", "Meaning", "Format", "Example"]
    for idx, header in enumerate(headers, start=1):
        cell = ws.cell(1, idx, header)
        cell.font = HEADER_FONT
        cell.fill = PatternFill("solid", fgColor="E8E0CF")
        cell.border = BOX
    for row_idx, item in enumerate(ALL_COLUMNS, start=2):
        values = [
            item["group"],
            item["header"],
            {"required": "必填", "conditional": "条件必填", "optional": "可选"}[item["requirement"]],
            f"{item['entity']} -> {item['field']}",
            item["applies"],
            item["description"],
            _glossary_format(item),
            item["example"],
        ]
        for col_idx, value in enumerate(values, start=1):
            ws.cell(row_idx, col_idx, value)
            cell = ws.cell(row_idx, col_idx)
            cell.alignment = WRAP
            cell.border = BOX
            cell.font = CHINESE_FONT if col_idx in {3, 6} else ENGLISH_FONT
    ws.freeze_panes = "A2"
    for idx, width in enumerate([14, 36, 10, 24, 14, 70, 28, 40], start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width


def _glossary_format(item: dict) -> str:
    fmt = item["format"]
    if _is_high_risk_text_header(item["header"]):
        return f"{fmt}；必须按文本维护，避免科学计数法或前导 0 丢失" if fmt else "必须按文本维护"
    return fmt


def _is_high_risk_text_header(header: str) -> bool:
    return any(token in header for token in HIGH_RISK_TEXT_TOKENS)


def _build_critical_warning_glossary(ws):
    headers = ["Code", "English Label", "OTHER", "Requires Comment", "Language Rule", "Usage Note"]
    for idx, header in enumerate(headers, start=1):
        cell = ws.cell(1, idx, header)
        cell.font = HEADER_FONT
        cell.fill = PatternFill("solid", fgColor="F8DEE0")
        cell.border = BOX
        cell.alignment = WRAP

    for row_idx, value in enumerate(ENUM_SOURCES.get("critical_warning", []), start=2):
        code, label = _split_enum(value)
        is_other = code == "CW999"
        values = [
            code,
            label,
            "Yes" if is_other else "No",
            "Yes" if is_other else "No",
            "选择具体语言，不能为 ANY" if is_other else "如填写 Comment，导出时使用 ANY",
            "找不到合适官方 warning 时才使用 OTHER，并在 Comment 说明。" if is_other else "优先使用官方枚举，不要用自由文本替代。",
        ]
        for col_idx, item in enumerate(values, start=1):
            cell = ws.cell(row_idx, col_idx, item)
            cell.font = CHINESE_FONT if col_idx in {5, 6} else ENGLISH_FONT
            cell.alignment = WRAP
            cell.border = BOX

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}1"
    for idx, width in enumerate([14, 80, 10, 18, 32, 54], start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width


def _split_enum(value: str) -> tuple[str, str]:
    if " - " in value:
        return tuple(value.split(" - ", 1))  # type: ignore[return-value]
    return value, ""


def _add_data_validations(ws, columns: list[dict]):
    enum_col_map = {name: idx for idx, name in enumerate(ENUM_SOURCES.keys(), start=1)}
    for col_idx, item in enumerate(columns, start=1):
        if not item["validation"]:
            continue
        enum_name = item["validation"]
        enum_col = enum_col_map[enum_name]
        enum_last_row = len(ENUM_SOURCES[enum_name]) + 1
        enum_letter = get_column_letter(enum_col)
        formula = f"=Enumerations!${enum_letter}$2:${enum_letter}${enum_last_row}"
        dv = DataValidation(type="list", formula1=formula, allow_blank=True)
        dv.prompt = item["description"]
        dv.error = "请输入下拉列表中的有效值。"
        target = f"{get_column_letter(col_idx)}{DATA_START_ROW}:{get_column_letter(col_idx)}{MAX_DATA_ROWS}"
        dv.add(target)
        ws.add_data_validation(dv)


def save_outputs():
    wb = build_workbook()
    for path in OUTPUTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(path)
        print(f"saved: {path}")


if __name__ == "__main__":
    save_outputs()
