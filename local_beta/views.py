import html
import json
import platform
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlencode

from .constants import (
    BASIC_FIELDS,
    BULK_UPLOAD_ENTITY_LIMIT,
    COPYRIGHT_HOLDER,
    COPYRIGHT_YEAR,
    EUDAMED_PLAYGROUND_HELP_URL,
    EUDAMED_PLAYGROUND_URL,
    EUDAMED_BULK_UPLOAD_HELP_URL,
    EUDAMED_PRODUCTION_URL,
    GITEE_RELEASES_PAGE_URL,
    RELEASES_API_URL,
    RELEASES_PAGE_URL,
    SCHEMA_VERSION,
    SERVICE_LABELS,
    STATIC_DIR,
    SUPPORT_EMAIL,
    TECHNICAL_DOCUMENTATION_URL,
    TEMPLATE_VERSION,
    TOOL_UPDATED,
    TOOL_VERSION,
    TOOL_VERSION_LABEL,
    UDI_FIELDS,
)
from .template_schema import ENUM_SOURCES, ENTRY_SHEETS, MAIN_COLUMNS, RELATED_SHEETS, columns_for_entry_sheet


# ---------------------------------------------------------------------------
# 语言上下文（线程局部）：route() 每次请求开头调用 set_lang()，视图内用 t() 取文案。
# ---------------------------------------------------------------------------
_lang_ctx = threading.local()
_sample_ctx = threading.local()


def set_lang(lang: str) -> None:
    _lang_ctx.lang = "en" if lang == "en" else "zh"


def set_sample_counts(counts: dict | None) -> None:
    _sample_ctx.counts = counts or {"basic": 0, "udi": 0}


def current_lang() -> str:
    return getattr(_lang_ctx, "lang", "zh")


def sample_counts() -> dict:
    return getattr(_sample_ctx, "counts", {"basic": 0, "udi": 0})


def t(zh: str, en: str) -> str:
    """界面框架文案：根据当前语言返回中文或英文。"""
    return en if current_lang() == "en" else zh


SUPPORTED_SERVICES = {
    "DEVICE.POST": {
        "task_zh": "注册新器械（Basic UDI-DI + 首个 UDI-DI）",
        "task_en": "Register a new device (Basic UDI-DI + first UDI-DI)",
        "label": "Upload of Legacy / Regulation Device / SPP ( Basic UDI and UDI-DI / Master UDI-DI )",
        "scope": "新上传 Legacy Device / Regulation Device / SPP 的 Basic UDI-DI + UDI-DI / Master UDI-DI，可一次选择多条 UDI-DI。MDD/AIMDD/IVDD 会按 Legacy EUDI 结构输出。",
        "scope_en": "New upload of Legacy Device / Regulation Device / SPP Basic UDI-DI + UDI-DI / Master UDI-DI; multiple UDI-DIs can be selected at once. MDD/AIMDD/IVDD are exported using the Legacy EUDI structure.",
        "requires": "Basic 和 UDI-DI 必填字段、Reference Number、市场信息；不需要现有 EUDAMED version。新上传时可随 UDI-DI 一起输出 container package；触发 NB / product certificate validation 的器械请填写 Device Certificates。",
        "requires_en": "Mandatory Basic and UDI-DI fields, Reference Number and market info; no existing EUDAMED version needed. Container packages can be exported together with the UDI-DI. Devices triggering NB / product certificate validation should include Device Certificates.",
        "after": "在 EUDAMED 选择该 bulk upload service 后上传 XML。MDR/IVDR 输出 Regulation Device XML；MDD/AIMDD/IVDD 输出 Legacy Device / EUDI XML。如 XML 含证书信息，后续可能需要 NB 在 Certificates module 确认。上传成功后请保存官方 response；本地不会自动标记为已提交。",
        "after_en": "In EUDAMED, pick this bulk upload service and upload the XML. MDR/IVDR are exported as Regulation Device XML; MDD/AIMDD/IVDD are exported as Legacy Device / EUDI XML. If certificate information is included, the NB may need to confirm it in the Certificates module. Keep the official response after a successful upload; this tool does not mark records as submitted automatically.",
    },
    "UDI_DI.POST": {
        "task_zh": "给已注册 Basic 增加新的 UDI-DI",
        "task_en": "Add a new UDI-DI to an existing Basic",
        "label": "Upload of UDI-DI / Master UDI-DI for existing Basic UDI-DI",
        "scope": "给已经存在于 EUDAMED 的 Basic UDI-DI 增加新的 UDI-DI。",
        "scope_en": "Add new UDI-DIs to a Basic UDI-DI that already exists in EUDAMED.",
        "requires": "Parent Basic UDI-DI 必须已存在于 EUDAMED；UDI-DI 不需要现有 version。新上传 UDI-DI 时可随 UDI-DI 一起输出 container package。",
        "requires_en": "The parent Basic UDI-DI must already exist in EUDAMED; the UDI-DI needs no existing version. Container packages can be exported together with the new UDI-DI.",
        "after": "适合后续追加规格、包装或型号，不适合首次创建 Basic。",
        "after_en": "Suitable for adding later specifications, packaging or models; not for creating a Basic UDI-DI for the first time.",
    },
    "Basic_UDI.PATCH": {
        "task_zh": "修改已注册 Basic UDI-DI 的信息",
        "task_en": "Update an existing Basic UDI-DI",
        "label": "Update Basic UDI",
        "scope": "更新已存在 Basic UDI-DI 的 Basic 层字段。",
        "scope_en": "Update Basic-level fields of an existing Basic UDI-DI.",
        "requires": "必须填写当前 EUDAMED version，否则官方会拒绝更新。请在模板主表 B 列 Basic - Current Version 填写 EUDAMED 网页中该 Basic 的当前版本号。",
        "requires_en": "The current EUDAMED version must be provided, otherwise the update will be rejected. Fill column B, Basic - Current Version, in the main template sheet with the current Basic version shown in EUDAMED.",
        "after": "只更新 Basic 层，不会更新 UDI-DI 层规格、市场或包装信息。",
        "after_en": "Updates the Basic level only; UDI-DI level specifications, market or packaging info are not changed.",
    },
    "UDI_DI.PATCH": {
        "task_zh": "修改已注册 UDI-DI 的信息",
        "task_en": "Update an existing UDI-DI",
        "label": "Update of UDI-DI / Master UDI-DI",
        "scope": "更新已存在 UDI-DI 的 UDI 层字段。",
        "scope_en": "Update UDI-level fields of an existing UDI-DI.",
        "requires": "必须填写当前 EUDAMED version，否则官方会拒绝更新。请在模板主表 UDI 区域的 UDI - Current Version 列填写 EUDAMED 网页中该 UDI-DI 的当前版本号。",
        "requires_en": "The current EUDAMED version must be provided, otherwise the update will be rejected. Fill the UDI - Current Version column in the UDI section of the main template sheet with the current UDI-DI version shown in EUDAMED.",
        "after": "适合更改规格、警告、存储条件等 UDI-DI 层数据。国家/市场信息错误应优先通过 update/create new version 修正；只有器械身份、UDI-DI 或 Basic 关联本身错误且无法更新纠正时，才考虑 discard/逻辑删除并重建。",
        "after_en": "Suitable for changing specifications, warnings, storage conditions and other UDI-DI level data. Market information errors should be corrected through update/create new version where possible; discard and re-registration should be reserved for device identity, UDI-DI or Basic linkage errors that cannot be corrected by update.",
    },
    "MARKET_INFO.PATCH": {
        "task_zh": "更新已注册 UDI-DI 的市场国家 / 上市日期",
        "task_en": "Update market countries / dates for an existing UDI-DI",
        "label": "Update market information",
        "scope": "更新已注册 UDI-DI 的上市国家、可用开始/结束日期和首次投放成员国。",
        "scope_en": "Update market countries, availability start/end dates and first placed Member State for an already registered UDI-DI.",
        "requires": "UDI-DI 必须已在 EUDAMED 注册；Market Info 明细表必须填写；Originally Placed on Market 必须且只能有一条 TRUE。本 service 不需要 EUDAMED version 字段。",
        "requires_en": "The UDI-DI must already be registered in EUDAMED; Market Info rows must be filled; Originally Placed on Market must have exactly one TRUE. This service does not require the EUDAMED version field.",
        "after": "用于纠正市场信息时，请提交期望的完整市场集合。停止在某国销售时优先填写 End Date，而不是删除该国行；不要通过删除并重建 UDI-DI 来改市场信息。",
        "after_en": "When correcting market information, submit the intended complete market set. To stop selling in a country, set End Date rather than deleting that country row; do not delete and re-register the UDI-DI just to correct market information.",
    },
    "PACKAGE_UDI.PATCH": {
        "task_zh": "更新已注册 UDI-DI 的包装结构",
        "task_en": "Update package hierarchy for an existing UDI-DI",
        "label": "Update container package",
        "scope": "更新已注册 UDI-DI 的 container package / 包装层级结构。",
        "scope_en": "Update container package / packaging hierarchy for an already registered UDI-DI.",
        "requires": "UDI-DI 必须已在 EUDAMED 注册；只有产品有 container package / 多层包装 DI 时才填写 Package Info。若填写 Package Info 行，该行必须包含 Package UDI-DI、issuing entity、child DI 和数量。本 service 不需要 EUDAMED version 字段。",
        "requires_en": "The UDI-DI must already be registered in EUDAMED. Fill Package Info only when the product has container packages / package DIs. If a Package Info row is used, it must include Package UDI-DI, issuing entity, child DI and quantity. This service does not require the EUDAMED version field.",
        "after": "适合维护已注册产品的包装层级。每一行 Package Info 表示一个 package DI 包含一个 child DI；多层包装请按层级关系填写。",
        "after_en": "Suitable for maintaining packaging hierarchy for registered products. Each Package Info row means one package DI contains one child DI; fill multi-level packaging by the hierarchy relationship.",
    },
}

UNAVAILABLE_SERVICES = [
    {
        "label": "Update product original manufacturer",
        "status": "暂未开放",
        "status_en": "Not available yet",
    },
]


# 字段规格映射：field 名 -> template_schema 列定义，用于详情页按 schema 渲染下拉 / 说明 / 必填
FIELD_SPECS = {col["field"]: col for col in MAIN_COLUMNS}
ENUM_SELECT_VALIDATIONS = {
    "issuing_entity",
    "risk_class",
    "legislation",
    "device_type",
    "device_status",
    "language",
    "language_any",
}


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


GLOSSARY = {
    "Basic UDI-DI": (
        "一组器械型号/产品族的主标识，一个 Basic UDI-DI 可以对应多个 UDI-DI。",
        "The main identifier for a device model/product family; one Basic UDI-DI may contain multiple UDI-DIs.",
    ),
    "UDI-DI": (
        "具体器械型号、规格或包装层级的唯一器械标识。",
        "The device identifier for a concrete model, specification or package level.",
    ),
    "EMDN Code": (
        "EUDAMED 使用的欧洲医疗器械命名分类代码。",
        "European Medical Device Nomenclature code used by EUDAMED.",
    ),
    "Manufacturer SRN": (
        "制造商在 EUDAMED Actor 模块中的 Single Registration Number。",
        "Single Registration Number of the manufacturer in EUDAMED Actor module.",
    ),
    "Authorised Representative SRN": (
        "欧盟授权代表 SRN。非欧盟/EEA 制造商通常需要填写。",
        "SRN of the EU authorised representative. Usually required for non-EU/EEA manufacturers.",
    ),
    "Issuing Entity": (
        "UDI 代码签发机构，例如 GS1、HIBCC、ICCBBA、IFA；EUDAMED 通常用于 legacy EUDAMED DI 场景。",
        "The issuing entity of the DI code, such as GS1, HIBCC, ICCBBA or IFA; EUDAMED is usually for legacy EUDAMED DI scenarios.",
    ),
    "Originally Placed on Market": (
        "首次投放市场成员国标记。同一 UDI-DI 必须且只能有一条 TRUE。",
        "Flag for the first placed Member State. One UDI-DI must have exactly one TRUE row.",
    ),
    "Device Status": (
        "器械是否在欧盟市场销售/曾销售。On the EU market 时必须维护 Market Info。",
        "Whether the device is/was on the EU market. Market Info is required when status is On the EU market.",
    ),
    "DTX service": (
        "EUDAMED Data Exchange 的批量上传服务类型。必须和生成的 XML service 对应。",
        "A bulk upload service type in EUDAMED Data Exchange. It must match the generated XML service.",
    ),
    "DEVICE.POST": (
        "用于新注册 Basic UDI-DI + 首批 UDI-DI 的 service。",
        "Service for creating a new Basic UDI-DI together with the first UDI-DI batch.",
    ),
    "UDI_DI.POST": (
        "用于给已存在 Basic UDI-DI 追加新的 UDI-DI。",
        "Service for adding new UDI-DIs to an existing Basic UDI-DI.",
    ),
    "Basic_UDI.PATCH": (
        "用于更新已注册 Basic UDI-DI，需要 EUDAMED 当前 version。",
        "Service for updating an existing Basic UDI-DI; current EUDAMED version is required.",
    ),
    "UDI_DI.PATCH": (
        "用于更新已注册 UDI-DI，需要 EUDAMED 当前 version。",
        "Service for updating an existing UDI-DI; current EUDAMED version is required.",
    ),
    "MARKET_INFO.PATCH": (
        "用于更新已注册 UDI-DI 的市场国家和上市日期。",
        "Service for updating market countries and dates for an existing UDI-DI.",
    ),
    "PACKAGE_UDI.PATCH": (
        "用于更新已注册 UDI-DI 的 container package / 包装层级。",
        "Service for updating container package / package hierarchy for an existing UDI-DI.",
    ),
}


def term_hint(term: str) -> str:
    definition = GLOSSARY.get(term)
    if not definition:
        return esc(term)
    text = definition[1] if current_lang() == "en" else definition[0]
    return f'<span class="term-tip" data-tip="{esc(text)}">{esc(term)}<sup>?</sup></span>'


def sample_badge() -> str:
    return f'<span class="badge sample">{esc(t("示例", "SAMPLE"))}</span>'


def service_text(service: dict, key: str) -> str:
    """取 SUPPORTED_SERVICES 的多语言文案。"""
    if current_lang() == "en":
        return service.get(f"{key}_en") or service.get(key, "")
    return service.get(key, "")


