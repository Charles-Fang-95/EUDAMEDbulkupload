"""Parse EUDAMED acknowledgement / response XML files.

The response XML shape can vary slightly by service and error type. This parser
therefore uses namespace-agnostic local-name matching and returns a best-effort
result for the web UI instead of validating against XSD.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET


SUCCESS_STATUSES = {"PROCESSED", "SUCCESS", "ACCEPTED"}
ERROR_STATUSES = {"PROCESSED_WITH_ERRORS", "REJECTED", "ERROR", "FAILED"}


def parse_acknowledgement(content: bytes, repository) -> dict:
    result = {
        "ok": False,
        "service_type": "",
        "entities": [],
        "errors": [],
    }
    if not content:
        result["errors"].append("空文件。")
        return result
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        result["errors"].append(f"XML 解析失败: {exc}")
        return result

    result["service_type"] = _infer_service_type(root)
    entities = []
    response_entities = _find_response_entities(root)
    if not response_entities:
        # Some acknowledgements report only a message-level status. Keep it useful.
        status = _first_text(root, {"responseCode", "status", "processStatus"})
        if status:
            entities.append(
                {
                    "entity_code": "",
                    "status": status,
                    "errors": _collect_errors(root),
                    "matched_record": None,
                }
            )
    for node in response_entities:
        code = _first_text(node, {"entityCode", "entityIdentifier", "code", "udiDI", "basicUDI"})
        status = _first_text(node, {"responseCode", "status", "processStatus"}) or "UNKNOWN"
        entities.append(
            {
                "entity_code": code,
                "status": status,
                "errors": _collect_errors(node),
                "matched_record": _match_record(repository, code),
            }
        )
    if not entities:
        result["errors"].append("没有识别到 response entity。")
        return result
    result["entities"] = entities
    result["ok"] = True
    return result


def rejected_record_ids(parsed: dict) -> list[int]:
    ids = []
    for item in parsed.get("entities") or []:
        status = str(item.get("status") or "").upper()
        matched = item.get("matched_record") or {}
        if (status in ERROR_STATUSES or item.get("errors")) and matched.get("type") == "udi":
            ids.append(int(matched["id"]))
    return list(dict.fromkeys(ids))


def _find_response_entities(root: ET.Element) -> list[ET.Element]:
    candidates = [
        node for node in root.iter()
        if _local(node.tag) in {"responseEntity", "ResponseEntity", "entityResponse"}
    ]
    if candidates:
        return candidates
    # Fallback: nodes with both entity code and status children.
    out = []
    for node in root.iter():
        child_names = {_local(child.tag) for child in list(node)}
        if child_names & {"entityCode", "entityIdentifier"} and child_names & {"responseCode", "status", "processStatus"}:
            out.append(node)
    return out


def _collect_errors(node: ET.Element) -> list[dict]:
    errors = []
    report_nodes = [
        child for child in node.iter()
        if _local(child.tag) in {"report", "elementReport", "operationError", "error", "validationError"}
    ]
    if not report_nodes:
        return errors
    for report in report_nodes:
        code = _first_text(report, {"operationErrorCode", "errorCode", "code", "ruleCode"})
        detail = _first_text(report, {"operationErrorDetail", "operationDetail", "detail", "message", "description", "text"})
        if not detail:
            detail = " ".join(text.strip() for text in report.itertext() if text and text.strip())
        if code or detail:
            errors.append({"code": code, "detail": detail})
    deduped = []
    seen = set()
    for item in errors:
        key = (item.get("code", ""), item.get("detail", ""))
        if key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


def _match_record(repository, code: str) -> dict | None:
    code = str(code or "").strip()
    if not code:
        return None
    basic = repository.get_basic_by_code(code)
    if basic:
        return {"type": "basic", "id": basic["id"], "code": basic["basic_code"]}
    udi = repository.get_udi_by_code(code)
    if udi:
        return {"type": "udi", "id": udi["id"], "code": udi["udi_code"]}
    return None


def _infer_service_type(root: ET.Element) -> str:
    service = _first_text(root, {"serviceID", "serviceId", "service"})
    operation = _first_text(root, {"operation", "operationType", "serviceOperation"})
    service = service.strip().upper()
    operation = operation.strip().upper()
    if service == "DEVICE" and operation == "POST":
        return "DEVICE.POST"
    if service == "UDI_DI":
        return f"UDI_DI.{operation or 'POST'}"
    if service in {"BASIC_UDI", "BASICUDI"}:
        return f"Basic_UDI.{operation or 'PATCH'}"
    if service in {"MARKET_INFO", "MKTINFO"}:
        return f"MARKET_INFO.{operation or 'PATCH'}"
    if service in {"PACKAGE_UDI", "CONTAINER_PACKAGE"}:
        return f"PACKAGE_UDI.{operation or 'PATCH'}"
    return ""


def _first_text(node: ET.Element, names: set[str]) -> str:
    for child in node.iter():
        if _local(child.tag) in names:
            text = "".join(child.itertext()).strip()
            if text:
                return text
    return ""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag
