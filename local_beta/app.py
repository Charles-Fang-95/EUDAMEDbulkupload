import json
import os
import shutil
import sys
import traceback
import threading
import webbrowser
from datetime import datetime, timedelta
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .constants import (
    BASIC_FIELDS,
    EXPORT_DIR,
    GITEE_RELEASES_API_URL,
    RELEASES_API_URL,
    STATIC_DIR,
    TEMPLATE_EN_PATH,
    TEMPLATE_PATH,
    TOOL_VERSION,
    UDI_FIELDS,
    UPLOAD_DIR,
)
from .exporter import BetaXMLExporter
from .importer import WorkbookImporter, parse_json_array
from .storage import Repository
from .template_migrator import migrate_workbook
from .ack_parser import parse_acknowledgement
from .update_checker import check_latest_release, release_download_links
from .views import (
    ack_page,
    basic_detail,
    dashboard,
    export_page,
    help_page,
    history_page,
    import_page,
    library_page,
    migrate_template_page,
    page,
    set_lang,
    set_sample_counts,
    shutdown_page,
    template_guide_page,
    t,
    udi_detail,
    xsd_version_page,
)
from .xsd_version import build_xsd_version_report


STATIC_CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}


LOG_DIR = UPLOAD_DIR.parent / "logs"
STARTUP_LOG = LOG_DIR / "run.log"
UPDATE_CHECK_CACHE = UPLOAD_DIR.parent / "update_check_cache.json"
UPDATE_CHECK_CACHE_TTL = timedelta(hours=12)
# DATA_DIR = UPLOAD_DIR.parent；其上一级是 exe/源码所在目录（用户能直接看到的地方）。
APP_ROOT_DIR = UPLOAD_DIR.parent.parent


def log_exception(context: str, exc: Exception) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "app.log"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n[{context}] {type(exc).__name__}: {exc}\n")
        handle.write(traceback.format_exc())
        handle.write("\n")
    return log_path


def log_startup(message: str) -> None:
    """把启动阶段的信息写到 run.log；无控制台的打包版靠它事后排查。"""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with STARTUP_LOG.open("a", encoding="utf-8") as handle:
            handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] {message}\n")
    except Exception:
        pass


def show_startup_error(summary: str, detail: str = "") -> None:
    """启动失败时尽量让用户看见：写一个可见的 txt，并在 Windows 上弹原生消息框。"""
    body = summary + (("\n\n" + detail) if detail else "") + f"\n\n日志位置 / Log: {STARTUP_LOG}"
    for target in (APP_ROOT_DIR, LOG_DIR.parent):
        try:
            (target / "启动失败_STARTUP_ERROR.txt").write_text(body, encoding="utf-8")
            break
        except Exception:
            continue
    if sys.platform.startswith("win"):
        try:
            import ctypes  # noqa: PLC0415

            ctypes.windll.user32.MessageBoxW(0, body, "EUDAMED 工具启动失败 / Startup failed", 0x10)
        except Exception:
            pass


def parse_multipart(headers, body: bytes):
    content_type = headers.get("Content-Type", "")
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    fields = {}
    files = {}
    for part in message.iter_parts():
        disposition = part.get_content_disposition()
        if disposition != "form-data":
            continue
        name = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        content = part.get_payload(decode=True)
        if filename:
            files[name] = {"filename": filename, "content": content}
        else:
            fields[name] = content.decode("utf-8")
    return fields, files


