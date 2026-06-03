import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .constants import DATA_DIR, DB_PATH, EXPORT_DIR, UPLOAD_DIR


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value) -> str:
    return json.dumps(_normalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalize(value):
    if isinstance(value, dict):
        return {key: _normalize(val) for key, val in sorted(value.items()) if key is not None}
    if isinstance(value, list):
        normalized = [_normalize(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    return value


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_list(raw: str) -> list:
    try:
        value = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


class Repository:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS imports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    validation_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS basic_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    basic_code TEXT NOT NULL UNIQUE,
                    import_id INTEGER,
                    row_number INTEGER,
                    payload_json TEXT NOT NULL,
                    cmr_json TEXT NOT NULL DEFAULT '[]',
                    cert_json TEXT NOT NULL DEFAULT '[]',
                    version TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL DEFAULT 'draft',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS udi_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    udi_code TEXT NOT NULL UNIQUE,
                    basic_code TEXT NOT NULL,
                    import_id INTEGER,
                    row_number INTEGER,
                    payload_json TEXT NOT NULL,
                    market_json TEXT NOT NULL DEFAULT '[]',
                    warnings_json TEXT NOT NULL DEFAULT '[]',
                    storage_json TEXT NOT NULL DEFAULT '[]',
                    package_json TEXT NOT NULL DEFAULT '[]',
                    trade_names_json TEXT NOT NULL DEFAULT '[]',
                    clinical_sizes_json TEXT NOT NULL DEFAULT '[]',
                    annex_xvi_json TEXT NOT NULL DEFAULT '[]',
                    version TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL DEFAULT 'draft',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS export_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_type TEXT NOT NULL,
                    code_list_json TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    validation_json TEXT NOT NULL,
                    record_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS import_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    import_id INTEGER NOT NULL,
                    entity_type TEXT NOT NULL,
                    code TEXT NOT NULL,
                    related_code TEXT NOT NULL DEFAULT '',
                    record_id INTEGER,
                    row_number INTEGER,
                    action TEXT NOT NULL,
                    changed_fields_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            self._ensure_record_columns(conn, "basic_records")
            self._ensure_record_columns(conn, "udi_records")

    def _ensure_record_columns(self, conn: sqlite3.Connection, table: str):
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name in ("first_imported_at", "last_imported_at", "last_changed_at", "last_change_type"):
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")
        if table == "udi_records" and "trade_names_json" not in existing:
            conn.execute("ALTER TABLE udi_records ADD COLUMN trade_names_json TEXT NOT NULL DEFAULT '[]'")
        if table == "udi_records" and "clinical_sizes_json" not in existing:
            conn.execute("ALTER TABLE udi_records ADD COLUMN clinical_sizes_json TEXT NOT NULL DEFAULT '[]'")
        if table == "udi_records" and "annex_xvi_json" not in existing:
            conn.execute("ALTER TABLE udi_records ADD COLUMN annex_xvi_json TEXT NOT NULL DEFAULT '[]'")
        if table == "basic_records" and "cert_json" not in existing:
            conn.execute("ALTER TABLE basic_records ADD COLUMN cert_json TEXT NOT NULL DEFAULT '[]'")
        if "is_sample" not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN is_sample INTEGER NOT NULL DEFAULT 0")
        conn.execute(
            f"""
            UPDATE {table}
            SET first_imported_at = CASE WHEN first_imported_at = '' THEN created_at ELSE first_imported_at END,
                last_imported_at = CASE WHEN last_imported_at = '' THEN updated_at ELSE last_imported_at END,
                last_changed_at = CASE WHEN last_changed_at = '' THEN updated_at ELSE last_changed_at END,
                last_change_type = CASE WHEN last_change_type = '' THEN 'existing' ELSE last_change_type END
            """
        )

    def create_import(self, filename: str, summary: dict, validation: dict) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO imports (filename, imported_at, summary_json, validation_json)
                VALUES (?, ?, ?, ?)
                """,
                (filename, utc_now(), json.dumps(summary, ensure_ascii=False), json.dumps(validation, ensure_ascii=False)),
            )
            return int(cursor.lastrowid)

    def update_import_validation(self, import_id: int, validation: dict) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE imports SET validation_json = ? WHERE id = ?",
                (json.dumps(validation, ensure_ascii=False), import_id),
            )

    def upsert_basic(
        self,
        import_id: int,
        row_number: int,
        payload: dict,
        cmr_rows: list[dict],
        cert_rows: list[dict] | None = None,
        version: str = "",
        is_sample: int = 0,
    ) -> dict | None:
        now = utc_now()
        basic_code = str(payload.get("Basic UDI-DI Code", "") or "").strip()
        if not basic_code:
            return None
        payload_json = _json(payload)
        cmr_json = _json(cmr_rows)
        cert_json = _json(cert_rows or [])
        with self.connect() as conn:
            existing = conn.execute("SELECT * FROM basic_records WHERE basic_code = ?", (basic_code,)).fetchone()
            if existing is None:
                cursor = conn.execute(
                    """
                    INSERT INTO basic_records
                    (basic_code, import_id, row_number, payload_json, cmr_json, cert_json, version, state, created_at, updated_at,
                     first_imported_at, last_imported_at, last_changed_at, last_change_type, is_sample)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, 'created', ?)
                    """,
                    (
                        basic_code,
                        import_id,
                        row_number,
                        payload_json,
                        cmr_json,
                        cert_json,
                        version,
                        now,
                        now,
                        now,
                        now,
                        now,
                        1 if is_sample else 0,
                    ),
                )
                change = self._record_import_change(
                    conn, import_id, "basic", basic_code, "", int(cursor.lastrowid), row_number, "created", ["record"]
                )
                return change

            effective_version = version if version else existing["version"]
            changed_fields = self._changed_fields(
                existing,
                {
                    "payload_json": payload_json,
                    "cmr_json": cmr_json,
                    "cert_json": cert_json,
                    "version": effective_version,
                    "is_sample": 1 if is_sample else 0,
                },
                {"payload_json": "fields", "cmr_json": "CMR Substances", "cert_json": "Device Certificates", "version": "version", "is_sample": "sample flag"},
            )
            action = "updated" if changed_fields else "unchanged"
            next_state = self._state_after_import(existing["state"], action)
            if action == "updated":
                conn.execute(
                    """
                    UPDATE basic_records
                    SET import_id = ?, row_number = ?, payload_json = ?, cmr_json = ?, cert_json = ?, version = ?,
                        state = ?, updated_at = ?, last_imported_at = ?, last_changed_at = ?, last_change_type = ?, is_sample = ?
                    WHERE id = ?
                    """,
                    (
                        import_id,
                        row_number,
                        payload_json,
                        cmr_json,
                        cert_json,
                        effective_version,
                        next_state,
                        now,
                        now,
                        now,
                        action,
                        1 if is_sample else 0,
                        existing["id"],
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE basic_records
                    SET import_id = ?, row_number = ?, last_imported_at = ?, last_change_type = ?, is_sample = ?
                    WHERE id = ?
                    """,
                    (import_id, row_number, now, action, 1 if is_sample else 0, existing["id"]),
                )
            return self._record_import_change(
                conn, import_id, "basic", basic_code, "", existing["id"], row_number, action, changed_fields
            )

    def upsert_udi(
        self,
        import_id: int,
        row_number: int,
        payload: dict,
        market_rows: list[dict],
        warning_rows: list[dict],
        storage_rows: list[dict],
        package_rows: list[dict],
        trade_name_rows: list[dict] | None = None,
        clinical_size_rows: list[dict] | None = None,
        annex_xvi_rows: list[dict] | None = None,
        version: str = "",
        is_sample: int = 0,
    ) -> dict | None:
        now = utc_now()
        udi_code = str(payload.get("UDI-DI Code", "") or "").strip()
        basic_code = str(payload.get("Parent Basic UDI-DI", "") or "").strip()
        if not udi_code:
            return None
        payload_json = _json(payload)
        market_json = _json(market_rows)
        warnings_json = _json(warning_rows)
        storage_json = _json(storage_rows)
        package_json = _json(package_rows)
        trade_names_json = _json(trade_name_rows or [])
        clinical_sizes_json = _json(clinical_size_rows or [])
        annex_xvi_json = _json(annex_xvi_rows or [])
        with self.connect() as conn:
            existing = conn.execute("SELECT * FROM udi_records WHERE udi_code = ?", (udi_code,)).fetchone()
            if existing is None:
                cursor = conn.execute(
                    """
                    INSERT INTO udi_records
                    (udi_code, basic_code, import_id, row_number, payload_json, market_json, warnings_json,
                     storage_json, package_json, trade_names_json, clinical_sizes_json, annex_xvi_json, version, state, created_at, updated_at,
                     first_imported_at, last_imported_at, last_changed_at, last_change_type, is_sample)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, 'created', ?)
                    """,
                    (
                        udi_code,
                        basic_code,
                        import_id,
                        row_number,
                        payload_json,
                        market_json,
                        warnings_json,
                        storage_json,
                        package_json,
                        trade_names_json,
                        clinical_sizes_json,
                        annex_xvi_json,
                        version,
                        now,
                        now,
                        now,
                        now,
                        now,
                        1 if is_sample else 0,
                    ),
                )
                return self._record_import_change(
                    conn, import_id, "udi", udi_code, basic_code, int(cursor.lastrowid), row_number, "created", ["record"]
                )

            effective_version = version if version else existing["version"]
            changed_fields = self._changed_fields(
                existing,
                {
                    "basic_code": basic_code,
                    "payload_json": payload_json,
                    "market_json": market_json,
                    "warnings_json": warnings_json,
                    "storage_json": storage_json,
                    "package_json": package_json,
                    "trade_names_json": trade_names_json,
                    "clinical_sizes_json": clinical_sizes_json,
                    "annex_xvi_json": annex_xvi_json,
                    "version": effective_version,
                    "is_sample": 1 if is_sample else 0,
                },
                {
                    "basic_code": "Parent Basic UDI-DI",
                    "payload_json": "fields",
                    "market_json": "Market Info",
                    "warnings_json": "Critical Warnings",
                    "storage_json": "Storage Conditions",
                    "package_json": "Package Info",
                    "trade_names_json": "Trade Names",
                    "clinical_sizes_json": "Clinical Sizes",
                    "annex_xvi_json": "Annex XVI Purposes",
                    "version": "version",
                    "is_sample": "sample flag",
                },
            )
            action = "updated" if changed_fields else "unchanged"
            next_state = self._state_after_import(existing["state"], action)
            if action == "updated":
                conn.execute(
                    """
                    UPDATE udi_records
                    SET basic_code = ?, import_id = ?, row_number = ?, payload_json = ?, market_json = ?,
                        warnings_json = ?, storage_json = ?, package_json = ?, trade_names_json = ?, clinical_sizes_json = ?, annex_xvi_json = ?,
                        version = ?, state = ?,
                        updated_at = ?, last_imported_at = ?, last_changed_at = ?, last_change_type = ?, is_sample = ?
                    WHERE id = ?
                    """,
                    (
                        basic_code,
                        import_id,
                        row_number,
                        payload_json,
                        market_json,
                        warnings_json,
                        storage_json,
                        package_json,
                        trade_names_json,
                        clinical_sizes_json,
                        annex_xvi_json,
                        effective_version,
                        next_state,
                        now,
                        now,
                        now,
                        action,
                        1 if is_sample else 0,
                        existing["id"],
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE udi_records
                    SET import_id = ?, row_number = ?, last_imported_at = ?, last_change_type = ?, is_sample = ?
                    WHERE id = ?
                    """,
                    (import_id, row_number, now, action, 1 if is_sample else 0, existing["id"]),
                )
            return self._record_import_change(
                conn, import_id, "udi", udi_code, basic_code, existing["id"], row_number, action, changed_fields
            )

    def _changed_fields(self, existing: sqlite3.Row, incoming: dict, labels: dict) -> list[str]:
        changed = []
        for key, value in incoming.items():
            old_value = existing[key]
            if key.endswith("_json"):
                old_value = json.loads(old_value or "[]")
                value = json.loads(value or "[]")
            if canonical_json(old_value) != canonical_json(value):
                changed.append(labels.get(key, key))
        return changed

    def _state_after_import(self, state: str, action: str) -> str:
        if action != "updated":
            return state
        if state in {"xml_generated", "submitted"}:
            return "pending_update"
        return state

    def _record_import_change(
        self,
        conn: sqlite3.Connection,
        import_id: int,
        entity_type: str,
        code: str,
        related_code: str,
        record_id: int,
        row_number: int,
        action: str,
        changed_fields: list[str],
    ) -> dict:
        now = utc_now()
        conn.execute(
            """
            INSERT INTO import_changes
            (import_id, entity_type, code, related_code, record_id, row_number, action, changed_fields_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (import_id, entity_type, code, related_code, record_id, row_number, action, _json(changed_fields), now),
        )
        return {
            "entity_type": entity_type,
            "code": code,
            "related_code": related_code,
            "record_id": record_id,
            "row_number": row_number,
            "action": action,
            "changed_fields": changed_fields,
        }

    def get_stats(self) -> dict:
        with self.connect() as conn:
            stats = {
                "basic_count": conn.execute("SELECT COUNT(*) FROM basic_records").fetchone()[0],
                "udi_count": conn.execute("SELECT COUNT(*) FROM udi_records").fetchone()[0],
                "sample_basic_count": conn.execute("SELECT COUNT(*) FROM basic_records WHERE is_sample = 1").fetchone()[0],
                "sample_udi_count": conn.execute("SELECT COUNT(*) FROM udi_records WHERE is_sample = 1").fetchone()[0],
                "pending_count": conn.execute(
                    "SELECT COUNT(*) FROM udi_records WHERE state IN ('pending_update', 'draft')"
                ).fetchone()[0],
                "import_count": conn.execute("SELECT COUNT(*) FROM imports").fetchone()[0],
                "export_count": conn.execute("SELECT COUNT(*) FROM export_jobs").fetchone()[0],
            }
            return stats

    def sample_data_count(self) -> dict:
        with self.connect() as conn:
            return {
                "basic": conn.execute("SELECT COUNT(*) FROM basic_records WHERE is_sample = 1").fetchone()[0],
                "udi": conn.execute("SELECT COUNT(*) FROM udi_records WHERE is_sample = 1").fetchone()[0],
            }

    def clear_sample_data(self) -> dict:
        with self.connect() as conn:
            udi_deleted = conn.execute("DELETE FROM udi_records WHERE is_sample = 1").rowcount
            basic_deleted = conn.execute("DELETE FROM basic_records WHERE is_sample = 1").rowcount
        return {"basic": basic_deleted, "udi": udi_deleted}

    def load_sample_data(self) -> dict:
        self.clear_sample_data()
        import_id = self.create_import(
            "Sample data / 示例数据",
            {"basic_count": 1, "udi_count": 2},
            {"errors": [], "warnings": ["示例数据仅供熟悉流程，请勿上传到 EUDAMED。"]},
        )
        basic_payload = {
            "Basic UDI-DI Code": "SAMPLE-BASIC-0001",
            "Issuing Entity": "GS1",
            "Manufacturer SRN": "CN-MF-000000001",
            "Risk Class": "Class IIa",
            "Applicable Legislation": "MDR",
            "Device Type": "Regular Device",
            "Device Name/Model": "SAMPLE Training Device",
            "EMDN Code": "M020101",
            "Active Device": "FALSE",
            "Measuring Function": "FALSE",
            "Administer Medicine": "FALSE",
            "Implantable": "FALSE",
            "Reusable Surgical Instrument": "FALSE",
            "Presence of Human Tissues": "FALSE",
            "Presence of Animal Tissues": "FALSE",
            "Medicinal Product Device": "FALSE",
            "Additional Description": "Sample data only - do not submit to EUDAMED",
            "Device Model": "",
            "Authorised Representative SRN": "NL-AR-000000001",
            "Special Device Type": "",
            "Is Suture/Staple/Filling/Brace (IIb Implant)": "FALSE",
        }
        basic_change = self.upsert_basic(
            import_id,
            4,
            basic_payload,
            cmr_rows=[],
            cert_rows=[],
            version="",
            is_sample=1,
        )
        base_udi_payload = {
            "Parent Basic UDI-DI": "SAMPLE-BASIC-0001",
            "UDI-DI Issuing Entity": "GS1",
            "Device Status": "On the EU market",
            "Quantity of Device": "1",
            "Single Use Device": "TRUE",
            "Max Number of Reuses": "0",
            "Device Labelled as Sterile": "FALSE",
            "Needs Sterilisation Before Use": "FALSE",
            "Containing Latex": "FALSE",
            "Reprocessed Single Use Device": "FALSE",
            "Direct Marking": "FALSE",
            "DM DI Same as UDI-DI": "TRUE",
            "DM Issuing Entity": "GS1",
            "Unit of Use Issuing Entity": "GS1",
            "Secondary Issuing Entity": "GS1",
            "Trade Name Applicable": "TRUE",
            "Trade Name Language": "ANY",
            "Nomenclature Code": "M020101",
            "Nomenclature System": "EMDN",
            "Description Language": "en",
            "Public Website": "https://example.com/sample-device",
            "Public Email": "",
            "PI Lot/Batch Number": "TRUE",
            "PI Expiration Date": "TRUE",
            "PI Manufacturing Date": "TRUE",
            "PI Serial Number": "FALSE",
            "PI Software Identification": "FALSE",
        }
        created = [basic_change] if basic_change else []
        sample_udis = [
            ("SAMPLE-UDI-0001", "SAMPLE-REF-001", "Sample Training Device 10x10 cm", "Sample Trade Name A"),
            ("SAMPLE-UDI-0002", "SAMPLE-REF-002", "Sample Training Device 20x20 cm", "Sample Trade Name B"),
        ]
        for index, (udi_code, reference, description, trade_name) in enumerate(sample_udis, start=5):
            payload = dict(base_udi_payload)
            payload.update(
                {
                    "UDI-DI Code": udi_code,
                    "Reference Number": reference,
                    "Additional Description": description,
                    "Trade Name": trade_name,
                }
            )
            change = self.upsert_udi(
                import_id,
                index,
                payload,
                market_rows=[
                    {
                        "UDI-DI Code": udi_code,
                        "Country Code": "IT",
                        "Placed on Market": "TRUE",
                        "Start Date": "2026-01-01",
                        "End Date": "",
                        "Originally Placed on Market": "TRUE",
                    }
                ],
                warning_rows=[],
                storage_rows=[
                    {
                        "UDI-DI Code": udi_code,
                        "Storage Condition Type": "SHC005 - Keep dry",
                        "Language": "ANY",
                        "Description": "",
                    }
                ],
                package_rows=[
                    {
                        "UDI-DI Code": udi_code,
                        "Package Level": "Outer carton",
                        "Package Type": "Carton",
                        "Package UDI-DI Code": f"SAMPLE-PACK-{udi_code[-4:]}",
                        "Package Issuing Entity": "GS1",
                        "Contains DI Code": udi_code,
                        "Contains DI Issuing Entity": "GS1",
                        "Quantity per Package": "10",
                    }
                ],
                trade_name_rows=[
                    {
                        "UDI-DI Code": udi_code,
                        "Trade Name": trade_name,
                        "Language": "ANY",
                    }
                ],
                version="",
                is_sample=1,
            )
            if change:
                created.append(change)
        return {"import_id": import_id, "changes": created, "counts": self.sample_data_count()}

    def recent_imports(self, limit: int = 5) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM imports ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    def recent_exports(self, limit: int = 5) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM export_jobs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    def list_udis(
        self,
        query: str = "",
        state: str = "",
        legislation: str = "",
        change_type: str = "",
        srn: str = "",
        freshness_filter: str = "",
        limit: int | None = 200,
    ) -> list[dict]:
        sql = """
            SELECT u.*, b.payload_json AS basic_payload_json
            FROM udi_records u
            LEFT JOIN basic_records b ON b.basic_code = u.basic_code
            WHERE 1=1
        """
        params = []
        if query:
            sql += """
                AND (
                    u.udi_code LIKE ? OR u.basic_code LIKE ? OR u.notes LIKE ?
                    OR u.payload_json LIKE ? OR b.payload_json LIKE ?
                )
            """
            like = f"%{query}%"
            params.extend([like, like, like, like, like])
        if state:
            sql += " AND u.state = ?"
            params.append(state)
        if legislation:
            sql += " AND json_extract(b.payload_json, '$.\"Applicable Legislation\"') = ?"
            params.append(legislation)
        if change_type:
            sql += " AND u.last_change_type = ?"
            params.append(change_type)
        if srn:
            sql += " AND json_extract(b.payload_json, '$.\"Manufacturer SRN\"') = ?"
            params.append(srn)
        sql += " ORDER BY u.updated_at DESC, u.id DESC"
        if limit is not None and not freshness_filter:
            sql += " LIMIT ?"
            params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        records = [self._row_to_udi_dict(row) for row in rows]
        records = self._filter_by_freshness("udi", records, freshness_filter)
        return records[:limit] if limit is not None and freshness_filter else records

    def list_basics(
        self,
        query: str = "",
        state: str = "",
        legislation: str = "",
        change_type: str = "",
        srn: str = "",
        freshness_filter: str = "",
        limit: int | None = 200,
    ) -> list[dict]:
        sql = "SELECT * FROM basic_records WHERE 1=1"
        params = []
        if query:
            sql += " AND (basic_code LIKE ? OR notes LIKE ? OR payload_json LIKE ?)"
            like = f"%{query}%"
            params.extend([like, like, like])
        if state:
            sql += " AND state = ?"
            params.append(state)
        if legislation:
            sql += " AND json_extract(payload_json, '$.\"Applicable Legislation\"') = ?"
            params.append(legislation)
        if change_type:
            sql += " AND last_change_type = ?"
            params.append(change_type)
        if srn:
            sql += " AND json_extract(payload_json, '$.\"Manufacturer SRN\"') = ?"
            params.append(srn)
        sql += " ORDER BY updated_at DESC, id DESC"
        if limit is not None and not freshness_filter:
            sql += " LIMIT ?"
            params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        records = [self._row_to_basic_dict(row) for row in rows]
        records = self._filter_by_freshness("basic", records, freshness_filter)
        return records[:limit] if limit is not None and freshness_filter else records

    def get_filtered_ids(
        self,
        entity_type: str,
        query: str = "",
        state: str = "",
        legislation: str = "",
        change_type: str = "",
        srn: str = "",
        freshness_filter: str = "",
    ) -> list[int]:
        records = (
            self.list_basics(query, state, legislation, change_type, srn, freshness_filter, limit=None)
            if entity_type == "basic"
            else self.list_udis(query, state, legislation, change_type, srn, freshness_filter, limit=None)
        )
        return [int(item["id"]) for item in records]

    def _filter_by_freshness(self, entity_type: str, records: list[dict], freshness_filter: str) -> list[dict]:
        freshness_filter = str(freshness_filter or "").strip()
        if not freshness_filter:
            return records
        freshness = self._freshness_for_records(entity_type, records)
        return [
            item for item in records
            if freshness.get(str((item.get("basic_code") if entity_type == "basic" else item.get("udi_code")) or "").strip(), {}).get("status") == freshness_filter
        ]

    def manufacturer_srn_summary(self) -> list[dict]:
        sql = """
            SELECT
                COALESCE(json_extract(b.payload_json, '$."Manufacturer SRN"'), '') AS srn,
                COUNT(DISTINCT b.id) AS basic_count,
                COUNT(DISTINCT u.id) AS udi_count
            FROM basic_records b
            LEFT JOIN udi_records u ON u.basic_code = b.basic_code
            GROUP BY srn
            ORDER BY srn
        """
        with self.connect() as conn:
            rows = conn.execute(sql).fetchall()
        return [
            {
                "srn": row["srn"] or "",
                "basic_count": row["basic_count"],
                "udi_count": row["udi_count"],
            }
            for row in rows
        ]

    def consistency_findings(self, srn_filter: str = "", only_codes: dict | None = None) -> list[dict]:
        """跨记录一致性提示。只做 warning/info，不阻断导出。"""
        basic_records = self.list_basics(srn=srn_filter, limit=None)
        udi_records = self.list_udis(srn=srn_filter, limit=None)
        selected_basic = set(str(code).strip() for code in (only_codes or {}).get("basic", []) if str(code).strip())
        selected_udi = set(str(code).strip() for code in (only_codes or {}).get("udi", []) if str(code).strip())
        findings: list[dict] = []

        def in_scope(codes: list[str], entity_type: str) -> bool:
            if not selected_basic and not selected_udi:
                return True
            selected = selected_basic if entity_type == "basic" else selected_udi
            return bool(set(codes) & selected)

        by_srn: dict[str, list[dict]] = {}
        for item in basic_records:
            srn = str((item.get("payload") or {}).get("Manufacturer SRN") or "").strip()
            if srn:
                by_srn.setdefault(srn, []).append(item)
        for srn, rows in by_srn.items():
            names = sorted({str((row.get("payload") or {}).get("Device Name/Model") or "").strip() for row in rows if str((row.get("payload") or {}).get("Device Name/Model") or "").strip()})
            ars = sorted({str((row.get("payload") or {}).get("Authorised Representative SRN") or "").strip() for row in rows if str((row.get("payload") or {}).get("Authorised Representative SRN") or "").strip()})
            codes = [row["basic_code"] for row in rows]
            if (len(names) > 1 or len(ars) > 1) and in_scope(codes, "basic"):
                findings.append({
                    "type": "srn_drift",
                    "severity": "warning",
                    "codes": codes,
                    "message": f"同一 Manufacturer SRN {srn} 下出现多个 Device Name/Model 或 Authorised Representative SRN，请确认是否属于同一 actor 的正常多产品数据。",
                    "message_en": f"Manufacturer SRN {srn} has multiple Device Name/Model or Authorised Representative SRN values. Confirm whether this is expected for the same actor.",
                    "detail": {"srn": srn, "device_names": names, "authorised_representatives": ars},
                })

        reference_map: dict[str, list[dict]] = {}
        for item in udi_records:
            reference = str((item.get("payload") or {}).get("Reference Number") or "").strip()
            if reference:
                reference_map.setdefault(reference, []).append(item)
        for reference, rows in reference_map.items():
            codes = [row["udi_code"] for row in rows]
            if len(codes) > 1 and in_scope(codes, "udi"):
                findings.append({
                    "type": "reference_reuse",
                    "severity": "warning",
                    "codes": codes,
                    "message": f"Reference Number {reference} 被多个 UDI-DI 使用，请确认是否为真实共用 reference。",
                    "message_en": f"Reference Number {reference} is used by multiple UDI-DIs. Confirm whether this reuse is intentional.",
                    "detail": {"reference": reference},
                })

        emdn_map: dict[str, list[dict]] = {}
        for item in basic_records:
            emdn = str((item.get("payload") or {}).get("EMDN Code") or "").strip()
            if emdn:
                emdn_map.setdefault(emdn, []).append(item)
        for emdn, rows in emdn_map.items():
            risks = sorted({str((row.get("payload") or {}).get("Risk Class") or "").strip() for row in rows if str((row.get("payload") or {}).get("Risk Class") or "").strip()})
            codes = [row["basic_code"] for row in rows]
            if len(risks) > 1 and in_scope(codes, "basic"):
                findings.append({
                    "type": "emdn_risk_split",
                    "severity": "info",
                    "codes": codes,
                    "message": f"同一 EMDN Code {emdn} 下出现多个 Risk Class。该情况可能合理，但建议确认分类依据。",
                    "message_en": f"EMDN Code {emdn} appears with multiple Risk Classes. This may be valid, but classification should be checked.",
                    "detail": {"emdn": emdn, "risk_classes": risks},
                })

        basic_by_code = {item["basic_code"]: item for item in basic_records}
        for udi in udi_records:
            payload = udi.get("payload") or {}
            basic = basic_by_code.get(udi.get("basic_code"))
            if not basic:
                continue
            basic_payload = basic.get("payload") or {}
            drift = []
            for field in ("Manufacturer SRN", "Authorised Representative SRN"):
                udi_value = str(payload.get(field) or "").strip()
                basic_value = str(basic_payload.get(field) or "").strip()
                if udi_value and basic_value and udi_value != basic_value:
                    drift.append(field)
            if drift and in_scope([udi["udi_code"]], "udi"):
                findings.append({
                    "type": "basic_member_drift",
                    "severity": "warning",
                    "codes": [udi["udi_code"]],
                    "message": f"UDI-DI {udi['udi_code']} 的 {', '.join(drift)} 与父 Basic UDI-DI 不一致，请核对父子关系。",
                    "message_en": f"UDI-DI {udi['udi_code']} has {', '.join(drift)} values inconsistent with its parent Basic UDI-DI. Check the linkage.",
                    "detail": {"basic_code": udi.get("basic_code"), "fields": drift},
                })
        return findings

    def export_freshness(self, entity_type: str, codes: list[str]) -> dict:
        requested = [str(code or "").strip() for code in codes if str(code or "").strip()]
        if not requested:
            return {}
        records_by_code = self._records_by_codes(entity_type, requested)
        result = self._freshness_for_records(
            entity_type,
            [records_by_code[code] for code in requested if code in records_by_code],
        )
        for code in requested:
            result.setdefault(
                code,
                {
                    "status": "never_exported",
                    "last_exported_at": "",
                    "last_changed_at": "",
                },
            )
        return result

    def export_freshness_summary(self, entity_type: str, codes: list[str]) -> dict:
        values = self.export_freshness(entity_type, codes).values()
        summary = {"never_exported": 0, "changed_since_export": 0, "up_to_date": 0}
        for item in values:
            status = item.get("status")
            if status in summary:
                summary[status] += 1
        return summary

    def _freshness_for_records(self, entity_type: str, records: list[dict]) -> dict:
        codes = [
            str((item.get("basic_code") if entity_type == "basic" else item.get("udi_code")) or "").strip()
            for item in records
            if str((item.get("basic_code") if entity_type == "basic" else item.get("udi_code")) or "").strip()
        ]
        if not codes:
            return {}
        last_export_by_code = self._last_export_by_code(entity_type, set(codes))
        result = {}
        for item in records:
            code = str((item.get("basic_code") if entity_type == "basic" else item.get("udi_code")) or "").strip()
            if not code:
                continue
            last_exported_at = last_export_by_code.get(code, "")
            last_changed_at = item.get("last_changed_at", "")
            if not last_exported_at:
                status = "never_exported"
            elif last_changed_at and last_changed_at > last_exported_at:
                status = "changed_since_export"
            else:
                status = "up_to_date"
            result[code] = {
                "status": status,
                "last_exported_at": last_exported_at,
                "last_changed_at": last_changed_at,
            }
        return result

    def _last_export_by_code(self, entity_type: str, requested_codes: set[str]) -> dict:
        last_export_by_code = {code: "" for code in requested_codes}
        udi_to_basic = {}
        with self.connect() as conn:
            if entity_type == "basic" and requested_codes:
                placeholders = ",".join("?" for _ in requested_codes)
                udi_rows = conn.execute(
                    f"SELECT udi_code, basic_code FROM udi_records WHERE basic_code IN ({placeholders})",
                    list(requested_codes),
                ).fetchall()
                udi_to_basic = {row["udi_code"]: row["basic_code"] for row in udi_rows}
            rows = conn.execute(
                "SELECT code_list_json, created_at FROM export_jobs ORDER BY created_at"
            ).fetchall()
        for row in rows:
            for code in self._parse_code_list(row["code_list_json"]):
                if code in requested_codes:
                    last_export_by_code[code] = row["created_at"]
                if entity_type == "basic" and udi_to_basic.get(code) in requested_codes:
                    last_export_by_code[udi_to_basic[code]] = row["created_at"]
        return last_export_by_code

    def _records_by_codes(self, entity_type: str, codes: list[str]) -> dict:
        unique_codes = list(dict.fromkeys(str(code or "").strip() for code in codes if str(code or "").strip()))
        if not unique_codes:
            return {}
        placeholders = ",".join("?" for _ in unique_codes)
        with self.connect() as conn:
            if entity_type == "basic":
                rows = conn.execute(
                    f"SELECT * FROM basic_records WHERE basic_code IN ({placeholders})",
                    unique_codes,
                ).fetchall()
                return {row["basic_code"]: self._row_to_basic_dict(row) for row in rows}
            rows = conn.execute(
                f"""
                SELECT u.*, b.payload_json AS basic_payload_json
                FROM udi_records u
                LEFT JOIN basic_records b ON b.basic_code = u.basic_code
                WHERE u.udi_code IN ({placeholders})
                """,
                unique_codes,
            ).fetchall()
            return {row["udi_code"]: self._row_to_udi_dict(row) for row in rows}

    def _parse_code_list(self, raw: str) -> list[str]:
        try:
            data = json.loads(raw or "[]")
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        return [str(item or "").strip() for item in data if str(item or "").strip()]

    def get_basic(self, record_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM basic_records WHERE id = ?", (record_id,)).fetchone()
        return self._row_to_basic_dict(row) if row else None

    def get_basic_by_code(self, basic_code: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM basic_records WHERE basic_code = ?", (basic_code,)).fetchone()
        return self._row_to_basic_dict(row) if row else None

    def get_udi(self, record_id: int) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM udi_records WHERE id = ?", (record_id,)).fetchone()
        return self._row_to_udi_dict(row) if row else None

    def get_udi_by_code(self, udi_code: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT u.*, b.payload_json AS basic_payload_json
                FROM udi_records u
                LEFT JOIN basic_records b ON b.basic_code = u.basic_code
                WHERE u.udi_code = ?
                """,
                (str(udi_code or "").strip(),),
            ).fetchone()
        return self._row_to_udi_dict(row) if row else None

    def get_udis_by_ids(self, record_ids: list[int]) -> list[dict]:
        if not record_ids:
            return []
        placeholders = ",".join("?" for _ in record_ids)
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT u.*, b.payload_json AS basic_payload_json FROM udi_records u "
                f"LEFT JOIN basic_records b ON b.basic_code = u.basic_code "
                f"WHERE u.id IN ({placeholders}) ORDER BY u.id",
                record_ids,
            ).fetchall()
        return [self._row_to_udi_dict(row) for row in rows]

    def get_basics_by_ids(self, record_ids: list[int]) -> list[dict]:
        if not record_ids:
            return []
        placeholders = ",".join("?" for _ in record_ids)
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM basic_records WHERE id IN ({placeholders}) ORDER BY id",
                record_ids,
            ).fetchall()
        return [self._row_to_basic_dict(row) for row in rows]

    def update_basic(self, record_id: int, payload: dict, cmr_rows: list[dict], cert_rows: list[dict], version: str, state: str, notes: str):
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE basic_records
                SET payload_json = ?, cmr_json = ?, cert_json = ?, version = ?, state = ?, notes = ?,
                    updated_at = ?, last_changed_at = ?, last_change_type = 'updated'
                WHERE id = ?
                """,
                (
                    _json(payload),
                    _json(cmr_rows),
                    _json(cert_rows),
                    version,
                    state,
                    notes,
                    now,
                    now,
                    record_id,
                ),
            )

    def update_udi(
        self,
        record_id: int,
        payload: dict,
        market_rows: list[dict],
        warning_rows: list[dict],
        storage_rows: list[dict],
        package_rows: list[dict],
        trade_name_rows: list[dict],
        clinical_size_rows: list[dict],
        annex_xvi_rows: list[dict],
        version: str,
        state: str,
        notes: str,
    ):
        now = utc_now()
        with self.connect() as conn:
            existing = conn.execute("SELECT basic_code FROM udi_records WHERE id = ?", (record_id,)).fetchone()
            current_basic_code = existing["basic_code"] if existing else ""
            next_basic_code = str(payload.get("Parent Basic UDI-DI", "") or "").strip() or current_basic_code
            conn.execute(
                """
                UPDATE udi_records
                SET basic_code = ?, payload_json = ?, market_json = ?, warnings_json = ?, storage_json = ?, package_json = ?, trade_names_json = ?,
                    clinical_sizes_json = ?, annex_xvi_json = ?,
                    version = ?, state = ?, notes = ?, updated_at = ?, last_changed_at = ?, last_change_type = 'updated'
                WHERE id = ?
                """,
                (
                    next_basic_code,
                    _json(payload),
                    _json(market_rows),
                    _json(warning_rows),
                    _json(storage_rows),
                    _json(package_rows),
                    _json(trade_name_rows),
                    _json(clinical_size_rows),
                    _json(annex_xvi_rows),
                    version,
                    state,
                    notes,
                    now,
                    now,
                    record_id,
                ),
            )

    def create_export_job(self, service_type: str, code_list: list[str], file_path: str, validation: dict) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO export_jobs (service_type, code_list_json, file_path, validation_json, record_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    service_type,
                    json.dumps(code_list, ensure_ascii=False),
                    file_path,
                    json.dumps(validation, ensure_ascii=False),
                    len(code_list),
                    utc_now(),
                ),
            )
            return int(cursor.lastrowid)

    def mark_records_xml_generated(self, service_type: str, record_ids: list[int]):
        if not record_ids:
            return
        now = utc_now()
        placeholders = ",".join("?" for _ in record_ids)
        with self.connect() as conn:
            if service_type == "Basic_UDI.PATCH":
                conn.execute(
                    f"UPDATE basic_records SET state = 'xml_generated', updated_at = ? WHERE id IN ({placeholders})",
                    [now, *record_ids],
                )
                return
            conn.execute(
                f"UPDATE udi_records SET state = 'xml_generated', updated_at = ? WHERE id IN ({placeholders})",
                [now, *record_ids],
            )
            if service_type == "DEVICE.POST":
                basic_codes = [
                    row["basic_code"]
                    for row in conn.execute(
                        f"SELECT DISTINCT basic_code FROM udi_records WHERE id IN ({placeholders})", record_ids
                    ).fetchall()
                ]
                if basic_codes:
                    basic_placeholders = ",".join("?" for _ in basic_codes)
                    conn.execute(
                        f"UPDATE basic_records SET state = 'xml_generated', updated_at = ? WHERE basic_code IN ({basic_placeholders})",
                        [now, *basic_codes],
                    )

    def get_import_changes(self, import_id: int, limit: int = 500) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM import_changes WHERE import_id = ? ORDER BY id LIMIT ?",
                (import_id, limit),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "import_id": row["import_id"],
                "entity_type": row["entity_type"],
                "code": row["code"],
                "related_code": row["related_code"],
                "record_id": row["record_id"],
                "row_number": row["row_number"],
                "action": row["action"],
                "changed_fields": _json_list(row["changed_fields_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_record_import_changes(self, entity_type: str, code: str, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT c.*, i.filename, i.imported_at
                FROM import_changes c
                LEFT JOIN imports i ON i.id = c.import_id
                WHERE c.entity_type = ? AND c.code = ?
                ORDER BY c.id DESC
                LIMIT ?
                """,
                (entity_type, code, limit),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "import_id": row["import_id"],
                "filename": row["filename"] or "",
                "imported_at": row["imported_at"] or row["created_at"],
                "entity_type": row["entity_type"],
                "code": row["code"],
                "related_code": row["related_code"],
                "record_id": row["record_id"],
                "row_number": row["row_number"],
                "action": row["action"],
                "changed_fields": _json_list(row["changed_fields_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def _row_to_basic_dict(self, row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        payload = json.loads(row["payload_json"])
        return {
            "id": row["id"],
            "basic_code": row["basic_code"],
            "row_number": row["row_number"],
            "payload": payload,
            "cmr_rows": json.loads(row["cmr_json"]),
            "cert_rows": json.loads(row["cert_json"]) if "cert_json" in row.keys() else [],
            "version": row["version"],
            "state": row["state"],
            "notes": row["notes"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "first_imported_at": row["first_imported_at"] if "first_imported_at" in row.keys() else row["created_at"],
            "last_imported_at": row["last_imported_at"] if "last_imported_at" in row.keys() else row["updated_at"],
            "last_changed_at": row["last_changed_at"] if "last_changed_at" in row.keys() else row["updated_at"],
            "last_change_type": row["last_change_type"] if "last_change_type" in row.keys() else "existing",
            "is_sample": bool(row["is_sample"]) if "is_sample" in row.keys() else False,
        }

    def _row_to_udi_dict(self, row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        payload = json.loads(row["payload_json"])
        basic_payload = json.loads(row["basic_payload_json"]) if "basic_payload_json" in row.keys() and row["basic_payload_json"] else None
        return {
            "id": row["id"],
            "udi_code": row["udi_code"],
            "basic_code": row["basic_code"],
            "row_number": row["row_number"],
            "payload": payload,
            "basic_payload": basic_payload,
            "market_rows": json.loads(row["market_json"]),
            "warning_rows": json.loads(row["warnings_json"]),
            "storage_rows": json.loads(row["storage_json"]),
            "package_rows": json.loads(row["package_json"]),
            "trade_name_rows": json.loads(row["trade_names_json"]) if "trade_names_json" in row.keys() else [],
            "clinical_size_rows": json.loads(row["clinical_sizes_json"]) if "clinical_sizes_json" in row.keys() else [],
            "annex_xvi_rows": json.loads(row["annex_xvi_json"]) if "annex_xvi_json" in row.keys() else [],
            "version": row["version"],
            "state": row["state"],
            "notes": row["notes"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "first_imported_at": row["first_imported_at"] if "first_imported_at" in row.keys() else row["created_at"],
            "last_imported_at": row["last_imported_at"] if "last_imported_at" in row.keys() else row["updated_at"],
            "last_changed_at": row["last_changed_at"] if "last_changed_at" in row.keys() else row["updated_at"],
            "last_change_type": row["last_change_type"] if "last_change_type" in row.keys() else "existing",
            "is_sample": bool(row["is_sample"]) if "is_sample" in row.keys() else False,
        }
