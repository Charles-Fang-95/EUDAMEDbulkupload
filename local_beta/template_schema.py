from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT_DIR = Path(__file__).resolve().parent.parent
XSD_BASE = ROOT_DIR / "official_docs" / "unpacked" / "xsd_production" / "data" / "Entity"
COMMON_DEVICE_XSD = XSD_BASE / "Device" / "CommonDeviceType.xsd"
REGULATION_UDI_XSD = XSD_BASE / "Device" / "RegulationDevice" / "UDIDIType.xsd"
COUNTRY_XSD = XSD_BASE / "Common" / "CountryEnum.xsd"
LANGUAGE_XSD = XSD_BASE / "Common" / "LanguageSpecificNameType.xsd"
ISSUING_ENTITY_XSD = XSD_BASE / "Device" / "RegulationDevice" / "UDIDIType.xsd"
LINK_XSD = XSD_BASE / "Links" / "LinkType.xsd"
TEMPLATE_VERSION = "v2.6"


def _col(
    group,
    header,
    entity,
    field,
    required=False,
    validation=None,
    description="",
    example="",
    fmt="",
    applies="all",
    requirement=None,
):
    return {
        "group": group,
        "header": header,
        "entity": entity,
        "field": field,
        "required": required,
        "requirement": requirement or ("required" if required else "optional"),
        "validation": validation,
        "description": description,
        "example": example,
        "format": fmt,
        "applies": applies,
    }


def _related_col(header, field, required=False, validation=None, description="", example="", fmt="", requirement=None):
    return _col("Related", header, "related", field, required, validation, description, example, fmt, "all", requirement)


def _xsd_enum_values_from_file(xsd_path: Path, type_name: str, other_code: str = "") -> list[str]:
    if not xsd_path.exists():
        return []
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    root = ET.parse(xsd_path).getroot()
    restriction = root.find(f".//xs:simpleType[@name='{type_name}']/xs:restriction", ns)
    if restriction is None:
        return []
    values = []
    for enum in restriction.findall("xs:enumeration", ns):
        code = enum.attrib.get("value", "")
        doc = enum.find(".//xs:documentation", ns)
        label = " ".join((doc.text or "").split()) if doc is not None else ""
        values.append(f"{code} - {label}" if label else code)
    if other_code:
        other_values = [item for item in values if item.split(" - ", 1)[0] == other_code]
        regular_values = [item for item in values if item.split(" - ", 1)[0] != other_code]
        return other_values + regular_values
    return values


def _xsd_enum_values(type_name: str, other_code: str = "") -> list[str]:
    return _xsd_enum_values_from_file(COMMON_DEVICE_XSD, type_name, other_code)


def _xsd_country_values(type_name: str = "EUCountryWithSpecialEnum") -> list[str]:
    if not COUNTRY_XSD.exists():
        return [
            "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES",
            "FI", "FR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU",
            "LV", "MT", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK",
            "TR", "XI",
        ]
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    root = ET.parse(COUNTRY_XSD).getroot()
    restriction = root.find(f".//xs:simpleType[@name='{type_name}']/xs:restriction", ns)
    if restriction is None:
        return []
    return [enum.attrib.get("value", "") for enum in restriction.findall("xs:enumeration", ns) if enum.attrib.get("value")]


def _xsd_simple_enum(xsd_path: Path, type_name: str) -> list[str]:
    """通用读取：从给定 XSD 文件读 simpleType 枚举值列表。文件不存在或类型缺失返回 []。"""
    if not xsd_path.exists():
        return []
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    try:
        root = ET.parse(xsd_path).getroot()
    except ET.ParseError:
        return []
    restriction = root.find(f".//xs:simpleType[@name='{type_name}']/xs:restriction", ns)
    if restriction is None:
        return []
    return [enum.attrib.get("value", "") for enum in restriction.findall("xs:enumeration", ns) if enum.attrib.get("value")]


_LANGUAGE_FALLBACK = [
    "ANY", "BG", "CS", "DA", "DE", "EL", "EN", "ES", "ET", "FI", "FR", "GA",
    "HR", "HU", "IS", "IT", "LT", "LV", "MT", "NL", "NO", "PL", "PT", "RO",
    "SK", "SL", "SV", "TR",
]


def _xsd_language_values(include_any: bool = False, lowercase: bool = True) -> list[str]:
    """从 LanguageSpecificNameType.xsd 读 LanguageEnum；默认小写以兼容历史数据；可选包含 ANY。"""
    values = _xsd_simple_enum(LANGUAGE_XSD, "LanguageEnum") or list(_LANGUAGE_FALLBACK)
    out: list[str] = []
    for value in values:
        upper = value.upper()
        if upper == "ANY":
            if include_any and "ANY" not in out:
                out.append("ANY")
            continue
        token = upper.lower() if lowercase else upper
        if token not in out:
            out.append(token)
    if include_any and "ANY" not in out:
        out.insert(0, "ANY")
    if include_any:
        # 把 ANY 放到列表最前面以便下拉一目了然
        out = ["ANY"] + [v for v in out if v != "ANY"]
    return out