def service_task(service: dict) -> str:
    return service.get("task_en" if current_lang() == "en" else "task_zh") or service.get("label", "")


def display_time(value) -> str:
    """把存储的 UTC ISO 时间串转成电脑本地时区的 YYYY-MM-DD HH:MM。"""
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if dt.tzinfo is not None:
        dt = dt.astimezone()
    return dt.strftime("%Y-%m-%d %H:%M")


def _enum_select(field: str, current: str, options: list) -> str:
    parts = [f'<option value="">{t("— 请选择 —", "— Select —")}</option>']
    matched = False
    for opt in options:
        text = str(opt)
        selected = " selected" if text == current else ""
        if selected:
            matched = True
        parts.append(f'<option value="{esc(text)}"{selected}>{esc(text)}</option>')
    if current and not matched:
        parts.append(f'<option value="{esc(current)}" selected>{esc(current)}{t("（当前值）", " (current)")}</option>')
    return f'<select name="field_{esc(field)}">{"".join(parts)}</select>'


def _bool_select(field: str, current: str) -> str:
    cur = current.strip().upper()
    values = [("", t("—（留空）", "— (empty)")), ("TRUE", t("是", "Yes")), ("FALSE", t("否", "No"))]
    parts = []
    matched = False
    for value, label in values:
        selected = " selected" if value == cur else ""
        if selected:
            matched = True
        parts.append(f'<option value="{value}"{selected}>{label}</option>')
    if cur and not matched:
        parts.append(f'<option value="{esc(current)}" selected>{esc(current)}{t("（当前值）", " (current)")}</option>')
    return f'<select name="field_{esc(field)}">{"".join(parts)}</select>'


def field_input(field: str, value) -> str:
    """按 template_schema 规格渲染单个详情页字段：枚举→下拉、布尔→是/否、其余→文本。"""
    spec = FIELD_SPECS.get(field)
    current = "" if value is None else str(value)
    validation = spec.get("validation") if spec else None
    if validation == "boolean":
        control = _bool_select(field, current)
    elif validation in ENUM_SELECT_VALIDATIONS and validation in ENUM_SOURCES:
        control = _enum_select(field, current, ENUM_SOURCES[validation])
    else:
        control = f'<input type="text" name="field_{esc(field)}" value="{esc(current)}">'
    star = ' <span class="req">*</span>' if spec and spec.get("required") else ""
    desc = spec.get("description") if spec else ""
    # 英文模式下隐藏中文字段说明
    hint = f'<small class="field-hint">{esc(desc)}</small>' if desc and current_lang() == "zh" else ""
    label = label_with_hint(field)
    return f"""
        <label>
          <span>{label}{star}</span>
          {control}
          {hint}
        </label>
        """


def label_with_hint(field: str) -> str:
    if field in GLOSSARY:
        return term_hint(field)
    if "Basic UDI-DI" in field:
        return esc(field).replace("Basic UDI-DI", term_hint("Basic UDI-DI"))
    if "UDI-DI" in field:
        return esc(field).replace("UDI-DI", term_hint("UDI-DI"))
    for term in ("EMDN Code", "Manufacturer SRN", "Authorised Representative SRN", "Issuing Entity", "Originally Placed on Market", "Device Status"):
        if term in field:
            return esc(field).replace(esc(term), term_hint(term))
    return esc(field)


def active_class(href: str, active_path: str) -> str:
    if not active_path:
        return ""
    if href == "/":
        return "active" if active_path == "/" else ""
    return "active" if active_path.startswith(href) else ""


def sample_banner(active_path: str) -> str:
    counts = sample_counts()
    total = int(counts.get("basic", 0) or 0) + int(counts.get("udi", 0) or 0)
    if total <= 0:
        return ""
    next_path = active_path or "/"
    return f"""
    <div class="sample-banner">
      <strong>{esc(t("当前包含示例数据", "Sample data is loaded"))}</strong>
      <span>{esc(t("仅供熟悉流程，请勿提交到 EUDAMED。", "Use it only for practice. Do not submit it to EUDAMED."))}</span>
      <form method="post" action="/sample-data/clear">
        <input type="hidden" name="next" value="{esc(next_path)}">
        <button class="button secondary" type="submit">{esc(t("清除示例数据", "Clear sample data"))}</button>
      </form>
    </div>
    """


def alert_block(message: str, level: str = "notice") -> str:
    if not message:
        return ""
    css_level = level if level in {"success", "error", "warning", "notice"} else alert_class(message)
    return f'<div class="alert {css_level}">{esc(message)}</div>'


def alert_class(message: str) -> str:
    text = str(message)
    if any(token in text for token in ("失败", "错误", "请选择", "缺少", "不一致", "无法", "fail", "error", "missing")):
        return "error"
    if any(token in text for token in ("成功", "完成", "success", "done")):
        return "success"
    return "notice"


def page(title: str, body: str, active_path: str = "") -> str:
    primary_items = [
        ("/", t("概览", "Overview")),
        ("/import", t("导入 Excel", "Import Excel")),
        ("/library", t("产品库", "Product Library")),
        ("/export", t("导出任务", "Export")),
        ("/history", t("导出历史", "Export History")),
    ]
    secondary_items = [
        ("/xsd-version", t("XSD 版本", "XSD Version")),
        ("/migrate-template", t("迁移模板", "Migrate Template")),
        ("/template-guide", t("模板指南", "Template Guide")),
        ("/ack", t("Response 解析", "Response Parser")),
        ("/download-template", t("下载模板", "Download Template")),
        ("/help", t("帮助", "Help")),
    ]
    primary_links = "".join(
        f'<a href="{href}" class="{active_class(href, active_path)}">{label}</a>'
        for href, label in primary_items
    )
    secondary_links = "".join(
        f'<a href="{href}" class="nav-secondary {active_class(href, active_path)}">{label}</a>'
        for href, label in secondary_items
    )
    next_path = active_path or "/"
    if current_lang() == "en":
        lang_link = f'<a class="lang-toggle" href="/set-lang?lang=zh&amp;next={quote(next_path, safe="")}">中文</a>'
    else:
        lang_link = f'<a class="lang-toggle" href="/set-lang?lang=en&amp;next={quote(next_path, safe="")}">EN</a>'
    nav = f"""
    <nav class="topbar">
      <div class="nav-group">{primary_links}</div>
      <div class="nav-group nav-group-end">{secondary_links}{lang_link}
        <form method="post" action="/shutdown" onsubmit="return confirm('{esc(t("确定退出本地工具？", "Exit the local tool?"))}');">
          <button class="nav-exit" type="submit">{esc(t("退出工具", "Exit"))}</button>
        </form>
      </div>
    </nav>
    """
    footer = f"""
    <footer class="site-footer">
      <div>{esc(t("工具版本", "Tool version"))} {esc(TOOL_VERSION_LABEL)}
      · {esc(t("最近更新", "Updated"))} {esc(TOOL_UPDATED)}</div>
      <div class="footer-copyright">© {esc(COPYRIGHT_YEAR)} {esc(COPYRIGHT_HOLDER)} ·
      {esc(t("保留所有权利", "All rights reserved"))} ·
      <a href="/help">{esc(t("免责声明", "Disclaimer"))}</a></div>
    </footer>
    """
    return f"""<!DOCTYPE html>
<html lang="{'en' if current_lang() == 'en' else 'zh-CN'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  {nav}
  {sample_banner(active_path)}
  <main class="shell">
    {body}
  </main>
  {footer}
  <script>
  function toggleChecks(formId, checked) {{
    var form = document.getElementById(formId);
    if (!form) return;
    var boxes = document.querySelectorAll('input[type=checkbox][form=' + formId + ']');
    if (boxes.length === 0) {{ boxes = form.querySelectorAll('input[type=checkbox]'); }}
    boxes.forEach(function (box) {{ box.checked = checked; }});
    updateSelectedCount(formId);
    syncExportUrl(formId);
  }}
  function selectedRecordCount(formId) {{
    var form = document.getElementById(formId);
    if (!form) return 0;
    var boxes = document.querySelectorAll('input[type=checkbox][form=' + formId + '][name=record_ids]:checked');
    if (boxes.length === 0) {{ boxes = form.querySelectorAll('input[type=checkbox][name=record_ids]:checked'); }}
    return boxes.length;
  }}
  function updateSelectedCount(formId) {{
    var count = selectedRecordCount(formId);
    document.querySelectorAll('[data-selected-count-for="' + formId + '"]').forEach(function (node) {{
      node.textContent = count;
    }});
  }}
  function requireLibrarySelection(mode) {{
    if (mode === 'selected' && selectedRecordCount('library-export') === 0) {{
      alert('{esc(t("请先勾选至少一条 UDI-DI，或使用“导出全部筛选结果”。", "Select at least one UDI-DI first, or use Export all filtered results."))}');
      return false;
    }}
    return true;
  }}
  function saveExportQuery(query) {{
    try {{
      if (query) sessionStorage.setItem('eudamed_export_query', query);
    }} catch (err) {{}}
  }}
  function loadExportQuery() {{
    try {{
      return sessionStorage.getItem('eudamed_export_query') || '';
    }} catch (err) {{
      return '';
    }}
  }}
  function addExportHidden(form, name, value) {{
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    input.className = 'js-export-state';
    form.appendChild(input);
  }}
  function copyCurrentExportState(form) {{
    if (!form || window.location.pathname !== '/export') return;
    if ((form.getAttribute('method') || 'get').toLowerCase() !== 'get') return;
    if ((form.getAttribute('action') || '/export') !== '/export') return;
    form.querySelectorAll('.js-export-state').forEach(function (node) {{ node.remove(); }});
    var exportForm = document.getElementById('export-form');
    if (!exportForm || form.id === 'export-form') return;
    var mode = exportForm.querySelector('input[name=selection_mode]:checked');
    if (mode) addExportHidden(form, 'selection_mode', mode.value);
    exportForm.querySelectorAll('input[name=record_ids]:checked').forEach(function (box) {{
      addExportHidden(form, 'record_ids', box.value);
    }});
  }}
  function updateExportNavLinks() {{
    var saved = loadExportQuery();
    if (!saved) return;
    document.querySelectorAll('a[href="/export"]').forEach(function (link) {{
      link.setAttribute('href', '/export?' + saved);
    }});
  }}
  function restoreExportPageIfNeeded() {{
    if (window.location.pathname !== '/export') return false;
    var params = new URLSearchParams(window.location.search);
    if (params.get('service_type')) {{
      saveExportQuery(params.toString());
      return false;
    }}
    var saved = loadExportQuery();
    if (saved) {{
      window.location.replace('/export?' + saved);
      return true;
    }}
    return false;
  }}
  function syncExportUrl(formId) {{
    if (formId !== 'export-form') return;
    var form = document.getElementById(formId);
    if (!form || window.location.pathname !== '/export') return;
    var params = new URLSearchParams(window.location.search);
    ['service_type', 'q', 'state', 'legislation', 'change_type', 'freshness_filter', 'srn'].forEach(function (name) {{
      var field = form.querySelector('[name="' + name + '"]');
      if (!field) return;
      if (field.value) params.set(name, field.value); else params.delete(name);
    }});
    params.delete('record_ids');
    form.querySelectorAll('input[name=record_ids]:checked').forEach(function (box) {{
      params.append('record_ids', box.value);
    }});
    var mode = form.querySelector('input[name=selection_mode]:checked');
    if (mode) params.set('selection_mode', mode.value);
    var query = params.toString();
    saveExportQuery(query);
    history.replaceState(null, '', '/export' + (query ? '?' + query : ''));
  }}
  document.addEventListener('change', function (event) {{
    var form = event.target.form;
    if (!form) return;
    if (form.id === 'library-export' || form.id === 'export-form') {{
      updateSelectedCount(form.id);
      syncExportUrl(form.id);
    }}
  }});
  document.addEventListener('submit', function (event) {{
    copyCurrentExportState(event.target);
  }});
  document.addEventListener('DOMContentLoaded', function () {{
    if (restoreExportPageIfNeeded()) return;
    updateExportNavLinks();
    updateSelectedCount('library-export');
    updateSelectedCount('export-form');
    syncExportUrl('export-form');
  }});
  </script>
</body>
</html>"""


def dashboard(
    stats: dict,
    imports: list,
    exports: list,
    xsd_report: dict | None = None,
    srn_summary: list[dict] | None = None,
) -> str:
    xsd_report = xsd_report or {"tool_version": SCHEMA_VERSION, "local_xsd_version": "", "status": "unknown"}
    import_cards = "".join(
        f"<li><strong>{esc(row['filename'])}</strong><span>{esc(display_time(row['imported_at']))}</span></li>" for row in imports
    ) or f"<li>{t('还没有导入记录', 'No imports yet')}</li>"
    export_cards = "".join(
        f"<li><strong>{esc(SERVICE_LABELS.get(row['service_type'], row['service_type']))}</strong>"
        f"<span>{esc(display_time(row['created_at']))}</span></li>"
        for row in exports
    ) or f"<li>{t('还没有导出记录', 'No exports yet')}</li>"
    quick_start = quick_start_card() if int(stats.get("basic_count", 0) or 0) == 0 and int(stats.get("udi_count", 0) or 0) == 0 else ""
    body = f"""
    <section class="hero">
      <div>
        <h1>{t('本地运行的 EUDAMED 公开测试版', 'EUDAMED helper — Public Beta')}</h1>
        <p>{t('先导入 Excel 总表，在网页端管理记录，再按官方 service 批量生成 XML。数据默认保存在本机 SQLite。',
              'Import the Excel workbook, manage records in the browser, then generate XML per official service. Data stays in a local SQLite file.')}</p>
      </div>
      <a class="button primary" href="/import">{t('开始导入 Excel', 'Start importing Excel')}</a>
    </section>
    {quick_start}
    <section class="grid cards">
      <article class="card"><h2>Basic UDI-DI</h2><p>{stats['basic_count']}</p></article>
      <article class="card"><h2>UDI-DI</h2><p>{stats['udi_count']}</p></article>
      <article class="card" title="{t('草稿，或导入后有变更、尚未生成 XML 的 UDI-DI 数量', 'Draft UDI-DIs, or UDI-DIs changed on import and not yet exported as XML')}">
        <h2>{t('待导出 UDI-DI', 'UDI-DI to export')}</h2><p>{stats['pending_count']}</p>
      </article>
      <article class="card"><h2>{t('导出历史', 'Export history')}</h2><p>{stats['export_count']}</p></article>
    </section>
    {actor_panel(srn_summary)}
    {support_status_panel(xsd_report)}
    <section class="grid columns">
      <article class="panel">
        <h2>{t('最近导入', 'Recent imports')}</h2>
        <ul class="simple-list">{import_cards}</ul>
      </article>
      <article class="panel">
        <h2>{t('最近导出', 'Recent exports')}</h2>
        <ul class="simple-list">{export_cards}</ul>
      </article>
    </section>
    """
    return page(t("概览", "Overview"), body, "/")


