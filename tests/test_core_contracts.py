import unittest

from local_beta import constants, template_schema
from local_beta.exporter import BULK_UPLOAD_ENTITY_LIMIT, BetaXMLExporter


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
        self.assertEqual(constants.SCHEMA_VERSION, "3.0.30")


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


if __name__ == "__main__":
    unittest.main()