_ISSUING_ENTITY_FALLBACK = ["EUDAMED", "GS1", "HIBCC", "ICCBBA", "IFA"]


def _xsd_issuing_entity_values() -> list[str]:
    """从 RegulationDevice/UDIDIType.xsd 读 IssuingEntityTypeEnum；fallback 含 5 项全集。"""
    values = _xsd_simple_enum(ISSUING_ENTITY_XSD, "IssuingEntityTypeEnum") or list(_ISSUING_ENTITY_FALLBACK)
    # 保持稳定顺序：GS1 在前（最常用），其他按 XSD 顺序
    preferred = ["GS1", "HIBCC", "ICCBBA", "IFA", "EUDAMED"]
    ordered = [v for v in preferred if v in values] + [v for v in values if v not in preferred]
    return ordered


_CERTIFICATE_TYPE_FALLBACK = [
    "IVDR_PRODUCTION_QUALITY_ASSURANCE",
    "IVDR_QUALITY_MANAGEMENT_SYSTEM",
    "IVDR_TECHNICAL_DOCUMENTATION",
    "IVDR_TYPE_EXAMINATION",
    "MDR_PRODUCT_VERIFICATION",
    "MDR_QUALITY_ASSURANCE",
    "MDR_QUALITY_MANAGEMENT_SYSTEM",
    "MDR_TECHNICAL_DOCUMENTATION",
    "MDR_TYPE_EXAMINATION",
    "MDD_II_EX_4",
    "MDD_II_4",
    "MDD_III",
    "MDD_IV",
    "MDD_V",
    "MDD_VI",
    "AIMDD_II_EX_4",
    "AIMDD_II_4",
    "AIMDD_III",
    "AIMDD_IV",
    "AIMDD_V",
    "IVDD_III_6",
    "IVDD_IV_EX_4_6",
    "IVDD_IV_4",
    "IVDD_IV_6",
    "IVDD_V",
    "IVDD_VI",
    "IVDD_VII_EX_5",
    "IVDD_VII_5",
]


def _certificate_type_values() -> list[str]:
    return _xsd_simple_enum(LINK_XSD, "GenericCertificateTypeEnum") or list(_CERTIFICATE_TYPE_FALLBACK)


def _clinical_size_type_values() -> list[str]:
    return _xsd_enum_values_from_file(COMMON_DEVICE_XSD, "ClinicalSizeTypeEnum", "CST999")


def _clinical_size_unit_values() -> list[str]:
    return _xsd_enum_values_from_file(REGULATION_UDI_XSD, "ClinicalSizeUnitEnum", "MU999")


def _annex_xvi_values() -> list[str]:
    return _xsd_enum_values_from_file(REGULATION_UDI_XSD, "NonMedicalDeviceEnum")


