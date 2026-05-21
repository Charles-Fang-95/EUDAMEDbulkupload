from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT_DIR = Path(__file__).resolve().parent.parent
XSD_BASE = ROOT_DIR / "official_docs" / "unpacked" / "xsd_production" / "data" / "Entity"
COMMON_DEVICE_XSD = XSD_BASE / "Device" / "CommonDeviceType.xsd"
COUNTRY_XSD = XSD_BASE / "Common" / "CountryEnum.xsd"
LANGUAGE_XSD = XSD_BASE / "Common" / "LanguageSpecificNameType.xsd"
ISSUING_ENTITY_XSD = XSD_BASE / "Device" / "RegulationDevice" / "UDIDIType.xsd"


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


def _xsd_enum_values(type_name: str, other_code: str = "") -> list[str]:
    if not COMMON_DEVICE_XSD.exists():
        return []
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    root = ET.parse(COMMON_DEVICE_XSD).getroot()
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


MAIN_COLUMNS = [
    _col("Meta", "Local - Record ID", "meta", "record_id", False, None, "用户自定义行号或内部编码，仅供本地追踪。", "ROW-001", "自由文本"),
    _col("Meta", "Basic - Current Version", "meta", "basic_version", False, None, "更新 Basic_UDI.PATCH 时填写 EUDAMED 当前版本号；新上传留空。", "", "数字或文本"),
    _col("Basic", "Basic - Basic UDI-DI Code*", "basic", "Basic UDI-DI Code", True, None, "Basic UDI-DI 的唯一代码。一个 Basic 可对应多个 UDI-DI。", "BASIC001234", "8-50 位字母数字"),
    _col("Basic", "Basic - Issuing Entity*", "basic", "Issuing Entity", True, "issuing_entity", "Basic UDI-DI 签发机构。常见为 GS1。", "GS1", "下拉选择"),
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
    _col("Basic", "Basic - Kit (IVDR)", "basic", "Kit (IVDR)", False, "boolean", "IVDR 下是否为试剂盒。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("Basic", "Basic - Microbial Origin (IVDR)", "basic", "Microbial Origin (IVDR)", False, "boolean", "IVDR 下是否具有微生物来源。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("Basic", "Basic - Additional Description", "basic", "Additional Description", False, None, "Basic UDI-DI 层级附加描述；不要填写随 UDI-DI 变化的尺寸规格。", "", "文本"),
    _col("Basic", "Basic - Device Model", "basic", "Device Model", False, None, "仅在 EUDAMED 中 Model 适用于 Basic UDI-DI 时填写；不适用则留空。", "", "文本"),
    _col("Basic", "Basic - Is it a Kit", "basic", "Is it a Kit", False, "boolean", "是否为套装/kit。", "FALSE", "TRUE / FALSE"),
    _col("Basic", "Basic - Authorised Representative SRN", "basic", "Authorised Representative SRN", False, None, "非欧盟/EEA 制造商的欧盟授权代表 SRN。", "NL-AR-000000247", "文本"),
    _col("Basic", "Basic - Special Device Type", "basic", "Special Device Type", False, None, "特殊设备类型。没有则留空。", "", "文本"),
    _col("Basic", "Basic - Reagent", "basic", "Reagent", False, "boolean", "IVDR 下是否为试剂。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("Basic", "Basic - Presence of Medicinal Substance", "basic", "Presence of Medicinal Substance", False, "boolean", "是否含药物物质。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Is Suture/Staple/Filling/Brace (IIb Implant)", "basic", "Is Suture/Staple/Filling/Brace (IIb Implant)", False, None, "IIb 植入物特殊情形。仅适用时填写 TRUE/FALSE。", "", "文本 / TRUE / FALSE", "mdr_mdd"),
    _col("Basic", "Basic - Certificate Number", "basic", "Certificate Number", False, None, "相关 CE 证书编号；当前 XML 暂不输出证书链接。", "", "文本"),
    _col("Meta", "UDI - Current Version", "meta", "udi_version", False, None, "更新 UDI_DI.PATCH 时填写 EUDAMED 当前版本号；新上传留空。", "", "数字或文本"),
    _col("UDI", "UDI - UDI-DI Code*", "udi", "UDI-DI Code", True, None, "具体 UDI-DI 的唯一代码。", "06942495390010", "8-50 位字母数字"),
    _col("UDI", "UDI - UDI-DI Issuing Entity*", "udi", "UDI-DI Issuing Entity", True, "issuing_entity", "UDI-DI 签发机构。", "GS1", "下拉选择"),
    _col("UDI", "UDI - Device Status*", "udi", "Device Status", True, "device_status", "设备状态。On the EU market 时必须在 Market Info 填市场国家，且每个 UDI-DI 只能有一个首次投放市场国家。国家/市场信息错误应优先通过 update/create new version 修正，不应默认删除 UDI-DI 重建。", "On the EU market", "下拉选择"),
    _col("UDI", "UDI - Quantity of Device", "udi", "Quantity of Device", False, None, "销售单元中的设备数量。", "1", "数字"),
    _col("UDI", "UDI - Single Use Device*", "udi", "Single Use Device", True, "boolean", "是否为一次性使用器械。", "TRUE", "TRUE / FALSE"),
    _col("UDI", "UDI - Max Number of Reuses", "udi", "Max Number of Reuses", False, None, "如果可重复使用，填写最大重复使用次数。一次性使用通常填 0。", "0", "数字"),
    _col("UDI", "UDI - Device Labelled as Sterile*", "udi", "Device Labelled as Sterile", True, "boolean", "标签上是否标示为无菌。", "FALSE", "TRUE / FALSE"),
    _col("UDI", "UDI - Needs Sterilisation Before Use", "udi", "Needs Sterilisation Before Use", False, "boolean", "使用前是否需要灭菌。", "FALSE", "TRUE / FALSE"),
    _col("UDI", "UDI - Containing Latex*", "udi", "Containing Latex", True, "boolean", "是否含天然橡胶乳胶。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("UDI", "UDI - Reprocessed Single Use Device", "udi", "Reprocessed Single Use Device", False, "boolean", "是否为重复处理的一次性使用器械。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
    _col("UDI", "UDI - New Device (IVDR)", "udi", "New Device (IVDR)", False, "boolean", "IVDR 下是否为新设备。", "FALSE", "TRUE / FALSE", "ivdr_ivdd"),
    _col("UDI", "UDI - Purpose Other Than Medical", "udi", "Purpose Other Than Medical", False, "boolean", "仅 Master UDI-DI 相关；普通 UDI-DI 当前不输出该字段。", "FALSE", "TRUE / FALSE", "mdr_mdd"),
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
    _col("UDI", "UDI - Trade Name Language", "udi", "Trade Name Language", False, "language_any", "商品名快捷列语言。可选 ANY 表示该商品名不限定具体语言；多语言/多个商品名请使用 Trade Names sheet。", "ANY", "下拉选择", requirement="conditional"),
    _col("UDI", "UDI - eIFU URL", "udi", "eIFU URL", False, None, "电子说明书链接。", "", "URL"),
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
    _col("UDI", "UDI - Clinical Size Value", "udi", "Clinical Size Value", False, None, "临床尺寸值；当前 XML 暂不输出结构化临床尺寸。", "", "数字或文本"),
    _col("UDI", "UDI - Clinical Size Unit", "udi", "Clinical Size Unit", False, None, "临床尺寸单位；当前 XML 暂不输出结构化临床尺寸。", "", "文本"),
    _col("UDI", "UDI - Additional Description", "udi", "Additional Description", False, None, "UDI-DI 层级附加描述；可填写尺寸、规格、包装形式等随单个 UDI-DI 变化的信息。", "40S, 15 threads, 10x10cm-4ply", "文本"),
    _col("UDI", "UDI - Description Language", "udi", "Description Language", False, "language", "附加描述语言。", "en", "下拉选择"),
    _col("UDI", "UDI - Public Website", "udi", "Public Website", False, None, "公开产品网址。", "", "URL"),
    _col("UDI", "UDI - Public Email", "udi", "Public Email", False, None, "公开联系邮箱。", "", "邮箱"),
]


RELATED_SHEETS = OrderedDict(
    {
        "Trade Names": {
            "target": "Trade Names",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "关联主表中的 UDI-DI Code。一个 UDI-DI 可填写多行 Trade Name。", "06942495390010", "文本"),
                _related_col("Trade Name*", "Trade Name", True, None, "UDI-DI 层商品名。可同语言多名称或不同语言多名称。", "Trade name", "文本"),
                _related_col("Language*", "Language", True, "language_any", "商品名语言。可选 ANY 表示该商品名不限定具体语言。", "ANY", "下拉选择"),
            ],
        },
        "Market Info": {
            "target": "Market Information",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "关联主表中的 UDI-DI Code。", "06942495390010", "文本"),
                _related_col("Country Code*", "Country Code", True, "country_code", "UDI-DI 层 made available / 市场国家代码，不属于 BUDI 层。一个 UDI-DI 可有多个 made available 国家。", "IT", "下拉选择"),
                _related_col("Placed on Market", "Placed on Market", False, "boolean", "是否已投放市场；保留给业务核对。", "TRUE", "TRUE / FALSE"),
                _related_col("Start Date", "Start Date", False, None, "在该国家上市开始日期。", "2026-01-01", "YYYY-MM-DD"),
                _related_col("End Date", "End Date", False, None, "在该国家上市结束日期。", "", "YYYY-MM-DD"),
                _related_col("Originally Placed on Market*", "Originally Placed on Market", True, "boolean", "是否首次投放市场成员国。每个 On the EU market UDI-DI 必须且只能有一条 TRUE；其它 made available 国家应填写 FALSE。国家/市场信息错误通常通过 update/create new version 修正，不应默认删除 UDI-DI 重建。", "TRUE", "TRUE / FALSE"),
            ],
        },
        "Package Info": {
            "target": "Package Information",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "关联主表中的 UDI-DI Code。", "06942495390010", "文本"),
                _related_col("Local - Package Level", "Package Level", False, None, "本地辅助说明：包装层级，例如中盒/外箱。不会直接输出到 EUDAMED XML。", "Middle layer", "文本"),
                _related_col("Local - Package Type", "Package Type", False, None, "本地辅助说明：包装类型，例如 box/carton/pallet。不会直接输出到 EUDAMED XML。", "Carton", "文本"),
                _related_col("Package UDI-DI Code*", "Package UDI-DI Code", True, None, "包装层级自身的 Package UDI-DI。填写 Package Info 行时必填。", "16942495390017", "文本"),
                _related_col("Package Issuing Entity*", "Package Issuing Entity", True, "issuing_entity", "Package UDI-DI 的签发机构。填写 Package Info 行时必填。", "GS1", "下拉选择"),
                _related_col("Contains DI Code", "Contains DI Code", False, None, "该包装直接包含的 child DI。可填主 UDI-DI，也可填同一 UDI-DI 包装结构里的下一级 Package DI；留空则默认包含主 UDI-DI。", "06942495390010", "文本"),
                _related_col("Contains DI Issuing Entity", "Contains DI Issuing Entity", False, "issuing_entity", "child DI 的签发机构。留空时按 child 类型自动使用主 UDI-DI 或对应 Package DI 的签发机构。", "GS1", "下拉选择"),
                _related_col("Quantity per Package*", "Quantity per Package", True, None, "每个 Package DI 中包含 child DI 的数量，必须为正整数。", "10", "正整数"),
            ],
        },
        "Critical Warnings": {
            "target": "Critical Warnings",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "关联主表中的 UDI-DI Code。", "06942495390010", "文本"),
                _related_col("Warning Type", "Warning Type", False, "critical_warning", "官方 CriticalWarningEnum。选择 CW999 - OTHER 时必须填写 Comment 且 Language 不能为 ANY。", "CW007 - Do not use if package is damaged", "下拉选择", requirement="conditional"),
                _related_col("Language", "Language", False, "language_any", "说明语言。非 OTHER 且填写 Comment 时导出为 ANY；OTHER 需要具体语言。", "ANY", "下拉选择", requirement="conditional"),
                _related_col("Comment", "Comment", False, None, "警告补充说明。CW999 - OTHER 时必填。", "Do not use if package is damaged", "文本", requirement="conditional"),
            ],
        },
        "Storage Conditions": {
            "target": "Storage Conditions",
            "columns": [
                _related_col("UDI-DI Code*", "UDI-DI Code", True, None, "关联主表中的 UDI-DI Code。", "06942495390010", "文本"),
                _related_col("Storage Condition Type", "Storage Condition Type", False, "storage_condition", "官方 StorageHandlingConditionEnum。选择 SHC099 - OTHER 时必须填写 Description 且 Language 不能为 ANY。", "SHC005 - Keep dry", "下拉选择", requirement="conditional"),
                _related_col("Language", "Language", False, "language_any", "说明语言。非 OTHER 且填写 Description 时导出为 ANY；OTHER 需要具体语言。", "ANY", "下拉选择", requirement="conditional"),
                _related_col("Description", "Description", False, None, "储存/处理条件补充说明。SHC099 - OTHER 时必填。", "Keep dry", "文本", requirement="conditional"),
            ],
        },
        "CMR Substances": {
            "target": "CMR Substances",
            "columns": [
                _related_col("Basic UDI-DI Code*", "Basic UDI-DI Code", True, None, "关联主表中的 Basic UDI-DI Code。", "BASIC001234", "文本"),
                _related_col("Substance Type", "Substance Type", False, None, "物质类型。", "CMR 1A", "文本"),
                _related_col("CAS Code", "CAS Code", False, None, "CAS 编码。", "50-00-0", "文本"),
                _related_col("EC Code", "EC Code", False, None, "EC 编码。", "200-001-8", "文本"),
                _related_col("Language", "Language", False, "language", "物质名称语言。", "en", "下拉选择"),
                _related_col("Substance Name", "Substance Name", False, None, "物质名称。", "Formaldehyde", "文本"),
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
