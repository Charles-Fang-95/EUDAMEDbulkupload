import csv
import html
import io
import uuid
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from xml.dom import minidom

from .constants import BULK_UPLOAD_ENTITY_LIMIT, EXPORT_DIR
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
        if service_type in {"DEVICE.POST", "UDI_DI.POST", "UDI_DI.PATCH"}:
            udis = self.repository.get_udis_by_ids(record_ids)
            selected_records = udis
            if len(udis) != len(record_ids):
                errors.append("部分 UDI-DI 记录不存在。")
            checked_basic_codes = set()
            for item in udis:
                payload = item["payload"]
                basic_payload = item.get("basic_payload") or {}
                if not payload.get("UDI-DI Code"):
                    errors.append(f"记录 #{item['id']} 缺少 UDI-DI Code。")
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
                        first_market_count = sum(
                            1 for row in item["market_rows"]
                            if self._is_true(row.get("Originally Placed on Market"))
                        )
                        if first_market_count != 1:
                            errors.append(
                                f"UDI-DI {item['udi_code']} 为 On the EU market，"
                                "Market Info 中 Originally Placed on Market 必须且只能有一条 TRUE。"
                            )
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
                if not item["version"]:
                    errors.append(f"Basic UDI-DI {item['basic_code']} 缺少当前版本号，无法导出更新 XML。")
        result = {"service_type": service_type, "errors": errors, "warnings": warnings, "batches": []}
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
                    payload_entity="device:BasicUDI" if service_type == "Basic_UDI.PATCH" else "device:UDIDIData",
                    records=chunk,
                    dependency="无业务依赖，顺序仅用于核对。",
                    dependency_en="No business dependency; order is for tracking only.",
                )
            )
        return batches

    def _plan_device_post_batches(self, records: list[dict]) -> list[dict]:
        grouped = {}
        for item in sorted(records, key=lambda row: (str(row["basic_code"] or ""), int(row["id"]))):
            grouped.setdefault(str(item["basic_code"] or ""), []).append(item)

        device_batches = []
        udi_post_batches = []
        device_groups = []
        for basic_code in sorted(grouped):
            rows = grouped[basic_code]
            first_chunk = rows[:BULK_UPLOAD_ENTITY_LIMIT]
            device_groups.append((basic_code, first_chunk))
            for chunk in self._chunks(rows[BULK_UPLOAD_ENTITY_LIMIT:], BULK_UPLOAD_ENTITY_LIMIT):
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

    def _positive_integer(self, value) -> bool:
        try:
            return int(str(value).strip()) > 0
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
            device.append(self._build_device_basic_node(basic["payload"], basic["cmr_rows"], include_version=False))
            return device
        device.append(self._build_device_basic_node(basic["payload"], basic["cmr_rows"], include_version=False))
        device.append(self._build_device_udi_node(item, profile, include_version=False))
        return device

    def _build_basic_patch_node(self, basic: dict):
        profile = self._profile(basic["payload"])
        node = ET.Element(qn("device", "BasicUDI"))
        node.set(qn("xsi", "type"), self._basic_patch_type(profile))
        self._build_basic_body(node, basic["payload"], basic["cmr_rows"], profile, include_version=True, version=basic["version"])
        return node

    def _build_udi_data_node(self, item: dict, include_version: bool):
        profile = self._profile(item.get("basic_payload") or item["payload"])
        node = ET.Element(qn("device", "UDIDIData"))
        node.set(qn("xsi", "type"), self._udi_data_type(profile))
        self._build_udi_body(node, item, profile, include_version=include_version)
        return node

    def _build_device_basic_node(self, data: dict, cmr_rows: list[dict], include_version: bool):
        profile = self._profile(data)
        legacy_tags = {"MDEU": "MDEUDI", "IVDEU": "IVDEUDI"}
        tag = legacy_tags.get(profile) or ("PRBasicUDI" if profile == "PR" else f"{profile}BasicUDI")
        node = ET.Element(qn("device", tag))
        if profile in {"MDR", "IVDR"}:
            node.set(qn("xsi", "type"), f"device:{profile}BasicUDIType")
        self._build_basic_body(node, data, cmr_rows, profile, include_version=include_version)
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

        if profile in {"IVDR", "IVDEU"}:
            self._text(parent, "basicudi", "specialDevice", data.get("Special Device Type"))
            self._bool(parent, "commondi", "companionDiagnostics", data.get("Companion Diagnostic (IVDR)"))
            self._bool(parent, "commondi", "instrument", data.get("Instrument (IVDR)"))
            self._bool(parent, "commondi", "kit", data.get("Kit (IVDR)"))
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
        self._text(parent, "basicudi", "specialDevice", data.get("Special Device Type"))
        self._text(parent, "basicudi", "type", DEVICE_TYPE_MAP.get(data.get("Device Type", ""), data.get("Device Type", "")) or "DEVICE")
        self._bool(parent, "commondi", "active", data.get("Active Device"))
        self._bool(parent, "commondi", "administeringMedicine", data.get("Administer Medicine"))
        self._bool(parent, "commondi", "implantable", data.get("Implantable"))
        self._bool(parent, "commondi", "measuringFunction", data.get("Measuring Function"))
        self._bool(parent, "commondi", "reusable", data.get("Reusable Surgical Instrument"))
        if profile == "MDEU":
            self._text(parent, "eudi", "applicableLegislation", data.get("Applicable Legislation"))

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
        if production_values:
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

        self._text(parent, "udidi", "website", data.get("Public Website"))
        self._append_storage_conditions(parent, item["storage_rows"])
        self._append_packages(parent, item["package_rows"], data)
        self._append_warnings(parent, item["warning_rows"])
        self._text(parent, "udidi", "numberOfReuses", self._number_of_reuses(data))
        self._append_market_information(parent, item["market_rows"])
        if self._has_value(data.get("Quantity of Device")):
            self._text(parent, "udidi", "baseQuantity", data.get("Quantity of Device"))

        self._append_device_marking(parent, data)

        if profile == "IVDR":
            self._bool(parent, "udidi", "newDevice", data.get("New Device (IVDR)"))
            return
        if profile == "IVDEU":
            return

        self._bool(parent, "udidi", "latex", data.get("Containing Latex"))
        self._bool(parent, "udidi", "reprocessed", data.get("Reprocessed Single Use Device"))
        self._append_substances(parent, item["basic_code"])

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

    def _comment_language(self, language, code: str, other_code: str) -> str:
        if code == other_code:
            return (language or "EN").upper()
        return "ANY"

    def _append_market_information(self, parent: ET.Element, market_rows: list[dict]):
        if not market_rows:
            return
        node = ET.SubElement(parent, qn("udidi", "marketInfos"))
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
            substance = ET.SubElement(container, qn("udidi", "substance"))
            substance.set(qn("xsi", "type"), self._substance_type(row.get("Substance Type")))
            if row.get("Substance Name"):
                names = ET.SubElement(substance, qn("udidi", "names"))
                name = ET.SubElement(names, qn("lsn", "name"))
                ET.SubElement(name, qn("lsn", "language")).text = (row.get("Language") or "ANY").upper()
                ET.SubElement(name, qn("lsn", "textValue")).text = str(row.get("Substance Name"))
            self._text(substance, "udidi", "CASCode", row.get("CAS Code"))
            self._text(substance, "udidi", "ECCode", row.get("EC Code"))
            self._text(substance, "udidi", "type", self._substance_value(row.get("Substance Type")))

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
        mapping = {
            "CMR 1A": "udidi:CMRSubstanceType",
            "CMR 1B": "udidi:CMRSubstanceType",
            "Endocrine Disrupting": "udidi:EndocrineSubstanceType",
            "Medicinal Product Substance": "udidi:MedicalHumanProductSubstanceType",
            "Human Blood or Plasma Substance": "udidi:MedicalHumanProductSubstanceType",
        }
        return mapping.get(substance_type or "", "udidi:CMRSubstanceType")

    def _substance_value(self, substance_type: str) -> str:
        mapping = {
            "CMR 1A": "CMR_1A",
            "CMR 1B": "CMR_1B",
            "Endocrine Disrupting": "ENDOCRINE_DISRUPTING_SUBSTANCE",
            "Medicinal Product Substance": "MEDICINAL_PRODUCT_SUBSTANCE",
            "Human Blood or Plasma Substance": "HUMAN_BLOOD_OR_PLASMA_SUBSTANCE",
        }
        return mapping.get(substance_type or "", "CMR_1A")

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
        raw = data.get("Max Number of Reuses")
        if self._has_value(raw):
            return raw
        if self._is_true(data.get("Single Use Device")):
            return "0"
        return "1"

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
