import unittest
import importlib.util
import re
from pathlib import Path

from openpyxl import Workbook

from local_beta import constants, template_schema
from local_beta import build_unified_template, views
from local_beta.exporter import BULK_UPLOAD_ENTITY_LIMIT, BetaXMLExporter
from local_beta.importer import WorkbookImporter


def _record(record_id, basic_code="BUDI-1", udi_code=None):
    return {
        "id": record_id,
        "basic_code": basic_code,
        "udi_code": udi_code or f"UDI-{record_id}",
    }


class VersionContractTests(unittest.TestCase):
    def test_template_version_constants_stay_aligned(self):
        self.assertEqual(constants.TEMPLATE_VERSION, template_schema.TEMPLATE_VERSION)
        self.assertEqual(constants.TEMPLATE_FILENAME, f"EUDAMED_Template_{constants.TEMPLATE_VERSION}.xlsx")
        self.assertEqual(constants.TEMPLATE_EN_FILENAME, f"EUDAMED_Template_{constants.TEMPLATE_VERSION}_EN.xlsx")
        self.assertEqual(constants.SCHEMA_VERSION, "3.0.30")

    def test_release_template_assets_exist(self):
        root = Path(__file__).resolve().parents[1]
        expected = [
            root / constants.TEMPLATE_FILENAME,
            root / constants.TEMPLATE_EN_FILENAME,
            root / "EUDAMED_TOOL_v2" / "templates" / constants.TEMPLATE_FILENAME,
            root / "EUDAMED_TOOL_v2" / "templates" / constants.TEMPLATE_EN_FILENAME,
        ]
        self.assertEqual([str(path) for path in expected if not path.is_file()], [])


class EnglishTemplateCopyTests(unittest.TestCase):
    def test_schema_fields_have_english_copy_without_cjk(self):
        cjk = re.compile(r"[\u3400-\u9fff]")
        missing = []
        leaked = []
        for item in template_schema.ALL_COLUMNS:
            for key in ("description_en", "format_en"):
                value = str(item.get(key) or "")
                if not value:
                    missing.append(f"{item['header']}:{key}")
                if cjk.search(value):
                    leaked.append(f"{item['header']}:{key}={value}")

        self.assertEqual(missing, [])
        self.assertEqual(leaked, [])

    def test_context_sensitive_english_copy_matches_field_semantics(self):
        by_header = {item["header"]: item for item in template_schema.MAIN_COLUMNS}
        medicinal = by_header["Basic - Presence of Medicinal Substance"]
        basic_description = by_header["Basic - Additional Description"]

        self.assertIn("not exported separately", medicinal["description_en"])
        self.assertIn("Basic UDI-DI-level", basic_description["description_en"])

        trade_name_columns = template_schema.RELATED_SHEETS["Trade Names"]["columns"]
        trade_name_copy = {item["field"]: item["description_en"] for item in trade_name_columns}
        self.assertIn("Trade Names row", trade_name_copy["Trade Name"])
        self.assertIn("Choose ANY", trade_name_copy["Language"])

    def test_english_how_to_use_matches_chinese_scope(self):
        zh = build_unified_template._how_to_use_lines_zh()
        en = build_unified_template._how_to_use_lines_en()

        self.assertEqual(len(en), len(zh))
        english_text = "\n".join(text for text, _ in en)
        for phrase in (
            "Update container package service",
            "Clinical Sizes",
            "Greece is EL, not GR",
            "IFA",
            "WPS / Excel compatibility",
            "Presence of Medicinal Substance",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, english_text)

    def test_dropdown_validation_displays_guidance_and_blocks_invalid_values(self):
        workbook = Workbook()
        worksheet = workbook.active
        boolean_column = next(item for item in template_schema.MAIN_COLUMNS if item["validation"] == "boolean")

        build_unified_template._add_data_validations(worksheet, [boolean_column], 20, "en")

        validation = list(worksheet.data_validations.dataValidation)[0]
        self.assertTrue(validation.showInputMessage)
        self.assertTrue(validation.showErrorMessage)
        self.assertEqual(validation.errorStyle, "stop")
        self.assertEqual(validation.promptTitle, "Field guidance")

    def test_english_web_fields_show_english_guidance_and_version_label(self):
        views.set_lang("en")
        try:
            field_html = views.field_input("Presence of Medicinal Substance", "")
            self.assertIn("field-hint", field_html)
            self.assertIn("not exported separately", field_html)
            self.assertEqual(views.version_label(), f"{constants.TOOL_VERSION} · Public Beta")
        finally:
            views.set_lang("zh")


