import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from local_beta import views
from local_beta.app import App
from local_beta.storage import Repository


class LibraryPaginationTests(unittest.TestCase):
    def setUp(self):
        self.tmp_context = tempfile.TemporaryDirectory()
        self.repo = Repository(db_path=Path(self.tmp_context.name) / "library.db")
        views.set_lang("zh")

    def tearDown(self):
        self.tmp_context.cleanup()

    def _new_import(self, name: str) -> int:
        return self.repo.create_import(name, {}, {"errors": [], "warnings": []})

    def _seed_udis(self, import_id: int, prefix: str, count: int, basic_code: str) -> None:
        self.repo.upsert_basic(
            import_id=import_id,
            row_number=4,
            payload={
                "Basic UDI-DI Code": basic_code,
                "Applicable Legislation": "MDR",
                "Manufacturer SRN": "DE-MF-000000001",
                "Device Name/Model": f"Batch {prefix}",
            },
            cmr_rows=[],
        )
        for index in range(count):
            self.repo.upsert_udi(
                import_id=import_id,
                row_number=index + 4,
                payload={
                    "UDI-DI Code": f"{prefix}-{index:04d}",
                    "Parent Basic UDI-DI": basic_code,
                    "Reference Number": f"REF-{prefix}-{index:04d}",
                },
                market_rows=[],
                warning_rows=[],
                storage_rows=[],
                package_rows=[],
            )

    def test_default_page_is_200_but_total_and_filtered_ids_include_all_250(self):
        import_id = self._new_import("250.xlsx")
        self._seed_udis(import_id, "BULK", 250, "BASIC-250")

        self.assertEqual(len(self.repo.list_udis()), 200)
        self.assertEqual(len(self.repo.get_filtered_ids("udi")), 250)
        self.assertEqual(len(self.repo.list_udis(limit=50, offset=200)), 50)

    def test_import_batch_filter_returns_only_batch_b_and_paginates(self):
        import_a = self._new_import("A.xlsx")
        self._seed_udis(import_a, "A", 100, "BASIC-A")
        import_b = self._new_import("B.xlsx")
        self._seed_udis(import_b, "B", 179, "BASIC-B")

        batch_b = self.repo.list_udis(import_id=import_b, limit=None)
        self.assertEqual(len(batch_b), 179)
        self.assertTrue(all(item["import_id"] == import_b for item in batch_b))
        self.assertEqual(len(self.repo.get_filtered_ids("udi", import_id=import_b)), 179)
        self.assertEqual(len(self.repo.list_udis(import_id=import_b, limit=100, offset=100)), 79)
        self.assertEqual(
            [item["basic_code"] for item in self.repo.list_basics(import_id=import_b, limit=None)],
            ["BASIC-B"],
        )
        self.assertEqual(len(self.repo.get_filtered_ids("basic", import_id=import_b)), 1)

        html = views.library_page(
            batch_b[:100],
            {"import_id": str(import_b)},
            total_filtered=179,
            page_number=1,
            page_size=100,
        )
        self.assertIn(f'仅显示导入批次 #{import_b}', html)
        self.assertIn('当前显示 <strong>1-100</strong>', html)
        self.assertIn('总匹配数量 <strong>179</strong>', html)
        self.assertIn('下一页', html)
        self.assertIn(f'name="import_id" value="{import_b}"', html)

    def test_filtered_export_uses_all_179_batch_records_not_visible_page(self):
        import_id = self._new_import("B.xlsx")
        self._seed_udis(import_id, "EXPORT", 179, "BASIC-EXPORT")

        class CapturingExporter:
            def __init__(self):
                self.record_ids = []

            def export(self, service_type, record_ids):
                self.record_ids = list(record_ids)
                return {"service_type": service_type, "errors": [], "warnings": []}

        app = App.__new__(App)
        app.repository = self.repo
        app.exporter = CapturingExporter()
        app.read_form = lambda request: {
            "service_type": ["UDI_DI.POST"],
            "selection_mode": ["filtered"],
            "import_id": [str(import_id)],
            "page": ["1"],
            "page_size": ["50"],
            "action": ["export"],
        }
        app.respond_html = lambda request, content, status=200: content

        with patch("local_beta.app.build_xsd_version_report", return_value={
            "tool_version": "3.0.30",
            "local_xsd_version": "3.0.30",
            "status": "ok",
        }):
            html = app.handle_export(object())

        self.assertEqual(len(app.exporter.record_ids), 179)
        self.assertEqual(len(set(app.exporter.record_ids)), 179)
        self.assertIn('选择记录: <strong>179</strong>', html)
        self.assertIn('导出全部筛选结果（179）', html)
        self.assertEqual(html.count('name="record_ids"'), 50)

    def test_reimport_updates_same_code_and_keeps_distinct_historical_records(self):
        import_a = self._new_import("A.xlsx")
        self._seed_udis(import_a, "OLD", 1, "BASIC-SHARED")
        self._seed_udis(import_a, "SAME", 1, "BASIC-SHARED")
        import_b = self._new_import("B.xlsx")
        self.repo.upsert_udi(
            import_id=import_b,
            row_number=4,
            payload={
                "UDI-DI Code": "SAME-0000",
                "Parent Basic UDI-DI": "BASIC-SHARED",
                "Reference Number": "UPDATED",
            },
            market_rows=[],
            warning_rows=[],
            storage_rows=[],
            package_rows=[],
        )
        self._seed_udis(import_b, "NEW", 1, "BASIC-SHARED")

        records = {item["udi_code"]: item for item in self.repo.list_udis(limit=None)}
        self.assertEqual(set(records), {"OLD-0000", "SAME-0000", "NEW-0000"})
        self.assertEqual(records["SAME-0000"]["payload"]["Reference Number"], "UPDATED")
        self.assertEqual(records["SAME-0000"]["import_id"], import_b)
        self.assertEqual(
            {item["udi_code"] for item in self.repo.list_udis(import_id=import_b, limit=None)},
            {"SAME-0000", "NEW-0000"},
        )

    def test_import_result_explains_cumulative_library_and_links_to_batch(self):
        html = views.import_page(result={
            "import_id": 123,
            "summary": {"basic_count": 1, "udi_count": 179},
            "validation": {"errors": [], "warnings": []},
            "change_summary": {"created": 179, "updated": 1, "unchanged": 2},
            "changes": [],
        })

        self.assertIn('href="/library?import_id=123"', html)
        self.assertIn('href="/export?import_id=123&amp;selection_mode=filtered"', html)
        self.assertIn('本地产品库会保留历史记录', html)
        self.assertIn('已更新”不代表清空或覆盖整个产品库', html)


if __name__ == "__main__":
    unittest.main()