class App:
    def __init__(self):
        self.repository = Repository()
        self.importer = WorkbookImporter(self.repository)
        self.exporter = BetaXMLExporter(self.repository)

    def handler(self):
        app = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                app.route(self)

            def do_POST(self):
                app.route(self)

            def log_message(self, fmt, *args):
                return

        return Handler

    def dashboard_update_hint(self) -> dict:
        cached = self._read_update_cache()
        if cached:
            return cached
        result = check_latest_release(RELEASES_API_URL, TOOL_VERSION, timeout=4, mirror_api_url=GITEE_RELEASES_API_URL)
        hint = {
            "status": result.get("status", "error"),
            "latest_version": result.get("latest_version", ""),
            "source": result.get("source", ""),
            "html_url": result.get("html_url", ""),
            "asset_url": result.get("asset_url", ""),
            "error": result.get("error", ""),
            "checked_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._write_update_cache(hint)
        return hint

    def _read_update_cache(self) -> dict:
        try:
            if not UPDATE_CHECK_CACHE.exists():
                return {}
            data = json.loads(UPDATE_CHECK_CACHE.read_text(encoding="utf-8"))
            checked_at = datetime.fromisoformat(str(data.get("checked_at", "")))
            if datetime.now() - checked_at > UPDATE_CHECK_CACHE_TTL:
                return {}
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_update_cache(self, data: dict):
        try:
            UPDATE_CHECK_CACHE.parent.mkdir(parents=True, exist_ok=True)
            UPDATE_CHECK_CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def route(self, request: BaseHTTPRequestHandler):
        parsed = urlparse(request.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        set_lang(self._lang_from_request(request))
        set_sample_counts(self.repository.sample_data_count())
        if request.command == "GET" and path == "/set-lang":
            return self.handle_set_lang(request, query)
        if request.command == "GET" and path == "/help":
            return self.respond_html(request, help_page())
        if request.command == "GET" and path == "/check-update":
            check_result = check_latest_release(RELEASES_API_URL, TOOL_VERSION, mirror_api_url=GITEE_RELEASES_API_URL)
            check_result["download_sources"] = release_download_links(RELEASES_API_URL, GITEE_RELEASES_API_URL)
            return self.respond_html(request, help_page(check_result=check_result))
        if request.command == "POST" and path == "/sample-data/load":
            self.repository.load_sample_data()
            return self.redirect(request, "/")
        if request.command == "POST" and path == "/sample-data/clear":
            next_path = self.read_form(request).get("next", ["/"])[0]
            self.repository.clear_sample_data()
            return self.redirect(request, next_path if next_path.startswith("/") and not next_path.startswith("//") else "/")
        if request.command == "POST" and path == "/shutdown":
            content = shutdown_page()
            self.respond_html(request, content)
            threading.Thread(target=request.server.shutdown, daemon=True).start()
            return
        if request.command == "GET" and path == "/":
            xsd_report = build_xsd_version_report(check_online=False)
            update_hint = self.dashboard_update_hint()
            return self.respond_html(
                request,
                dashboard(
                    self.repository.get_stats(),
                    self.repository.recent_imports(),
                    self.repository.recent_exports(),
                    xsd_report,
                    self.repository.manufacturer_srn_summary(),
                    update_hint,
                ),
            )
        if request.command == "GET" and path == "/import":
            return self.respond_html(request, import_page())
        if request.command == "POST" and path == "/import":
            return self.handle_import(request)
        if request.command == "GET" and path == "/migrate-template":
            return self.respond_html(request, migrate_template_page())
        if request.command == "POST" and path == "/migrate-template":
            return self.handle_migrate_template(request)
        if request.command == "GET" and path == "/template-guide":
            return self.respond_html(request, template_guide_page())
        if request.command == "GET" and path == "/ack":
            return self.respond_html(request, ack_page())
        if request.command == "POST" and path == "/ack":
            return self.handle_ack(request)
        if request.command == "GET" and path == "/library":
            filters = self._filters_from_query(query)
            pagination = self._pagination_from_query(query)
            records, total_filtered, pagination = self._paged_records("udi", filters, pagination)
            return self.respond_html(
                request,
                library_page(
                    records,
                    filters,
                    self._srn_options(),
                    total_filtered=total_filtered,
                    page_number=pagination["page"],
                    page_size=pagination["page_size"],
                ),
            )
        if request.command == "GET" and path.startswith("/basic-code/"):
            basic_code = unquote(path.split("/", 2)[2])
            record = self.repository.get_basic_by_code(basic_code)
            if not record:
                return self.respond_html(request, page(t("未找到","Not found"), f"<section class='panel'><h1>{t('未找到 Basic UDI-DI','Basic UDI-DI not found')}</h1></section>"), HTTPStatus.NOT_FOUND)
            freshness = self.repository.export_freshness("basic", [record["basic_code"]]).get(record["basic_code"], {})
            changes = self.repository.get_record_import_changes("basic", record["basic_code"])
            return self.respond_html(request, basic_detail(record, freshness=freshness, changes=changes))
        if request.command == "GET" and path.startswith("/basic/"):
            record_id = self._parse_int_id(path)
            if record_id is None:
                return self.not_found(request, t("未找到 Basic UDI-DI","Basic UDI-DI not found"))
            record = self.repository.get_basic(record_id)
            if not record:
                return self.not_found(request, t("未找到 Basic UDI-DI","Basic UDI-DI not found"))
            freshness = self.repository.export_freshness("basic", [record["basic_code"]]).get(record["basic_code"], {})
            changes = self.repository.get_record_import_changes("basic", record["basic_code"])
            return self.respond_html(request, basic_detail(record, freshness=freshness, changes=changes))
        if request.command == "POST" and path.startswith("/basic/"):
            record_id = self._parse_int_id(path)
            if record_id is None:
                return self.not_found(request, t("未找到 Basic UDI-DI","Basic UDI-DI not found"))
            return self.handle_basic_update(request, record_id)
        if request.command == "GET" and path.startswith("/udi/"):
            record_id = self._parse_int_id(path)
            if record_id is None:
                return self.not_found(request, t("未找到 UDI-DI","UDI-DI not found"))
            record = self.repository.get_udi(record_id)
            if not record:
                return self.not_found(request, t("未找到 UDI-DI","UDI-DI not found"))
            freshness = self.repository.export_freshness("udi", [record["udi_code"]]).get(record["udi_code"], {})
            changes = self.repository.get_record_import_changes("udi", record["udi_code"])
            return self.respond_html(request, udi_detail(record, freshness=freshness, changes=changes))
        if request.command == "POST" and path.startswith("/udi/"):
            record_id = self._parse_int_id(path)
            if record_id is None:
                return self.not_found(request, t("未找到 UDI-DI","UDI-DI not found"))
            return self.handle_udi_update(request, record_id)
        if request.command == "GET" and path == "/export":
            service_type = query.get("service_type", [""])[0]
            selection_mode = query.get("selection_mode", ["selected"])[0]
            filters = self._filters_from_query(query)
            pagination = self._pagination_from_query(query)
            xsd_report = build_xsd_version_report(check_online=False)
            if not service_type:
                return self.respond_html(
                    request,
                    export_page(
                        "", [], None, filters, xsd_report, 0, [], self._srn_options(), selection_mode,
                        page_number=pagination["page"], page_size=pagination["page_size"],
                    ),
                )
            entity_type = self._entity_type_for_service(service_type)
            records, total_filtered, pagination = self._paged_records(entity_type, filters, pagination)
            selected_ids, _ = self._parse_record_ids(query.get("record_ids", []))
            return self.respond_html(
                request,
                export_page(
                    service_type, records, None, filters, xsd_report, total_filtered, selected_ids,
                    self._srn_options(), selection_mode,
                    page_number=pagination["page"], page_size=pagination["page_size"],
                ),
            )
        if request.command == "POST" and path == "/export":
            return self.handle_export(request)
        if request.command == "GET" and path == "/history":
            return self.respond_html(request, history_page(self.repository.recent_exports(200)))
        if request.command == "GET" and path == "/xsd-version":
            return self.respond_html(request, xsd_version_page(build_xsd_version_report()))
        if request.command == "GET" and path.startswith("/static/"):
            filename = Path(path).name
            content_type = STATIC_CONTENT_TYPES.get(Path(filename).suffix.lower())
            if not content_type:
                return self.not_found(request, t("文件不存在", "File not found"))
            return self.respond_file(request, STATIC_DIR / filename, content_type, inline=True)
        if request.command == "GET" and path == "/download-template":
            locale = (query.get("locale", [""])[0] or "").lower()
            template_path = TEMPLATE_EN_PATH if locale == "en" or (not locale and self._lang_from_request(request) == "en") else TEMPLATE_PATH
            return self.respond_file(request, template_path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if request.command == "GET" and path.startswith("/download/"):
            filename = path.split("/")[-1]
            return self.respond_file(request, EXPORT_DIR / filename, self._download_content_type(filename))
        return self.respond_html(request, page(t("未找到","Not found"), f"<section class='panel'><h1>{t('页面不存在','Page not found')}</h1></section>"), HTTPStatus.NOT_FOUND)

    def handle_import(self, request: BaseHTTPRequestHandler):
        try:
            body = self.read_body(request)
            _, files = parse_multipart(request.headers, body)
            file_part = files.get("workbook")
            if not file_part:
                return self.respond_html(request, import_page(t("请选择一个 Excel 文件。", "Please choose an Excel file."), message_level="error"), HTTPStatus.BAD_REQUEST)
            upload_path = UPLOAD_DIR / Path(file_part["filename"]).name
            upload_path.write_bytes(file_part["content"])
            result = self.importer.import_workbook(upload_path)
            error_count = len(result.get("validation", {}).get("errors", []))
            if error_count:
                return self.respond_html(request, import_page(t("导入完成，但发现错误，请先处理后再导出。", "Import finished, but errors were found — please fix them before exporting."), result, "warning"))
            return self.respond_html(request, import_page(t("导入完成。", "Import finished."), result, "success"))
        except Exception as exc:
            log_path = log_exception("import", exc)
            message = (
                f"{t('导入失败，工具已记录错误日志。请把 Excel 原文件和日志文件发给作者排查。日志位置：', 'Import failed. The tool recorded an error log. Please send the original Excel and the log file to the author. Log path: ')}"
                f"{log_path}"
            )
            return self.respond_html(request, import_page(message, message_level="error"), HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_migrate_template(self, request: BaseHTTPRequestHandler):
        try:
            body = self.read_body(request)
            _, files = parse_multipart(request.headers, body)
            file_part = files.get("workbook")
            if not file_part:
                return self.respond_html(
                    request,
                    migrate_template_page(t("请选择一个 Excel 文件。", "Please choose an Excel file."), message_level="error"),
                    HTTPStatus.BAD_REQUEST,
                )
            upload_path = UPLOAD_DIR / Path(file_part["filename"]).name
            upload_path.write_bytes(file_part["content"])
            result = migrate_workbook(upload_path, EXPORT_DIR)
            if not result.get("ok"):
                message = "；".join(result.get("errors") or [t("迁移失败。", "Migration failed.")])
                return self.respond_html(request, migrate_template_page(message, result, "error"), HTTPStatus.BAD_REQUEST)
            warnings = result.get("warnings") or []
            if warnings:
                return self.respond_html(request, migrate_template_page(t("迁移完成，但需要检查提示。", "Migration finished, but warnings need review."), result, "warning"))
            return self.respond_html(request, migrate_template_page(t("迁移完成。", "Migration finished."), result, "success"))
        except Exception as exc:
            log_path = log_exception("migrate-template", exc)
            message = (
                f"{t('迁移失败，工具已记录错误日志。请把 Excel 原文件和日志文件发给作者排查。日志位置：', 'Migration failed. The tool recorded an error log. Please send the original Excel and the log file to the author. Log path: ')}"
                f"{log_path}"
            )
            return self.respond_html(request, migrate_template_page(message, message_level="error"), HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_ack(self, request: BaseHTTPRequestHandler):
        body = self.read_body(request)
        _, files = parse_multipart(request.headers, body)
        file_part = files.get("ack_xml")
        if not file_part:
            return self.respond_html(
                request,
                ack_page(message=t("请选择一个 EUDAMED response XML。", "Please choose an EUDAMED response XML."), message_level="error"),
                HTTPStatus.BAD_REQUEST,
            )
        result = parse_acknowledgement(file_part["content"], self.repository)
        level = "error" if result.get("errors") else "success" if result.get("ok") else "warning"
        message = (
            t("解析完成。", "Parsed.")
            if result.get("ok")
            else t("无法识别该 response XML，请确认上传的是 EUDAMED 回传文件。", "Cannot recognize this response XML; make sure it is the response returned by EUDAMED.")
        )
        return self.respond_html(request, ack_page(result=result, message=message, message_level=level))

    def handle_basic_update(self, request: BaseHTTPRequestHandler, record_id: int):
        record = self.repository.get_basic(record_id)
        if not record:
            return self.respond_html(request, page(t("未找到","Not found"), f"<section class='panel'><h1>{t('未找到 Basic UDI-DI','Basic UDI-DI not found')}</h1></section>"), HTTPStatus.NOT_FOUND)
        form = self.read_form(request)
        payload = dict(record["payload"])
        for field in BASIC_FIELDS:
            payload[field] = form.get(f"field_{field}", [""])[0]
        try:
            cmr_rows = parse_json_array(form.get("cmr_json", [""])[0])
            cert_rows = parse_json_array(form.get("cert_json", [""])[0])
        except ValueError as exc:
            return self.respond_html(request, basic_detail(record, f"{t('保存失败','Save failed')}: {exc}", "error"), HTTPStatus.BAD_REQUEST)
        self.repository.update_basic(
            record_id=record_id,
            payload=payload,
            cmr_rows=cmr_rows,
            cert_rows=cert_rows,
            version=form.get("version", [""])[0],
            state=form.get("state", ["draft"])[0],
            notes=form.get("notes", [""])[0],
        )
        updated = self.repository.get_basic(record_id)
        freshness = self.repository.export_freshness("basic", [updated["basic_code"]]).get(updated["basic_code"], {}) if updated else {}
        changes = self.repository.get_record_import_changes("basic", updated["basic_code"]) if updated else []
        return self.respond_html(request, basic_detail(updated, t("保存成功。","Saved."), "success", freshness, changes))

    def handle_udi_update(self, request: BaseHTTPRequestHandler, record_id: int):
        record = self.repository.get_udi(record_id)
        if not record:
            return self.respond_html(request, page(t("未找到","Not found"), f"<section class='panel'><h1>{t('未找到 UDI-DI','UDI-DI not found')}</h1></section>"), HTTPStatus.NOT_FOUND)
        form = self.read_form(request)
        payload = dict(record["payload"])
        for field in UDI_FIELDS:
            payload[field] = form.get(f"field_{field}", [""])[0]
        try:
            market_rows = parse_json_array(form.get("market_json", [""])[0])
            warning_rows = parse_json_array(form.get("warning_json", [""])[0])
            storage_rows = parse_json_array(form.get("storage_json", [""])[0])
            package_rows = parse_json_array(form.get("package_json", [""])[0])
            trade_name_rows = parse_json_array(form.get("trade_name_json", [""])[0])
            clinical_size_rows = parse_json_array(form.get("clinical_size_json", [""])[0])
            annex_xvi_rows = parse_json_array(form.get("annex_xvi_json", [""])[0])
        except ValueError as exc:
            return self.respond_html(request, udi_detail(record, f"{t('保存失败','Save failed')}: {exc}", "error"), HTTPStatus.BAD_REQUEST)
        self.repository.update_udi(
            record_id=record_id,
            payload=payload,
            market_rows=market_rows,
            warning_rows=warning_rows,
            storage_rows=storage_rows,
            package_rows=package_rows,
            trade_name_rows=trade_name_rows,
            clinical_size_rows=clinical_size_rows,
            annex_xvi_rows=annex_xvi_rows,
            version=form.get("version", [""])[0],
            state=form.get("state", ["draft"])[0],
            notes=form.get("notes", [""])[0],
        )
        updated = self.repository.get_udi(record_id)
        freshness = self.repository.export_freshness("udi", [updated["udi_code"]]).get(updated["udi_code"], {}) if updated else {}
        changes = self.repository.get_record_import_changes("udi", updated["udi_code"]) if updated else []
        return self.respond_html(request, udi_detail(updated, t("保存成功。","Saved."), "success", freshness, changes))

    def handle_export(self, request: BaseHTTPRequestHandler):
        form = self.read_form(request)
        service_type = form.get("service_type", [""])[0]
        selection_mode = form.get("selection_mode", ["selected"])[0]
        filters = self._filters_from_form(form)
        pagination = self._pagination_from_form(form)
        xsd_report = build_xsd_version_report(check_online=False)
        if not service_type:
            return self.respond_html(
                request,
                export_page(
                    "", [], None, filters, xsd_report, 0, [], self._srn_options(), selection_mode,
                    page_number=pagination["page"], page_size=pagination["page_size"],
                ),
            )
        entity_type = self._entity_type_for_service(service_type)
        invalid_ids = []
        if selection_mode == "filtered":
            record_ids = self.repository.get_filtered_ids(entity_type, **filters)
        else:
            record_ids, invalid_ids = self._parse_record_ids(form.get("record_ids", []))

        result = self._xsd_blocking_result(service_type, xsd_report)
        action = form.get("action", ["export"])[0]
        if not result:
            result = self.exporter.validate(service_type, record_ids) if action == "preflight" else self.exporter.export(service_type, record_ids)
            if invalid_ids:
                result["warnings"].append(
                    f"{t('忽略了无效记录 ID', 'Ignored invalid record IDs')}: {', '.join(invalid_ids)}"
                )
            result["selection_mode"] = selection_mode
            result["selected_count"] = len(record_ids)
            result["action"] = action

        records, total_filtered, pagination = self._paged_records(entity_type, filters, pagination)
        return self.respond_html(
            request,
            export_page(
                service_type, records, result, filters, xsd_report, total_filtered, record_ids,
                self._srn_options(), selection_mode,
                page_number=pagination["page"], page_size=pagination["page_size"],
            ),
        )

    def _filters_from_query(self, query: dict) -> dict:
        return {
            "query": query.get("q", [""])[0],
            "state": query.get("state", [""])[0],
            "legislation": query.get("legislation", [""])[0],
            "change_type": query.get("change_type", [""])[0],
            "srn": query.get("srn", [""])[0],
            "freshness_filter": query.get("freshness_filter", [""])[0],
            "import_id": self._positive_int_text(query.get("import_id", [""])[0]),
        }

    def _filters_from_form(self, form: dict) -> dict:
        return {
            "query": form.get("q", [""])[0],
            "state": form.get("state", [""])[0],
            "legislation": form.get("legislation", [""])[0],
            "change_type": form.get("change_type", [""])[0],
            "srn": form.get("srn", [""])[0],
            "freshness_filter": form.get("freshness_filter", [""])[0],
            "import_id": self._positive_int_text(form.get("import_id", [""])[0]),
        }

    def _pagination_from_query(self, query: dict) -> dict:
        return self._pagination(
            query.get("page", ["1"])[0],
            query.get("page_size", ["200"])[0],
        )

    def _pagination_from_form(self, form: dict) -> dict:
        return self._pagination(
            form.get("page", ["1"])[0],
            form.get("page_size", ["200"])[0],
        )

    def _pagination(self, page_value, page_size_value) -> dict:
        try:
            page = max(int(page_value), 1)
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(max(int(page_size_value), 1), 500)
        except (TypeError, ValueError):
            page_size = 200
        return {"page": page, "page_size": page_size}

    def _positive_int_text(self, value) -> str:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return ""
        return str(parsed) if parsed > 0 else ""

    def _paged_records(self, entity_type: str, filters: dict, pagination: dict) -> tuple[list[dict], int, dict]:
        total_filtered = len(self.repository.get_filtered_ids(entity_type, **filters))
        page_size = pagination["page_size"]
        total_pages = max(1, (total_filtered + page_size - 1) // page_size)
        page = min(pagination["page"], total_pages)
        offset = (page - 1) * page_size
        records = (
            self.repository.list_basics(**filters, limit=page_size, offset=offset)
            if entity_type == "basic"
            else self.repository.list_udis(**filters, limit=page_size, offset=offset)
        )
        return records, total_filtered, {"page": page, "page_size": page_size}

    def _entity_type_for_service(self, service_type: str) -> str:
        return "basic" if service_type == "Basic_UDI.PATCH" else "udi"

    def _srn_options(self) -> list[str]:
        return [item["srn"] for item in self.repository.manufacturer_srn_summary() if item["srn"]]

    def _parse_int_id(self, path: str) -> int | None:
        try:
            return int(path.rstrip("/").split("/")[-1])
        except (TypeError, ValueError):
            return None

    def _parse_record_ids(self, values: list[str]) -> tuple[list[int], list[str]]:
        record_ids = []
        invalid = []
        for value in values:
            try:
                record_ids.append(int(value))
            except (TypeError, ValueError):
                invalid.append(str(value))
        return record_ids, invalid

    def _xsd_blocking_result(self, service_type: str, report: dict) -> dict | None:
        tool_version = report.get("tool_version") or ""
        local_version = report.get("local_xsd_version") or ""
        if local_version and tool_version != local_version:
            return {
                "service_type": service_type,
                "errors": [
                    f"{t('本地 XSD 版本', 'Local XSD version')} {local_version} "
                    f"{t('与工具声明版本', 'differs from tool version')} {tool_version} "
                    f"{t('不一致，已阻止导出。', '— export blocked.')}"
                ],
                "warnings": [],
                "selected_count": 0,
                "action": "blocked",
            }
        return None

    def _download_content_type(self, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix == ".zip":
            return "application/zip"
        if suffix == ".csv":
            return "text/csv; charset=utf-8"
        if suffix == ".html":
            return "text/html; charset=utf-8"
        if suffix == ".xlsx":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return "application/xml; charset=utf-8"

    def read_form(self, request: BaseHTTPRequestHandler):
        body = self.read_body(request)
        return parse_qs(body.decode("utf-8"), keep_blank_values=True)

    def read_body(self, request: BaseHTTPRequestHandler) -> bytes:
        length = int(request.headers.get("Content-Length", "0"))
        return request.rfile.read(length)

    def respond_html(self, request: BaseHTTPRequestHandler, content: str, status=HTTPStatus.OK):
        data = content.encode("utf-8")
        request.send_response(status)
        request.send_header("Content-Type", "text/html; charset=utf-8")
        request.send_header("Content-Length", str(len(data)))
        request.end_headers()
        request.wfile.write(data)

    def redirect(self, request: BaseHTTPRequestHandler, location: str):
        request.send_response(HTTPStatus.FOUND)
        request.send_header("Location", location)
        request.send_header("Content-Length", "0")
        request.end_headers()

    def not_found(self, request: BaseHTTPRequestHandler, message: str):
        return self.respond_html(
            request,
            page(t("未找到", "Not found"), f"<section class='panel'><h1>{message}</h1></section>"),
            HTTPStatus.NOT_FOUND,
        )

    def respond_file(self, request: BaseHTTPRequestHandler, path: Path, content_type: str, inline: bool = False):
        if not path.exists() or not path.is_file():
            return self.not_found(request, t("文件不存在", "File not found"))
        data = path.read_bytes()
        request.send_response(HTTPStatus.OK)
        request.send_header("Content-Type", content_type)
        request.send_header("Content-Length", str(len(data)))
        if not inline:
            request.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
        request.end_headers()
        request.wfile.write(data)

    def _lang_from_request(self, request: BaseHTTPRequestHandler) -> str:
        raw = request.headers.get("Cookie", "")
        if not raw:
            return "zh"
        try:
            cookie = SimpleCookie(raw)
        except Exception:
            return "zh"
        morsel = cookie.get("lang")
        value = morsel.value if morsel else "zh"
        return "en" if value == "en" else "zh"

    def handle_set_lang(self, request: BaseHTTPRequestHandler, query: dict):
        lang = "en" if query.get("lang", ["zh"])[0] == "en" else "zh"
        next_path = query.get("next", ["/"])[0]
        if not next_path.startswith("/") or next_path.startswith("//"):
            next_path = "/"
        set_lang(lang)
        request.send_response(HTTPStatus.FOUND)
        request.send_header("Location", next_path)
        request.send_header("Set-Cookie", f"lang={lang}; Path=/; Max-Age=31536000; SameSite=Lax")
        request.send_header("Content-Length", "0")
        request.end_headers()


def run_server(host: str = "127.0.0.1", port: int = 8765, max_port_tries: int = 12):
    # 1) 初始化（建库等）。失败时记录并尽量让用户看见。
    try:
        app = App()
    except Exception as exc:
        log_startup(f"初始化失败 / init failed: {type(exc).__name__}: {exc}\n{traceback.format_exc()}")
        show_startup_error(
            "EUDAMED 工具启动失败（初始化阶段）。\nStartup failed during initialization.",
            f"{type(exc).__name__}: {exc}",
        )
        raise

    # 2) 端口回退：8765 被占就依次尝试 8766..，绑定第一个可用端口。
    server = None
    chosen_port = None
    last_error = None
    for candidate in range(port, port + max_port_tries):
        try:
            server = ThreadingHTTPServer((host, candidate), app.handler())
            chosen_port = candidate
            break
        except OSError as exc:
            last_error = exc
            log_startup(f"端口 {candidate} 不可用 / unavailable: {exc}")

    if server is None:
        last_port = port + max_port_tries - 1
        summary = (
            f"找不到可用端口（已尝试 {port}-{last_port}）。\n"
            f"No free port found (tried {port}-{last_port})."
        )
        detail = (
            f"最后错误 / last error: {last_error}\n"
            "可能原因：1) 工具已有一个实例在后台运行；2) 其它程序占用了这些端口；"
            "3) 防火墙/杀毒拦截了本程序。\n"
            "Likely causes: another instance already running; another app using these ports; "
            "firewall/antivirus blocking this program."
        )
        log_startup(summary + " " + detail)
        show_startup_error("EUDAMED 工具启动失败：" + summary, detail)
        raise SystemExit(1)

    # 3) 让浏览器打开【真正绑定到的】端口，而不是写死的 8765。
    url = f"http://{host}:{chosen_port}"
    log_startup(f"启动成功 / started at {url}")
    print(f"Local beta is running at {url}")
    if chosen_port != port:
        print(f"(端口 {port} 不可用，已改用 {chosen_port} / port {port} busy, using {chosen_port})")
    if not os.environ.get("EUDAMED_NO_BROWSER") and not os.environ.get("EUDAMED_RELOAD_CHILD"):
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        log_startup(f"运行中异常退出 / crashed while serving: {type(exc).__name__}: {exc}\n{traceback.format_exc()}")
        raise