MAIN_COLUMNS = [
    _col("Meta", "Local - Record ID", "meta", "record_id", False, None, "用户自定义行号或内部编码，仅供本地追踪。", "ROW-001", "自由文本"),
    _col("Meta", "Basic - Current Version", "meta", "basic_version", False, None, "条件必填：仅在使用 Update Basic UDI / Basic_UDI.PATCH 时填写 EUDAMED 当前版本号。该字段位于主表 B 列；新上传留空。", "", "数字或文本", requirement="conditional"),
    _col("Basic", "Basic - Basic UDI-DI Code*", "basic", "Basic UDI-DI Code", True, None, "Basic UDI-DI 的唯一代码。一个 Basic 可对应多个 UDI-DI。", "BASIC001234", "8-50 位字母数字"),
    _col("Basic", "Basic - Issuing Entity*", "basic", "Issuing Entity", True, "issuing_entity", "Basic UDI-DI 签发机构。普通 UDI 通常按实际发码机构选择 GS1/HIBCC/ICCBBA/IFA；EUDAMED 通常用于 EUDAMED DI 等 legacy 场景。", "GS1", "下拉选择"),
    _col("Basic", "Basic - Manufacturer SRN*", "basic", "Manufacturer SRN", True, None, "制造商 SRN。非欧盟/EEA 制造商必须填写授权代表 SRN。", "CN-MF-000001", "文本"),
    _col("Basic", "Basic - Risk Class*", "basic", "Risk Class", True, "risk_class", "器械风险等级。MDR/MDD、AIMDD、IVDR/IVDD 取值不同。", "Class IIa", "下拉选择"),
    _col("Basic", "Basic - Applicable Legislation*", "basic", "Applicable Legislation", True, "legislation", "适用法规。MDR/IVDR 输出 Regulation Device；MDD/AIMDD/IVDD 输出 Legacy Device / EUDI。", "MDR", "下拉选择"),
    _col("Basic", "Basic - Device Type*", "basic", "Device Type", True, "device_type", "设备类型。普通器械选择 Regular Device。", "Regular Device", "下拉选择"),
    _col("Basic", "Basic - Device Name*", "basic", "Device Name/Model", True, None, "Basic UDI-DI 层级设备名称。Model 不适用于 BUDI 时填本列并留空 Basic - Device Model。", "Cardiac Stent", "文本"),
    _col("Basic", "Basic - EMDN Code*", "basic", "EMDN Code", True, None, "EUDAMED 使用的 EMDN 分类代码。", "Z120302", "文本"),
    _col("Basic", "Basic - Active Device", "basic", "Active Device", False, "boolean", "是否为有源设备。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Measuring Function", "basic", "Measuring Function", False, "boolean", "是否具有测量功能。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Administer Medicine", "basic", "Administer Medicine", False, "boolean", "是否用于给药。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Implantable", "basic", "Implantable", False, "boolean", "是否为植入式器械。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Reusable Surgical Instrument", "basic", "Reusable Surgical Instrument", False, "boolean", "是否为可重复使用的外科器械。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Presence of Human Tissues", "basic", "Presence of Human Tissues", False, "boolean", "是否含有人源组织。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Presence of Animal Tissues", "basic", "Presence of Animal Tissues", False, "boolean", "是否含有动物源组织。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Medicinal Product Device", "basic", "Medicinal Product Device", False, "boolean", "是否含药品/药物相关属性。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Companion Diagnostic (IVDR)", "basic", "Companion Diagnostic (IVDR)", False, "boolean", "IVDR 下是否为伴随诊断。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("Basic", "Basic - Near Patient Testing (IVDR)", "basic", "Near Patient Testing (IVDR)", False, "boolean", "IVDR 下是否为近患者检测。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("Basic", "Basic - Self-Testing (IVDR)", "basic", "Self-Testing (IVDR)", False, "boolean", "IVDR 下是否为自检。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("Basic", "Basic - Professional Testing (IVDR)", "basic", "Professional Testing (IVDR)", False, "boolean", "IVDR 下是否为专业人员检测。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("Basic", "Basic - Instrument (IVDR)", "basic", "Instrument (IVDR)", False, "boolean", "IVDR 下是否为仪器。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("Basic", "Basic - Microbial Origin (IVDR)", "basic", "Microbial Origin (IVDR)", False, "boolean", "IVDR 下是否具有微生物来源。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("Basic", "Basic - Additional Description", "basic", "Additional Description", False, None, "Basic UDI-DI 层级附加描述；不要填写随 UDI-DI 变化的尺寸规格。", "", "文本"),
    _col("Basic", "Basic - Device Model", "basic", "Device Model", False, None, "仅在 EUDAMED 中 Model 适用于 Basic UDI-DI 时填写；不适用则留空。", "", "文本"),
    _col("Basic", "Basic - Is it a Kit", "basic", "Is it a Kit", False, "boolean", "是否为 Kit。当前按官方 XSD 在 IVDR/IVDD 相关 kit 字段输出；旧模板中的 Basic - Kit (IVDR) 已合并到本列。MDR/MDD 暂无安全输出位置，不会强行写入 XML。", "FALSE", "TRUE / FALSE"),
    _col("Basic", "Basic - Authorised Representative SRN", "basic", "Authorised Representative SRN", False, None, "非欧盟/EEA 制造商的欧盟授权代表 SRN。", "NL-AR-000000247", "文本"),
    _col("Basic", "Basic - Special Device Type", "basic", "Special Device Type", False, None, "特殊设备类型。没有则留空。", "", "文本"),
    _col("Basic", "Basic - Reagent", "basic", "Reagent", False, "boolean", "IVDR 下是否为试剂。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("Basic", "Basic - Presence of Medicinal Substance", "basic", "Presence of Medicinal Substance", False, "boolean", "待审计字段：当前 XML 不单独输出；目前导出的是 Basic - Medicinal Product Device。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Is Suture/Staple/Filling/Brace (IIb Implant)", "basic", "Is Suture/Staple/Filling/Brace (IIb Implant)", False, None, "IIb 植入物特殊情形。仅适用时填写 TRUE/FALSE。", "", "文本 / TRUE / FALSE", "mdr_mdd"),
    _col("Meta", "UDI - Current Version", "meta", "udi_version", False, None, "条件必填：仅在使用 Update of UDI-DI / Master UDI-DI（UDI_DI.PATCH）时填写 EUDAMED 当前版本号；新上传留空。", "", "数字或文本", requirement="conditional"),
    _col("UDI", "UDI - UDI-DI Code*", "udi", "UDI-DI Code", True, None, "具体 UDI-DI 的唯一代码。", "06942495390010", "8-50 位字母数字"),
    _col("UDI", "UDI - UDI-DI Issuing Entity*", "udi", "UDI-DI Issuing Entity", True, "issuing_entity", "UDI-DI 签发机构。普通 UDI 通常按实际发码机构选择 GS1/HIBCC/ICCBBA/IFA；EUDAMED 通常用于 EUDAMED DI 等 legacy 场景。", "GS1", "下拉选择"),
    _col("UDI", "UDI - Device Status*", "udi", "Device Status", True, "device_status", "设备状态。On the EU market 时必须在 Market Info 填市场国家，且每个 UDI-DI 只能有一个首次投放市场国家。国家/市场信息错误应优先通过 update/create new version 修正，不应默认删除 UDI-DI 重建。", "On the EU market", "下拉选择"),
    _col("UDI", "UDI - Quantity of Device", "udi", "Quantity of Device", False, None, "销售单元中的设备数量。", "1", "数字"),
    _col("UDI", "UDI - Single Use Device*", "udi", "Single Use Device", True, "boolean", "是否为一次性使用器械。", "TRUE", "TRUE / FALSE"),
    _col("UDI", "UDI - Max Number of Reuses", "udi", "Max Number of Reuses", False, None, "如果可重复使用，填写最大重复使用次数。一次性使用通常填 0。", "0", "数字"),
    _col("UDI", "UDI - Device Labelled as Sterile*", "udi", "Device Labelled as Sterile", True, "boolean", "标签上是否标示为无菌。", "FALSE", "TRUE / FALSE"),
    _col("UDI", "UDI - Needs Sterilisation Before Use", "udi", "Needs Sterilisation Before Use", False, "boolean", "使用前是否需要灭菌。", "FALSE", "TRUE / FALSE"),
    _col("UDI", "UDI - Containing Latex*", "udi", "Containing Latex", True, "boolean", "是否含天然橡胶乳胶。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("UDI", "UDI - Reprocessed Single Use Device", "udi", "Reprocessed Single Use Device", False, "boolean", "是否为重复处理的一次性使用器械。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("UDI", "UDI - New Device (IVDR)", "udi", "New Device (IVDR)", False, "boolean", "IVDR 下是否为新设备。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("UDI", "UDI - Direct Marking", "udi", "Direct Marking", False, "boolean", "是否进行直接标识。", "FALSE", "TRUE / FALSE"),
    _col("UDI", "UDI - DM DI Same as UDI-DI", "udi", "DM DI Same as UDI-DI", False, "boolean", "直接标识 DI 是否与 UDI-DI 相同。", "TRUE", "TRUE / FALSE"),
    _col("UDI", "UDI - DM Issuing Entity", "udi", "DM Issuing Entity", False, "issuing_entity", "直接标识 DI 的签发机构。", "GS1", "下拉选择"),
    _col("UDI", "UDI - DM DI Code", "udi", "DM DI Code", False, None, "直接标识 DI 代码。", "", "文本"),
    _col("UDI", "UDI - Unit of Use DI Code", "udi", "Unit of Use DI Code", False, None, "使用单元 DI 代码。", "", "文本"),
    _col("UDI", "UDI - Unit of Use Issuing Entity", "udi", "Unit of Use Issuing Entity", False, "issuing_entity", "使用单元 DI 的签发机构。", "GS1", "下拉选择"),
    _col("UDI", "UDI - Secondary UDI-DI Code", "udi", "Secondary UDI-DI Code", False, None, "第二 UDI-DI。", "", "文本"),
    _col("UDI", "UDI - Secondary Issuing Entity", "udi", "Secondary Issuing Entity", False, "issuing_entity", "第二 UDI-DI 的签发机构。", "GS1", "下拉选择"),
    _col("UDI", "UDI - Trade Name Applicable*", "udi", "Trade Name Applicable", True, "boolean", "是否适用商品名字段。TRUE 时通常必须填写 Trade Name。", "TRUE", "TRUE / FALSE"),
    _col("UDI", "UDI - Trade Name", "udi", "Trade Name", False, None, "商品名快捷列。若上一列为 TRUE，通常应填写；多语言/多个商品名请使用 Trade Names sheet。", "Trade name", "文本", requirement="conditional"),
    _col("UDI", "UDI - Trade Name Language", "udi", "Trade Name Language", False, "language_any", "商品名快捷列语言。ANY 表示不限定具体语言；不会自动翻译，也不代表只能有一个 Trade Name。多语言/多个商品名请使用 Trade Names sheet。", "ANY", "下拉选择", requirement="conditional"),
    _col("UDI", "UDI - eIFU URL", "udi", "eIFU URL", False, None, "电子说明书链接。当前官方 UDI-DI XML 未确认安全输出路径，本工具不输出到 XML，不会提交到 EUDAMED。", "", "URL"),
    _col("UDI", "UDI - Reference Number*", "udi", "Reference Number", True, None, "Reference / Catalogue Number；EUDAMED XML 必填。", "REF-001", "文本"),
    _col("UDI", "UDI - Product Designer SRN", "udi", "Product Designer SRN", False, None, "产品原始制造商/设计者 SRN；当前独立 update service 未实现。", "", "文本"),
    _col("UDI", "UDI - Product Designer ID", "udi", "Product Designer ID", False, None, "产品设计者内部 ID；当前独立 update service 未实现。", "", "文本"),
    _col("UDI", "UDI - PI Lot/Batch Number*", "udi", "PI Lot/Batch Number", True, "boolean", "生产标识是否包含批号/批次号。", "TRUE", "TRUE / FALSE"),
    _col("UDI", "UDI - PI Expiration Date*", "udi", "PI Expiration Date", True, "boolean", "生产标识是否包含失效日期。", "TRUE", "TRUE / FALSE"),
    _col("UDI", "UDI - PI Manufacturing Date", "udi", "PI Manufacturing Date", False, "boolean", "生产标识是否包含生产日期。", "TRUE", "TRUE / FALSE"),
    _col("UDI", "UDI - PI Serial Number", "udi", "PI Serial Number", False, "boolean", "生产标识是否包含序列号。", "FALSE", "TRUE / FALSE"),
    _col("UDI", "UDI - PI Software Identification", "udi", "PI Software Identification", False, "boolean", "生产标识是否包含软件识别号。", "FALSE", "TRUE / FALSE"),
    _col("UDI", "UDI - Nomenclature Code*", "udi", "Nomenclature Code", True, None, "命名代码，例如 EMDN。", "M0201030201", "文本"),
    _col("UDI", "UDI - Nomenclature System", "udi", "Nomenclature System", False, None, "命名系统。通常为 EMDN。", "EMDN", "文本"),
    _col("UDI", "UDI - Additional Description", "udi", "Additional Description", False, None, "UDI-DI 层级附加描述；可填写尺寸、规格、包装形式等随单个 UDI-DI 变化的信息。", "40S, 15 threads, 10x10cm-4ply", "文本"),
    _col("UDI", "UDI - Description Language", "udi", "Description Language", False, "language", "附加描述语言。", "en", "下拉选择"),
    _col("UDI", "UDI - Public Website", "udi", "Public Website", False, None, "公开产品网址。", "", "URL"),
    _col("UDI", "UDI - Public Email", "udi", "Public Email", False, None, "公开联系邮箱。当前普通 UDI-DI XML 未确认安全输出路径，本工具不输出到 XML，不会提交到 EUDAMED；公开网址 Public Website 已输出。", "", "邮箱"),
]


RELATED_SHEETS = OrderedDict(
    {
        "Trade Names": {
            "target": "Trade Names",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "条件必填：主表 Trade Name 快捷列不够用、需要多语言/多个商品名时才填写本 sheet。若填写 Trade Names 行，本列必须关联主表 UDI-DI Code。", "06942495390010", "文本", requirement="conditional"),
                _related_col("Trade Name*", "Trade Name", True, None, "条件必填：若填写 Trade Names 行，本列为 UDI-DI 层商品名，必须填写；可同语言多名称或不同语言多名称。", "Trade name", "文本", requirement="conditional"),
                _related_col("Language*", "Language", True, "language_any", "条件必填：若填写 Trade Names 行，本列为商品名语言，必须填写。ANY 表示不限定具体语言；不会自动翻译，也不代表只能有一个 Trade Name。", "ANY", "下拉选择", requirement="conditional"),
            ],
        },
        "Market Info": {
            "target": "Market Information",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "条件必填：当主表 Device Status 为 On the EU market，或使用 Update market information service 时填写 Market Info。若填写 Market Info 行，本列必须关联主表 UDI-DI Code。", "06942495390010", "文本", requirement="conditional"),
                _related_col("Country Code*", "Country Code", True, "country_code", "条件必填：若填写 Market Info 行，本列为 UDI-DI 层 made available / 市场国家代码，必须填写；希腊使用官方代码 EL，不是 GR。", "IT", "下拉选择", requirement="conditional"),
                _related_col("Placed on Market", "Placed on Market", False, "boolean", "条件必填/业务核对：若填写 Market Info 行，建议说明该国家是否已投放市场。", "TRUE", "TRUE / FALSE", requirement="conditional"),
                _related_col("Start Date", "Start Date", False, None, "条件必填：若该国家已投放或将投放市场，建议填写上市开始日期；无法确认时先与客户核对。", "2026-01-01", "YYYY-MM-DD", requirement="conditional"),
                _related_col("End Date", "End Date", False, None, "条件必填：仅当该国家已经或计划停止上市时填写结束日期；仍在销售则留空。", "", "YYYY-MM-DD", requirement="conditional"),
                _related_col("Originally Placed on Market*", "Originally Placed on Market", True, "boolean", "条件必填：若填写 Market Info，一个 On the EU market UDI-DI 必须且只能有一条 TRUE；其它 made available 国家应填写 FALSE。国家/市场信息错误通常通过 update/create new version 修正。", "TRUE", "TRUE / FALSE", requirement="conditional"),
            ],
        },
        "Package Info": {
            "target": "Package Information",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "条件必填：只有产品存在 container package / 多层包装 DI 时才需要填写 Package Info。若填写本 sheet 任意包装行，本列用于关联主表 UDI-DI Code，必须填写；无包装层级时整张 sheet 可留空。", "06942495390010", "文本", requirement="conditional"),
                _related_col("Local - Package Level", "Package Level", False, None, "可选本地辅助说明：包装层级，例如中盒/外箱。不会直接输出到 EUDAMED XML。", "Middle layer", "文本"),
                _related_col("Local - Package Type", "Package Type", False, None, "可选本地辅助说明：包装类型，例如 box/carton/pallet。不会直接输出到 EUDAMED XML。", "Carton", "文本"),
                _related_col("Package UDI-DI Code*", "Package UDI-DI Code", True, None, "条件必填：只有存在包装 DI 时填写。若填写 Package Info 行，本列为包装层级自身的 Package UDI-DI，必须填写；无包装层级时整张 sheet 可留空。", "16942495390017", "文本", requirement="conditional"),
                _related_col("Package Issuing Entity*", "Package Issuing Entity", True, "issuing_entity", "条件必填：若填写 Package Info 行，本列为 Package UDI-DI 的签发机构，必须填写。", "GS1", "下拉选择", requirement="conditional"),
                _related_col("Contains DI Code", "Contains DI Code", False, None, "条件必填：该包装直接包含的 child DI。可填主 UDI-DI，也可填同一 UDI-DI 包装结构里的下一级 Package DI；留空则默认包含主 UDI-DI。", "06942495390010", "文本", requirement="conditional"),
                _related_col("Contains DI Issuing Entity", "Contains DI Issuing Entity", False, "issuing_entity", "条件必填：child DI 的签发机构。留空时按 child 类型自动使用主 UDI-DI 或对应 Package DI 的签发机构。", "GS1", "下拉选择", requirement="conditional"),
                _related_col("Quantity per Package*", "Quantity per Package", True, None, "条件必填：若填写 Package Info 行，本列为每个 Package DI 中包含 child DI 的数量，必须为正整数。", "10", "正整数", requirement="conditional"),
            ],
        },
        "Clinical Sizes": {
            "target": "Clinical Sizes",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "条件必填：仅 MDR 设备存在结构化 Clinical Sizes 时填写。若填写 Clinical Sizes 行，本列必须关联主表 UDI-DI Code。", "06942495390010", "文本", requirement="conditional"),
                _related_col("Clinical Size Type*", "Clinical Size Type", True, "clinical_size_type", "条件必填：若填写 Clinical Sizes 行，本列必须选择官方 ClinicalSizeTypeEnum。CST999 - OTHER 时必须填写 Clinical Size Type Description。", "CST48 - Length", "下拉选择", requirement="conditional"),
                _related_col("Clinical Size Type Description", "Clinical Size Type Description", False, None, "条件必填：Clinical Size Type 为 CST999 - OTHER 时填写具体说明；其它类型通常留空。", "", "文本", requirement="conditional"),
                _related_col("Description Language", "Description Language", False, "language", "条件必填：填写 Clinical Size Type Description 时说明语言。", "en", "下拉选择", requirement="conditional"),
                _related_col("Precision*", "Precision", True, "clinical_size_precision", "条件必填：Range=范围值，Value=单一数值，Text=文本值。", "Value", "下拉选择", requirement="conditional"),
                _related_col("Minimum", "Minimum", False, None, "条件必填：Precision=Range 时填写最小值。", "5", "数字", requirement="conditional"),
                _related_col("Maximum", "Maximum", False, None, "条件必填：Precision=Range 时填写最大值。", "10", "数字", requirement="conditional"),
                _related_col("Value", "Value", False, None, "条件必填：Precision=Value 时填写单一数值。", "10", "数字", requirement="conditional"),
                _related_col("Text Value", "Text Value", False, None, "条件必填：Precision=Text 时填写文本尺寸。", "Small", "文本", requirement="conditional"),
                _related_col("Measure Unit", "Measure Unit", False, "clinical_size_unit", "条件必填：Precision=Range 或 Value 时必须选择官方 ClinicalSizeUnitEnum。MU999 - OTHER 时必须填写 Measure Unit Description。", "MU08 - centimetre (cm)", "下拉选择", requirement="conditional"),
                _related_col("Measure Unit Description", "Measure Unit Description", False, None, "条件必填：Measure Unit 为 MU999 - OTHER 时填写单位说明；其它单位通常留空。", "", "文本", requirement="conditional"),
                _related_col("Measure Unit Description Language", "Measure Unit Description Language", False, "language", "条件必填：填写 Measure Unit Description 时说明语言。", "en", "下拉选择", requirement="conditional"),
            ],
        },
        "Annex XVI Purposes": {
            "target": "Annex XVI Purposes",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "条件必填：仅 MDR Annex XVI 非医疗目的产品填写。若填写 Annex XVI Purposes 行，本列必须关联主表 UDI-DI Code。", "06942495390010", "文本", requirement="conditional"),
                _related_col("Non-Medical Device Type*", "Non-Medical Device Type", True, "annex_xvi_nmd", "条件必填：若填写 Annex XVI Purposes 行，本列必须选择官方 NonMedicalDeviceEnum；一个 UDI-DI 可填写多行。", "CONTACT_LENSES - Contact Lenses", "下拉选择", requirement="conditional"),
            ],
        },
        "Critical Warnings": {
            "target": "Critical Warnings",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "条件必填：只有产品标签/说明书存在 critical warning 或 contraindication 时填写本 sheet。若填写 Critical Warnings 行，本列必须关联主表 UDI-DI Code。", "06942495390010", "文本", requirement="conditional"),
                _related_col("Warning Type", "Warning Type", False, "critical_warning", "条件必填：若填写 Critical Warnings 行，通常必须选择官方 CriticalWarningEnum。选择 CW999 - OTHER 时必须填写 Comment 且 Language 不能为 ANY。", "CW007 - Do not use if package is damaged", "下拉选择", requirement="conditional"),
                _related_col("Language", "Language", False, "language_any", "条件必填：CW999 - OTHER 需要具体语言；非 OTHER 且填写 Comment 时导出为 ANY。", "ANY", "下拉选择", requirement="conditional"),
                _related_col("Comment", "Comment", False, None, "条件必填：CW999 - OTHER 时必填；其它 warning 只有需要补充说明时填写。", "Do not use if package is damaged", "文本", requirement="conditional"),
            ],
        },
        "Storage Conditions": {
            "target": "Storage Conditions",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "条件必填：只有产品存在储存/处理条件时填写本 sheet。若填写 Storage Conditions 行，本列必须关联主表 UDI-DI Code。", "06942495390010", "文本", requirement="conditional"),
                _related_col("Storage Condition Type", "Storage Condition Type", False, "storage_condition", "条件必填：若填写 Storage Conditions 行，通常必须选择官方 StorageHandlingConditionEnum。选择 SHC099 - OTHER 时必须填写 Description 且 Language 不能为 ANY。", "SHC005 - Keep dry", "下拉选择", requirement="conditional"),
                _related_col("Language", "Language", False, "language_any", "条件必填：SHC099 - OTHER 需要具体语言；非 OTHER 且填写 Description 时导出为 ANY。", "ANY", "下拉选择", requirement="conditional"),
                _related_col("Description", "Description", False, None, "条件必填：SHC099 - OTHER 时必填；其它 storage condition 只有需要补充说明时填写。", "Keep dry", "文本", requirement="conditional"),
            ],
        },
        "CMR Substances": {
            "target": "CMR Substances",
            "columns": [
                _related_col("Basic UDI-DI Code*", "Basic UDI-DI Code", True, None, "条件必填：只有 Basic UDI-DI 涉及 CMR / endocrine disrupting substances 时填写本 sheet。若填写 CMR 行，本列必须关联主表 Basic UDI-DI Code。", "BASIC001234", "文本", requirement="conditional"),
                _related_col("Substance Type", "Substance Type", False, None, "条件必填：若填写 CMR 行，建议填写物质类型，例如 CMR 1A/1B。", "CMR 1A", "文本", requirement="conditional"),
                _related_col("CAS Code", "CAS Code", False, None, "条件必填：如有 CAS 编码应填写；没有时与客户确认其它识别信息。", "50-00-0", "文本", requirement="conditional"),
                _related_col("EC Code", "EC Code", False, None, "条件必填：如有 EC 编码应填写；没有则留空。", "200-001-8", "文本", requirement="conditional"),
                _related_col("Language", "Language", False, "language_any", "条件必填：若填写 Substance Name，本列用于说明物质名称语言；不限定具体语言时可用 ANY。", "ANY", "下拉选择", requirement="conditional"),
                _related_col("Substance Name", "Substance Name", False, None, "条件必填：若填写 CMR 行，建议填写物质名称。", "Formaldehyde", "文本", requirement="conditional"),
            ],
        },
        "Device Certificates": {
            "target": "Device Certificates",
            "columns": [
                _related_col("Basic UDI-DI Code*", "Basic UDI-DI Code", True, None, "条件必填：只有需要 NB validation / product certificate 覆盖的 Basic UDI-DI 才填写本 sheet。若填写证书行，本列必须关联主表 Basic UDI-DI Code。", "BASIC001234", "文本", requirement="conditional"),
                _related_col("Certificate Type*", "Certificate Type", True, "certificate_type", "条件必填：若填写证书行，本列必须选择官方 GenericCertificateTypeEnum，例如 MDR_TYPE_EXAMINATION、MDR_TECHNICAL_DOCUMENTATION、MDD_III。", "MDR_TYPE_EXAMINATION", "下拉选择", requirement="conditional"),
                _related_col("Notified Body ID*", "Notified Body ID", True, None, "条件必填：若填写证书行，本列必须填写签发 product certificate 的公告机构 NANDO ID / NB Actor Code，例如 0483。", "0483", "文本", requirement="conditional"),
                _related_col("Certificate Number", "Certificate Number", False, None, "条件必填：Legacy 指令证书通常需要填写；Regulation certificate 如可取得建议填写。", "CE-123456", "文本", requirement="conditional"),
                _related_col("Revision Number", "Revision Number", False, None, "条件必填：证书存在 revision number 时填写；没有则留空。", "1", "文本", requirement="conditional"),
                _related_col("Expiry Date", "Expiry Date", False, None, "条件必填：证书有有效期时填写；Legacy 指令证书通常需要填写。", "2028-12-31", "YYYY-MM-DD", requirement="conditional"),
            ],
        },
    }
)


