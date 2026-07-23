import csv
import html
import io
import re
import uuid
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from xml.dom import minidom

from .constants import BULK_UPLOAD_ENTITY_LIMIT, EXPORT_DIR
from .template_schema import ENUM_SOURCES
from .xsd_version import get_tool_xsd_version
from .storage import Repository

NS = {
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "m": "https://ec.europa.eu/tools/eudamed/dtx/servicemodel/Message/v1",
    "s": "https://ec.europa.eu/tools/eudamed/dtx/servicemodel/Service/v1",
    "e": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/v1",
    "device": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Device/v1",
    "basicudi": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Device/BasicUDI/v1",
    "udidi": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/UDIDI/v1",
    "commondi": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Device/CommonDevice/v1",
    "lsn": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Common/LanguageSpecific/v1",
    "mktinfo": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/MktInfo/v1",
    "marketinfo": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/MktInfo/MarketInfo/v1",
    "links": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Links/v1",
    "eudi": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Device/LegacyDevice/EUDI/v1",
    "eudididata": "https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Device/LegacyDevice/EUDIData/v1",
}
SCHEMA_LOCATION = (
    "https://ec.europa.eu/tools/eudamed/dtx/servicemodel/Message/v1 "
    "https://webgate.ec.europa.eu/tools/eudamed/dtx/service/Message.xsd"
)
RECIPIENT_NODE_ID = "eDelivery:EUDAMED"

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

ISSUING_ENTITY_MAP = {
    "GS1": "GS1",
    "HIBCC": "HIBCC",
    "ICCBBA": "ICCBBA",
    "IFA": "IFA",
    "EUDAMED": "EUDAMED",
    "9999": "GS1",
    "9998": "HIBCC",
    "9997": "ICCBBA",
}
RISK_CLASS_MAP = {
    "Class I": "CLASS_I",
    "Class IIa": "CLASS_IIA",
    "Class IIb": "CLASS_IIB",
    "Class III": "CLASS_III",
    "Class A": "CLASS_A",
    "Class B": "CLASS_B",
    "Class C": "CLASS_C",
    "Class D": "CLASS_D",
    "IVD Annex II List A": "IVD_ANNEX_II_LIST_A",
    "IVD Annex II List B": "IVD_ANNEX_II_LIST_B",
    "IVD Self Testing": "IVD_DEVICES_SELF_TESTING",
    "IVD General": "IVD_GENERAL",
    "AIMDD": "AIMDD",
    "IVD_ANNEX_II_LIST_A": "IVD_ANNEX_II_LIST_A",
    "IVD_ANNEX_II_LIST_B": "IVD_ANNEX_II_LIST_B",
    "IVD_DEVICES_SELF_TESTING": "IVD_DEVICES_SELF_TESTING",
    "IVD_GENERAL": "IVD_GENERAL",
}
DEVICE_TYPE_MAP = {
    "Regular Device": "DEVICE",
    "System": "SYSTEM",
    "Procedure Pack": "PROCEDURE_PACK",
}
DEVICE_STATUS_MAP = {
    "On the EU market": "ON_THE_MARKET",
    "No longer placed on the EU market": "NO_LONGER_PLACED_ON_THE_MARKET",
    "Not intended for the EU market": "NOT_INTENDED_FOR_EU_MARKET",
}
SUBSTANCE_TYPE_EXPORT_MAP = {
    "CMR 1A": ("udidi:CMRSubstanceType", "CMR_1A"),
    "CMR 1B": ("udidi:CMRSubstanceType", "CMR_1B"),
    "Endocrine Disrupting": ("udidi:EndocrineSubstanceType", "ENDOCRINE_DISRUPTING_SUBSTANCE"),
    "Medicinal Product Substance": ("udidi:MedicalHumanProductSubstanceType", "MEDICINAL_PRODUCT_SUBSTANCE"),
    "Human Blood or Plasma Substance": ("udidi:MedicalHumanProductSubstanceType", "HUMAN_PRODUCT_SUBSTANCE"),
}
SUBSTANCE_TYPE_ALIASES = {
    "CMR_1A": "CMR 1A",
    "CMR 1A": "CMR 1A",
    "CMR_1B": "CMR 1B",
    "CMR 1B": "CMR 1B",
    "ENDOCRINE_DISRUPTING_SUBSTANCE": "Endocrine Disrupting",
    "ENDOCRINE DISRUPTING": "Endocrine Disrupting",
    "MEDICINAL_PRODUCT_SUBSTANCE": "Medicinal Product Substance",
    "MEDICINAL PRODUCT SUBSTANCE": "Medicinal Product Substance",
    "HUMAN_PRODUCT_SUBSTANCE": "Human Blood or Plasma Substance",
    "HUMAN_BLOOD_OR_PLASMA_SUBSTANCE": "Human Blood or Plasma Substance",
    "HUMAN PRODUCT SUBSTANCE": "Human Blood or Plasma Substance",
    "HUMAN BLOOD OR PLASMA SUBSTANCE": "Human Blood or Plasma Substance",
}
PRODUCTION_IDENTIFIER_MAP = {
    "PI Lot/Batch Number": "BATCH_NUMBER",
    "PI Expiration Date": "EXPIRATION_DATE",
    "PI Manufacturing Date": "MANUFACTURING_DATE",
    "PI Serial Number": "SERIALISATION_NUMBER",
    "PI Software Identification": "SOFTWARE_IDENTIFICATION",
}
EU_COUNTRY_CODES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE", "IS", "LI", "NO",
}
COUNTRY_CODE_MAP = {
    "GR": "EL",
    "GREECE": "EL",
    "希腊": "EL",
}

# 官方 XSD occurrence=1 的器械特征布尔字段：留空时工具仍按 false 输出，但预检要提示用户确认，
# 避免「漏填 Implantable 等于声明非植入」这类无声错报。按法规分组，只对该法规会输出的字段提示。
MANDATORY_BASIC_BOOLEANS = {
    "common_device": [
        "Presence of Human Tissues",
        "Presence of Animal Tissues",
    ],
    "mdr_mdd": [
        "Active Device",
        "Measuring Function",
        "Administer Medicine",
        "Implantable",
        "Reusable Surgical Instrument",
    ],
    "ivdr_ivdd": [
        "Companion Diagnostic (IVDR)",
        "Near Patient Testing (IVDR)",
        "Self-Testing (IVDR)",
        "Professional Testing (IVDR)",
        "Instrument (IVDR)",
        "Is it a Kit",
        "Microbial Origin (IVDR)",
        "Reagent",
    ],
}
MANDATORY_UDI_BOOLEANS = {
    "all": [
        "Single Use Device",
        "Device Labelled as Sterile",
        "Needs Sterilisation Before Use",
        "Trade Name Applicable",
    ],
    "mdr_mdd": [
        "Containing Latex",
        "Reprocessed Single Use Device",
    ],
    "ivdr": [
        "New Device (IVDR)",
    ],
}