def quick_start_card() -> str:
    return f"""
    <section class="panel quick-start">
      <h2>{t('快速开始', 'Quick start')}</h2>
      <div class="grid cards quick-steps">
        <article class="card"><h3>1. {t('下载模板', 'Download template')}</h3><p>{t('先用 Excel 维护主数据。', 'Maintain master data in Excel first.')}</p></article>
        <article class="card"><h3>2. {t('导入并核对', 'Import and check')}</h3><p>{t('系统会显示新增、更新、错误和警告。', 'The tool shows created, updated, errors and warnings.')}</p></article>
        <article class="card"><h3>3. {t('选择 service 导出', 'Choose service and export')}</h3><p>{t('先预检，再生成 XML/ZIP。', 'Pre-check first, then generate XML/ZIP.')}</p></article>
      </div>
      <div class="toolbar">
        <a class="button primary" href="/download-template">{t('下载模板', 'Download template')}</a>
        <form method="post" action="/sample-data/load">
          <button class="button secondary" type="submit">{t('载入示例数据', 'Load sample data')}</button>
        </form>
        <a class="button" href="/import">{t('去导入 Excel', 'Go to import')}</a>
        <a class="button" href="/template-guide">{t('查看模板怎么填', 'Open template guide')}</a>
      </div>
    </section>
    """


def actor_panel(srn_summary: list[dict] | None) -> str:
    rows = [item for item in (srn_summary or []) if item.get("srn")]
    if not rows:
        return ""
    items = "".join(
        f"""
        <li>
          <span><strong>{esc(item['srn'])}</strong>
            <span class="muted"> · Basic {esc(item['basic_count'])} / UDI-DI {esc(item['udi_count'])}</span>
          </span>
          <a href="/library?srn={quote(item['srn'], safe='')}">{t('在产品库查看', 'Open in library')}</a>
        </li>
        """
        for item in rows
    )
    return f"""
    <section class="panel">
      <h2>{t('制造商 / Actor', 'Manufacturer / Actor')}</h2>
      <p class="muted">{t('按导入 Excel 中的 Manufacturer SRN 分组。一家公司若有多个 actor（如 System/Procedure Pack Producer），可在产品库按 SRN 切换查看。',
                          'Grouped by the Manufacturer SRN from the imported Excel. If a company has several actors (e.g. System/Procedure Pack Producer), switch between them by SRN in the product library.')}</p>
      <ul class="simple-list">{items}</ul>
    </section>
    """


def support_status_panel(xsd_report: dict) -> str:
    supported = "".join(
        f"<li><strong>{esc(service_task(item))}</strong><br><span class='muted'>{esc(item['label'])}</span><br><span class='muted'>{esc(service_text(item, 'scope'))}</span></li>"
        for item in SUPPORTED_SERVICES.values()
    )
    unavailable = "".join(
        f"<li><strong>{esc(item['label'])}</strong> <span class='badge muted-badge'>{esc(service_text(item, 'status'))}</span></li>"
        for item in UNAVAILABLE_SERVICES
    )
    return f"""
    <section class="panel">
      <h2>{t('EUDAMED 支持状态', 'EUDAMED support status')}</h2>
      {xsd_panel(xsd_report)}
      <div class="grid columns">
        <article>
          <h3>{t('当前工具可生成 XML 的 service', 'Services this tool can generate XML for')}</h3>
          <ul>{supported}</ul>
        </article>
        <article>
          <h3>{t('暂未开放', 'Not available yet')}</h3>
          <ul>{unavailable}</ul>
        </article>
      </div>
    </section>
    """


def import_page(message: str = "", result: dict | None = None, message_level: str = "notice") -> str:
    alert = alert_block(message, message_level)
    import_notes = f"""
    <details class="advanced-edit">
      <summary>{t('填写须知（点击展开）', 'Filling checklist (click to expand)')}</summary>
      <ul>
        <li>{t('确认 UDI/GTIN/Reference/SRN 等编码按文本维护，没有科学计数法或丢失前导 0。', 'Confirm UDI/GTIN/Reference/SRN codes are maintained as text, with no scientific notation or lost leading zeros.')}</li>
        <li>{t(f'使用当前 {TEMPLATE_VERSION} 模板；旧模板或客户原始 Excel 请先走迁移/映射。', f'Use the current {TEMPLATE_VERSION} template; migrate/map old templates or customer source Excel first.')}</li>
        <li>{t('Market Info：同一 UDI-DI 可有多个 made available 国家，但 Originally Placed on Market 必须且只能有一个 TRUE。', 'Market Info: one UDI-DI may have multiple made available countries, but Originally Placed on Market must have exactly one TRUE.')}</li>
        <li>{t('国家/市场信息填报错误时，优先通过 EUDAMED update/create new version 纠正，不要默认删除 UDI-DI 重建。', 'Market information errors should be corrected through EUDAMED update/create new version where possible; do not default to deleting and re-registering the UDI-DI.')}</li>
      </ul>
    </details>
    """
    details = ""
    if result:
        errors = result["validation"]["errors"]
        warnings = result["validation"]["warnings"]
        change_summary = result.get("change_summary", {})
        changes = result.get("changes", [])
        change_cards = f"""
        <section class="grid cards">
          <article class="card"><h2>{t('新增', 'Created')}</h2><p>{change_summary.get('created', 0)}</p></article>
          <article class="card"><h2>{t('已更新', 'Updated')}</h2><p>{change_summary.get('updated', 0)}</p></article>
          <article class="card"><h2>{t('未变化', 'Unchanged')}</h2><p>{change_summary.get('unchanged', 0)}</p></article>
          <article class="card"><h2>{t('错误', 'Errors')}</h2><p>{len(errors)}</p></article>
        </section>
        """
        change_rows = "".join(_import_change_row(item) for item in changes[:300])
        if not change_rows:
            change_rows = f'<tr><td colspan="6">{t("没有可展示的入库记录。", "No records to show.")}</td></tr>'
        error_rows = "".join(
            f"<li>{esc(item.get('sheet'))} {t('第', 'row')} {esc(item.get('row'))} {esc(item.get('field'))}: {esc(item.get('message'))}</li>"
            for item in errors[:50]
        ) or f"<li>{t('无', 'None')}</li>"
        warning_rows = "".join(
            f"<li>{esc(item.get('sheet'))} {t('第', 'row')} {esc(item.get('row'))} {esc(item.get('field'))}: {esc(item.get('message'))}</li>"
            for item in warnings[:50]
        ) or f"<li>{t('无', 'None')}</li>"
        details = f"""
        <section class="panel">
          <h2>{t('导入结果', 'Import result')}</h2>
          <p>Basic UDI-DI: {result['summary']['basic_count']} · UDI-DI: {result['summary']['udi_count']}</p>
          {change_cards}
          <h3>{t('差异报告', 'Change report')}</h3>
          <div class="table-wrap"><table>
            <thead><tr>
              <th>{t('类型', 'Type')}</th><th>{t('动作', 'Action')}</th><th>{t('编码', 'Code')}</th>
              <th>{t('关联 Basic', 'Related Basic')}</th><th>{t('Excel 行', 'Excel row')}</th><th>{t('变化字段', 'Changed fields')}</th>
            </tr></thead>
            <tbody>{change_rows}</tbody>
          </table></div>
          <div class="grid columns">
            <article><h3>{t('错误', 'Errors')}</h3><ul>{error_rows}</ul></article>
            <article><h3>{t('警告', 'Warnings')}</h3><ul>{warning_rows}</ul></article>
          </div>
          <p><a class="button primary" href="/library">{t('进入产品库', 'Open product library')}</a></p>
        </section>
        """
    body = f"""
    <section class="panel narrow">
      <h1>{t('导入产品总表', 'Import product workbook')}</h1>
      <p>{t('上传最新版 Excel template。Excel 是主维护文件；本地库用于批量校验、筛选、选择 service 和导出 XML。',
            'Upload the latest Excel template. The Excel file is the master data; the local database is for bulk validation, filtering, choosing a service and exporting XML.')}</p>
      {alert}
      <form action="/import" method="post" enctype="multipart/form-data" class="stack">
        <input type="file" name="workbook" accept=".xlsx" required>
        <button class="button primary" type="submit">{t('开始导入', 'Start import')}</button>
      </form>
      {import_notes}
    </section>
    {details}
    """
    return page(t("导入 Excel", "Import Excel"), body, "/import")


def migrate_template_page(message: str = "", result: dict | None = None, message_level: str = "notice") -> str:
    alert = alert_block(message, message_level)
    result_html = ""
    if result:
        report = result.get("report") or {}
        copied = report.get("copied_rows") or {}
        unmapped = report.get("unmapped_headers") or {}
        copied_rows = "".join(
            f"<tr><td>{esc(sheet)}</td><td>{esc(count)}</td></tr>"
            for sheet, count in sorted(copied.items())
        ) or f"<tr><td colspan='2'>{t('没有自动搬迁的数据行', 'No rows were automatically migrated')}</td></tr>"
        unmapped_rows = "".join(
            f"<tr><td>{esc(sheet)}</td><td>{esc(', '.join(headers))}</td></tr>"
            for sheet, headers in sorted(unmapped.items())
            if headers
        ) or f"<tr><td colspan='2'>{t('无', 'None')}</td></tr>"
        download = ""
        if result.get("output_filename"):
            download = f'<p><a class="button primary" href="/download/{esc(result["output_filename"])}">{t("下载迁移后的新版模板", "Download migrated current template")}</a></p>'
        result_html = f"""
        <section class="panel">
          <h2>{t('迁移结果', 'Migration result')}</h2>
          {download}
          <p class="muted">{t('识别模式', 'Detected mode')}: {esc(report.get('mode', ''))}</p>
          <div class="grid columns">
            <article>
              <h3>{t('已搬迁行数', 'Migrated rows')}</h3>
              <div class="table-wrap"><table><thead><tr><th>Sheet</th><th>{t('行数', 'Rows')}</th></tr></thead><tbody>{copied_rows}</tbody></table></div>
            </article>
            <article>
              <h3>{t('未自动映射字段', 'Unmapped source headers')}</h3>
              <div class="table-wrap"><table><thead><tr><th>Sheet</th><th>{t('字段', 'Headers')}</th></tr></thead><tbody>{unmapped_rows}</tbody></table></div>
            </article>
          </div>
          <p class="muted">{t('迁移工具只复制能明确匹配的字段；客户自定义字段不会被猜测映射。下载后请先检查 Migration Report sheet，再导入系统。', 'The migrator copies only clearly matched fields. Custom customer columns are not guessed. Check the Migration Report sheet before importing the result.')}</p>
        </section>
        """
    body = f"""
    <section class="panel narrow">
      <h1>{t('迁移到当前模板', 'Migrate to current template')}</h1>
      <p>{t(f'用于把旧版 EUDAMED template 或客户已填写的旧模板搬到当前最新版 {TEMPLATE_VERSION} 模板，保留数据并更新说明、下拉和帮助页。', f'Use this to move an older EUDAMED template or a filled workbook into the latest current {TEMPLATE_VERSION} template, preserving data while refreshing notes, validations and help sheets.')}</p>
      <p class="muted">{t('支持 .xlsx。旧 .xls 请先用 Excel/WPS 另存为 .xlsx。完全自定义客户清单会生成映射报告，但不会强行猜字段。', 'Supports .xlsx. Save old .xls files as .xlsx first in Excel/WPS. Fully custom customer lists produce a mapping report, but fields are not guessed.')}</p>
      {alert}
      <form action="/migrate-template" method="post" enctype="multipart/form-data" class="stack">
        <input type="file" name="workbook" accept=".xlsx" required>
        <button class="button primary" type="submit">{t('生成新版模板', 'Generate current template')}</button>
      </form>
    </section>
    {result_html}
    """
    return page(t("迁移模板", "Migrate Template"), body, "/migrate-template")


def _import_change_row(item: dict) -> str:
    detail_path = "/basic/" if item.get("entity_type") == "basic" else "/udi/"
    fields = ", ".join(item.get("changed_fields", [])) or t("无", "None")
    return f"""
    <tr>
      <td>{esc(_entity_label(item.get('entity_type')))}</td>
      <td>{change_badge(item.get('action'))}</td>
      <td><a href="{detail_path}{esc(item.get('record_id'))}">{esc(item.get('code'))}</a></td>
      <td>{esc(item.get('related_code'))}</td>
      <td>{esc(item.get('row_number'))}</td>
      <td>{esc(fields)}</td>
    </tr>
    """


