import sys
import os
from pathlib import Path

if getattr(sys, "frozen", False):
    ROOT_DIR = Path(sys.executable).resolve().parent
    RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", ROOT_DIR))
    APP_DIR = RESOURCE_ROOT / "local_beta"
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent
    RESOURCE_ROOT = ROOT_DIR
    APP_DIR = Path(__file__).resolve().parent

DATA_DIR = Path(os.environ.get("EUDAMED_DATA_DIR", ROOT_DIR / "local_beta_data"))
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "eudamed_beta.db"
STATIC_DIR = APP_DIR / "static"
STYLE_PATH = STATIC_DIR / "style.css"
TEMPLATE_VERSION = "v2.12"
TEMPLATE_FILENAME = f"EUDAMED_Template_{TEMPLATE_VERSION}.xlsx"
TEMPLATE_PATH = RESOURCE_ROOT / TEMPLATE_FILENAME
TEMPLATE_EN_FILENAME = f"EUDAMED_Template_{TEMPLATE_VERSION}_EN.xlsx"
TEMPLATE_EN_PATH = RESOURCE_ROOT / TEMPLATE_EN_FILENAME
VENDOR_LIB = RESOURCE_ROOT / "EUDAMED_TOOL_v2" / "lib"
TOOL_DIR = RESOURCE_ROOT / "EUDAMED_TOOL_v2"
OFFICIAL_DOCS_DIR = RESOURCE_ROOT / "official_docs"
LOCAL_MESSAGE_XSD = OFFICIAL_DOCS_DIR / "unpacked" / "xsd_production" / "service" / "Message" / "MessageType.xsd"
TECHNICAL_DOCUMENTATION_URL = "https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html"

SCHEMA_VERSION = "3.0.30"
BULK_UPLOAD_ENTITY_LIMIT = 300
BULK_UPLOAD_LIMIT_SOURCE = (
    "EUDAMED official XSD schemas.zip 3.0.30, "
    "service/Message/MessageType.xsd payload xs:choice maxOccurs=300"
)

# 工具自身版本与最近更新日期（页脚展示，由维护者更新）
# TOOL_VERSION 是语义化版本号，用于「检查更新」比对；TOOL_VERSION_LABEL 给人看，可带中文修饰。
TOOL_VERSION = "0.9.8"
TOOL_VERSION_LABEL = "0.9.8 · 公开测试版"
TOOL_UPDATED = "2026-08-14"

# 检查更新：优先 GitHub Releases API，失败时尝试 Gitee Release API；留空时帮助页显示「未配置更新源」。
RELEASES_API_URL = "https://api.github.com/repos/Charles-Fang-95/EUDAMEDbulkupload/releases/latest"
RELEASES_PAGE_URL = "https://github.com/Charles-Fang-95/EUDAMEDbulkupload/releases"
GITEE_RELEASES_API_URL = "https://gitee.com/api/v5/repos/Charles-Fang-95/EUDAMEDbulkupload/releases?per_page=1"
GITEE_RELEASES_PAGE_URL = "https://gitee.com/Charles-Fang-95/EUDAMEDbulkupload/releases"

# 版权信息（页脚 / 帮助页展示）
COPYRIGHT_YEAR = "2026"
COPYRIGHT_HOLDER = "Xiongfei Fang"

# EUDAMED 官方环境入口（帮助页展示）
EUDAMED_PLAYGROUND_URL = "https://webgate.training.ec.europa.eu/eudamed-play/landing-page#/"
EUDAMED_PRODUCTION_URL = "https://webgate.ec.europa.eu/eudamed/landing-page#/"
EUDAMED_PLAYGROUND_HELP_URL = "https://webgate.ec.europa.eu/eudamed-play-help/en/getting-started/eudamed-environments.html"
EUDAMED_BULK_UPLOAD_HELP_URL = "https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/bulk-uploading-downloading/bulk-upload.html"
SUPPORT_EMAIL = "qecslan@hotmail.com"

