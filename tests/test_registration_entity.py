"""Registration entity regressions. All records and actors are fictional."""
import csv
import io
import zipfile
from copy import deepcopy

from local_beta import template_migrator, views
from local_beta.constants import ROOT_DIR
from local_beta.exporter import NS
from local_beta.importer import WorkbookImporter
from openpyxl import Workbook, load_workbook
from test_xsd_validation import ET, XSDValidationBase, _schema

ENTITY = "Registration Entity Type"
PACK = "Procedure Pack"


def write_pack_workbook(path, entities=(None,), *, pr=False, full_template=False):
    """Use the headers of the shipped workbook, including historical starred headers."""
    version = "2.14" if all(e is None for e in entities) else "2.15"
    template = ROOT_DIR / f"EUDAMED_Template_v{version}.xlsx"
    if full_template:
        workbook = load_workbook(template)
    else:
        source = load_workbook(template, read_only=True)
        workbook = Workbook()
        workbook.remove(workbook.active)
        for sheet in ("MDR", "Market Info", "How to Use"):
            workbook.create_sheet(sheet).append(next(source[sheet].values))
        source.close()
    sheet = workbook["MDR"]
    headers = {cell.value.rstrip("*"): cell.column for cell in sheet[1] if cell.value}
    basic_code = "FICT-PR-BASIC" if pr else "FICT-DEVICE-BASIC"
    for number, entity in enumerate(entities, 4):
        code = f"{basic_code}-UDI-{number}"
        values = {
            "Basic - Basic UDI-DI Code": basic_code, "Basic - Issuing Entity": "GS1",
            "Basic - Manufacturer SRN": "DE-PR-000000091" if pr else "DE-MF-000000091",
            "Basic - Applicable Legislation": "MDR", "Basic - Device Type": PACK,
            "Basic - Registration Entity Type": entity, "Basic - Device Name": "Fictional review device",
            "Basic - Risk Class": "Class I", "Basic - EMDN Code": "W0101",
            "Basic - Current Version": "1", "UDI - Current Version": "1",
            "UDI - UDI-DI Code": code, "UDI - UDI-DI Issuing Entity": "GS1",
            "UDI - Reference Number": f"FICTION-{number}", "UDI - Device Status": "On the EU market",
            "UDI - Device Labelled as Sterile": True, "UDI - Needs Sterilisation Before Use": False,
            "UDI - Trade Name Applicable": False, "UDI - Nomenclature Code": "W0101",
            "UDI - Additional Description": "Fictional pack for software testing", "UDI - Description Language": "en",
        }
        if pr:
            values.update({"Basic - Additional Description": "Fictional producer medical purpose",
                           "Basic - PR Medical Purpose Language": "de"})
        else:
            values.update({"UDI - Quantity of Device": "3", "UDI - Single Use Device": True,
                           "UDI - Containing Latex": False, "UDI - Reprocessed Single Use Device": False})
            market = workbook["Market Info"]
            for cell in market[1]:
                key = str(cell.value).rstrip("*")
                field = {"UDI-DI Code": code, "Country Code": "DE", "Originally Placed on Market": True}.get(key)
                if field is not None:
                    market.cell(number, cell.column, field)
        for key, value in values.items():
            if value is not None:
                sheet.cell(number, headers[key], value)
    workbook.save(path)
    workbook.close()