def qn(prefix: str, local: str) -> str:
    return f"{{{NS[prefix]}}}{local}"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class BetaXMLExporter:
    def __init__(self, repository: Repository):
        self.repository = repository

    def export(self, service_type: str, record_ids: list[int]) -> dict:
        validation = self.validate(service_type, record_ids)
        if validation["errors"]:
            return validation

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = []
        all_codes = []
        for batch in validation["batches"]:
            all_codes.extend(batch["codes"])
        if len(set(all_codes)) != len(record_ids) or len(all_codes) != len(record_ids):
            validation["errors"].append("导出分片数量与选中记录数量不一致，已阻止导出以避免漏传或重复。")
            return validation

        for batch in validation["batches"]:
            root = self._build_batch_root(batch)
            file_path = self._write_batch_xml(batch, root, timestamp)
            batch_file = dict(batch)
            batch_file["file_path"] = str(file_path)
            batch_file["file_name"] = file_path.name
            files.append(batch_file)

        output_path = Path(files[0]["file_path"]) if len(files) == 1 else self._write_export_zip(service_type, timestamp, files)
        validation["file_path"] = str(output_path)
        validation["codes"] = all_codes
        validation["batches"] = [self._public_batch(batch) for batch in validation["batches"]]
        validation["files"] = [self._public_batch(batch) for batch in files]

        job_id = self.repository.create_export_job(service_type, all_codes, str(output_path), validation)
        self.repository.mark_records_xml_generated(service_type, record_ids)
        validation["job_id"] = job_id
        return validation

    def _build_batch_root(self, batch: dict):
        records = batch["records"]
        service_type = batch["service_type"]
        if service_type == "Basic_UDI.PATCH":
            return self._build_basic_patch(records)
        if service_type == "MARKET_INFO.PATCH":
            return self._build_market_info_patch(records)
        if service_type == "PACKAGE_UDI.PATCH":
            return self._build_package_udi_patch(records)
        if service_type == "UDI_DI.PATCH":
            return self._build_udi_patch(records)
        if service_type == "UDI_DI.POST":
            return self._build_udi_post(records)
        return self._build_device_post(records)

    def _write_batch_xml(self, batch: dict, root: ET.Element, timestamp: str):
        safe_service = batch["service_type"].replace(".", "_")
        output_path = EXPORT_DIR / f"{safe_service}_{timestamp}_{batch['sequence']:03d}.xml"
        xml_bytes = minidom.parseString(ET.tostring(root, encoding="utf-8")).toprettyxml(
            indent="  ", encoding="UTF-8"
        )
        output_path.write_bytes(xml_bytes)
        return output_path

    def _write_export_zip(self, service_type: str, timestamp: str, files: list[dict]):
        safe_service = service_type.replace(".", "_")
        zip_path = EXPORT_DIR / f"{safe_service}_{timestamp}_bulk_upload.zip"
        csv_text = self._manifest_csv(files)
        html_text = self._manifest_html(service_type, files)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in files:
                archive.write(item["file_path"], arcname=item["file_name"])
            archive.writestr("manifest.csv", csv_text)
            archive.writestr("manifest.html", html_text)
        return zip_path

    def _public_batch(self, batch: dict) -> dict:
        return {key: value for key, value in batch.items() if key != "records"}

    def _manifest_csv(self, files: list[dict]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "upload_order",
            "file_name",
            "service",
            "payload_entity",
            "record_count",
            "basic_udi_di",
            "depends_on_upload_order",
            "dependency_note",
            "udi_di_codes",
        ])
        for item in files:
            writer.writerow([
                item["sequence"],
                item["file_name"],
                item["service_type"],
                item["payload_entity"],
                item["record_count"],
                " ".join(item.get("basic_codes") or []),
                item.get("depends_on") or "",
                item.get("dependency") or "",
                " ".join(item.get("codes") or []),
            ])
        return output.getvalue()

    def _manifest_html(self, service_type: str, files: list[dict]) -> str:
        rows = []
        for item in files:
            rows.append(
                "<tr>"
                f"<td>{item['sequence']}</td>"
                f"<td>{html.escape(item['file_name'])}</td>"
                f"<td>{html.escape(item['service_type'])}</td>"
                f"<td>{html.escape(item['payload_entity'])}</td>"
                f"<td>{item['record_count']}</td>"
                f"<td>{html.escape(' '.join(item.get('basic_codes') or []))}</td>"
                f"<td>{html.escape(str(item.get('depends_on') or ''))}</td>"
                f"<td>{html.escape(item.get('dependency') or '')}</td>"
                f"<td>{html.escape(' '.join(item.get('codes') or []))}</td>"
                "</tr>"
            )
        return f"""<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <title>EUDAMED bulk upload manifest</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #24312d; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d8ded8; padding: 8px; vertical-align: top; }}
    th {{ background: #edf3ed; text-align: left; }}
    .warning {{ background: #fff4d8; padding: 12px; border-left: 4px solid #c98a00; }}
  </style>
</head>
<body>
  <h1>EUDAMED bulk upload manifest</h1>
  <p>Original selected service: <strong>{html.escape(service_type)}</strong></p>
  <p class="warning">如果某一行依赖前序上传，请先确认前序 XML 在 EUDAMED 上传成功并保存 response，再继续上传依赖文件。</p>
  <table>
    <thead><tr><th>Order</th><th>File</th><th>Service</th><th>Payload entity</th><th>Count</th><th>Basic UDI-DI</th><th>Depends on</th><th>Dependency note</th><th>Codes</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""

    def validate(self, service_type: str, record_ids: list[int]) -> dict:
        errors = []
        warnings = []
        if not record_ids:
            errors.append("请至少选择一条记录。")

        selected_records = []
        if service_type in {"DEVICE.POST", "UDI_DI.POST", "UDI_DI.PATCH", "MARKET_INFO.PATCH", "PACKAGE_UDI.PATCH"}:
            udis = self.repository.get_udis_by_ids(record_ids)
            selected_records = udis
            if len(udis) != len(record_ids):
                errors.append("部分 UDI-DI 记录不存在。")
            checked_basic_codes = set()
            checked_basic_enum_codes = set()
            for item in udis:
                payload = item["payload"]
                basic_payload = item.get("basic_payload") or {}
                if not payload.get("UDI-DI Code"):
                    errors.append(f"记录 #{item['id']} 缺少 UDI-DI Code。")
                if not payload.get("UDI-DI Issuing Entity"):
                    errors.append(f"UDI-DI {item['udi_code']} 缺少 UDI-DI Issuing Entity。")
                if service_type in {"DEVICE.POST", "UDI_DI.POST", "UDI_DI.PATCH"}:
                    if not payload.get("Parent Basic UDI-DI"):
                        errors.append(f"UDI-DI {item['udi_code']} 缺少 Parent Basic UDI-DI。")
                    if not payload.get("Device Status"):
                        errors.append(f"UDI-DI {item['udi_code']} 缺少 Device Status。")
                    if not (payload.get("Nomenclature Code") or basic_payload.get("EMDN Code")):
                        errors.append(f"UDI-DI {item['udi_code']} 缺少 Nomenclature Code / EMDN Code。")
                    if not payload.get("Reference Number"):
                        errors.append(f"UDI-DI {item['udi_code']} 缺少 Reference Number。")
                    status = payload.get("Device Status", "")
                    if status == "On the EU market":
                        if not item["market_rows"]:
                            errors.append(
                                f"UDI-DI {item['udi_code']} 为 On the EU market，缺少 Market Info。"
                            )
                        else:
                            self._validate_market_rows(errors, item)
                    self._validate_package_rows(errors, item)
                    self._validate_number_of_reuses(errors, warnings, item)
                    self._validate_mdr_detail_rows(errors, warnings, item)
                    self._warn_blank_udi_booleans(warnings, item)
                    self._warn_quantity_of_device(warnings, item)
                    self._warn_pr_ignored_udi_fields(warnings, item)
                    self._warn_legacy_production_identifiers(warnings, item)
                    self._warn_website_url_selection(warnings, item)
                    basic_code = str(item.get("basic_code") or payload.get("Parent Basic UDI-DI") or "").strip()
                    if basic_code and basic_code not in checked_basic_enum_codes:
                        checked_basic_enum_codes.add(basic_code)
                        basic = self.repository.get_basic_by_code(basic_code)
                        if basic:
                            self._validate_basic_enum_fields(errors, basic["basic_code"], basic["payload"])
                            self._validate_cmr_rows(errors, basic["basic_code"], basic.get("cmr_rows") or [])
                            self._warn_blank_basic_booleans(warnings, basic["basic_code"], basic["payload"])
                if service_type == "MARKET_INFO.PATCH":
                    self._validate_market_rows(errors, item, require_rows=True)
                if service_type == "PACKAGE_UDI.PATCH":
                    if not payload.get("Device Status"):
                        errors.append(f"UDI-DI {item['udi_code']} 缺少 Device Status，无法生成 Package UDI status。")
                    if not item.get("package_rows"):
                        errors.append(f"UDI-DI {item['udi_code']} 没有 Package Info，无法生成 PACKAGE_UDI.PATCH。")
                    else:
                        self._validate_package_rows(errors, item)
                if service_type == "DEVICE.POST":
                    basic = self.repository.get_basic_by_code(item["basic_code"])
                    if not basic:
                        errors.append(f"UDI-DI {item['udi_code']} 找不到对应的 Basic UDI-DI。")
                    else:
                        basic_data = basic["payload"]
                        if basic["basic_code"] not in checked_basic_codes:
                            checked_basic_codes.add(basic["basic_code"])
                            if not basic_data.get("Manufacturer SRN"):
                                errors.append(f"Basic UDI-DI {basic['basic_code']} 缺少 Manufacturer SRN。")
                            self._validate_authorised_representative(errors, basic["basic_code"], basic_data)
                            if not basic_data.get("Risk Class"):
                                errors.append(f"Basic UDI-DI {basic['basic_code']} 缺少 Risk Class。")
                            self._certificate_warning_if_needed(warnings, basic)
                if service_type == "UDI_DI.PATCH" and not item["version"]:
                    errors.append(f"UDI-DI {item['udi_code']} 缺少当前版本号，无法导出更新 XML。")
        else:
            basics = self.repository.get_basics_by_ids(record_ids)
            selected_records = basics
            if len(basics) != len(record_ids):
                errors.append("部分 Basic UDI-DI 记录不存在。")
            for item in basics:
                payload = item["payload"]
                if not payload.get("Basic UDI-DI Code"):
                    errors.append(f"记录 #{item['id']} 缺少 Basic UDI-DI Code。")
                if not payload.get("Manufacturer SRN"):
                    errors.append(f"Basic UDI-DI {item['basic_code']} 缺少 Manufacturer SRN。")
                self._validate_authorised_representative(errors, item["basic_code"], payload)
                if not payload.get("Risk Class"):
                    errors.append(f"Basic UDI-DI {item['basic_code']} 缺少 Risk Class。")
                self._validate_basic_enum_fields(errors, item["basic_code"], payload)
                self._validate_cmr_rows(errors, item["basic_code"], item.get("cmr_rows") or [])
                self._certificate_warning_if_needed(warnings, item)
                if not item["version"]:
                    errors.append(f"Basic UDI-DI {item['basic_code']} 缺少当前版本号，无法导出更新 XML。")
        entity_type = "basic" if service_type == "Basic_UDI.PATCH" else "udi"
        selected_codes = [
            str((item.get("basic_code") if entity_type == "basic" else item.get("udi_code")) or "").strip()
            for item in selected_records
        ]
        result = {
            "service_type": service_type,
            "errors": errors,
            "warnings": warnings,
            "batches": [],
            "freshness_summary": self.repository.export_freshness_summary(entity_type, selected_codes),
        }
        sample_codes = [
            code for code, item in zip(selected_codes, selected_records)
            if item.get("is_sample") and code
        ]
        if sample_codes:
            warnings.append(
                "本次选择包含示例数据（"
                + ", ".join(sample_codes[:8])
                + ("..." if len(sample_codes) > 8 else "")
                + "）。示例数据仅供熟悉流程，请勿上传到 EUDAMED。"
            )
        self._append_consistency_warnings(warnings, service_type, selected_records)
        if not errors:
            result["batches"] = self.plan_export_batches(service_type, selected_records)
            batch_codes = [code for batch in result["batches"] for code in batch["codes"]]
            if len(batch_codes) != len(record_ids) or len(set(batch_codes)) != len(batch_codes):
                result["errors"].append("导出分片计划与选中记录数量不一致，已阻止导出以避免漏传或重复。")
            if len(result["batches"]) > 1:
                result["warnings"].append(
                    f"根据 EUDAMED 官方 XSD {get_tool_xsd_version()}，单个 XML 同类 payload entity 最多 "
                    f"{BULK_UPLOAD_ENTITY_LIMIT} 条；本次将自动拆分为 {len(result['batches'])} 个 XML。"
                )
            if any(batch.get("depends_on") for batch in result["batches"]):
                result["warnings"].append(
                    "本次包含跨 service 顺序导出：请先上传对应 DEVICE.POST 并确认 EUDAMED 成功，再上传依赖的 UDI_DI.POST。"
                )
        return result

    def _certificate_warning_if_needed(self, warnings: list[str], basic: dict):
        payload = basic.get("payload") or {}
        cert_rows = basic.get("cert_rows") or []
        may_require = self._may_require_certificate_info(payload)
        if not may_require and not cert_rows:
            return
        if not cert_rows:
            warnings.append(
                f"Basic UDI-DI {basic.get('basic_code')} 可能触发 EUDAMED NB / certificate validation，"
                "但未填写 Device Certificates。请确认是否需要 product certificate 信息；如需要，"
                "请在模板 Device Certificates sheet 填写 Certificate Type、Notified Body ID 等字段。"
            )
            return
        invalid_nb_codes = sorted({
            str(row.get("Notified Body ID") or "").strip()
            for row in cert_rows
            if row.get("Notified Body ID") and not self._valid_nb_actor_code(row.get("Notified Body ID"))
        })
        if invalid_nb_codes:
            warnings.append(
                f"Basic UDI-DI {basic.get('basic_code')} 的 Device Certificates 中 Notified Body ID / NANDO ID "
                f"格式可能无效：{', '.join(invalid_nb_codes)}。应填写 4 位数字，例如 0483；否则官方 XSD 可能拒绝 XML。"
            )
        # 方案 A：只检查【跨法规】证书（法规内部的 class→证书类型匹配规则模糊、易误报，交给用户判断）。
        # 例如 MDR 器械挂了 MDD/AIMDD/IVDD/IVDR 体系的证书类型 → 几乎肯定填错了法规。
        legislation = str(payload.get("Applicable Legislation") or "").strip().upper()
        if legislation not in self._CERT_LEGISLATIONS:
            return
        actual = sorted({self._certificate_type(row) for row in cert_rows if self._certificate_type(row)})
        mismatched = sorted({
            cert_type for cert_type in actual
            if self._certificate_legislation(cert_type) in self._CERT_LEGISLATIONS
            and self._certificate_legislation(cert_type) != legislation
        })
        if mismatched:
            warnings.append(
                f"Basic UDI-DI {basic.get('basic_code')} 的 Applicable Legislation 为 {legislation}，"
                f"但 Device Certificates 中存在其他法规体系的 Certificate Type：{', '.join(mismatched)}。"
                "请核对证书是否填错了法规。"
            )

    def _append_consistency_warnings(self, warnings: list[str], service_type: str, selected_records: list[dict]):
        if not selected_records:
            return
        if service_type == "Basic_UDI.PATCH":
            only_codes = {"basic": [item.get("basic_code", "") for item in selected_records], "udi": []}
        else:
            only_codes = {
                "basic": [item.get("basic_code", "") for item in selected_records],
                "udi": [item.get("udi_code", "") for item in selected_records],
            }
        for finding in self.repository.consistency_findings(only_codes=only_codes):
            prefix = "提示" if finding.get("severity") == "info" else "警告"
            warnings.append(f"{prefix} · {finding.get('message', '')}")

    # 证书类型枚举的前缀法规家族（来自官方 CertificateTypeEnum），用于跨法规检测。
    _CERT_LEGISLATIONS = frozenset({"MDR", "IVDR", "MDD", "AIMDD", "IVDD"})

    def _certificate_type(self, row: dict) -> str:
        value = str(row.get("Certificate Type") or "").strip()
        return value.split(" - ", 1)[0].strip() if " - " in value else value

    def _certificate_legislation(self, cert_type: str) -> str:
        """从 Certificate Type 枚举值（如 MDR_TYPE_EXAMINATION）取法规家族前缀（MDR）。"""
        value = str(cert_type or "").strip().upper()
        return value.split("_", 1)[0] if value else ""

    def _valid_nb_actor_code(self, value) -> bool:
        return bool(re.fullmatch(r"\d{4}", str(value or "").strip()))

    def _may_require_certificate_info(self, payload: dict) -> bool:
        legislation = str(payload.get("Applicable Legislation") or "").strip().upper()
        risk = str(payload.get("Risk Class") or "").strip()
        if legislation in {"MDD", "AIMDD", "IVDD"}:
            return True
        if legislation == "MDR":
            if risk == "Class III":
                return True
            if risk == "Class IIb":
                implantable = self._is_true(payload.get("Implantable"))
                exception = self._is_true(payload.get("Is Suture/Staple/Filling/Brace (IIb Implant)"))
                return (not implantable) or (implantable and exception)
        if legislation == "IVDR":
            if risk in {"Class C", "Class D"}:
                return True
            if risk == "Class B":
                return self._is_true(payload.get("Self-Testing (IVDR)")) or self._is_true(payload.get("Near Patient Testing (IVDR)"))
        return False

    def _validate_number_of_reuses(self, errors: list[str], warnings: list[str], item: dict):
        payload = item.get("payload") or {}
        raw = payload.get("Max Number of Reuses")
        if self._is_true(payload.get("Single Use Device")):
            if self._has_value(raw):
                normalized = self._normalised_number_of_reuses(raw)
                if normalized != "0":
                    warnings.append(
                        f"UDI-DI {item.get('udi_code')} 是一次性使用器械，Max Number of Reuses 将按官方 XML 输出 0；"
                        "请在模板中留空或填 0，避免误解。"
                    )
            return
        if not self._has_value(raw):
            return
        normalized = self._normalised_number_of_reuses(raw)
        if normalized is None:
            errors.append(
                f"UDI-DI {item.get('udi_code')} 的 Max Number of Reuses 必须填写整数："
                "一次性使用填 0；可重复使用但未声明最大次数请留空或填 -1；有明确上限时填正整数。"
            )
            return
        if int(normalized) < -1:
            errors.append(
                f"UDI-DI {item.get('udi_code')} 的 Max Number of Reuses 不能小于 -1。"
            )

    def _legislation_group(self, legislation) -> str:
        leg = str(legislation or "").strip().upper()
        if leg in {"MDR", "MDD", "AIMDD"}:
            return "mdr_mdd"
        if leg in {"IVDR", "IVDD"}:
            return "ivdr_ivdd"
        return ""

    def _is_blank_bool(self, value) -> bool:
        return str(value or "").strip() == ""

    def _warn_blank_basic_booleans(self, warnings: list[str], basic_code: str, basic_payload: dict):
        profile = self._profile(basic_payload)
        if profile == "PR":
            return
        group = self._legislation_group(basic_payload.get("Applicable Legislation"))
        fields = list(MANDATORY_BASIC_BOOLEANS.get("common_device", []))
        if group:
            fields += MANDATORY_BASIC_BOOLEANS.get(group, [])
        blank = [f for f in fields if self._is_blank_bool(basic_payload.get(f))]
        if blank:
            warnings.append(
                f"Basic UDI-DI {basic_code} 的必填布尔字段留空，导出将按 false 处理，"
                f"请确认是否确为 FALSE：{', '.join(blank)}"
            )

    def _warn_blank_udi_booleans(self, warnings: list[str], item: dict):
        payload = item.get("payload") or {}
        basic_payload = item.get("basic_payload") or {}
        profile = self._profile(basic_payload or payload)
        group = self._legislation_group(basic_payload.get("Applicable Legislation") or payload.get("Applicable Legislation"))
        fields = list(MANDATORY_UDI_BOOLEANS.get("all", []))
        if group:
            fields += MANDATORY_UDI_BOOLEANS.get(group, [])
        if profile == "IVDR":
            fields += MANDATORY_UDI_BOOLEANS.get("ivdr", [])
        blank = [f for f in fields if self._is_blank_bool(payload.get(f))]
        if blank:
            warnings.append(
                f"UDI-DI {item.get('udi_code')} 的必填布尔字段留空，导出将按 false 处理，"
                f"请确认是否确为 FALSE：{', '.join(blank)}"
            )

    def _warn_quantity_of_device(self, warnings: list[str], item: dict):
        payload = item.get("payload") or {}
        profile = self._profile(item.get("basic_payload") or payload)
        value = payload.get("Quantity of Device")
        if profile in {"MDR", "IVDR"} and not self._has_value(value):
            warnings.append(
                f"UDI-DI {item.get('udi_code')} 是 Regulation Device，Quantity of Device 为空；"
                "EUDAMED 可能要求填写销售单元中的设备数量。"
            )
        if profile in {"MDEU", "IVDEU"} and self._has_value(value):
            warnings.append(
                f"UDI-DI {item.get('udi_code')} 是 Legacy Device，Quantity of Device 不会输出到 XML。"
            )

    def _warn_pr_ignored_udi_fields(self, warnings: list[str], item: dict):
        payload = item.get("payload") or {}
        profile = self._profile(item.get("basic_payload") or payload)
        if profile != "PR":
            return
        ignored = []
        if item.get("market_rows"):
            ignored.append("Market Info")
        if self._has_value(payload.get("Quantity of Device")):
            ignored.append("Quantity of Device")
        if (
            self._is_true(payload.get("Direct Marking"))
            or self._has_value(payload.get("DM DI Code"))
            or self._has_value(payload.get("Unit of Use DI Code"))
        ):
            ignored.append("Direct Marking / Unit of Use DI")
        if self._is_true(payload.get("Single Use Device")) or self._has_value(payload.get("Max Number of Reuses")):
            ignored.append("Single Use / Max Number of Reuses")
        if self._is_true(payload.get("Containing Latex")):
            ignored.append("Containing Latex")
        if self._is_true(payload.get("Reprocessed Single Use Device")):
            ignored.append("Reprocessed Single Use Device")
        if self._is_true(payload.get("New Device (IVDR)")):
            ignored.append("New Device (IVDR)")
        if not ignored:
            return
        warnings.append(
            f"UDI-DI {item.get('udi_code')} 是 System / Procedure Pack；官方 PRUDIDIDataType 不支持输出 "
            f"{', '.join(ignored)}。这些值仅本地保留，不会写入 XML。"
        )

    def _warn_legacy_production_identifiers(self, warnings: list[str], item: dict):
        payload = item.get("payload") or {}
        profile = self._profile(item.get("basic_payload") or payload)
        if profile not in {"MDEU", "IVDEU"}:
            return
        selected = [field for field in PRODUCTION_IDENTIFIER_MAP if self._is_true(payload.get(field))]
        if selected:
            warnings.append(
                f"UDI-DI {item.get('udi_code')} 是 Legacy Device（MDD/AIMDD/IVDD）；"
                f"UDI-PI 类型字段 {', '.join(selected)} 不会输出到 XML。"
            )

    def _warn_website_url_selection(self, warnings: list[str], item: dict):
        payload = item.get("payload") or {}
        public_url = str(payload.get("Public Website") or "").strip()
        additional_url = str(payload.get("Additional Information URL") or "").strip()
        legacy_eifu_url = str(payload.get("eIFU URL") or "").strip()
        if legacy_eifu_url:
            warnings.append(
                f"UDI-DI {item.get('udi_code')} 填写了旧字段 eIFU URL；0.9.6 模板曾明确该字段不输出到 XML，"
                "因此本工具不会自动把它写入 EUDAMED。若该链接确实要作为官方 URL for additional information 提交，"
                "请人工复制到当前模板的 UDI - Additional Information URL / eIFU webpage。"
            )
        if public_url and additional_url and public_url != additional_url:
            warnings.append(
                f"UDI-DI {item.get('udi_code')} 同时填写了 Public Website 和 URL for additional information；"
                "EUDAMED DTX 只有一个 URL for additional information（XML 元素 udidi:website），"
                "本工具将优先输出 Public Website。"
            )

    def _website_url(self, payload: dict) -> str:
        return (
            str(payload.get("Public Website") or "").strip()
            or str(payload.get("Additional Information URL") or "").strip()
        )

    def plan_export_batches(self, service_type: str, records: list[dict]) -> list[dict]:
        if service_type == "DEVICE.POST":
            return self._plan_device_post_batches(records)
        return self._plan_simple_batches(service_type, records)

    def _plan_simple_batches(self, service_type: str, records: list[dict]) -> list[dict]:
        sorted_records = sorted(records, key=lambda item: int(item["id"]))
        batches = []
        for chunk in self._chunks(sorted_records, BULK_UPLOAD_ENTITY_LIMIT):
            batches.append(
                self._batch(
                    sequence=len(batches) + 1,
                    service_type=service_type,
                    payload_entity=self._payload_entity(service_type),
                    records=chunk,
                    dependency="无业务依赖，顺序仅用于核对。",
                    dependency_en="No business dependency; order is for tracking only.",
                )
            )
        return batches

    def _payload_entity(self, service_type: str) -> str:
        return {
            "Basic_UDI.PATCH": "device:BasicUDI",
            "MARKET_INFO.PATCH": "mktinfo:DTXMarketInfo",
            "PACKAGE_UDI.PATCH": "device:DTXPackageUDI",
        }.get(service_type, "device:UDIDIData")

    def _plan_device_post_batches(self, records: list[dict]) -> list[dict]:
        grouped = {}
        for item in sorted(records, key=lambda row: (str(row["basic_code"] or ""), int(row["id"]))):
            grouped.setdefault(str(item["basic_code"] or ""), []).append(item)

        device_batches = []
        udi_post_batches = []
        device_groups = []
        for basic_code in sorted(grouped):
            rows = grouped[basic_code]
            # 官方 DTX: 一个 Device = [1..1] BasicUDI + [1..1] UDIDIData，且同一个 Basic 在一次
            # DEVICE.POST 里只能创建一次。因此每个 Basic 只把【第 1 个】UDI-DI 放进 DEVICE.POST
            # （随 Basic 一起创建），该 Basic 其余所有 UDI-DI 一律走 UDI_DI.POST（与数量无关），
            # 否则重复的 Basic 会被 EUDAMED 拒为 "already exists"。
            first_chunk = rows[:1]
            device_groups.append((basic_code, first_chunk))
            for chunk in self._chunks(rows[1:], BULK_UPLOAD_ENTITY_LIMIT):
                udi_post_batches.append(
                    self._batch(
                        sequence=0,
                        service_type="UDI_DI.POST",
                        payload_entity="device:UDIDIData",
                        records=chunk,
                        basic_code=basic_code,
                        depends_on_basic=basic_code,
                        dependency=(
                            f"依赖 Basic UDI-DI {basic_code} 的 DEVICE.POST 成功；"
                            "请保存官方 response 后再上传。"
                        ),
                        dependency_en=(
                            f"Depends on a successful DEVICE.POST for Basic UDI-DI {basic_code}; "
                            "keep the official response before uploading this file."
                        ),
                    )
                )

        current_groups = []
        current_count = 0
        for basic_code, first_chunk in device_groups:
            if current_groups and current_count + len(first_chunk) > BULK_UPLOAD_ENTITY_LIMIT:
                device_batches.append(self._device_post_bin(current_groups))
                current_groups = []
                current_count = 0
            current_groups.append((basic_code, first_chunk))
            current_count += len(first_chunk)
        if current_groups:
            device_batches.append(self._device_post_bin(current_groups))

        batches = device_batches + udi_post_batches
        for index, batch in enumerate(batches, start=1):
            batch["sequence"] = index
            if batch.get("depends_on_basic"):
                for prior in batches:
                    if prior["service_type"] == "DEVICE.POST" and batch["depends_on_basic"] in prior.get("basic_codes", []):
                        batch["depends_on"] = prior["sequence"]
                        break
        return batches

    def _device_post_bin(self, groups: list[tuple[str, list[dict]]]) -> dict:
        records = [item for _, chunk in groups for item in chunk]
        basic_codes = [basic_code for basic_code, _ in groups]
        batch = self._batch(
            sequence=0,
            service_type="DEVICE.POST",
            payload_entity="device:Device",
            records=records,
            basic_code="",
            dependency="创建 Basic UDI-DI + 首批 UDI-DI；多个 Basic 已按 300 条上限合并装箱。",
            dependency_en="Create Basic UDI-DIs and first UDI-DIs; multiple Basics are packed together up to the 300-entity limit.",
        )
        batch["basic_codes"] = basic_codes
        return batch

    def _batch(
        self,
        sequence: int,
        service_type: str,
        payload_entity: str,
        records: list[dict],
        dependency: str,
        dependency_en: str,
        basic_code: str = "",
        depends_on_basic: str = "",
    ) -> dict:
        return {
            "sequence": sequence,
            "service_type": service_type,
            "payload_entity": payload_entity,
            "record_count": len(records),
            "record_ids": [item["id"] for item in records],
            "codes": [item.get("udi_code") or item.get("basic_code") for item in records],
            "basic_codes": sorted({str(item.get("basic_code") or basic_code or "") for item in records if item.get("basic_code") or basic_code}),
            "basic_code": basic_code,
            "depends_on_basic": depends_on_basic,
            "depends_on": None,
            "dependency": dependency,
            "dependency_en": dependency_en,
            "records": records,
        }

    def _chunks(self, records: list[dict], size: int):
        for index in range(0, len(records), size):
            chunk = records[index:index + size]
            if chunk:
                yield chunk

    def _validate_package_rows(self, errors: list[str], item: dict):
        rows = item.get("package_rows") or []
        if not rows:
            return
        udi_code = item["payload"].get("UDI-DI Code")
        package_by_code = {}
        for row in rows:
            package_code = str(row.get("Package UDI-DI Code") or "").strip()
            if not package_code:
                errors.append(f"UDI-DI {udi_code} 的 Package Info 缺少 Package UDI-DI Code。")
                continue
            if package_code in package_by_code:
                errors.append(f"UDI-DI {udi_code} 的 Package UDI-DI Code {package_code} 重复。")
            package_by_code[package_code] = row
            if not row.get("Package Issuing Entity"):
                errors.append(f"Package UDI-DI {package_code} 缺少 Package Issuing Entity。")
            if not self._positive_integer(row.get("Quantity per Package")):
                errors.append(f"Package UDI-DI {package_code} 的 Quantity per Package 必须为正整数。")
            child_code = str(row.get("Contains DI Code") or "").strip() or udi_code
            if child_code == package_code:
                errors.append(f"Package UDI-DI {package_code} 不能包含自己。")

        valid_children = {udi_code} | set(package_by_code.keys())
        edges = {}
        for row in rows:
            package_code = str(row.get("Package UDI-DI Code") or "").strip()
            child_code = str(row.get("Contains DI Code") or "").strip() or udi_code
            if child_code not in valid_children:
                errors.append(f"Package UDI-DI {package_code} 的 child DI {child_code} 不存在于该 UDI-DI 包装结构。")
            if package_code and child_code in package_by_code and child_code != package_code:
                edges[package_code] = child_code
        reported_cycles = set()
        for package_code in list(edges):
            cycle = self._package_cycle(package_code, edges)
            if cycle:
                cycle_key = frozenset(cycle)
                if cycle_key in reported_cycles:
                    continue
                reported_cycles.add(cycle_key)
                errors.append(f"UDI-DI {udi_code} 的 Package Info 存在循环包含关系：{' -> '.join(cycle)}。")

    def _validate_market_rows(self, errors: list[str], item: dict, require_rows: bool = False):
        rows = item.get("market_rows") or []
        udi_code = item.get("udi_code") or item.get("payload", {}).get("UDI-DI Code", "")
        if require_rows and not rows:
            errors.append(f"UDI-DI {udi_code} 没有 Market Info，无法生成 MARKET_INFO.PATCH。")
            return
        if not rows:
            return
        first_market_count = sum(
            1 for row in rows
            if self._is_true(row.get("Originally Placed on Market"))
        )
        if first_market_count != 1:
            errors.append(
                f"UDI-DI {udi_code} 的 Market Info 中 Originally Placed on Market 必须且只能有一条 TRUE。"
            )

    def _validate_mdr_detail_rows(self, errors: list[str], warnings: list[str], item: dict):
        profile = self._profile(item.get("basic_payload") or item.get("payload") or {})
        clinical_rows = item.get("clinical_size_rows") or []
        annex_rows = item.get("annex_xvi_rows") or []
        udi_code = item.get("udi_code") or item.get("payload", {}).get("UDI-DI Code", "")

        if profile != "MDR":
            if clinical_rows:
                warnings.append(f"UDI-DI {udi_code} 填写了 Clinical Sizes，但该结构仅适用于 MDR UDI-DI；导出时会忽略。")
            if annex_rows:
                warnings.append(f"UDI-DI {udi_code} 填写了 Annex XVI Purposes，但该结构仅适用于 MDR UDI-DI；导出时会忽略。")
            return

        self._validate_clinical_size_rows(errors, item)
        self._validate_annex_xvi_rows(errors, item)

    def _validate_basic_enum_fields(self, errors: list[str], basic_code: str, payload: dict):
        special_device = self._special_device_code(payload.get("Special Device Type"), payload)
        raw_special_device = str(payload.get("Special Device Type") or "").strip()
        if raw_special_device and not special_device:
            errors.append(
                f"Basic UDI-DI {basic_code} 的 Special Device Type 不是当前法规对应的官方枚举；普通器械请留空。"
            )

        ii_b_exception = payload.get("Is Suture/Staple/Filling/Brace (IIb Implant)")
        if ii_b_exception not in ("", None) and not self._valid_bool_token(ii_b_exception):
            errors.append(
                f"Basic UDI-DI {basic_code} 的 Is Suture/Staple/Filling/Brace (IIb Implant) 必须为 TRUE/FALSE。"
            )

    def _validate_cmr_rows(self, errors: list[str], basic_code: str, rows: list[dict]):
        for row in rows or []:
            raw_type = str(row.get("Substance Type") or "").strip()
            if not raw_type:
                errors.append(f"Basic UDI-DI {basic_code} 的 CMR Substances 缺少 Substance Type。")
            elif not self._normal_substance_type(raw_type):
                errors.append(f"Basic UDI-DI {basic_code} 的 CMR/Substance Type {raw_type} 不在当前支持的安全输出类型中。")

    def _validate_clinical_size_rows(self, errors: list[str], item: dict):
        rows = item.get("clinical_size_rows") or []
        if not rows:
            return
        udi_code = item.get("udi_code") or item.get("payload", {}).get("UDI-DI Code", "")
        type_codes = {self._enum_code(value) for value in ENUM_SOURCES.get("clinical_size_type", [])}
        unit_codes = {self._enum_code(value) for value in ENUM_SOURCES.get("clinical_size_unit", [])}
        for row in rows:
            size_type = str(self._enum_code(row.get("Clinical Size Type")) or "").strip()
            unit = str(self._enum_code(row.get("Measure Unit")) or "").strip()
            precision = str(row.get("Precision") or "").strip()
            if not size_type:
                errors.append(f"UDI-DI {udi_code} 的 Clinical Sizes 缺少 Clinical Size Type。")
            elif size_type not in type_codes:
                errors.append(f"UDI-DI {udi_code} 的 Clinical Size Type {size_type} 不在官方枚举中。")
            if size_type == "CST999" and not row.get("Clinical Size Type Description"):
                errors.append(f"UDI-DI {udi_code} 的 Clinical Size Type 为 CST999 - OTHER 时必须填写 Clinical Size Type Description。")
            if precision not in {"Range", "Value", "Text"}:
                errors.append(f"UDI-DI {udi_code} 的 Clinical Sizes Precision 必须为 Range、Value 或 Text。")
                continue
            if precision == "Range":
                if not self._is_number(row.get("Minimum")):
                    errors.append(f"UDI-DI {udi_code} 的 Clinical Sizes Precision=Range 时 Minimum 必须填写数字。")
                if not self._is_number(row.get("Maximum")):
                    errors.append(f"UDI-DI {udi_code} 的 Clinical Sizes Precision=Range 时 Maximum 必须填写数字。")
                self._validate_clinical_size_unit(errors, udi_code, unit, unit_codes, row)
            elif precision == "Value":
                if not self._is_number(row.get("Value")):
                    errors.append(f"UDI-DI {udi_code} 的 Clinical Sizes Precision=Value 时 Value 必须填写数字。")
                self._validate_clinical_size_unit(errors, udi_code, unit, unit_codes, row)
            elif not row.get("Text Value"):
                errors.append(f"UDI-DI {udi_code} 的 Clinical Sizes Precision=Text 时 Text Value 必须填写。")

    def _validate_clinical_size_unit(self, errors: list[str], udi_code: str, unit: str, unit_codes: set[str], row: dict):
        if not unit:
            errors.append(f"UDI-DI {udi_code} 的 Clinical Sizes Precision=Range/Value 时必须填写 Measure Unit。")
        elif unit not in unit_codes:
            errors.append(f"UDI-DI {udi_code} 的 Clinical Sizes Measure Unit {unit} 不在官方枚举中。")
        if unit == "MU999" and not row.get("Measure Unit Description"):
            errors.append(f"UDI-DI {udi_code} 的 Measure Unit 为 MU999 - OTHER 时必须填写 Measure Unit Description。")

    def _validate_annex_xvi_rows(self, errors: list[str], item: dict):
        rows = item.get("annex_xvi_rows") or []
        if not rows:
            return
        udi_code = item.get("udi_code") or item.get("payload", {}).get("UDI-DI Code", "")
        annex_codes = {self._enum_code(value) for value in ENUM_SOURCES.get("annex_xvi_nmd", [])}
        for row in rows:
            value = str(self._enum_code(row.get("Non-Medical Device Type")) or "").strip()
            if not value:
                errors.append(f"UDI-DI {udi_code} 的 Annex XVI Purposes 缺少 Non-Medical Device Type。")
            elif value not in annex_codes:
                errors.append(f"UDI-DI {udi_code} 的 Annex XVI Non-Medical Device Type {value} 不在官方枚举中。")

    def _positive_integer(self, value) -> bool:
        try:
            return int(str(value).strip()) > 0
        except (TypeError, ValueError):
            return False

    def _is_number(self, value) -> bool:
        if value in (None, ""):
            return False
        try:
            float(str(value).strip())
            return True
        except (TypeError, ValueError):
            return False

    def _package_cycle(self, start: str, edges: dict[str, str]) -> list[str]:
        seen = []
        current = start
        while current in edges:
            if current in seen:
                return seen[seen.index(current):] + [current]
            seen.append(current)
            current = edges[current]
        return []

    def _validate_authorised_representative(self, errors: list[str], basic_code: str, payload: dict):
        manufacturer_srn = str(payload.get("Manufacturer SRN") or "").strip()
        ar_srn = str(payload.get("Authorised Representative SRN") or "").strip()
        if manufacturer_srn and manufacturer_srn[:2].upper() not in EU_COUNTRY_CODES and not ar_srn:
            errors.append(
                f"Basic UDI-DI {basic_code} 的制造商 SRN 为 {manufacturer_srn}，"
                "属于非欧盟/EEA 制造商，缺少 Authorised Representative SRN（BR-UDID-018）。"
            )

    def _build_device_post(self, udis: list[dict]):
        payload_nodes = []
        sender_code = ""
        for item in udis:
            basic = self.repository.get_basic_by_code(item["basic_code"])
            if not basic:
                continue
            payload_nodes.append(self._build_device_node(basic, item))
            sender_code = sender_code or self._sender_code_from_basic(basic["payload"])
        return self._build_push_message(
            recipient_service_id="DEVICE",
            recipient_operation="POST",
            payload_nodes=payload_nodes,
            sender_code=sender_code,
            sender_service_id="DEVICE",
            sender_operation="POST",
        )

    def _build_udi_post(self, udis: list[dict]):
        payload_nodes = [self._build_udi_data_node(item, include_version=False) for item in udis]
        sender_code = self._sender_code_from_udi_rows(udis)
        return self._build_push_message(
            recipient_service_id="UDI_DI",
            recipient_operation="POST",
            payload_nodes=payload_nodes,
            sender_code=sender_code,
            sender_service_id="REPLY_SERVICE",
            sender_operation="GET",
        )

    def _build_basic_patch(self, basics: list[dict]):
        payload_nodes = [self._build_basic_patch_node(item) for item in basics]
        sender_code = self._sender_code_from_basic_rows(basics)
        return self._build_push_message(
            recipient_service_id="BASIC_UDI",
            recipient_operation="PATCH",
            payload_nodes=payload_nodes,
            sender_code=sender_code,
            sender_service_id="REPLY_SERVICE",
            sender_operation="GET",
        )

    def _build_udi_patch(self, udis: list[dict]):
        payload_nodes = [self._build_udi_data_node(item, include_version=True) for item in udis]
        sender_code = self._sender_code_from_udi_rows(udis)
        return self._build_push_message(
            recipient_service_id="UDI_DI",
            recipient_operation="PATCH",
            payload_nodes=payload_nodes,
            sender_code=sender_code,
            sender_service_id="REPLY_SERVICE",
            sender_operation="GET",
        )

    def _build_market_info_patch(self, udis: list[dict]):
        payload_nodes = [self._build_market_info_node(item) for item in udis]
        sender_code = self._sender_code_from_udi_rows(udis)
        return self._build_push_message(
            recipient_service_id="MARKET_INFO",
            recipient_operation="PATCH",
            payload_nodes=payload_nodes,
            sender_code=sender_code,
            sender_service_id="REPLY_SERVICE",
            sender_operation="GET",
        )

    def _build_package_udi_patch(self, udis: list[dict]):
        payload_nodes = [self._build_package_udi_node(item) for item in udis]
        sender_code = self._sender_code_from_udi_rows(udis)
        return self._build_push_message(
            recipient_service_id="PACKAGE_UDI",
            recipient_operation="PATCH",
            payload_nodes=payload_nodes,
            sender_code=sender_code,
            sender_service_id="REPLY_SERVICE",
            sender_operation="GET",
        )

    def _build_push_message(
        self,
        recipient_service_id: str,
        recipient_operation: str,
        payload_nodes: list[ET.Element],
        sender_code: str,
        sender_service_id: str,
        sender_operation: str,
    ):
        root = ET.Element(
            qn("m", "Push"),
            {
                "version": get_tool_xsd_version(),
                qn("xsi", "schemaLocation"): SCHEMA_LOCATION,
            },
        )
        ET.SubElement(root, qn("m", "conversationID")).text = str(uuid.uuid4())
        ET.SubElement(root, qn("m", "correlationID")).text = str(uuid.uuid4())
        ET.SubElement(root, qn("m", "creationDateTime")).text = utc_now()
        ET.SubElement(root, qn("m", "messageID")).text = str(uuid.uuid4())

        recipient = ET.SubElement(root, qn("m", "recipient"))
        self._append_endpoint(
            recipient,
            node_actor_code="EUDAMED",
            node_id=RECIPIENT_NODE_ID,
            service_id=recipient_service_id,
            service_operation=recipient_operation,
        )

        payload = ET.SubElement(root, qn("m", "payload"))
        for node in payload_nodes:
            payload.append(node)
        self._declare_xsi_type_namespaces(root)

        sender = ET.SubElement(root, qn("m", "sender"))
        self._append_endpoint(
            sender,
            node_actor_code=sender_code or "LOCAL_BULK_UPLOAD",
            node_id="",
            service_id=sender_service_id,
            service_operation=sender_operation,
        )
        return root

    def _declare_xsi_type_namespaces(self, root: ET.Element):
        type_prefixes = {
            str(value).split(":", 1)[0]
            for element in root.iter()
            for key, value in element.attrib.items()
            if key == qn("xsi", "type") and isinstance(value, str) and ":" in value
        }
        for prefix in type_prefixes:
            uri = NS.get(prefix)
            if uri and not self._namespace_used_in_tags(root, uri):
                root.set(f"xmlns:{prefix}", uri)

    def _namespace_used_in_tags(self, root: ET.Element, uri: str) -> bool:
        namespace = f"{{{uri}}}"
        return any(str(element.tag).startswith(namespace) for element in root.iter())

    def _append_endpoint(
        self,
        parent: ET.Element,
        node_actor_code: str,
        node_id: str,
        service_id: str,
        service_operation: str,
    ):
        node = ET.SubElement(parent, qn("m", "node"))
        ET.SubElement(node, qn("s", "nodeActorCode")).text = node_actor_code
        if node_id:
            ET.SubElement(node, qn("s", "nodeID")).text = node_id

        service = ET.SubElement(parent, qn("m", "service"))
        ET.SubElement(service, qn("s", "serviceID")).text = service_id
        ET.SubElement(service, qn("s", "serviceOperation")).text = service_operation

    def _build_device_node(self, basic: dict, item: dict):
        profile = self._profile(basic["payload"])
        device = ET.Element(qn("device", "Device"))
        device.set(qn("xsi", "type"), f"device:{profile}DeviceType")
        if profile in {"MDEU", "IVDEU"}:
            device.append(self._build_device_udi_node(item, profile, include_version=False))
            device.append(self._build_device_basic_node(basic["payload"], basic["cmr_rows"], basic.get("cert_rows", []), include_version=False))
            return device
        device.append(self._build_device_basic_node(basic["payload"], basic["cmr_rows"], basic.get("cert_rows", []), include_version=False))
        device.append(self._build_device_udi_node(item, profile, include_version=False))
        return device

    def _build_basic_patch_node(self, basic: dict):
        profile = self._profile(basic["payload"])
        node = ET.Element(qn("device", "BasicUDI"))
        node.set(qn("xsi", "type"), self._basic_patch_type(profile))
        self._build_basic_body(node, basic["payload"], basic["cmr_rows"], basic.get("cert_rows", []), profile, include_version=True, version=basic["version"])
        return node

    def _build_udi_data_node(self, item: dict, include_version: bool):
        profile = self._profile(item.get("basic_payload") or item["payload"])
        node = ET.Element(qn("device", "UDIDIData"))
        node.set(qn("xsi", "type"), self._udi_data_type(profile))
        self._build_udi_body(node, item, profile, include_version=include_version)
        return node

    def _build_market_info_node(self, item: dict):
        payload = item["payload"]
        node = ET.Element(qn("mktinfo", "DTXMarketInfo"))
        self._append_identifier(
            node,
            "marketinfo",
            "uDIDIIdentifier",
            payload.get("UDI-DI Code"),
            payload.get("UDI-DI Issuing Entity"),
        )
        self._append_market_information(node, item.get("market_rows") or [], container_prefix="marketinfo")
        return node

    def _build_package_udi_node(self, item: dict):
        payload = item["payload"]
        node = ET.Element(qn("device", "DTXPackageUDI"))
        self._append_identifier(
            node,
            "udidi",
            "udiIdentifier",
            payload.get("UDI-DI Code"),
            payload.get("UDI-DI Issuing Entity"),
        )
        self._append_packages(node, item.get("package_rows") or [], payload)
        return node

    def _build_device_basic_node(self, data: dict, cmr_rows: list[dict], cert_rows: list[dict], include_version: bool):
        profile = self._profile(data)
        legacy_tags = {"MDEU": "MDEUDI", "IVDEU": "IVDEUDI"}
        tag = legacy_tags.get(profile) or ("PRBasicUDI" if profile == "PR" else f"{profile}BasicUDI")
        node = ET.Element(qn("device", tag))
        if profile in {"MDR", "IVDR"}:
            node.set(qn("xsi", "type"), f"device:{profile}BasicUDIType")
        self._build_basic_body(node, data, cmr_rows, cert_rows, profile, include_version=include_version)
        return node

    def _build_device_udi_node(self, item: dict, profile: str, include_version: bool):
        legacy_tags = {"MDEU": "MDEUData", "IVDEU": "IVDEUData"}
        tag = legacy_tags.get(profile) or ("PRUDIDIData" if profile == "PR" else f"{profile}UDIDIData")
        node = ET.Element(qn("device", tag))
        if profile in {"MDR", "IVDR"}:
            node.set(qn("xsi", "type"), f"device:{profile}UDIDIDataType")
        self._build_udi_body(node, item, profile, include_version=include_version)
        return node

    def _build_basic_body(
        self,
        parent: ET.Element,
        data: dict,
        cmr_rows: list[dict],
        cert_rows: list[dict],
        profile: str,
        include_version: bool,
        version: str = "",
    ):
        if include_version:
            ET.SubElement(parent, qn("e", "version")).text = version

        self._text(parent, "basicudi", "riskClass", RISK_CLASS_MAP.get(data.get("Risk Class", ""), data.get("Risk Class", "")))
        self._append_basic_model(parent, data)
        self._append_identifier(parent, "basicudi", "identifier", data.get("Basic UDI-DI Code"), data.get("Issuing Entity"))

        if profile == "PR":
            self._append_language_texts(
                parent,
                "basicudi",
                "medicinalPurpose",
                [
                    (
                        data.get("Description Language") or "EN",
                        data.get("Additional Description") or data.get("Device Name/Model") or data.get("Basic UDI-DI Code"),
                    )
                ],
            )
            self._text(parent, "basicudi", "PRActorCode", data.get("Manufacturer SRN"))
            self._text(parent, "basicudi", "type", DEVICE_TYPE_MAP.get(data.get("Device Type", ""), data.get("Device Type", "")) or "SYSTEM")
            return

        self._bool(parent, "basicudi", "animalTissuesCells", data.get("Presence of Animal Tissues"))
        self._text(parent, "basicudi", "ARActorCode", data.get("Authorised Representative SRN"))
        self._bool(parent, "basicudi", "humanTissuesCells", data.get("Presence of Human Tissues"))
        self._text(parent, "basicudi", "MFActorCode", data.get("Manufacturer SRN"))
        self._append_device_certificates(parent, cert_rows)

        if profile in {"IVDR", "IVDEU"}:
            self._text(parent, "basicudi", "specialDevice", self._special_device_code(data.get("Special Device Type"), data))
            self._bool(parent, "commondi", "companionDiagnostics", data.get("Companion Diagnostic (IVDR)"))
            self._bool(parent, "commondi", "instrument", data.get("Instrument (IVDR)"))
            self._bool(parent, "commondi", "kit", data.get("Is it a Kit") or data.get("Kit (IVDR)"))
            self._bool(parent, "commondi", "microbialSubstances", data.get("Microbial Origin (IVDR)"))
            self._bool(parent, "commondi", "nearPatientTesting", data.get("Near Patient Testing (IVDR)"))
            self._bool(parent, "commondi", "professionalTesting", data.get("Professional Testing (IVDR)"))
            self._bool(parent, "commondi", "reagent", data.get("Reagent"))
            self._bool(parent, "commondi", "selfTesting", data.get("Self-Testing (IVDR)"))
            return

        self._bool(parent, "basicudi", "humanProductCheck", False)
        if self._has_value(data.get("Is Suture/Staple/Filling/Brace (IIb Implant)")):
            self._bool(parent, "basicudi", "IIb_implantable_exceptions", data.get("Is Suture/Staple/Filling/Brace (IIb Implant)"))
        self._bool(parent, "basicudi", "medicinalProductCheck", data.get("Medicinal Product Device"))
        self._text(parent, "basicudi", "specialDevice", self._special_device_code(data.get("Special Device Type"), data))
        self._text(parent, "basicudi", "type", DEVICE_TYPE_MAP.get(data.get("Device Type", ""), data.get("Device Type", "")) or "DEVICE")
        self._bool(parent, "commondi", "active", data.get("Active Device"))
        self._bool(parent, "commondi", "administeringMedicine", data.get("Administer Medicine"))
        self._bool(parent, "commondi", "implantable", data.get("Implantable"))
        self._bool(parent, "commondi", "measuringFunction", data.get("Measuring Function"))
        self._bool(parent, "commondi", "reusable", data.get("Reusable Surgical Instrument"))
        if profile == "MDEU":
            self._text(parent, "eudi", "applicableLegislation", data.get("Applicable Legislation"))

    def _append_device_certificates(self, parent: ET.Element, rows: list[dict]):
        rows = [row for row in (rows or []) if row.get("Certificate Type") and row.get("Notified Body ID")]
        if not rows:
            return
        container = ET.SubElement(parent, qn("basicudi", "deviceCertificateLinks"))
        for row in rows:
            link = ET.SubElement(container, qn("links", "deviceCertificateLink"))
            self._text(link, "links", "certificateNumber", row.get("Certificate Number"))
            self._text(link, "links", "expiryDate", row.get("Expiry Date"))
            self._text(link, "links", "NBActorCode", row.get("Notified Body ID"))
            self._text(link, "links", "certificateRevisionNumber", row.get("Revision Number"))
            self._text(link, "links", "certificateType", self._enum_code(row.get("Certificate Type")))

    def _build_udi_body(self, parent: ET.Element, item: dict, profile: str, include_version: bool):
        data = item["payload"]
        basic = self.repository.get_basic_by_code(item["basic_code"])
        basic_payload = item.get("basic_payload") or (basic["payload"] if basic else {})
        if include_version:
            ET.SubElement(parent, qn("e", "version")).text = item["version"]

        self._append_identifier(parent, "udidi", "identifier", data.get("UDI-DI Code"), data.get("UDI-DI Issuing Entity"))
        status = ET.SubElement(parent, qn("udidi", "status"))
        ET.SubElement(status, qn("commondi", "code")).text = DEVICE_STATUS_MAP.get(
            data.get("Device Status", ""), data.get("Device Status", "")
        )

        description = data.get("Additional Description")
        if description:
            self._append_language_texts(
                parent,
                "udidi",
                "additionalDescription",
                [(data.get("Description Language") or "EN", description)],
            )

        self._append_identifier(parent, "udidi", "basicUDIIdentifier", data.get("Parent Basic UDI-DI"), basic_payload.get("Issuing Entity"))
        mdn_codes = data.get("Nomenclature Code") or basic_payload.get("EMDN Code")
        self._text(parent, "udidi", "MDNCodes", mdn_codes)

        production_values = [code for field, code in PRODUCTION_IDENTIFIER_MAP.items() if self._is_true(data.get(field))]
        if production_values and profile not in {"MDEU", "IVDEU"}:
            self._text(parent, "udidi", "productionIdentifier", " ".join(production_values))

        self._text(parent, "udidi", "referenceNumber", data.get("Reference Number"))
        if data.get("Secondary UDI-DI Code"):
            self._append_identifier(
                parent,
                "udidi",
                "secondaryIdentifier",
                data.get("Secondary UDI-DI Code"),
                data.get("Secondary Issuing Entity"),
            )
        self._bool(parent, "udidi", "sterile", data.get("Device Labelled as Sterile"))
        self._bool(parent, "udidi", "sterilization", data.get("Needs Sterilisation Before Use"))

        trade_names = self._trade_name_values(item)
        if self._is_true(data.get("Trade Name Applicable")) and trade_names:
            self._append_language_texts(
                parent,
                "udidi",
                "tradeNames",
                trade_names,
            )

        self._text(parent, "udidi", "website", self._website_url(data))
        self._append_storage_conditions(parent, item["storage_rows"])
        self._append_packages(parent, item["package_rows"], data)
        self._append_warnings(parent, item["warning_rows"])
        if profile == "PR":
            return
        self._text(parent, "udidi", "numberOfReuses", self._number_of_reuses(data))
        self._append_market_information(parent, item["market_rows"])
        self._append_device_marking(parent, data)
        if profile in {"MDR", "IVDR"} and self._has_value(data.get("Quantity of Device")):
            self._text(parent, "udidi", "baseQuantity", data.get("Quantity of Device"))

        if profile == "MDR":
            self._append_annex_xvi(parent, item.get("annex_xvi_rows") or [])
        if profile == "IVDR":
            self._bool(parent, "udidi", "newDevice", data.get("New Device (IVDR)"))
            return
        if profile == "IVDEU":
            return

        self._bool(parent, "udidi", "latex", data.get("Containing Latex"))
        self._bool(parent, "udidi", "reprocessed", data.get("Reprocessed Single Use Device"))
        self._append_substances(parent, item["basic_code"])
        if profile == "MDR":
            self._append_clinical_sizes(parent, item.get("clinical_size_rows") or [])

    def _append_basic_model(self, parent: ET.Element, data: dict):
        model = (data.get("Device Model") or "").strip()
        name = (data.get("Device Name/Model") or "").strip()
        if name:
            model_name = ET.SubElement(parent, qn("basicudi", "modelName"))
            if model and model != name:
                ET.SubElement(model_name, qn("commondi", "model")).text = model
            ET.SubElement(model_name, qn("commondi", "name")).text = name
            return
        ET.SubElement(parent, qn("basicudi", "model")).text = model or data.get("Basic UDI-DI Code") or ""

    def _append_identifier(self, parent: ET.Element, prefix: str, tag: str, code: str, issuing_entity: str):
        node = ET.SubElement(parent, qn(prefix, tag))
        ET.SubElement(node, qn("commondi", "DICode")).text = str(code or "")
        ET.SubElement(node, qn("commondi", "issuingEntityCode")).text = self._issuing_entity(issuing_entity)
        return node

    def _append_language_texts(self, parent: ET.Element, prefix: str, tag: str, values: list[tuple[str, str]]):
        filtered = [(lang, text) for lang, text in values if text]
        if not filtered:
            return None
        container = ET.SubElement(parent, qn(prefix, tag))
        for language, text in filtered:
            name = ET.SubElement(container, qn("lsn", "name"))
            ET.SubElement(name, qn("lsn", "language")).text = (language or "EN").upper()
            ET.SubElement(name, qn("lsn", "textValue")).text = str(text)
        return container

    def _trade_name_values(self, item: dict) -> list[tuple[str, str]]:
        data = item["payload"]
        rows = item.get("trade_name_rows") or []
        values = []
        if data.get("Trade Name"):
            values.append((data.get("Trade Name Language") or "EN", data.get("Trade Name")))
        for row in rows:
            values.append((row.get("Language") or "EN", row.get("Trade Name")))

        seen = set()
        deduped = []
        for language, text in values:
            key = (str(language or "").strip().upper(), str(text or "").strip())
            if not key[1] or key in seen:
                continue
            seen.add(key)
            deduped.append(key)
        return deduped

    def _enum_code(self, value):
        if isinstance(value, str) and " - " in value:
            return value.split(" - ", 1)[0].strip()
        return value

    def _normal_substance_type(self, value) -> str:
        code = str(self._enum_code(value) or "").strip()
        if not code:
            return ""
        if code in SUBSTANCE_TYPE_EXPORT_MAP:
            return code
        return SUBSTANCE_TYPE_ALIASES.get(code.upper().replace("-", " ").replace("/", " "))

    def _special_device_code(self, value, payload: dict) -> str:
        text = str(self._enum_code(value) or "").strip()
        if not text:
            return ""
        values = self._special_device_values_for_payload(payload)
        allowed_codes = {str(self._enum_code(item) or "").strip() for item in values}
        if text in allowed_codes:
            return text
        normalized_code = text.upper().replace(" ", "_").replace("-", "_")
        if normalized_code in allowed_codes:
            return normalized_code

        legacy_map = {
            "SOFTWARE": "SOFTWARE",
            "ORTHOPEDIC": "ORTHOPEDIC",
            "ORTHOPAEDIC": "ORTHOPEDIC",
            "STANDARD SOFT CONTACT LENSES": "STANDARD_SOFT_CONTACT_LENSES",
            "RIGID GAS PERMEABLE": "RIGID_GAS_PERMEABLE",
            "MADE TO ORDER": "MADE_TO_ORDER",
            "SPECTACLES FRAMES": "SPECTACLES_FRAMES",
            "SPECTACLES LENSES": "SPECTACLES_LENSES",
            "READY MADE SPECTACLES": "READY_MADE_SPECTACLES",
        }
        suffix = legacy_map.get(text.upper().replace("_", " ").replace("-", " "))
        if suffix:
            preferred_code = f"{self._special_device_preferred_prefix(payload)}_{suffix}"
            if preferred_code in allowed_codes:
                return preferred_code

        label_matches = []
        for item in values:
            code, label = self._split_enum_label(item)
            if label and label.lower() == text.lower():
                label_matches.append(code)
        if len(label_matches) == 1:
            return label_matches[0]
        if label_matches:
            preferred = self._special_device_preferred_prefix(payload)
            for code in label_matches:
                if code.startswith(preferred):
                    return code

        return ""

    def _special_device_values_for_payload(self, payload: dict) -> list[str]:
        legislation = str(payload.get("Applicable Legislation") or "").strip().upper()
        if legislation in {"IVDR", "IVDD"}:
            return ENUM_SOURCES.get("special_device_ivdr", [])
        return ENUM_SOURCES.get("special_device_mdr", [])

    def _special_device_preferred_prefix(self, payload: dict) -> str:
        legislation = str(payload.get("Applicable Legislation") or "").strip().upper()
        if legislation in {"MDR", "MDD", "AIMDD", "IVDR", "IVDD"}:
            return legislation
        profile = self._profile(payload)
        return {"MDEU": "MDD", "IVDEU": "IVDD"}.get(profile, profile)

    def _split_enum_label(self, value: str) -> tuple[str, str]:
        text = str(value or "")
        if " - " in text:
            return tuple(text.split(" - ", 1))  # type: ignore[return-value]
        return text, ""

    def _valid_bool_token(self, value) -> bool:
        if isinstance(value, bool):
            return True
        return str(value or "").strip().upper() in {"TRUE", "FALSE", "YES", "NO", "Y", "N", "1", "0"}

    def _comment_language(self, language, code: str, other_code: str) -> str:
        if code == other_code:
            return (language or "EN").upper()
        return "ANY"

    def _append_market_information(self, parent: ET.Element, market_rows: list[dict], container_prefix: str = "udidi"):
        if not market_rows:
            return
        node = ET.SubElement(parent, qn(container_prefix, "marketInfos"))
        for row in market_rows:
            item = ET.SubElement(node, qn("marketinfo", "marketInfo"))
            self._text(item, "marketinfo", "country", self._country_code(row.get("Country Code")))
            self._text(item, "marketinfo", "endDate", row.get("End Date"))
            self._bool(item, "marketinfo", "originalPlacedOnTheMarket", row.get("Originally Placed on Market"))
            self._text(item, "marketinfo", "startDate", row.get("Start Date"))

    def _country_code(self, value) -> str:
        code = str(value or "").strip().upper()
        return COUNTRY_CODE_MAP.get(code, code)

    def _append_warnings(self, parent: ET.Element, rows: list[dict]):
        if not rows:
            return
        container = ET.SubElement(parent, qn("udidi", "criticalWarnings"))
        for row in rows:
            node = ET.SubElement(container, qn("commondi", "warning"))
            if row.get("Comment"):
                comments = ET.SubElement(node, qn("commondi", "comments"))
                name = ET.SubElement(comments, qn("lsn", "name"))
                ET.SubElement(name, qn("lsn", "language")).text = self._comment_language(
                    row.get("Language"), self._enum_code(row.get("Warning Type")), "CW999"
                )
                ET.SubElement(name, qn("lsn", "textValue")).text = str(row.get("Comment"))
            self._text(node, "commondi", "warningValue", self._enum_code(row.get("Warning Type")))

    def _append_storage_conditions(self, parent: ET.Element, rows: list[dict]):
        if not rows:
            return
        container = ET.SubElement(parent, qn("udidi", "storageHandlingConditions"))
        for row in rows:
            node = ET.SubElement(container, qn("commondi", "condition"))
            if row.get("Description"):
                comments = ET.SubElement(node, qn("commondi", "comments"))
                name = ET.SubElement(comments, qn("lsn", "name"))
                ET.SubElement(name, qn("lsn", "language")).text = self._comment_language(
                    row.get("Language"), self._enum_code(row.get("Storage Condition Type")), "SHC099"
                )
                ET.SubElement(name, qn("lsn", "textValue")).text = str(row.get("Description"))
            self._text(node, "commondi", "storageHandlingConditionValue", self._enum_code(row.get("Storage Condition Type")))

    def _append_annex_xvi(self, parent: ET.Element, rows: list[dict]):
        values = [self._enum_code(row.get("Non-Medical Device Type")) for row in (rows or [])]
        values = [str(value).strip() for value in values if str(value or "").strip()]
        if not values:
            return
        container = ET.SubElement(parent, qn("udidi", "annexXVINonMedicalDeviceTypes"))
        for value in dict.fromkeys(values):
            self._text(container, "udidi", "nmdType", value)

    def _append_clinical_sizes(self, parent: ET.Element, rows: list[dict]):
        rows = rows or []
        if not rows:
            return
        container = ET.SubElement(parent, qn("udidi", "clinicalSizes"))
        for row in rows:
            precision = str(row.get("Precision") or "").strip()
            type_name = {
                "Range": "commondi:RangeClinicalSizeType",
                "Value": "commondi:ValueClinicalSizeType",
                "Text": "commondi:TextClinicalSizeType",
            }.get(precision)
            if not type_name:
                continue
            size = ET.SubElement(container, qn("commondi", "clinicalSize"))
            size.set(qn("xsi", "type"), type_name)
            self._text(size, "commondi", "clinicalSizeType", self._enum_code(row.get("Clinical Size Type")))
            if row.get("Clinical Size Type Description"):
                self._append_language_texts(
                    size,
                    "commondi",
                    "clinicalSizeDescription",
                    [(row.get("Description Language") or "EN", row.get("Clinical Size Type Description"))],
                )
            if precision == "Range":
                self._text(size, "commondi", "maximum", row.get("Maximum"))
                self._text(size, "commondi", "minimum", row.get("Minimum"))
                self._text(size, "commondi", "valueUnit", self._enum_code(row.get("Measure Unit")))
                self._append_measure_unit_description(size, row)
            elif precision == "Value":
                self._text(size, "commondi", "value", row.get("Value"))
                self._text(size, "commondi", "valueUnit", self._enum_code(row.get("Measure Unit")))
                self._append_measure_unit_description(size, row)
            elif precision == "Text":
                self._text(size, "commondi", "text", row.get("Text Value"))
        if len(container) == 0:
            parent.remove(container)

    def _append_measure_unit_description(self, parent: ET.Element, row: dict):
        if not row.get("Measure Unit Description"):
            return
        self._append_language_texts(
            parent,
            "commondi",
            "measureUnitDescription",
            [(row.get("Measure Unit Description Language") or "EN", row.get("Measure Unit Description"))],
        )

    def _append_packages(self, parent: ET.Element, package_rows: list[dict], payload: dict):
        if not package_rows:
            return
        package_by_code = {
            str(row.get("Package UDI-DI Code") or "").strip(): row
            for row in package_rows
            if str(row.get("Package UDI-DI Code") or "").strip()
        }
        container = ET.SubElement(parent, qn("udidi", "packages"))
        for row in package_rows:
            if not row.get("Package UDI-DI Code") or not row.get("Quantity per Package"):
                continue
            child_code = str(row.get("Contains DI Code") or "").strip() or payload.get("UDI-DI Code")
            child_issuing = row.get("Contains DI Issuing Entity") or self._package_child_issuing(
                child_code,
                package_by_code,
                payload,
            )
            node = ET.SubElement(container, qn("udidi", "package"))
            self._append_identifier(
                node,
                "udidi",
                "identifier",
                row.get("Package UDI-DI Code"),
                row.get("Package Issuing Entity"),
            )
            status = ET.SubElement(node, qn("udidi", "status"))
            ET.SubElement(status, qn("commondi", "code")).text = DEVICE_STATUS_MAP.get(
                payload.get("Device Status", ""), payload.get("Device Status", "")
            )
            self._append_identifier(
                node,
                "udidi",
                "child",
                child_code,
                child_issuing,
            )
            self._text(node, "udidi", "numberOfItems", row.get("Quantity per Package"))
        if len(container) == 0:
            parent.remove(container)

    def _package_child_issuing(self, child_code: str, package_by_code: dict[str, dict], payload: dict):
        if child_code in package_by_code:
            return package_by_code[child_code].get("Package Issuing Entity")
        return payload.get("UDI-DI Issuing Entity")

    def _append_substances(self, parent: ET.Element, basic_code: str):
        basic = self.repository.get_basic_by_code(basic_code)
        if not basic or not basic["cmr_rows"]:
            return
        container = ET.SubElement(parent, qn("udidi", "substances"))
        for row in basic["cmr_rows"]:
            normal_type = self._normal_substance_type(row.get("Substance Type"))
            if not normal_type:
                continue
            substance = ET.SubElement(container, qn("udidi", "substance"))
            substance.set(qn("xsi", "type"), self._substance_type(normal_type))
            if row.get("Substance Name"):
                names = ET.SubElement(substance, qn("udidi", "names"))
                name = ET.SubElement(names, qn("lsn", "name"))
                ET.SubElement(name, qn("lsn", "language")).text = (row.get("Language") or "ANY").upper()
                ET.SubElement(name, qn("lsn", "textValue")).text = str(row.get("Substance Name"))
            if normal_type in {"CMR 1A", "CMR 1B", "Endocrine Disrupting"}:
                self._text(substance, "udidi", "CASCode", row.get("CAS Code"))
                self._text(substance, "udidi", "ECCode", row.get("EC Code"))
            if normal_type != "Endocrine Disrupting":
                self._text(substance, "udidi", "type", self._substance_value(normal_type))
        if len(container) == 0:
            parent.remove(container)

    def _append_device_marking(self, parent: ET.Element, data: dict):
        has_direct = self._is_true(data.get("Direct Marking")) and (
            self._is_true(data.get("DM DI Same as UDI-DI")) or data.get("DM DI Code")
        )
        has_unit_of_use = bool(data.get("Unit of Use DI Code"))
        if not has_direct and not has_unit_of_use:
            return
        node = ET.SubElement(parent, qn("udidi", "deviceMarking"))
        if has_direct:
            direct = ET.SubElement(node, qn("udidi", "directMarkingDI"))
            ET.SubElement(direct, qn("commondi", "DICode")).text = (
                data.get("UDI-DI Code") if self._is_true(data.get("DM DI Same as UDI-DI")) else str(data.get("DM DI Code") or "")
            )
            ET.SubElement(direct, qn("commondi", "issuingEntityCode")).text = self._issuing_entity(
                data.get("UDI-DI Issuing Entity") if self._is_true(data.get("DM DI Same as UDI-DI")) else data.get("DM Issuing Entity")
            )
            return
        unit = ET.SubElement(node, qn("udidi", "unitOfUseIdentifier"))
        ET.SubElement(unit, qn("commondi", "DICode")).text = str(data.get("Unit of Use DI Code") or "")
        ET.SubElement(unit, qn("commondi", "issuingEntityCode")).text = self._issuing_entity(
            data.get("Unit of Use Issuing Entity")
        )

    def _profile(self, data: dict) -> str:
        device_type = data.get("Device Type", "")
        legislation = str(data.get("Applicable Legislation", "") or "").strip().upper()
        if device_type in {"System", "Procedure Pack"}:
            return "PR"
        if legislation in {"MDD", "AIMDD"}:
            return "MDEU"
        if legislation == "IVDD":
            return "IVDEU"
        if legislation == "IVDR":
            return "IVDR"
        return "MDR"

    def _basic_patch_type(self, profile: str) -> str:
        if profile == "MDEU":
            return "eudi:MDEUDIType"
        if profile == "IVDEU":
            return "eudi:IVDEUDIType"
        if profile == "PR":
            return "basicudi:PRBasicUDIType"
        return f"device:{profile}BasicUDIType"

    def _udi_data_type(self, profile: str) -> str:
        if profile == "MDEU":
            return "eudididata:MDEUDataType"
        if profile == "IVDEU":
            return "eudididata:IVDEUDataType"
        if profile == "PR":
            return "udidi:PRUDIDIDataType"
        return f"udidi:{profile}UDIDIDataType"

    def _substance_type(self, substance_type: str) -> str:
        return SUBSTANCE_TYPE_EXPORT_MAP.get(substance_type or "", ("", ""))[0]

    def _substance_value(self, substance_type: str) -> str:
        return SUBSTANCE_TYPE_EXPORT_MAP.get(substance_type or "", ("", ""))[1]

    def _sender_code_from_basic(self, payload: dict) -> str:
        return (
            payload.get("Manufacturer SRN")
            or payload.get("Authorised Representative SRN")
            or "LOCAL_BULK_UPLOAD"
        )

    def _sender_code_from_basic_rows(self, basics: list[dict]) -> str:
        for item in basics:
            code = self._sender_code_from_basic(item["payload"])
            if code:
                return code
        return "LOCAL_BULK_UPLOAD"

    def _sender_code_from_udi_rows(self, udis: list[dict]) -> str:
        for item in udis:
            basic_payload = item.get("basic_payload") or {}
            code = self._sender_code_from_basic(basic_payload)
            if code:
                return code
        return "LOCAL_BULK_UPLOAD"

    def _issuing_entity(self, value) -> str:
        return ISSUING_ENTITY_MAP.get(str(value or "GS1").strip(), str(value or "GS1").strip() or "GS1")

    def _number_of_reuses(self, data: dict):
        if self._is_true(data.get("Single Use Device")):
            return "0"
        raw = data.get("Max Number of Reuses")
        if self._has_value(raw):
            normalized = self._normalised_number_of_reuses(raw)
            return normalized if normalized is not None else raw
        # Official XSD annotation for numberOfReuses:
        # -1 = maximum number of reuses not defined / not applicable
        #  0 = single-use device
        # >0 = limited maximum number of reuses
        return "-1"

    def _normalised_number_of_reuses(self, value):
        text = str(value or "").strip()
        if not text:
            return None
        compact = text.upper().replace(" ", "")
        if text in {"-", "不适用", "未定义", "无"} or compact in {
            "N/A",
            "NA",
            "NOTAPPLICABLE",
            "NOTDEFINED",
            "UNDEFINED",
        }:
            return "-1"
        if not re.fullmatch(r"[+-]?\d+", text):
            return None
        return str(int(text))

    def _text(self, parent: ET.Element, prefix: str, tag: str, value):
        if value in (None, ""):
            return None
        node = ET.SubElement(parent, qn(prefix, tag))
        node.text = str(value)
        return node

    def _bool(self, parent: ET.Element, prefix: str, tag: str, value):
        node = ET.SubElement(parent, qn(prefix, tag))
        node.text = "true" if self._is_true(value) else "false"
        return node

    def _is_true(self, value) -> bool:
        return str(value).strip().upper() in {"TRUE", "YES", "1"}

    def _has_value(self, value) -> bool:
        return value not in (None, "")