def library_page(records: list[dict], filters: dict, srn_options: list[str] | None = None) -> str:
    rows = []
    for item in records:
        payload = item["payload"]
        basic_payload = item.get("basic_payload") or {}
        product_name = _product_name(item)
        spec = payload.get("Additional Description") or basic_payload.get("Device Name/Model") or basic_payload.get("Device Model", "")
        reference = payload.get("Reference Number", "")
        sample = bool(item.get("is_sample"))
        rows.append(
            f"""
            <tr class="{'row-sample' if sample else ''}">
              <td><input type="checkbox" form="library-export" name="record_ids" value="{item['id']}"></td>
              <td>{sample_badge() if sample else ''}<a href="/udi/{item['id']}">{esc(product_name or item['udi_code'])}</a><br><span class="muted">{esc(spec)}</span></td>
              <td>{esc(reference)}</td>
              <td><a href="/basic-code/{quote(item['basic_code'], safe='')}">{esc(item['basic_code'])}</a><br><span class="muted">{esc(item['udi_code'])}</span></td>
              <td>{esc(basic_payload.get('Applicable Legislation', ''))}</td>
              <td>{state_badge(item['state'])}<br>{change_badge(item.get('last_change_type'))}</td>
              <td><span class="muted">{t('首次', 'First')}</span> {esc(display_time(item.get('first_imported_at')))}<br><span class="muted">{t('最近导入', 'Last import')}</span> {esc(display_time(item.get('last_imported_at')))}<br><span class="muted">{t('最近更新', 'Last update')}</span> {esc(display_time(item.get('last_changed_at')))}</td>
            </tr>
            """
        )
    if rows:
        table = "".join(rows)
    elif any(filters.get(key) for key in ("query", "state", "legislation", "change_type", "freshness_filter", "srn")):
        table = f'<tr><td colspan="7">{t("没有符合条件的记录。", "No records match the filter.")} <a href="/library">{t("清除筛选", "Clear filters")}</a></td></tr>'
    else:
        table = f'<tr><td colspan="7"><div class="empty-state">{t("还没有产品记录。先下载模板填写，再导入 Excel。", "No product records yet. Download the template, fill it in, then import Excel.")} <a class="button" href="/download-template">{t("下载模板", "Download template")}</a> <a class="button primary" href="/import">{t("导入 Excel", "Import Excel")}</a></div></td></tr>'
    body = f"""
    <section class="panel">
      <h1>{t('产品库', 'Product Library')}</h1>
      <p class="muted">{t('这里管理本地库中的 UDI-DI。搜索会匹配产品名、Reference、Basic UDI-DI、UDI-DI 和备注；可按 Manufacturer SRN 切换不同 actor 的产品。',
                          'Manage local UDI-DI records here. Search matches product name, Reference, Basic UDI-DI, UDI-DI and notes; switch between actors by Manufacturer SRN.')}</p>
      {filter_form('/library', filters, srn_options)}
      <form id="library-export" method="get" action="/export" class="toolbar">
        <select name="service_type" required>{service_options("")}</select>
        <input type="hidden" name="q" value="{esc(filters.get('query', ''))}">
        <input type="hidden" name="state" value="{esc(filters.get('state', ''))}">
        <input type="hidden" name="legislation" value="{esc(filters.get('legislation', ''))}">
        <input type="hidden" name="change_type" value="{esc(filters.get('change_type', ''))}">
        <input type="hidden" name="freshness_filter" value="{esc(filters.get('freshness_filter', ''))}">
        <input type="hidden" name="srn" value="{esc(filters.get('srn', ''))}">
        <button class="button" type="button" onclick="toggleChecks('library-export', true)">{t('全选', 'Select all')}</button>
        <button class="button" type="button" onclick="toggleChecks('library-export', false)">{t('取消勾选', 'Clear')}</button>
        <button class="button primary" type="submit" name="selection_mode" value="selected" onclick="return requireLibrarySelection('selected')">{t('导出勾选记录', 'Export checked records')} (<span data-selected-count-for="library-export">0</span>)</button>
        <button class="button secondary" type="submit" name="selection_mode" value="filtered">{t('导出全部筛选结果', 'Export all filtered results')}</button>
      </form>
      <p class="muted">{t('先选择 EUDAMED service；“导出勾选记录”只带走已勾选行，“导出全部筛选结果”会按当前筛选条件导出全部匹配记录。',
                          'Choose an EUDAMED service first. Export checked records uses only ticked rows; Export all filtered results uses every row matching the current filters.')}</p>
      <div class="table-wrap"><table>
        <thead>
          <tr><th>{t('选择', 'Select')}</th><th>{t('产品/规格', 'Product / spec')}</th><th>Reference</th><th>{term_hint('Basic UDI-DI')} / {term_hint('UDI-DI')}</th><th>{t('法规', 'Legislation')}</th><th>{t('状态', 'State')}</th><th>{t('日期', 'Dates')}</th></tr>
        </thead>
        <tbody>{table}</tbody>
      </table></div>
    </section>
    """
    return page(t("产品库", "Product Library"), body, "/library")


def _advanced_json_block(sections: list[tuple[str, str, int, str]]) -> str:
    """sections: (name, label, rows, json_text)。统一折叠为「高级编辑」。"""
    fields = "".join(
        f"""
        <label><span>{esc(label)}</span>
          <textarea name="{esc(name)}" rows="{rows}">{esc(text)}</textarea>
        </label>
        """
        for name, label, rows, text in sections
    )
    return f"""
    <details class="advanced-edit">
      <summary>{t('高级编辑（JSON）—— 建议优先在 Excel 模板中维护这些明细', 'Advanced edit (JSON) — prefer maintaining these details in the Excel template')}</summary>
      <p class="muted">{t('这些明细数据请优先在 Excel template 中修改后重新导入；此处仅供临时排错，格式必须是合法 JSON。',
                          'Edit these detail rows in the Excel template and re-import; this area is for quick fixes only and must contain valid JSON.')}</p>
      {fields}
    </details>
    """


def freshness_badge(freshness: dict | None) -> str:
    status = (freshness or {}).get("status", "")
    labels = {
        "never_exported": t("从未导出", "Never exported"),
        "changed_since_export": t("导出后有更新", "Changed since export"),
        "up_to_date": t("已导出且未变化", "Exported and unchanged"),
    }
    if not status:
        return ""
    return f'<span class="badge freshness-{esc(status)}">{esc(labels.get(status, status))}</span>'


def record_history_block(changes: list[dict] | None) -> str:
    if not changes:
        return ""
    rows = []
    for item in changes[:100]:
        fields = ", ".join(item.get("changed_fields") or []) or t("无", "None")
        rows.append(
            f"""
            <tr>
              <td>{esc(display_time(item.get('imported_at') or item.get('created_at')))}</td>
              <td>{change_badge(item.get('action'))}</td>
              <td>{esc(item.get('filename', ''))}</td>
              <td>{esc(item.get('row_number', ''))}</td>
              <td>{esc(fields)}</td>
            </tr>
            """
        )
    return f"""
    <section class="panel">
      <h2>{t('导入变更历史', 'Import change history')}</h2>
      <div class="table-wrap"><table>
        <thead><tr><th>{t('时间', 'Time')}</th><th>{t('动作', 'Action')}</th><th>{t('文件', 'File')}</th><th>{t('Excel 行', 'Excel row')}</th><th>{t('变化字段', 'Changed fields')}</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table></div>
    </section>
    """


def basic_detail(record: dict, message: str = "", message_level: str = "notice", freshness: dict | None = None, changes: list[dict] | None = None) -> str:
    form_fields = "".join(field_input(field, record["payload"].get(field, "")) for field in BASIC_FIELDS)
    cmr_json = json.dumps(record["cmr_rows"], ensure_ascii=False, indent=2)
    cert_json = json.dumps(record.get("cert_rows", []), ensure_ascii=False, indent=2)
    advanced = _advanced_json_block(
        [
            ("cmr_json", "CMR Substances JSON", 8, cmr_json),
            ("cert_json", "Device Certificates JSON", 8, cert_json),
        ]
    )
    body = f"""
    <section class="panel">
      <h1>{t('Basic UDI-DI 详情', 'Basic UDI-DI detail')}</h1>
      <p>{sample_badge() if record.get('is_sample') else ''}Basic UDI-DI Code: <strong>{esc(record['basic_code'])}</strong></p>
      <p>{state_badge(record['state'])} {change_badge(record.get('last_change_type'))} {freshness_badge(freshness)}</p>
      {message_block(message, message_level)}
      <form action="/basic/{record['id']}" method="post" class="stack">
        <div class="form-grid">{form_fields}</div>
        <label><span>{t('当前 EUDAMED 版本号（更新用）', 'Current EUDAMED version (for updates)')}</span><input type="text" name="version" value="{esc(record['version'])}"></label>
        <label><span>{t('本地状态', 'Local state')}</span>{state_select(record['state'])}</label>
        <label><span>{t('备注', 'Notes')}</span><textarea name="notes">{esc(record['notes'])}</textarea></label>
        {advanced}
        <button class="button primary" type="submit">{t('保存', 'Save')}</button>
      </form>
    </section>
    {record_history_block(changes)}
    """
    return page(t("Basic UDI-DI 详情", "Basic UDI-DI detail"), body, "/library")


def udi_detail(record: dict, message: str = "", message_level: str = "notice", freshness: dict | None = None, changes: list[dict] | None = None) -> str:
    form_fields = "".join(field_input(field, record["payload"].get(field, "")) for field in UDI_FIELDS)

    def _dump(value):
        return json.dumps(value, ensure_ascii=False, indent=2)

    advanced = _advanced_json_block(
        [
            ("market_json", "Market Information JSON", 8, _dump(record["market_rows"])),
            ("trade_name_json", "Trade Names JSON", 6, _dump(record.get("trade_name_rows", []))),
            ("warning_json", "Critical Warnings JSON", 6, _dump(record["warning_rows"])),
            ("storage_json", "Storage Conditions JSON", 6, _dump(record["storage_rows"])),
            ("package_json", "Package Information JSON", 6, _dump(record["package_rows"])),
            ("clinical_size_json", "Clinical Sizes JSON", 6, _dump(record.get("clinical_size_rows", []))),
            ("annex_xvi_json", "Annex XVI Purposes JSON", 6, _dump(record.get("annex_xvi_rows", []))),
        ]
    )
    body = f"""
    <section class="panel">
      <h1>{t('UDI-DI 详情', 'UDI-DI detail')}</h1>
      <p>{sample_badge() if record.get('is_sample') else ''}UDI-DI: <strong>{esc(record['udi_code'])}</strong></p>
      <p>Parent Basic UDI-DI: <a href="/basic-code/{quote(record['basic_code'], safe='')}">{esc(record['basic_code'])}</a></p>
      <p>{state_badge(record['state'])} {change_badge(record.get('last_change_type'))} {freshness_badge(freshness)}</p>
      {message_block(message, message_level)}
      <form action="/udi/{record['id']}" method="post" class="stack">
        <div class="form-grid">{form_fields}</div>
        <label><span>{t('当前 EUDAMED 版本号（更新用）', 'Current EUDAMED version (for updates)')}</span><input type="text" name="version" value="{esc(record['version'])}"></label>
        <label><span>{t('本地状态', 'Local state')}</span>{state_select(record['state'])}</label>
        <label><span>{t('备注', 'Notes')}</span><textarea name="notes">{esc(record['notes'])}</textarea></label>
        {advanced}
        <button class="button primary" type="submit">{t('保存', 'Save')}</button>
      </form>
    </section>
    {record_history_block(changes)}
    """
    return page(t("UDI-DI 详情", "UDI-DI detail"), body, "/library")


def export_page(
    service_type: str,
    records: list[dict],
    result: dict | None = None,
    filters: dict | None = None,
    xsd_report: dict | None = None,
    total_filtered: int = 0,
    selected_ids: list[int] | None = None,
    srn_options: list[str] | None = None,
    selection_mode: str = "selected",
) -> str:
    filters = filters or {"query": "", "state": "", "legislation": "", "change_type": "", "freshness_filter": "", "srn": ""}
    xsd_report = xsd_report or {}
    selected_id_set = {int(item) for item in (selected_ids or [])}
    selection_mode = "filtered" if selection_mode == "filtered" else "selected"
    entity_type = "basic" if service_type == "Basic_UDI.PATCH" else "udi"
    preview = export_result_panel(result, service_type) if result else ""
    step_state = export_step_state(service_type, result)
    xsd = xsd_panel(xsd_report)
    steps = f"""
      <div class="steps">
        {step_badge("service", t("1 选择 service", "1 Choose service"), step_state)}
        {step_badge("filter", t("2 筛选记录", "2 Filter records"), step_state)}
        {step_badge("preflight", t("3 预检版本和字段", "3 Pre-check version & fields"), step_state)}
        {step_badge("generated", t("4 生成 XML", "4 Generate XML"), step_state)}
        {step_badge("generated", t("5 按指引上传", "5 Upload as guided"), step_state)}
      </div>
    """
    service_picker = f"""
      <form method="get" action="/export" class="filters">
        <select name="service_type">{service_options(service_type)}</select>
        {filter_controls(filters, srn_options)}
        <button class="button" type="submit">{t('载入记录', 'Load records')}</button>
      </form>
    """

    if not service_type:
        body = f"""
    <section class="panel">
      <h1>{t('导出任务', 'Export task')}</h1>
      {steps}
      {alert_block(t('请先在下方选择一个 EUDAMED service，再载入并勾选要导出的记录。', 'Choose an EUDAMED service below first, then load and select the records to export.'), "notice")}
      {bulk_limit_notice()}
      {xsd}
      {service_picker}
      {service_wizard()}
    </section>
    """
        return page(t("导出任务", "Export"), body, "/export")

    record_rows = []
    for item in records:
        code = item.get("udi_code") or item.get("basic_code")
        detail_link = f"/udi/{item['id']}" if item.get("udi_code") else f"/basic/{item['id']}"
        secondary = item.get("basic_code", "")
        product = _product_name(item) if item.get("udi_code") else item["payload"].get("Device Name/Model", "")
        sample = bool(item.get("is_sample"))
        record_rows.append(
            f"""
            <tr class="{'row-sample' if sample else ''}">
              <td><input type="checkbox" name="record_ids" value="{item['id']}"{" checked" if int(item["id"]) in selected_id_set else ""}></td>
              <td>{sample_badge() if sample else ''}<a href="{detail_link}">{esc(code)}</a><br><span class="muted">{esc(product)}</span></td>
              <td>{esc(secondary)}</td>
              <td>{state_badge(item['state'])}</td>
              <td>{esc(item['version']) or f'<span class="muted">{t("无", "none")}</span>'}</td>
              <td>{change_badge(item.get('last_change_type'))}</td>
            </tr>
            """
        )
    table = "".join(record_rows) or f'<tr><td colspan="6"><div class="empty-state">{t("没有可导出的记录。请检查筛选条件，或先导入 Excel。", "No records to export. Check filters or import Excel first.")} <a class="button" href="/library">{t("去产品库", "Open library")}</a> <a class="button primary" href="/import">{t("导入 Excel", "Import Excel")}</a></div></td></tr>'
    service = SUPPORTED_SERVICES.get(service_type, SUPPORTED_SERVICES["DEVICE.POST"])
    unavailable = "".join(
        f"<li><strong>{esc(item['label'])}</strong><br><span class='muted'>{esc(service_text(item, 'status'))}</span></li>"
        for item in UNAVAILABLE_SERVICES
    )
    body = f"""
    <section class="panel">
      <h1>{t('导出任务', 'Export task')}</h1>
      {steps}
      <div class="grid columns">
        <article>
          <h2>{t('当前 service', 'Current service')}</h2>
          <p><strong>{esc(service_task(service))}</strong></p>
          <p class="muted">{term_hint(service_type)} · {esc(service['label'])}</p>
          <p>{esc(service_text(service, 'scope'))}</p>
          <p><strong>{t('要求：', 'Requires: ')}</strong>{esc(service_text(service, 'requires'))}</p>
        </article>
        <article>
          <h2>{t('暂未开放', 'Not available yet')}</h2>
          <ul>{unavailable}</ul>
        </article>
      </div>
      {bulk_limit_notice()}
      {xsd}
      {service_picker}
      <form id="export-form" method="post" action="/export#result" class="stack">
        <input type="hidden" name="service_type" value="{esc(service_type)}">
        {hidden_filters(filters)}
        <div class="selection-bar">
          <label><input type="radio" name="selection_mode" value="selected"{" checked" if selection_mode == "selected" else ""}> {t('只导出下方勾选记录', 'Export only the rows checked below')} (<span data-selected-count-for="export-form">0</span>)</label>
          <label><input type="radio" name="selection_mode" value="filtered"{" checked" if selection_mode == "filtered" else ""}> {t('导出全部筛选结果', 'Export all filtered results')}（{total_filtered}）</label>
          <button class="button" type="button" onclick="toggleChecks('export-form', true)">{t('全选', 'Select all')}</button>
          <button class="button" type="button" onclick="toggleChecks('export-form', false)">{t('取消勾选', 'Clear')}</button>
        </div>
        <div class="table-wrap"><table>
          <thead>
            <tr><th>{t('选择', 'Select')}</th><th>{t('编码/产品', 'Code / product')}</th><th>{'Parent Basic' if entity_type == 'udi' else 'Basic'}</th><th>{t('本地状态', 'Local state')}</th><th>{t('版本号', 'Version')}</th><th>{t('最近变化', 'Last change')}</th></tr>
          </thead>
          <tbody>{table}</tbody>
        </table></div>
        <div class="toolbar">
          <button class="button" type="submit" name="action" value="preflight">{t('只做预检', 'Pre-check only')}</button>
          <button class="button primary" type="submit" name="action" value="export">{t('生成 XML', 'Generate XML')}</button>
        </div>
      </form>
    </section>
    {preview}
    """
    return page(t("导出任务", "Export"), body, "/export")