SERVICE_LABELS = {
    "DEVICE.POST": "Upload of Legacy / Regulation Device / SPP ( Basic UDI and UDI-DI / Master UDI-DI )",
    "UDI_DI.POST": "Upload of UDI-DI / Master UDI-DI for existing Basic UDI-DI",
    "Basic_UDI.PATCH": "Update Basic UDI",
    "UDI_DI.PATCH": "Update of UDI-DI / Master UDI-DI",
    "MARKET_INFO.PATCH": "Update Market Information (countries / availability dates)",
    "PACKAGE_UDI.PATCH": "Update Container Package (packaging structure)",
}

BASIC_FIELDS = [
    "Local Record ID",
    "Legacy EUDAMED DI",
    "Basic UDI-DI Code",
    "Issuing Entity",
    "Manufacturer SRN",
    "Risk Class",
    "Applicable Legislation",
    "Device Type",
    "Device Name/Model",
    "EMDN Code",
    "Active Device",
    "Measuring Function",
    "Administer Medicine",
    "Implantable",
    "Reusable Surgical Instrument",
    "Presence of Human Tissues",
    "Presence of Animal Tissues",
    "Medicinal Product Device",
    "Companion Diagnostic (IVDR)",
    "Near Patient Testing (IVDR)",
    "Self-Testing (IVDR)",
    "Professional Testing (IVDR)",
    "Instrument (IVDR)",
    "Microbial Origin (IVDR)",
    "Additional Description",
    "Device Model",
    "Is it a Kit",
    "Authorised Representative SRN",
    "Special Device Type",
    "Reagent",
    "Presence of Medicinal Substance",
    "Is Suture/Staple/Filling/Brace (IIb Implant)",
]

UDI_FIELDS = [
    "Local Record ID",
    "Legacy Has Assigned UDI-DI",
    "Legacy EUDAMED DI Input",
    "Legacy EUDAMED DI",
    "Legacy EUDAMED ID",
    "Legacy Identifier Method",
    "Parent Basic UDI-DI",
    "UDI-DI Code",
    "UDI-DI Issuing Entity",
    "Device Status",
    "Quantity of Device",
    "Single Use Device",
    "Max Number of Reuses",
    "Device Labelled as Sterile",
    "Needs Sterilisation Before Use",
    "Containing Latex",
    "Reprocessed Single Use Device",
    "New Device (IVDR)",
    "Direct Marking",
    "DM DI Same as UDI-DI",
    "DM Issuing Entity",
    "DM DI Code",
    "Unit of Use DI Code",
    "Unit of Use Issuing Entity",
    "Secondary UDI-DI Code",
    "Secondary Issuing Entity",
    "Trade Name Applicable",
    "Trade Name",
    "Trade Name Language",
    "Additional Information URL",
    "Reference Number",
    "Product Designer SRN",
    "Product Designer ID",
    "PI Lot/Batch Number",
    "PI Expiration Date",
    "PI Manufacturing Date",
    "PI Serial Number",
    "PI Software Identification",
    "Nomenclature Code",
    "Nomenclature System",
    "Additional Description",
    "Description Language",
    "Public Website",
    "Public Email",
]

MARKET_FIELDS = [
    "UDI-DI Code",
    "Country Code",
    "Placed on Market",
    "Start Date",
    "End Date",
    "Originally Placed on Market",
]

CRITICAL_WARNING_FIELDS = [
    "UDI-DI Code",
    "Warning Type",
    "Language",
    "Comment",
]

STORAGE_FIELDS = [
    "UDI-DI Code",
    "Storage Condition Type",
    "Language",
    "Description",
]

PACKAGE_FIELDS = [
    "UDI-DI Code",
    "Package Level",
    "Package Type",
    "Package UDI-DI Code",
    "Package Issuing Entity",
    "Contains DI Code",
    "Contains DI Issuing Entity",
    "Quantity per Package",
]

CMR_FIELDS = [
    "Basic UDI-DI Code",
    "Substance Type",
    "CAS Code",
    "EC Code",
    "Language",
    "Substance Name",
]