class RegistrationEntityTests(XSDValidationBase):
    def test_mdr_attributes_preserve_full_device_values(self):
        for kind, xml_kind in (("Regular Device", "DEVICE"), ("System", "SYSTEM"), (PACK, "PROCEDURE_PACK")):
            with self.subTest(kind=kind):
                bid, uid = self._seed("MDR", version="1", basic_over={ENTITY: "Device", "Device Type": kind},
                                      udi_over={"Single Use Device": True, "Quantity of Device": "3",
                                                "Containing Latex": False, "Reprocessed Single Use Device": True,
                                                "Additional Description": "Fictional device", "Description Language": "de"})
                for service in ("DEVICE.POST", "Basic_UDI.PATCH", "UDI_DI.POST", "UDI_DI.PATCH"):
                    xml, = self._xmls(service, [bid if service == "Basic_UDI.PATCH" else uid])
                    doc = ET.fromstring(xml)
                    _schema().assertValid(doc)
                    if service in {"DEVICE.POST", "Basic_UDI.PATCH"}:
                        self.assertEqual(doc.xpath("//basicudi:type/text()", namespaces=NS), [xml_kind])
                    if service != "Basic_UDI.PATCH":
                        for element, expected in (("numberOfReuses", "0"), ("baseQuantity", "3"),
                                                  ("latex", "false"), ("reprocessed", "true")):
                            self.assertEqual(doc.xpath(f"//udidi:{element}/text()", namespaces=NS), [expected])
                        self.assertEqual(doc.xpath("//udidi:marketInfos//marketinfo:country/text()", namespaces=NS), ["IT"])
                        self.assertEqual(doc.xpath("//udidi:additionalDescription//lsn:language/text()", namespaces=NS), ["DE"])

    def test_old_xsd_valid_pr_projection_omitted_device_declarations(self):
        _, uid = self._seed("MDR", basic_over={ENTITY: "Device", "Device Type": PACK},
                            udi_over={"Single Use Device": True, "Containing Latex": False,
                                      "Additional Description": "Fictional MDR pack", "Description Language": "en"})
        xml, = self._xmls("UDI_DI.POST", [uid])
        actual = ET.fromstring(xml)
        _schema().assertValid(actual)
        old = deepcopy(actual)
        node = old.find(".//device:UDIDIData", NS)
        node.set(f"{{{NS['xsi']}}}type", "udidi:PRUDIDIDataType")
        for tag, expected in (("numberOfReuses", "0"), ("baseQuantity", "1"),
                              ("latex", "false"), ("reprocessed", "false")):
            child = node.find(f"udidi:{tag}", NS)
            self.assertEqual(child.text, expected)
            node.remove(child)
        market = node.find("udidi:marketInfos", NS)
        self.assertEqual(market.findtext(".//marketinfo:country", namespaces=NS), "IT")
        node.remove(market)
        _schema().assertValid(old)  # The historical omission escaped structural validation.

    def test_legacy_pack_registered_as_device_uses_legacy_identifiers(self):
        for legislation in ("MDD", "AIMDD"):
            _, uid = self._seed(legislation, basic_over={ENTITY: "Device", "Device Type": PACK},
                                udi_over={"Additional Description": "Fictional device", "Description Language": "en"})
            xml, = self._xmls("DEVICE.POST", [uid])
            doc = ET.fromstring(xml)
            _schema().assertValid(doc)
            self.assertEqual(doc.xpath("//basicudi:type/text()", namespaces=NS), ["PROCEDURE_PACK"])
            self.assertEqual(doc.xpath("//eudi:applicableLegislation/text()", namespaces=NS), [legislation])
            self.assertEqual(doc.xpath("//udidi:basicUDIIdentifier/commondi:DICode/text()", namespaces=NS),
                             ["B-" + self.repo.get_udi(uid)["udi_code"]])

    def test_old_ambiguous_rows_saved_and_block_every_service_until_basic_confirmed(self):
        path = self.tmp / "fiction.xlsx"
        write_pack_workbook(path, (None, None))
        result = WorkbookImporter(self.repo).import_workbook(path)
        self.assertEqual(result["summary"]["udi_count"], 2)
        errors = result["validation"]["errors"]
        self.assertEqual([(e["sheet"], e["row"], e["field"]) for e in errors], [("MDR", 4, ENTITY)])
        self.assertIn("FICT-DEVICE-BASIC", errors[0]["message"])
        basic = self.repo.get_basic_by_code("FICT-DEVICE-BASIC")
        self.assertIn("alert error", views.basic_detail(basic))
        uids = [u["id"] for u in self.repo.list_udis()]
        for service in ("DEVICE.POST", "UDI_DI.POST", "UDI_DI.PATCH", "Basic_UDI.PATCH",
                        "MARKET_INFO.PUT", "PACKAGE_UDI.PUT", "PRODUCT_DESIGNER.PUT"):
            result = self.exporter.export(service, [basic["id"]] if service == "Basic_UDI.PATCH" else uids)
            self.assertTrue(any(ENTITY in e for e in result["errors"]), service)
            self.assertNotIn("file_path", result)
        basic["payload"][ENTITY] = "Device"
        self.repo.update_basic(basic["id"], basic["payload"], [], [], "1", "draft", "")
        self._assert_valid("UDI_DI.POST", uids, "one confirmed Basic for both UDIs")

    def test_conflicting_registration_survives_import_deduplication(self):
        for entities in (("Device", "PR/SPP", "Device"), ("PR/SPP", "Device", "PR/SPP")):
            path = self.tmp / "fiction.xlsx"
            write_pack_workbook(path, entities)
            result = WorkbookImporter(self.repo).import_workbook(path)
            error = next(e for e in result["validation"]["errors"] if e["field"] == ENTITY)
            for value in ("MDR!4", "MDR!5", "Device", "PR/SPP", "FICT-DEVICE-BASIC"):
                self.assertIn(value, error["message"])
            self.assertTrue(self.exporter.export("UDI_DI.POST", [u["id"] for u in self.repo.list_udis()])["errors"])

    def test_migration_keeps_basic_and_udi_description_and_version_separate(self):
        headers = ["Basic - Additional Description", "UDI - Additional Description",
                   "Basic - Current Version", "UDI - Current Version", "Basic - Registration Entity Type"]
        self.assertEqual(template_migrator._header_map(headers, headers), {h: h for h in headers})
        self.assertEqual(template_migrator._header_map(["Additional Description"], headers), {})
        mapped = template_migrator._legacy_combined_row(
            {"Additional Description": "Fictional medical purpose"},
            {"Additional Description": "Fictional product description"})
        sheet = Workbook().active
        sheet.title = "MDR"
        sheet.append(headers)
        template_migrator._write_by_field(sheet, headers, 4, mapped)
        self.assertEqual(sheet["A4"].value, "Fictional medical purpose")
        self.assertEqual(sheet["B4"].value, "Fictional product description")

    def test_conflicting_reimport_cannot_replace_confirmed_entity_on_retry(self):
        path = self.tmp / "fiction.xlsx"
        write_pack_workbook(path, ("Device",))
        importer = WorkbookImporter(self.repo)
        self.assertEqual(importer.import_workbook(path)["validation"]["errors"], [])
        write_pack_workbook(path, ("PR/SPP",))
        for attempt in range(2):
            with self.subTest(attempt=attempt):
                result = importer.import_workbook(path)
                self.assertTrue(any("分类冲突" in e["message"] for e in result["validation"]["errors"]))
                uid = self.repo.list_udis()[0]["id"]
                self.assertNotIn("file_path", self.exporter.export("UDI_DI.POST", [uid]))

    def test_explicit_false_in_pr_device_only_field_is_not_silently_lost(self):
        _, uid = self._seed("PR", udi_over={"Containing Latex": False})
        result = self.exporter.export("UDI_DI.POST", [uid])
        self.assertTrue(any("Containing Latex" in e for e in result["errors"]))
        self.assertNotIn("file_path", result)

    def test_invalid_combinations_block_basic_and_udi(self):
        for entity, legislation, kind in (("PR/SPP", "MDR", "Regular Device"), ("PR/SPP", "IVDR", PACK),
                                           ("", "MDR", "System"), ("unknown", "MDR", "Regular Device"),
                                           ("", "", "Regular Device"), ("", "MDR", "")):
            bid, uid = self._seed("MDR", version="1", basic_over={
                ENTITY: entity, "Applicable Legislation": legislation, "Device Type": kind})
            for service, record in (("Basic_UDI.PATCH", bid), ("UDI_DI.POST", uid)):
                self.assertTrue(any(ENTITY in e for e in self.exporter.export(service, [record])["errors"]))

    def test_mixed_export_sender_order_counts_links_and_manifests(self):
        path = self.tmp / "fiction.xlsx"
        for pr, entity in ((False, "Device"), (True, "PR/SPP")):
            write_pack_workbook(path, (entity, entity), pr=pr)
            imported = WorkbookImporter(self.repo).import_workbook(path)
            self.assertEqual(imported["validation"]["errors"], [])
        selected = self.repo.list_udis()
        ids = [item["id"] for item in selected]
        blocked = self.exporter.export("DEVICE.POST", ids)
        self.assertTrue(blocked["requires_udi_post"])
        self.assertNotIn("file_path", blocked)
        result = self.exporter.export("DEVICE.POST", ids, include_udi_post=True)
        self.assertEqual(result["errors"], [])
        expected_codes = {item["udi_code"]: item["basic_code"] for item in selected}
        with zipfile.ZipFile(result["file_path"]) as archive:
            rows = list(csv.DictReader(io.StringIO(archive.read("manifest.csv").decode())))
            self.assertEqual(len(rows), 4)
            self.assertEqual(set(archive.namelist()), {r["file_name"] for r in rows} | {"manifest.csv", "manifest.html"})
            seen = []
            for row in rows:
                code = row["udi_di_codes"]
                seen.append(code)
                self.assertEqual(row["record_count"], "1")
                self.assertEqual(row["basic_udi_di"], expected_codes[code])
                doc = ET.fromstring(archive.read(row["file_name"]))
                _schema().assertValid(doc)
                self.assertEqual(doc.findtext("m:sender/m:node/s:nodeActorCode", namespaces=NS), row["sender_actor"])
                self.assertEqual(doc.xpath("//udidi:basicUDIIdentifier/*[local-name()='DICode']/text()", namespaces=NS), [expected_codes[code]])
                pr = "-PR-" in row["sender_actor"]
                self.assertEqual(doc.xpath("boolean(//udidi:numberOfReuses)", namespaces=NS), not pr)
                if row["service"] == "UDI_DI.POST":
                    parent = rows[int(row["depends_on_upload_order"]) - 1]
                    self.assertEqual((parent["service"], parent["basic_udi_di"]), ("DEVICE.POST", expected_codes[code]))
                elif pr:
                    self.assertEqual(doc.xpath("//basicudi:medicinalPurpose//lsn:textValue/text()", namespaces=NS), ["Fictional producer medical purpose"])
            self.assertCountEqual(seen, expected_codes.keys())