def export_result_panel(result: dict, service_type: str) -> str:
    errors = "".join(f"<li>{esc(item)}</li>" for item in result.get("errors", [])) or f"<li>{t('无', 'None')}</li>"
    warnings = "".join(f"<li>{esc(item)}</li>" for item in result.get("warnings", [])) or f"<li>{t('无', 'None')}</li>"
    selected_count = result.get("selected_count", len(result.get("codes", [])))
    download = export_downloads(result)
    guidance = upload_guidance(service_type) if result.get("file_path") else ""
    batches = export_batch_table(result.get("files") or result.get("batches") or [])
    freshness = freshness_summary_block(result.get("freshness_summary") or {})
    title = t("预检结果", "Pre-check result") if result.get("action") == "preflight" else t("导出结果", "Export result")
    return f"""
    <section class="panel" id="result">
      <h2>{title}</h2>
      <p>Service: <strong>{esc(result['service_type'])}</strong> · {t('选择记录', 'Selected records')}: <strong>{esc(selected_count)}</strong></p>
      {freshness}
      <div class="grid columns">
        <article><h3>{t('错误', 'Errors')}</h3><ul>{errors}</ul></article>
        <article><h3>{t('警告', 'Warnings')}</h3><ul>{warnings}</ul></article>
      </div>
      {batches}
      {download}
      {guidance}
    </section>
    """


def service_wizard() -> str:
    options = "".join(
        f'<option value="{esc(key)}">{esc(service_task(service))} — {esc(key)}</option>'
        for key, service in SUPPORTED_SERVICES.items()
    )
    cards = "".join(
        f"""
        <div class="wizard-result" data-service="{esc(key)}" hidden>
          <strong>{esc(service_task(service))}</strong>
          <span class="muted"> — {esc(key)}</span>
          <p>{esc(service_text(service, 'scope'))}</p>
          <a class="button primary" href="/export?service_type={esc(key)}">{t('用这个 service', 'Use this service')}</a>
        </div>
        """
        for key, service in SUPPORTED_SERVICES.items()
    )
    return f"""
    <section class="panel inset service-wizard">
      <h2>{t('我该选哪个 service？', 'Which service should I choose?')}</h2>
      <div class="wizard-grid">
        <label><span>{t('这是新注册还是修改已注册数据？', 'New registration or update existing data?')}</span>
          <select id="wiz-kind">
            <option value="new">{t('新注册 / 新增', 'New registration / add')}</option>
            <option value="update">{t('修改已注册数据', 'Update existing data')}</option>
          </select>
        </label>
        <label><span>{t('具体任务', 'Specific task')}</span>
          <select id="wiz-task">
            {options}
          </select>
        </label>
      </div>
      <p class="muted">{t('如果不确定，请先用 Playground 测试环境验证。', 'If unsure, validate in the Playground test environment first.')}</p>
      {cards}
    </section>
    <script>
    (function () {{
      var kind = document.getElementById('wiz-kind');
      var task = document.getElementById('wiz-task');
      if (!kind || !task) return;
      var newTasks = ['DEVICE.POST', 'UDI_DI.POST'];
      var updateTasks = ['Basic_UDI.PATCH', 'UDI_DI.PATCH', 'MARKET_INFO.PATCH', 'PACKAGE_UDI.PATCH'];
      function chooseDefault() {{
        var list = kind.value === 'new' ? newTasks : updateTasks;
        if (list.indexOf(task.value) === -1) task.value = list[0];
      }}
      function render() {{
        chooseDefault();
        document.querySelectorAll('.wizard-result').forEach(function (node) {{
          node.hidden = node.getAttribute('data-service') !== task.value;
        }});
      }}
      kind.addEventListener('change', render);
      task.addEventListener('change', render);
      render();
    }})();
    </script>
    """


def freshness_summary_block(summary: dict) -> str:
    if not summary:
        return ""
    return f"""
    <div class="alert notice">
      <strong>{t('导出新鲜度', 'Export freshness')}</strong>
      <span>{t('从未导出', 'Never exported')}: {esc(summary.get('never_exported', 0))}</span>
      <span> · {t('导出后有更新', 'Changed since export')}: {esc(summary.get('changed_since_export', 0))}</span>
      <span> · {t('已导出且未变化', 'Exported and unchanged')}: {esc(summary.get('up_to_date', 0))}</span>
    </div>
    """


def bulk_limit_notice() -> str:
    return f"""
    <article class="alert notice">
      <strong>{t('EUDAMED bulk upload 官方限制', 'Official EUDAMED bulk upload limit')}</strong>
      <p>{t(
          f'由于 EUDAMED 限制，每次只能上传 {BULK_UPLOAD_ENTITY_LIMIT} 条数据。如您选择的数据超过 {BULK_UPLOAD_ENTITY_LIMIT} 条，工具会自动拆分成多份 XML；请按页面/manifest 顺序分多次上传。',
          f'Due to EUDAMED limits, each upload can contain at most {BULK_UPLOAD_ENTITY_LIMIT} records. If you select more than {BULK_UPLOAD_ENTITY_LIMIT} records, this tool automatically splits them into multiple XML files; upload them in the order shown on this page / manifest.'
      )}</p>
    </article>
    """


def export_downloads(result: dict) -> str:
    if not result.get("file_path"):
        return ""
    main_name = Path(result["file_path"]).name
    label = t("下载 ZIP 总包", "Download ZIP package") if main_name.lower().endswith(".zip") else t("下载 XML", "Download XML")
    links = [f'<a class="button primary" href="/download/{esc(main_name)}">{label}</a>']
    files = result.get("files") or []
    if len(files) > 1:
        links.extend(
            f'<a class="button" href="/download/{esc(Path(item["file_path"]).name)}">{esc(item["file_name"])}</a>'
            for item in files
        )
    return f'<div class="toolbar">{"".join(links)}</div>'


def export_batch_table(batches: list[dict]) -> str:
    if not batches:
        return ""
    rows = []
    for item in batches:
        file_name = item.get("file_name") or t("预检后生成", "Generated after export")
        rows.append(
            f"""
            <tr>
              <td>{esc(item.get('sequence'))}</td>
              <td>{esc(file_name)}</td>
              <td>{esc(item.get('service_type'))}</td>
              <td>{esc(item.get('payload_entity'))}</td>
              <td>{esc(item.get('record_count'))}</td>
              <td>{esc(', '.join(item.get('basic_codes') or []))}</td>
              <td>{esc(item.get('depends_on') or '')}</td>
              <td>{esc(item.get('dependency') or '')}</td>
            </tr>
            """
        )
    return f"""
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>{t('顺序', 'Order')}</th><th>{t('文件', 'File')}</th><th>Service</th><th>Payload</th><th>{t('数量', 'Count')}</th><th>Basic UDI-DI</th><th>{t('依赖', 'Depends on')}</th><th>{t('说明', 'Note')}</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """


def export_step_state(service_type: str, result: dict | None) -> str:
    if not service_type:
        return "service"
    if not result:
        return "filter"
    if result.get("file_path"):
        return "generated"
    return "preflight"


def step_badge(step: str, label: str, current: str) -> str:
    return f'<span class="{"active" if step == current else ""}">{esc(label)}</span>'


def upload_guidance(service_type: str) -> str:
    service = SUPPORTED_SERVICES.get(service_type, SUPPORTED_SERVICES["DEVICE.POST"])
    return f"""
    <article class="upload-guide">
      <h3>{t('Bulk upload 指引', 'Bulk upload guide')}</h3>
      <ol>
        <li>{t('先在 EUDAMED Playground TEST 环境验收。', 'Validate in the EUDAMED Playground TEST environment first.')}</li>
        <li>{t('进入 EUDAMED：Data exchange / Bulk upload，选择与本工具完全一致的 service：', 'In EUDAMED: Data exchange / Bulk upload, choose the service exactly as shown here: ')}<strong>{esc(service['label'])}</strong></li>
        <li>{esc(service_text(service, 'after'))}</li>
        <li>{t(
            '如果导出结果包含多个 XML，请按分片表或 ZIP 内 manifest 的顺序上传；带依赖的 UDI_DI.POST 必须等对应 DEVICE.POST 上传成功后再上传。',
            'If multiple XML files are generated, upload them in the order shown in the batch table or ZIP manifest; dependent UDI_DI.POST files must wait until the corresponding DEVICE.POST has succeeded.'
        )}</li>
        <li>{t('上传后保存 EUDAMED response XML；如果失败，可在本工具解析 response 并只重导被拒记录。', 'Save the EUDAMED response XML after upload. If it fails, parse the response in this tool and re-export only rejected records.')}</li>
      </ol>
      <p><a class="button" href="{esc(EUDAMED_BULK_UPLOAD_HELP_URL)}" target="_blank" rel="noopener">{t('官方 bulk upload 帮助', 'Official bulk upload help')}</a>
         <a class="button" href="/ack">{t('解析 EUDAMED response', 'Parse EUDAMED response')}</a></p>
      <p class="muted">{t('本工具只把本地状态标记为 XML 已生成；请不要把这个状态等同于 EUDAMED 上传成功。',
                          'This tool only marks the local state as XML generated; do not treat that as a successful EUDAMED upload.')}</p>
    </article>
    """


def history_page(exports: list) -> str:
    rows = []
    for item in exports:
        rows.append(
            f"""
            <tr>
              <td>{item['id']}</td>
              <td>{esc(SERVICE_LABELS.get(item['service_type'], item['service_type']))}</td>
              <td>{esc(item['record_count'])}</td>
              <td>{esc(display_time(item['created_at']))}</td>
              <td><a href="/download/{esc(Path(item['file_path']).name)}">{t('下载 XML', 'Download XML')}</a></td>
            </tr>
            """
        )
    table = "".join(rows) or f'<tr><td colspan="5"><div class="empty-state">{t("还没有导出记录。去导出任务生成第一个 XML。", "No exports yet. Go to Export to generate the first XML.")} <a class="button primary" href="/export">{t("去导出任务", "Go to export")}</a></div></td></tr>'
    body = f"""
    <section class="panel">
      <h1>{t('导出历史', 'Export History')}</h1>
      <div class="table-wrap"><table>
        <thead><tr><th>ID</th><th>Service</th><th>{t('条数', 'Count')}</th><th>{t('时间', 'Time')}</th><th>{t('文件', 'File')}</th></tr></thead>
        <tbody>{table}</tbody>
      </table></div>
    </section>
    """
    return page(t("导出历史", "Export History"), body, "/history")


def download_update_help_block(check_result: dict | None = None) -> str:
    update_section = update_check_block(check_result)
    return f"""
    <div class="panel inset">
      <h3>{t('下载与更新工具', 'Download and update the tool')}</h3>
      {update_section}
      <ol>
        <li>{t('优先使用 GitHub Releases；如果 GitHub 访问慢或失败，使用 Gitee 国内镜像。', 'Use GitHub Releases first; if GitHub is slow or unavailable, use the Gitee mirror.')}</li>
        <li>{t('下载最新的 Windows ZIP 或模板附件。', 'Download the latest Windows ZIP or template asset.')}</li>
        <li>{t('解压 ZIP 后运行其中的启动程序；旧版本不用卸载，但建议先关闭正在运行的工具。', 'Unzip it and run the launcher inside; no uninstall is needed, but close the old tool first.')}</li>
        <li>{t('本地数据默认在 local_beta_data，不会因为替换新版程序而被覆盖。', 'Local data is stored under local_beta_data by default and is not overwritten by replacing the program.')}</li>
      </ol>
      <p>
        <a class="button" href="{esc(RELEASES_PAGE_URL)}" target="_blank" rel="noopener">GitHub Releases</a>
        <a class="button" href="{esc(GITEE_RELEASES_PAGE_URL)}" target="_blank" rel="noopener">Gitee Releases</a>
      </p>
    </div>
    """