ENTRY_SHEETS = OrderedDict(
    {
        "MDR_MDD": {"applies": {"all", "mdr_mdd"}, "default_legislation": "MDR"},
        "IVDR_IVDD": {"applies": {"all", "ivdr_ivdd"}, "default_legislation": "IVDR"},
    }
)


ENUM_SOURCES = OrderedDict(
    {
        "boolean": ["TRUE", "FALSE"],
        "issuing_entity": _xsd_issuing_entity_values(),
        "risk_class": [
            "Class I", "Class IIa", "Class IIb", "Class III",
            "Class A", "Class B", "Class C", "Class D",
            "AIMDD", "IVD Annex II List A", "IVD Annex II List B", "IVD Self Testing", "IVD General",
        ],
        "legislation": ["MDR", "MDD", "AIMDD", "IVDR", "IVDD"],
        "device_type": ["Regular Device", "System", "Procedure Pack"],
        "device_status": [
            "On the EU market",
            "No longer placed on the EU market",
            "Not intended for the EU market",
        ],
        "language": _xsd_language_values(include_any=False),
        "language_any": _xsd_language_values(include_any=True),
        "country_code": _xsd_country_values(),
        "storage_condition": _xsd_enum_values("StorageHandlingConditionEnum", "SHC099"),
        "critical_warning": _xsd_enum_values("CriticalWarningEnum", "CW999"),
        "certificate_type": _certificate_type_values(),
        "clinical_size_type": _clinical_size_type_values(),
        "clinical_size_unit": _clinical_size_unit_values(),
        "clinical_size_precision": ["Range", "Value", "Text"],
        "annex_xvi_nmd": _annex_xvi_values(),
    }
)


def columns_for_entry_sheet(sheet_name: str) -> list[dict]:
    applies = ENTRY_SHEETS[sheet_name]["applies"]
    return [item for item in MAIN_COLUMNS if item["applies"] in applies]


ALL_COLUMNS = MAIN_COLUMNS + [col for spec in RELATED_SHEETS.values() for col in spec["columns"]]
BASIC_HEADERS = [item["header"] for item in MAIN_COLUMNS if item["entity"] == "basic"]
UDI_HEADERS = [item["header"] for item in MAIN_COLUMNS if item["entity"] == "udi"]
META_HEADERS = [item["header"] for item in MAIN_COLUMNS if item["entity"] == "meta"]
RELATED_HEADERS = [item["header"] for item in ALL_COLUMNS if item["entity"] == "related"]