class ImportHeaderCompatibilityTests(unittest.TestCase):
    def test_old_starred_pi_headers_map_to_current_fields(self):
        importer = WorkbookImporter(repository=None)
        mapping = importer._schema_by_header(template_schema.columns_for_entry_sheet("IVDR_IVDD"))

        old_lot = "UDI - PI Lot/Batch Number*"
        old_expiration = "UDI - PI Expiration Date*"
        lot_item = mapping.get(old_lot) or mapping.get(importer._canonical_header(old_lot))
        expiration_item = mapping.get(old_expiration) or mapping.get(importer._canonical_header(old_expiration))

        self.assertEqual(lot_item["field"], "PI Lot/Batch Number")
        self.assertEqual(expiration_item["field"], "PI Expiration Date")


class ExportBatchPlanningTests(unittest.TestCase):
    def setUp(self):
        self.exporter = BetaXMLExporter(repository=None)

    def test_simple_services_split_at_official_bulk_limit(self):
        records = [_record(i) for i in range(1, BULK_UPLOAD_ENTITY_LIMIT + 2)]

        batches = self.exporter.plan_export_batches("UDI_DI.POST", records)

        self.assertEqual([batch["record_count"] for batch in batches], [300, 1])
        self.assertEqual({batch["service_type"] for batch in batches}, {"UDI_DI.POST"})

    def test_device_post_packs_multiple_basics_into_one_file_when_possible(self):
        records = [_record(i, basic_code=f"BUDI-{i}") for i in range(1, 51)]

        batches = self.exporter.plan_export_batches("DEVICE.POST", records)

        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0]["service_type"], "DEVICE.POST")
        self.assertEqual(batches[0]["record_count"], 50)
        self.assertEqual(len(batches[0]["basic_codes"]), 50)

    def test_device_post_creates_basic_once_and_posts_remaining_udis_later(self):
        records = [_record(i, basic_code="BUDI-SAME") for i in range(1, 4)]

        batches = self.exporter.plan_export_batches("DEVICE.POST", records)

        self.assertEqual([batch["service_type"] for batch in batches], ["DEVICE.POST", "UDI_DI.POST"])
        self.assertEqual([batch["record_count"] for batch in batches], [1, 2])
        self.assertEqual(batches[1]["depends_on"], batches[0]["sequence"])


class NumberOfReusesTests(unittest.TestCase):
    def setUp(self):
        self.exporter = BetaXMLExporter(repository=None)

    def test_single_use_always_outputs_zero(self):
        value = self.exporter._number_of_reuses({
            "Single Use Device": "TRUE",
            "Max Number of Reuses": "12",
        })

        self.assertEqual(value, "0")

    def test_reusable_without_declared_limit_outputs_minus_one(self):
        value = self.exporter._number_of_reuses({
            "Single Use Device": "FALSE",
            "Max Number of Reuses": "",
        })

        self.assertEqual(value, "-1")

    def test_reusable_not_applicable_aliases_normalize_to_minus_one(self):
        for raw in ["-", "N/A", "不适用", "not defined"]:
            with self.subTest(raw=raw):
                self.assertEqual(self.exporter._normalised_number_of_reuses(raw), "-1")


class LegacyValidatorApplicabilityTests(unittest.TestCase):
    def test_ivdd_does_not_require_pi_lot_or_expiration(self):
        validator_path = Path(__file__).resolve().parents[1] / "EUDAMED_TOOL_v2" / "validator.py"
        spec = importlib.util.spec_from_file_location("legacy_validator", validator_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        data = {
            "Basic UDI-DI": [{
                "Basic UDI-DI Code": "BIVDD0001",
                "Issuing Entity": "EUDAMED",
                "Manufacturer SRN": "DE-MF-000000001",
                "Risk Class": "IVD General",
                "Applicable Legislation": "IVDD",
                "Device Type": "Regular Device",
                "Device Name/Model": "Legacy IVDD Device",
                "EMDN Code": "W0101",
            }],
            "UDI-DI": [{
                "Parent Basic UDI-DI": "BIVDD0001",
                "UDI-DI Code": "UIVDD0001",
                "UDI-DI Issuing Entity": "EUDAMED",
                "Device Status": "On the EU market",
                "Single Use Device": "FALSE",
                "Device Labelled as Sterile": "FALSE",
                "Trade Name Applicable": "FALSE",
                "Nomenclature Code": "W0101",
            }],
        }

        errors, _ = module.DataValidator(data).validate_all()
        pi_errors = [
            error for error in errors
            if error.field in {"PI Lot/Batch Number", "PI Expiration Date"}
        ]
        self.assertEqual(pi_errors, [])


if __name__ == "__main__":
    unittest.main()