def bulk_upload_help_block() -> str:
    return f"""
    <div class="panel inset">
      <h3>{t('EUDAMED bulk upload 简要步骤', 'EUDAMED bulk upload quick steps')}</h3>
      <ol>
        <li>{t('在本工具选择对应 service，先预检，再生成 XML 或 ZIP。', 'Choose the matching service in this tool, run the pre-check, then generate XML or ZIP.')}</li>
        <li>{t('进入 EUDAMED 的 Data exchange / Bulk upload 页面，选择与本工具显示一致的 service。', 'In EUDAMED, open Data exchange / Bulk upload and choose the same service shown by this tool.')}</li>
        <li>{t('如果是 ZIP 分片包，按 manifest.html / manifest.csv 的顺序逐个上传；有依赖的 UDI_DI.POST 必须等 DEVICE.POST 成功后再传。', 'If a ZIP package was generated, upload each XML in the order shown by manifest.html / manifest.csv; dependent UDI_DI.POST files must wait until DEVICE.POST has succeeded.')}</li>
        <li>{t('上传后保存官方 response XML；本工具的“XML 已生成”不等于 EUDAMED 已提交成功。', 'Save the official response XML after upload; “XML generated” in this tool does not mean EUDAMED submission succeeded.')}</li>
      </ol>
      <p><a class="button" href="{esc(EUDAMED_BULK_UPLOAD_HELP_URL)}" target="_blank" rel="noopener">{t('查看官方 bulk upload 帮助', 'Open official bulk upload help')}</a></p>
    </div>
    """


def feedback_block() -> str:
    subject_prefix = json.dumps(f"EUDAMED tool test / issue report - v{TOOL_VERSION}")
    support_email = json.dumps(SUPPORT_EMAIL)
    tool_info = json.dumps(f"Tool version: {TOOL_VERSION_LABEL}\\nXSD version: {SCHEMA_VERSION}\\nOS: {platform.platform()}")
    copy_ok = json.dumps(t("已复制。请在邮件中粘贴，并附上勾选的文件。", "Copied. Paste it into your email and attach the selected files."))
    copy_fail = json.dumps(t("复制失败，请手动复制下方内容。", "Copy failed; please copy the text below manually."))
    return f"""
    <div class="panel inset">
      <h3>{t('反馈错误 / 发送测试结果', 'Report an issue / send test result')}</h3>
      <p>{t('如果 EUDAMED 上传失败，建议先用 Response 解析页读取官方 response XML，确认是哪条记录/哪条规则失败；然后再把 response XML 和必要附件发给作者。', 'If EUDAMED upload fails, first use the Response Parser to read the official response XML and identify which record/rule failed; then email the response XML and any needed attachments to the author.')}</p>
      <p>{t('邮件请附上：EUDAMED response XML、本工具生成的 XML、使用的 Excel 模板、截图和操作步骤。', 'Attach: EUDAMED response XML, the XML generated by this tool, the Excel template used, screenshots and operation steps.')}</p>
      <p class="muted">{t('点击按钮会打开你本机邮箱，邮件只由你主动发送；工具不会自动上传任何客户数据。发送前请先脱敏敏感信息。', 'The button opens your local mail app; nothing is uploaded automatically by this tool. Remove sensitive information before sending.')}</p>
      <div class="feedback-builder">
        <div class="form-grid">
          <label><span>{t('反馈类型', 'Report type')}</span>
            <select id="feedback-kind">
              <option value="{t('EUDAMED 上传失败', 'EUDAMED upload failed')}">{t('EUDAMED 上传失败', 'EUDAMED upload failed')}</option>
              <option value="{t('Playground 测试成功', 'Playground test succeeded')}">{t('Playground 测试成功', 'Playground test succeeded')}</option>
              <option value="{t('模板/导入问题', 'Template / import issue')}">{t('模板/导入问题', 'Template / import issue')}</option>
              <option value="{t('功能建议', 'Feature request')}">{t('功能建议', 'Feature request')}</option>
            </select>
          </label>
          <label><span>{t('问题发生在哪一步', 'Step')}</span>
            <select id="feedback-step">
              <option>{t('导入 Excel', 'Import Excel')}</option>
              <option>{t('产品库 / 数据管理', 'Library / data management')}</option>
              <option>{t('导出预检', 'Export pre-check')}</option>
              <option>{t('生成 XML', 'Generate XML')}</option>
              <option>{t('EUDAMED bulk upload', 'EUDAMED bulk upload')}</option>
              <option>{t('检查更新 / 下载', 'Check update / download')}</option>
            </select>
          </label>
        </div>
        <label><span>{t('请描述现象和你希望我判断的问题', 'Describe what happened and what you need checked')}</span>
          <textarea id="feedback-detail" rows="5" placeholder="{esc(t('例如：上传 DEVICE.POST 后失败，response 里出现 RULE-00015，请帮我判断是模板填写问题还是工具生成 XML 问题。', 'Example: DEVICE.POST upload failed and the response shows RULE-00015. Please help check whether this is a template input issue or XML generation issue.'))}"></textarea>
        </label>
        <div class="checklist">
          <strong>{t('准备附上的文件', 'Files to attach')}</strong>
          <label><input type="checkbox" value="{t('EUDAMED 系统回传的 response XML（上传失败时必需）', 'EUDAMED response XML returned by the system (required for upload failures)')}" checked> {t('EUDAMED response XML（失败时必需）', 'EUDAMED response XML (required if failed)')}</label>
          <label><input type="checkbox" value="{t('本工具生成的 XML 或 ZIP', 'XML or ZIP generated by this tool')}" checked> {t('本工具生成的 XML / ZIP', 'Generated XML / ZIP')}</label>
          <label><input type="checkbox" value="{t('使用的 Excel 模板', 'Excel template used')}" checked> {t('使用的 Excel 模板', 'Excel template used')}</label>
          <label><input type="checkbox" value="{t('EUDAMED 页面截图或操作步骤', 'EUDAMED screenshot or operation steps')}"> {t('截图 / 操作步骤', 'Screenshots / steps')}</label>
        </div>
        <div class="toolbar">
          <button class="button secondary" type="button" id="feedback-build">{t('生成邮件内容', 'Generate email text')}</button>
          <button class="button" type="button" id="feedback-copy">{t('复制邮件内容', 'Copy email text')}</button>
          <a class="button" id="feedback-mail" href="{esc(_mailto_link())}">{t('打开邮件', 'Open email')}</a>
          <span id="feedback-status" class="muted"></span>
        </div>
        <textarea id="feedback-output" rows="8" readonly>{esc(t('点击“生成邮件内容”后，这里会生成可复制的邮件正文。', 'Click “Generate email text” to create a copyable email body here.'))}</textarea>
      </div>
      <div class="toolbar">
        <a class="button primary" href="/ack">{t('先解析 EUDAMED response', 'Parse EUDAMED response first')}</a>
        <a class="button" href="{esc(_mailto_link())}">{t('给作者发送错误报告', 'Email an issue report')}</a>
      </div>
      <script>
      (function() {{
        var build = document.getElementById('feedback-build');
        if (!build) return;
        var output = document.getElementById('feedback-output');
        var mail = document.getElementById('feedback-mail');
        var status = document.getElementById('feedback-status');
        function text(id) {{
          var el = document.getElementById(id);
          return el ? (el.value || '') : '';
        }}
        function selectedFiles() {{
          return Array.prototype.slice.call(document.querySelectorAll('.feedback-builder input[type="checkbox"]:checked'))
            .map(function(el) {{ return '- ' + el.value; }})
            .join('\\n') || '- {esc(t('未选择附件', 'No attachment selected'))}';
        }}
        function compose() {{
          var body = [
            'Report type / 反馈类型: ' + text('feedback-kind'),
            'Step / 发生步骤: ' + text('feedback-step'),
            '',
            'Description / 问题描述:',
            text('feedback-detail') || '（请填写 / please fill in）',
            '',
            'Attachments / 附件:',
            selectedFiles(),
            '',
            'Note / 注意:',
            '{esc(t('如涉及客户敏感信息，请先脱敏。EUDAMED 上传失败时，请务必附上官方 response XML。', 'Remove sensitive customer information first. For EUDAMED upload failures, attach the official response XML.'))}',
            '',
            {tool_info}
          ].join('\\n');
          output.value = body;
          mail.href = 'mailto:' + {support_email} + '?subject=' + encodeURIComponent({subject_prefix} + ' - ' + text('feedback-kind')) + '&body=' + encodeURIComponent(body);
          if (status) status.textContent = '';
        }}
        build.addEventListener('click', compose);
        document.getElementById('feedback-copy').addEventListener('click', function() {{
          compose();
          if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(output.value).then(function() {{
              if (status) status.textContent = {copy_ok};
            }}).catch(function() {{
              if (status) status.textContent = {copy_fail};
            }});
          }} else if (status) {{
            status.textContent = {copy_fail};
          }}
        }});
      }})();
      </script>
    </div>
    """


def _mailto_link() -> str:
    subject = f"EUDAMED tool issue report - v{TOOL_VERSION}"
    body = "\n".join(
        [
            "请在这里描述问题 / Describe the issue here:",
            "",
            "发生在哪一步 / Step:",
            "导入 Excel / 产品库 / 预检 / 生成 XML / EUDAMED 上传 / 检查更新",
            "",
            "如果是 EUDAMED 上传失败，请附上 EUDAMED 系统回传的 response XML 文件。",
            "If this is an EUDAMED upload failure, please attach the response XML returned by EUDAMED.",
            "",
            "如方便，也可附上本工具生成的 XML、使用的 Excel 模板、截图和操作步骤。",
            "If helpful, also attach the generated XML, Excel template, screenshots and operation steps.",
            "",
            "请勿发送客户敏感信息，必要时请先脱敏。",
            "",
            f"Tool version: {TOOL_VERSION_LABEL}",
            f"XSD version: {SCHEMA_VERSION}",
            f"OS: {platform.platform()}",
            "Browser language: （请填写 / please fill in）",
        ]
    )
    return f"mailto:{SUPPORT_EMAIL}?subject={quote(subject)}&body={quote(body)}"


def help_page(check_result: dict | None = None) -> str:
    body = f"""
    <section class="panel narrow help-page">
      <h1>{t('帮助与关于', 'Help & About')}</h1>
      <p class="lead">{t('EUDAMED 内测工具：把 Excel 总表导入本地库，批量校验并按官方 service 生成上传用 XML。',
            'EUDAMED helper (beta): import the Excel workbook into a local database, validate in bulk and generate upload-ready XML per official service.')}</p>
      <h2>{t('下载 / 更新', 'Download / Update')}</h2>
      {download_update_help_block(check_result)}
      <h2>Bulk upload</h2>
      {bulk_upload_help_block()}
      <h2>{t('反馈', 'Feedback')}</h2>
      {feedback_block()}
      <h2>{t('作者', 'Author')}</h2>
      <ul class="simple-list">
        <li><span>{t('姓名', 'Name')}</span><span><strong>Xiongfei Fang</strong></span></li>
        <li><span>{t('邮箱', 'Email')}</span><span><a href="mailto:{esc(SUPPORT_EMAIL)}">{esc(SUPPORT_EMAIL)}</a></span></li>
      </ul>
      <h2>{t('支持作者', 'Support the author')}</h2>
      <p class="muted">{t('如果这个工具帮到了你，欢迎请作者喝杯咖啡。', 'If this tool helps you, feel free to buy the author a coffee.')}</p>
      <div class="grid cards">
        {_qr_slot('alipay.jpg', t('支付宝', 'Alipay'))}
        {_qr_slot('wechat.png', t('微信', 'WeChat Pay'))}
        {_kofi_slot()}
      </div>
      <h2>{t('EUDAMED 官方环境', 'Official EUDAMED environments')}</h2>
      <p class="muted">{t('Playground 是独立的官方测试环境，账号和 SRN 都需要在里面单独注册，数据为虚构数据，不会影响生产环境。',
                          'The Playground is a separate official test environment; its account and SRN must be registered there separately and all data is fictional, never affecting Production.')}</p>
      <ul class="simple-list">
        <li><span>{t('Playground（测试环境）', 'Playground (test)')}</span>
          <span><a href="{esc(EUDAMED_PLAYGROUND_URL)}" target="_blank" rel="noopener">{t('打开登录页', 'Open landing page')}</a></span></li>
        <li><span>{t('Playground 环境说明', 'Playground environment guide')}</span>
          <span><a href="{esc(EUDAMED_PLAYGROUND_HELP_URL)}" target="_blank" rel="noopener">{t('查看官方说明', 'Official help')}</a></span></li>
        <li><span>{t('Production（生产环境）', 'Production')}</span>
          <span><a href="{esc(EUDAMED_PRODUCTION_URL)}" target="_blank" rel="noopener">{t('打开登录页', 'Open landing page')}</a></span></li>
      </ul>
      <h2>{t('版权与授权', 'Copyright')}</h2>
      <p>© {esc(COPYRIGHT_YEAR)} {esc(COPYRIGHT_HOLDER)}. {t('保留所有权利。', 'All rights reserved.')}</p>
      <p class="muted">{t('本软件未经作者书面许可，不得复制、修改、分发或用于商业用途。',
                          'This software may not be copied, modified, distributed or used commercially without written permission from the author.')}</p>
      <h2>{t('免责声明', 'Disclaimer')}</h2>
      <div class="disclaimer">
        <ul>
          <li>{t('本工具由个人开发，与欧盟委员会、EUDAMED 官方无任何关联，非官方软件。',
                 'This tool is developed by an individual and is not affiliated with the European Commission or EUDAMED in any way; it is unofficial software.')}</li>
          <li>{t('工具按「现状」提供，不对生成的 XML 是否完全符合 EUDAMED 要求作任何明示或默示担保。',
                 'The tool is provided "as is" with no express or implied warranty that the generated XML fully meets EUDAMED requirements.')}</li>
          <li>{t('数据准确性、完整性与法规合规的最终责任由使用者承担。',
                 'The user bears final responsibility for data accuracy, completeness and regulatory compliance.')}</li>
          <li>{t('正式提交前请务必在 EUDAMED 官方 TEST 环境（', 'Always validate in the official EUDAMED ')}<a href="{esc(EUDAMED_PLAYGROUND_URL)}" target="_blank" rel="noopener">Playground</a>{t('）验收。', ' TEST environment before any production submission.')}</li>
          <li>{t('作者不对因使用或无法使用本工具导致的任何直接或间接损失负责。',
                 'The author is not liable for any direct or indirect loss arising from the use of, or inability to use, this tool.')}</li>
        </ul>
      </div>
    </section>
    """
    return page(t("帮助", "Help"), body, "/help")


def update_check_block(check_result: dict | None) -> str:
    """渲染「检查更新」区块。默认显示当前版本 + 按钮；点击后渲染结果。"""
    current_label = f'<p class="muted">{esc(t("当前版本", "Current version"))}: <strong>{esc(TOOL_VERSION_LABEL)}</strong></p>'
    if check_result is None:
        button = f'<a class="button" href="/check-update">{esc(t("检查更新", "Check for updates"))}</a>'
        if not RELEASES_API_URL:
            hint = f'<p class="muted">{esc(t("更新源尚未配置；联系作者获取最新版本。", "Update source not configured yet; contact the author for the latest version."))}</p>'
        else:
            hint = f'<p class="muted">{esc(t("点击按钮联网检查最新版本。", "Click the button to check the latest version online."))}</p>'
        return f'<div class="update-check">{current_label}{hint}{button}</div>'

    source_downloads = dual_release_download_buttons(check_result.get("download_sources") or {})
    status = check_result.get("status", "error")
    latest = check_result.get("latest_version", "")
    page_url = check_result.get("html_url") or RELEASES_PAGE_URL
    asset = check_result.get("asset_url", "")
    assets = check_result.get("assets") or []
    published = check_result.get("published_at", "")
    body = check_result.get("body", "")
    error = check_result.get("error", "")
    prerelease = bool(check_result.get("prerelease"))
    source = check_result.get("source") or "github"
    source_name = "Gitee" if source == "gitee" else "GitHub"
    fallback_error = check_result.get("fallback_error") or ""
    fallback_note = (
        f'<p class="muted">{esc(t("GitHub 检查失败，已自动使用 Gitee 镜像结果。", "GitHub check failed; showing Gitee mirror result instead."))} {esc(fallback_error)}</p>'
        if source == "gitee" and fallback_error
        else ""
    )
    prerelease_badge = f' <span class="badge muted-badge">{esc(t("公开测试版", "Public Beta"))}</span>' if prerelease else ""

    if status == "ok":
        level = "warning"
        title = t("发现新版本", "New version available")
        details = t("最新版本", "Latest version") + f": <strong>{esc(latest)}</strong>{prerelease_badge}"
        if published:
            details += f' · {esc(t("发布于", "released"))} {esc(display_time(published) or published)}'
        details += f' · {esc(t("来源", "Source"))}: <strong>{esc(source_name)}</strong>'
        download_links = [source_downloads] if source_downloads else _release_download_links(assets, asset)
        if not download_links and asset:
            download_links.append(f'<a class="button primary" href="{esc(asset)}" target="_blank" rel="noopener">{esc(t("下载新版安装包", "Download package"))}</a>')
        if page_url:
            download_links.append(f'<a class="button" href="{esc(page_url)}" target="_blank" rel="noopener">{esc(t("打开发布页", "Open release page"))}</a>')
        notes = ""
        if body:
            snippet = body.strip().splitlines()
            first_lines = "\n".join(snippet[:10])
            notes = f'<details><summary>{esc(t("查看更新说明", "View release notes"))}</summary><pre class="release-notes">{esc(first_lines)}</pre></details>'
        return f"""
        <div class="alert {level}">
          <strong>{esc(title)}</strong>
          <p>{details}</p>
          {''.join(download_links)}
          {fallback_note}
          {notes}
        </div>
        {current_label}
        """
    if status == "up_to_date":
        return f"""
        <div class="alert success">
          <strong>{esc(t("已是最新版本", "You are up to date"))}</strong>
          <p>{esc(t("当前版本", "Current version"))} <strong>{esc(TOOL_VERSION_LABEL)}</strong> {esc(t("等于线上最新", "matches the latest release"))} <strong>{esc(latest)}</strong>{prerelease_badge}. {esc(t("来源", "Source"))}: <strong>{esc(source_name)}</strong></p>
          {source_downloads}
          {fallback_note}
        </div>
        """
    if status == "local_newer":
        return f"""
        <div class="alert notice">
          <strong>{esc(t("当前本地版本高于线上最新发布版本", "Local version is newer than the latest online release"))}</strong>
          <p>{esc(t("本地版本", "Local version"))}: <strong>{esc(TOOL_VERSION_LABEL)}</strong> · {esc(source_name)}: <strong>{esc(latest or t("未识别", "unknown"))}</strong></p>
          <p class="muted">{esc(t("这通常表示你正在使用开发版/公开测试版，尚未发布成正式 Release。", "This usually means you are using a development/Public Beta build that has not been published as a formal Release yet."))}</p>
          {source_downloads}
          {fallback_note}
        </div>
        {current_label}
        """
    if status == "unconfigured":
        return f"""
        <div class="alert notice">
          <strong>{esc(t("未配置更新源", "Update source not configured"))}</strong>
          <p>{esc(t("仓库地址未填，无法联网比对版本。联系作者获取最新版本。", "Repository URL is not set; cannot compare versions online. Contact the author for the latest version."))}</p>
        </div>
        {current_label}
        """
    if status == "no_release":
        link = ""
        if page_url:
            link = f'<a class="button" href="{esc(page_url)}" target="_blank" rel="noopener">{esc(t("打开发布页", "Open releases page"))}</a>'
        return f"""
        <div class="alert notice">
          <strong>{esc(t("仓库尚未发布版本", "No release has been published yet"))}</strong>
          <p>{esc(t("仓库已配置，但还没有创建 tag + Release + 上传 ZIP；第一次发布完成后，用户才能在这里检查更新。", "The repository is configured, but no tag + Release + ZIP asset has been published yet. Users can check updates here after the first release is published."))}</p>
          {link}
        </div>
        {current_label}
        """
    if status == "offline":
        return f"""
        <div class="alert error">
          <strong>{esc(t("无法联网检查", "Cannot reach update server"))}</strong>
          <p class="muted">{esc(error or t("请检查网络后重试。", "Please check your network and try again."))}</p>
          <a class="button" href="/check-update">{esc(t("重试", "Retry"))}</a>
          <a class="button" href="{esc(GITEE_RELEASES_PAGE_URL)}" target="_blank" rel="noopener">Gitee Releases</a>
        </div>
        {current_label}
        """
    return f"""
    <div class="alert error">
      <strong>{esc(t("检查失败", "Update check failed"))}</strong>
      <p class="muted">{esc(error or t("未知错误", "Unknown error"))}</p>
      <a class="button" href="/check-update">{esc(t("重试", "Retry"))}</a>
      <a class="button" href="{esc(GITEE_RELEASES_PAGE_URL)}" target="_blank" rel="noopener">Gitee Releases</a>
    </div>
    {current_label}
    """


def _release_download_links(assets: list[dict], preferred_url: str) -> list[str]:
    links = []
    for item in assets[:8]:
        url = item.get("url", "")
        name = item.get("name", "") or t("下载附件", "Download asset")
        size = _format_size(item.get("size", 0))
        label = f"{name} ({size})" if size else name
        klass = "button primary" if url == preferred_url else "button"
        links.append(f'<a class="{klass}" href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>')
    return links


def dual_release_download_buttons(sources: dict) -> str:
    if not sources:
        return ""
    labels = {
        "github": t("从 GitHub 下载 Windows ZIP", "Download Windows ZIP from GitHub"),
        "gitee": t("从 Gitee 下载 Windows ZIP（国内推荐）", "Download Windows ZIP from Gitee (recommended in China)"),
    }
    buttons = []
    for key in ("github", "gitee"):
        data = sources.get(key) or {}
        url = data.get("zip_url") or data.get("page_url") or ""
        if not url:
            continue
        version = data.get("version") or ""
        label = labels[key] + (f" v{version}" if version else "")
        klass = "button primary" if key == "gitee" else "button"
        buttons.append(f'<a class="{klass}" href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>')
    if not buttons:
        return ""
    return f"""
    <div class="toolbar release-sources">
      {''.join(buttons)}
      <span class="muted">{esc(t("两个来源的包内容应一致；国内访问优先 Gitee。", "Packages from both sources should be identical; use Gitee first in mainland China."))}</span>
    </div>
    """


def _format_size(size) -> str:
    try:
        value = int(size)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    units = ["B", "KB", "MB", "GB"]
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} B"
        amount /= 1024
    return ""


def _qr_slot(filename: str, label: str) -> str:
    if (STATIC_DIR / filename).exists():
        inner = f'<img class="qr-img" src="/static/{esc(filename)}" alt="{esc(label)}">'
    else:
        inner = f'<span class="muted">{t("收款码待补充", "QR code coming soon")}</span>'
    return f'<article class="card qr-slot"><h3>{esc(label)}</h3>{inner}</article>'


def _kofi_slot() -> str:
    return f"""
    <article class="card qr-slot">
      <h3>Ko-fi</h3>
      <p class="support-copy">{t('海外用户可通过 Ko-fi 支持。', 'International users can support via Ko-fi.')}</p>
      <a class="button primary kofi-link" href="https://ko-fi.com/charles_fang" target="_blank" rel="noopener">{t('前往 Ko-fi', 'Open Ko-fi')}</a>
    </article>
    """


def template_guide_page() -> str:
    entry_sections = "".join(_sheet_guide_section(sheet, columns_for_entry_sheet(sheet)) for sheet in ENTRY_SHEETS)
    related_sections = "".join(_sheet_guide_section(sheet, spec["columns"], spec.get("target", "")) for sheet, spec in RELATED_SHEETS.items())
    body = f"""
    <section class="panel template-guide">
      <h1>{t('模板怎么填', 'How to fill the template')}</h1>
      <p class="badge">{t('当前模板版本', 'Current template version')}: {esc(TEMPLATE_VERSION)}</p>
      <p class="lead">{t('本页自动来自当前 template schema，和 Excel 模板列保持同源。Excel 仍是主维护文件，本工具用于导入、校验、筛选和导出 XML。',
            'This page is generated from the current template schema, so it stays aligned with the Excel template. Excel remains the master data file; this tool imports, validates, filters and exports XML.')}</p>
      <div class="template-guide-search">
        <label><span>{t('搜索字段 / sheet / 说明', 'Search field / sheet / description')}</span>
          <input type="text" id="template-guide-search" placeholder="{esc(t('例如：version、Package、Reference、市场', 'e.g. version, Package, Reference, market'))}">
        </label>
        <p class="muted">{t('输入关键词后，只显示匹配的字段行；清空搜索可恢复全部。', 'Type a keyword to show matching field rows only; clear it to restore all rows.')}</p>
      </div>
      <div class="alert notice">
        <strong>{t('常见错误', 'Common mistakes')}</strong>
        <ul>
          <li>{t('UDI/GTIN/Reference/SRN 必须按文本维护，避免科学计数法和前导 0 丢失。', 'Maintain UDI/GTIN/Reference/SRN as text to avoid scientific notation and lost leading zeros.')}</li>
          <li>{t('希腊国家代码使用 EL，不是 GR。', 'Greece uses country code EL, not GR.')}</li>
          <li>{t('同一 UDI-DI 的 Market Info 中 Originally Placed on Market 必须且只能一条 TRUE。', 'Market Info for one UDI-DI must have exactly one Originally Placed on Market = TRUE row.')}</li>
          <li>{t('数据从第 4 行开始填写；前三行是字段名/说明/示例，不要改。', 'Start filling data from row 4; rows 1-3 are headers/instructions/examples and should not be changed.')}</li>
          <li>{t('明细表通过 UDI-DI Code 或 Basic UDI-DI Code 关联主表。', 'Related sheets link back to the main sheet through UDI-DI Code or Basic UDI-DI Code.')}</li>
        </ul>
      </div>
      <h2>{t('主表', 'Main sheets')}</h2>
      {entry_sections}
      <h2>{t('明细表', 'Related sheets')}</h2>
      {related_sections}
    </section>
    <script>
    (function () {{
      var input = document.getElementById('template-guide-search');
      if (!input) return;
      function applyFilter() {{
        var q = input.value.trim().toLowerCase();
        document.querySelectorAll('.sheet-guide').forEach(function (section) {{
          var visible = 0;
          section.querySelectorAll('[data-guide-row]').forEach(function (row) {{
            var haystack = row.getAttribute('data-guide-row') || '';
            var show = !q || haystack.indexOf(q) !== -1;
            row.hidden = !show;
            if (show) visible += 1;
          }});
          section.hidden = q && visible === 0;
          if (q && visible > 0) section.open = true;
        }});
      }}
      input.addEventListener('input', applyFilter);
    }})();
    </script>
    """
    return page(t("模板指南", "Template Guide"), body, "/template-guide")


def _sheet_guide_section(sheet_name: str, columns: list[dict], target: str = "") -> str:
    rows = []
    for col in columns:
        requirement = {
            "required": t("必填", "Required"),
            "conditional": t("条件必填", "Conditional"),
            "optional": t("可选", "Optional"),
        }.get(col.get("requirement"), col.get("requirement", ""))
        search_blob = " ".join(
            str(value or "")
            for value in (
                sheet_name,
                target,
                col.get("field"),
                col.get("header"),
                col.get("description"),
                col.get("example"),
                col.get("format"),
                requirement,
            )
        ).lower()
        rows.append(
            f"""
            <tr data-guide-row="{esc(search_blob)}">
              <td>{label_with_hint(col.get('field') or col.get('header') or '')}<br><span class="muted">{esc(col.get('header', ''))}</span></td>
              <td><span class="badge requirement-{esc(col.get('requirement', 'optional'))}">{esc(requirement)}</span></td>
              <td>{esc(col.get('description', ''))}</td>
              <td>{esc(col.get('example', ''))}</td>
              <td>{esc(col.get('format', ''))}</td>
            </tr>
            """
        )
    subtitle = f'<p class="muted">{esc(target)}</p>' if target else ""
    return f"""
    <details class="sheet-guide" open>
      <summary>{esc(sheet_name)}</summary>
      {subtitle}
      <div class="table-wrap"><table>
        <thead><tr><th>{t('字段', 'Field')}</th><th>{t('要求', 'Requirement')}</th><th>{t('说明', 'Description')}</th><th>{t('示例', 'Example')}</th><th>{t('格式', 'Format')}</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table></div>
    </details>
    """


def ack_page(result: dict | None = None, message: str = "", message_level: str = "notice") -> str:
    parsed = ack_result_panel(result) if result else ""
    body = f"""
    <section class="panel narrow">
      <h1>{t('解析 EUDAMED response XML', 'Parse EUDAMED response XML')}</h1>
      <p>{t('在 EUDAMED bulk upload 后下载官方 response / acknowledgement XML，上传到这里查看哪些实体成功、哪些被拒，以及能否匹配到本地记录。',
            'After EUDAMED bulk upload, download the official response / acknowledgement XML and upload it here to see which entities passed, which were rejected, and whether they match local records.')}</p>
      <p class="muted">{t('工具不会自动上传任何文件；response XML 只在本机解析。', 'The tool does not upload anything automatically; the response XML is parsed locally only.')}</p>
      {alert_block(message, message_level)}
      <form action="/ack" method="post" enctype="multipart/form-data" class="stack">
        <input type="file" name="ack_xml" accept=".xml,text/xml" required>
        <button class="button primary" type="submit">{t('解析 response', 'Parse response')}</button>
      </form>
      <div class="alert notice">
        <strong>{t('需要作者协助？', 'Need help from the author?')}</strong>
        <p>{t('解析后如果仍无法判断，请邮件发送 EUDAMED response XML、本工具生成的 XML、使用的 Excel 模板、截图和操作步骤。', 'If the parsed result is still unclear, email the EUDAMED response XML, generated XML, Excel template, screenshots and operation steps.')}</p>
        <a class="button" href="{esc(_mailto_link())}">{t('发送错误报告', 'Email an issue report')}</a>
      </div>
    </section>
    {parsed}
    """
    return page(t("Response 解析", "Response Parser"), body, "/ack")


def ack_result_panel(result: dict | None) -> str:
    if not result:
        return ""
    if result.get("errors") and not result.get("entities"):
        errors = "".join(f"<li>{esc(item)}</li>" for item in result.get("errors", []))
        return f'''
        <section class="panel">
          <h2>{t("解析结果", "Parse result")}</h2>
          <div class="alert error"><ul>{errors}</ul></div>
          <p>{t("如果确认这是 EUDAMED 官方 response XML，请把该 response XML 连同生成的 XML 和模板发给作者。", "If this is definitely an official EUDAMED response XML, send it to the author together with the generated XML and template.")}</p>
          <a class="button" href="{esc(_mailto_link())}">{t("发送错误报告", "Email an issue report")}</a>
        </section>
        '''
    rows = []
    rejected_ids = []
    for item in result.get("entities") or []:
        status = str(item.get("status") or "UNKNOWN")
        matched = item.get("matched_record") or {}
        errors = item.get("errors") or []
        detail = "".join(
            f"<li><strong>{esc(error.get('code'))}</strong> {esc(error.get('detail'))}</li>"
            for error in errors
        ) or f"<li>{t('无', 'None')}</li>"
        link = ""
        if matched:
            path = "/basic/" if matched.get("type") == "basic" else "/udi/"
            link = f'<a href="{path}{esc(matched.get("id"))}">{esc(matched.get("type"))} #{esc(matched.get("id"))}</a>'
            rejected = errors or status.upper() not in {"PROCESSED", "SUCCESS", "ACCEPTED"}
            if rejected and (
                (result.get("service_type") == "Basic_UDI.PATCH" and matched.get("type") == "basic")
                or (result.get("service_type") != "Basic_UDI.PATCH" and matched.get("type") == "udi")
            ):
                rejected_ids.append(str(matched.get("id")))
        rows.append(
            f"""
            <tr>
              <td>{esc(item.get('entity_code'))}</td>
              <td>{ack_status_badge(status)}</td>
              <td>{link or '<span class="muted">未匹配 / not matched</span>'}</td>
              <td><ul>{detail}</ul></td>
            </tr>
            """
        )
    service = result.get("service_type") or ""
    reexport = ""
    if rejected_ids:
        query = urlencode({"service_type": service or "UDI_DI.PATCH", "record_ids": rejected_ids}, doseq=True)
        reexport = f'<p><a class="button primary" href="/export?{query}">{t("只重新导出被拒记录", "Re-export rejected records only")}</a></p>'
    if not rejected_ids and rows:
        reexport = f'<p class="alert success">{t("没有识别到需要返工的本地 UDI-DI。", "No local UDI-DI needing rework was identified.")}</p>'
    return f"""
    <section class="panel">
      <h2>{t('解析结果', 'Parse result')}</h2>
      <p>{term_hint('DTX service')}: <strong>{esc(service or t('未识别', 'unknown'))}</strong></p>
      <div class="table-wrap"><table>
        <thead><tr><th>{t('实体编码', 'Entity code')}</th><th>{t('状态', 'Status')}</th><th>{t('本地匹配', 'Local match')}</th><th>{t('错误明细', 'Error details')}</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table></div>
      {reexport}
      <div class="toolbar">
        <a class="button" href="{esc(_mailto_link())}">{t('把 response 结果发给作者', 'Email this response result')}</a>
        <a class="button" href="/help">{t('查看反馈说明', 'View feedback instructions')}</a>
      </div>
    </section>
    """


def ack_status_badge(status: str) -> str:
    value = str(status or "UNKNOWN").upper()
    if value in {"PROCESSED", "SUCCESS", "ACCEPTED"}:
        css = "ack-success"
    elif value in {"PROCESSED_WITH_ERRORS", "REJECTED", "ERROR", "FAILED"}:
        css = "ack-error"
    else:
        css = "muted-badge"
    return f'<span class="badge {esc(css)}">{esc(status or "UNKNOWN")}</span>'


def shutdown_page() -> str:
    body = f"""
    <section class="panel narrow">
      <h1>{t('工具已退出', 'Tool has exited')}</h1>
      <p>{t('本地服务正在关闭。现在可以关闭这个浏览器页面。', 'The local server is shutting down. You can close this browser page now.')}</p>
      <p class="muted">{t('如需再次使用，请重新双击启动程序或运行 python3 run_local_beta.py。', 'To use it again, double-click the launcher or run python3 run_local_beta.py again.')}</p>
    </section>
    """
    return page(t("工具已退出", "Tool exited"), body, "/shutdown")


def xsd_version_page(report: dict) -> str:
    status_label = {
        "ok": t("一致", "Consistent"),
        "mismatch": t("不一致", "Mismatch"),
        "unknown": t("无法确认", "Unknown"),
    }.get(report["status"], t("无法确认", "Unknown"))
    status_class = f"status {report['status']}"
    error = f"<p class='muted'>{esc(report['error'])}</p>" if report.get("error") else ""
    body = f"""
    <section class="panel narrow">
      <h1>{t('XSD 版本检查', 'XSD version check')}</h1>
      <p><span class="{status_class}">{esc(status_label)}</span></p>
      <div class="table-wrap"><table>
        <tbody>
          <tr><th>{t('工具当前版本', 'Tool XSD version')}</th><td>{esc(report.get('tool_version'))}</td></tr>
          <tr><th>{t('本地官方 XSD 包版本', 'Local official XSD version')}</th><td>{esc(report.get('local_xsd_version') or t('未找到', 'not found'))}</td></tr>
          <tr><th>{t('官方技术文档页版本', 'Official documentation version')}</th><td>{esc(report.get('official_xsd_version') or t('未识别', 'not detected'))}</td></tr>
          <tr><th>{t('官方页面', 'Official page')}</th><td><a href="{esc(report.get('official_url'))}">{esc(report.get('official_url'))}</a></td></tr>
        </tbody>
      </table></div>
      {error}
      <p><a class="button" href="/xsd-version">{t('重新检查', 'Re-check')}</a></p>
    </section>
    """
    return page(t("XSD 版本检查", "XSD version check"), body, "/xsd-version")


def xsd_panel(report: dict) -> str:
    status = report.get("status", "unknown")
    label = {
        "ok": t("版本一致", "Version OK"),
        "mismatch": t("版本不一致", "Version mismatch"),
        "unknown": t("离线确认", "Offline check"),
    }.get(status, t("离线确认", "Offline check"))
    local = report.get("local_xsd_version") or t("未找到", "not found")
    tool = report.get("tool_version") or ""
    return f"""
    <div class="xsd-strip">
      <span class="status {esc(status)}">{esc(label)}</span>
      <span>{t('当前支持 EUDAMED XSD', 'Supported EUDAMED XSD')}: <strong>{esc(tool)}</strong></span>
      <span>{t('本地 XSD', 'Local XSD')}: <strong>{esc(local)}</strong></span>
      <a href="{esc(TECHNICAL_DOCUMENTATION_URL)}">{t('官方技术文档', 'Official documentation')}</a>
      <a href="/xsd-version">{t('联网检查', 'Check online')}</a>
    </div>
    """


def filter_form(action: str, filters: dict, srn_options: list[str] | None = None) -> str:
    return f"""
    <form method="get" action="{esc(action)}" class="filters">
      {filter_controls(filters, srn_options)}
      <button class="button" type="submit">{t('筛选', 'Filter')}</button>
    </form>
    """


def filter_controls(filters: dict, srn_options: list[str] | None = None) -> str:
    placeholder = t("产品名 / Reference / Basic / UDI / 备注", "Product / Reference / Basic / UDI / notes")
    return f"""
    <input type="text" name="q" value="{esc(filters.get('query', ''))}" placeholder="{esc(placeholder)}">
    <select name="state">{state_options(filters.get('state', ''))}</select>
    <select name="legislation">{legislation_options(filters.get('legislation', ''))}</select>
    <select name="change_type">{change_options(filters.get('change_type', ''))}</select>
    <select name="freshness_filter">{freshness_options(filters.get('freshness_filter', ''))}</select>
    <select name="srn">{srn_filter_options(filters.get('srn', ''), srn_options)}</select>
    """


def srn_filter_options(current: str, srn_options: list[str] | None) -> str:
    parts = [f'<option value=""{" selected" if not current else ""}>{t("全部 Manufacturer SRN", "All Manufacturer SRNs")}</option>']
    found = False
    for srn in srn_options or []:
        selected = " selected" if srn == current else ""
        if selected:
            found = True
        parts.append(f'<option value="{esc(srn)}"{selected}>{esc(srn)}</option>')
    if current and not found:
        parts.append(f'<option value="{esc(current)}" selected>{esc(current)}</option>')
    return "".join(parts)


def hidden_filters(filters: dict) -> str:
    return "".join(
        f'<input type="hidden" name="{esc(name)}" value="{esc(value)}">'
        for name, value in {
            "q": filters.get("query", ""),
            "state": filters.get("state", ""),
            "legislation": filters.get("legislation", ""),
            "change_type": filters.get("change_type", ""),
            "freshness_filter": filters.get("freshness_filter", ""),
            "srn": filters.get("srn", ""),
        }.items()
    )


def message_block(message: str, level: str = "notice") -> str:
    return alert_block(message, level)


def state_options(current: str) -> str:
    values = [
        ("", t("全部状态", "All states")),
        ("draft", t("草稿", "Draft")),
        ("xml_generated", t("XML 已生成", "XML generated")),
        ("pending_update", t("待更新", "Pending update")),
        ("submitted", t("已提交", "Submitted")),
    ]
    return "".join(
        f'<option value="{value}"{" selected" if value == current else ""}>{label}</option>'
        for value, label in values
    )


def state_select(current: str) -> str:
    values = [
        ("draft", t("草稿", "Draft")),
        ("xml_generated", t("XML 已生成", "XML generated")),
        ("pending_update", t("待更新", "Pending update")),
        ("submitted", t("已提交", "Submitted")),
    ]
    options = "".join(
        f'<option value="{value}"{" selected" if value == current else ""}>{label}</option>'
        for value, label in values
    )
    return f'<select name="state">{options}</select>'


def legislation_options(current: str) -> str:
    values = [("", t("全部法规", "All legislation")), ("MDR", "MDR"), ("MDD", "MDD"), ("AIMDD", "AIMDD"), ("IVDR", "IVDR"), ("IVDD", "IVDD")]
    return "".join(
        f'<option value="{value}"{" selected" if value == current else ""}>{label}</option>'
        for value, label in values
    )


def change_options(current: str) -> str:
    values = [
        ("", t("全部变化", "All changes")),
        ("created", t("新增", "Created")),
        ("updated", t("已更新", "Updated")),
        ("unchanged", t("未变化", "Unchanged")),
        ("existing", t("历史数据", "Existing")),
    ]
    return "".join(
        f'<option value="{value}"{" selected" if value == current else ""}>{label}</option>'
        for value, label in values
    )


def freshness_options(current: str) -> str:
    values = [
        ("", t("全部导出状态", "All export freshness")),
        ("never_exported", t("从未导出", "Never exported")),
        ("changed_since_export", t("导出后有更新", "Changed since export")),
        ("up_to_date", t("已导出且未变化", "Exported and unchanged")),
    ]
    return "".join(
        f'<option value="{value}"{" selected" if value == current else ""}>{label}</option>'
        for value, label in values
    )


def service_options(current: str) -> str:
    parts = [
        f'<option value=""{" selected" if not current else ""}>{t("— 请选择 service —", "— Choose a service —")}</option>'
    ]
    parts.extend(
        f'<option value="{key}"{" selected" if key == current else ""}>{esc(service_task(SUPPORTED_SERVICES[key]))} — {esc(key)}</option>'
        for key in SERVICE_LABELS
        if key in SUPPORTED_SERVICES
    )
    return "".join(parts)


def state_badge(state: str) -> str:
    labels = {
        "draft": t("草稿", "Draft"),
        "xml_generated": t("XML 已生成", "XML generated"),
        "pending_update": t("待更新", "Pending update"),
        "submitted": t("已提交", "Submitted"),
    }
    return f'<span class="badge state-{esc(state)}">{esc(labels.get(state, state))}</span>'


def change_badge(action: str | None) -> str:
    labels = {
        "created": t("新增", "Created"),
        "updated": t("已更新", "Updated"),
        "unchanged": t("未变化", "Unchanged"),
        "existing": t("历史数据", "Existing"),
    }
    key = action or "existing"
    return f'<span class="badge change-{esc(key)}">{esc(labels.get(key, key))}</span>'


def _entity_label(entity_type: str | None) -> str:
    return "Basic" if entity_type == "basic" else "UDI-DI"


def _product_name(item: dict) -> str:
    payload = item.get("payload") or {}
    basic_payload = item.get("basic_payload") or {}
    return (
        payload.get("Trade Name")
        or basic_payload.get("Device Name/Model")
        or basic_payload.get("Device Model")
        or payload.get("Reference Number")
        or ""
    )


def filter_query(filters: dict) -> str:
    return urlencode(
        {
            "q": filters.get("query", ""),
            "state": filters.get("state", ""),
            "legislation": filters.get("legislation", ""),
            "change_type": filters.get("change_type", ""),
            "freshness_filter": filters.get("freshness_filter", ""),
            "srn": filters.get("srn", ""),
        }
    )
