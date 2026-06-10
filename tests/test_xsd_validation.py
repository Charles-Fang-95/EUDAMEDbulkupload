"""全量官方 XSD validation 回归测试。

对每个 (service × profile) 组合 + 每个字段变体造一份结构完整的合法数据，
导出 XML 并校验通过打包的官方生产 XSD（service/Message.xsd 的全局 Push 元素）。

注意：这只校验【结构层 XSD 合法性】，不等于 EUDAMED 的业务规则（条件必填、actor
注册状态、证书匹配等只有 Playground 实测才知道）。它的作用是保证任何改动 exporter /
模板的代码不会把任意法规/service 的 XML 结构搞坏。

运行：
    python3 -m unittest tests.test_xsd_validation
lxml 未安装时整模块自动跳过（lxml 仅测试需要，工具本身不打包它）。

PR（System / Procedure Pack）走官方 PRUDIDIDataType，只能输出基础 UDI-DI
字段；numberOfReuses / marketInfos / deviceMarking / latex / reprocessed 等
device-only 字段不得输出。
"""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from local_beta import constants
from local_beta.storage import Repository
import local_beta.exporter as exporter_module
from local_beta.exporter import BetaXMLExporter

try:
    import lxml.etree as ET

    HAS_LXML = True
except Exception:  # pragma: no cover
    HAS_LXML = False

MESSAGE_XSD = (
    constants.OFFICIAL_DOCS_DIR / "unpacked" / "xsd_production" / "service" / "Message.xsd"
)

_SCHEMA = None


def _schema():
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = ET.XMLSchema(ET.parse(str(MESSAGE_XSD)))
    return _SCHEMA


# profile -> 造数据所需的法规 / 设备类型 / 风险等级 / (legacy) 证书类型
PROFILES = {
    "MDR": dict(legislation="MDR", device_type="Regular Device", risk="Class IIa"),
    "IVDR": dict(legislation="IVDR", device_type="Regular Device", risk="Class B"),
    "MDD": dict(legislation="MDD", device_type="Regular Device", risk="Class IIa", cert="MDD_III"),
    "AIMDD": dict(legislation="AIMDD", device_type="Regular Device", risk="AIMDD", cert="AIMDD_III"),
    "IVDD": dict(legislation="IVDD", device_type="Regular Device", risk="IVD General", cert="IVDD_VII_5"),
    "PR": dict(legislation="MDR", device_type="System", risk="Class III"),
}
# 目前结构正确、应全程 XSD 通过的 profile。
WORKING_PROFILES = ["MDR", "IVDR", "MDD", "AIMDD", "IVDD"]


def _basic_payload(code: str, cfg: dict) -> dict:
    return {
        "Basic UDI-DI Code": code,
        "Issuing Entity": "GS1",
        "Manufacturer SRN": "DE-MF-000000001",  # EU 制造商，免 AR 必填
        "Risk Class": cfg["risk"],
        "Applicable Legislation": cfg["legislation"],
        "Device Type": cfg["device_type"],
        "Device Name/Model": "Test Device",
        "EMDN Code": "W0101",
        "Active Device": "TRUE",
        "Measuring Function": "FALSE",
        "Administer Medicine": "FALSE",
        "Implantable": "FALSE",
        "Reusable Surgical Instrument": "FALSE",
        "Presence of Human Tissues": "FALSE",
        "Presence of Animal Tissues": "FALSE",
        "Companion Diagnostic (IVDR)": "FALSE",
        "Near Patient Testing (IVDR)": "FALSE",
        "Self-Testing (IVDR)": "FALSE",
        "Professional Testing (IVDR)": "FALSE",
        "Instrument (IVDR)": "FALSE",
        "Microbial Origin (IVDR)": "FALSE",
        "Reagent": "FALSE",
        "Is it a Kit": "FALSE",
    }


def _udi_payload(code: str, basic_code: str) -> dict:
    return {
        "UDI-DI Code": code,
        "UDI-DI Issuing Entity": "GS1",
        "Parent Basic UDI-DI": basic_code,
        "Device Status": "On the EU market",
        "Reference Number": "REF-" + code,
        "Quantity of Device": "1",
        "Single Use Device": "FALSE",
        "Device Labelled as Sterile": "FALSE",
        "Needs Sterilisation Before Use": "FALSE",
        "Trade Name Applicable": "FALSE",
        "Containing Latex": "FALSE",
        "Reprocessed Single Use Device": "FALSE",
        "New Device (IVDR)": "FALSE",
    }


@unittest.skipUnless(HAS_LXML, "lxml not installed (test-only dependency)")
class XSDValidationBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        exporter_module.EXPORT_DIR = self.tmp / "exports"
        exporter_module.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.repo = Repository(db_path=self.tmp / "test.db")
        self.exporter = BetaXMLExporter(self.repo)
        self._n = 0

    def _uid(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}{self._n:04d}"

    def _seed(self, profile, version="", market_rows=None, package_rows=None,
              clinical_size_rows=None, annex_xvi_rows=None, cert_rows=None, udi_over=None,
              warning_rows=None, storage_rows=None, trade_name_rows=None):
        cfg = PROFILES[profile]
        bcode, ucode = self._uid("B"), self._uid("U")
        certs = cert_rows
        if certs is None and "cert" in cfg:
            certs = [{"Certificate Type": cfg["cert"], "Notified Body ID": "1234",
                      "Certificate Number": "C-1", "Expiry Date": "2030-01-01"}]
        self.repo.upsert_basic(import_id=1, row_number=4, payload=_basic_payload(bcode, cfg),
                               cmr_rows=[], cert_rows=certs or [], version=version)
        udi = _udi_payload(ucode, bcode)
        if udi_over:
            udi.update(udi_over)
        if market_rows is None:
            market_rows = [{"Country Code": "IT", "Originally Placed on Market": "TRUE"}]
        # 自动把 UDI-DI Code 填进所有关联明细行，调用方不用关心实际 code
        def _link(rows):
            return [dict(r, **{"UDI-DI Code": ucode}) for r in (rows or [])]
        self.repo.upsert_udi(import_id=1, row_number=4, payload=udi,
                             market_rows=_link(market_rows), warning_rows=_link(warning_rows),
                             storage_rows=_link(storage_rows),
                             package_rows=_link(package_rows), trade_name_rows=_link(trade_name_rows),
                             clinical_size_rows=_link(clinical_size_rows),
                             annex_xvi_rows=_link(annex_xvi_rows), version=version)
        bid = next(b["id"] for b in self.repo.list_basics(limit=999) if b["basic_code"] == bcode)
        uid = next(u["id"] for u in self.repo.list_udis(limit=999) if u["udi_code"] == ucode)
        return bid, uid

    def _xmls(self, service, record_ids):
        result = self.exporter.export(service, record_ids)
        self.assertFalse(result.get("errors"),
                         msg=f"{service} 导出预检报错（fixture 不合法）：{result.get('errors')}")
        fp = result["file_path"]
        if str(fp).endswith(".zip"):
            zf = zipfile.ZipFile(fp)
            return [zf.read(n) for n in zf.namelist() if n.endswith(".xml")]
        return [Path(fp).read_bytes()]

    def _assert_valid(self, service, record_ids, label):
        schema = _schema()
        for xml in self._xmls(service, record_ids):
            doc = ET.fromstring(xml)
            if not schema.validate(doc):
                errs = "\n".join(e.message for e in schema.error_log)
                self.fail(f"[{label}] {service} 未通过官方 XSD：\n{errs}")


class ServiceProfileMatrix(XSDValidationBase):
    """6 service × 5 个结构正确的 profile，全程 XSD 校验。"""

    def test_device_post(self):
        for p in WORKING_PROFILES:
            with self.subTest(profile=p):
                _, uid = self._seed(p)
                self._assert_valid("DEVICE.POST", [uid], f"DEVICE.POST/{p}")

    def test_udi_post(self):
        for p in WORKING_PROFILES:
            with self.subTest(profile=p):
                _, uid = self._seed(p)
                self._assert_valid("UDI_DI.POST", [uid], f"UDI_DI.POST/{p}")

    def test_basic_patch(self):
        for p in WORKING_PROFILES:
            with self.subTest(profile=p):
                bid, _ = self._seed(p, version="1")
                self._assert_valid("Basic_UDI.PATCH", [bid], f"Basic_UDI.PATCH/{p}")

    def test_udi_patch(self):
        for p in WORKING_PROFILES:
            with self.subTest(profile=p):
                _, uid = self._seed(p, version="1")
                self._assert_valid("UDI_DI.PATCH", [uid], f"UDI_DI.PATCH/{p}")

    def test_market_info_patch(self):
        for p in WORKING_PROFILES:
            with self.subTest(profile=p):
                _, uid = self._seed(p)
                self._assert_valid("MARKET_INFO.PATCH", [uid], f"MARKET_INFO.PATCH/{p}")

    def test_package_udi_patch(self):
        pkg = [{"Package UDI-DI Code": "16942495390017", "Package Issuing Entity": "GS1", "Quantity per Package": "10"}]
        for p in WORKING_PROFILES:
            with self.subTest(profile=p):
                _, uid = self._seed(p, package_rows=pkg)
                self._assert_valid("PACKAGE_UDI.PATCH", [uid], f"PACKAGE_UDI.PATCH/{p}")


class FieldVariants(XSDValidationBase):
    """字段变体（结构层）——主要在 MDR 上。"""

    def test_clinical_sizes_three_variants(self):
        clinical = [
            {"Clinical Size Type": "CST1 - Acidity", "Precision": "Range", "Minimum": "1.0", "Maximum": "5.0", "Measure Unit": "MU01 - %"},
            {"Clinical Size Type": "CST999 - OTHER", "Clinical Size Type Description": "custom", "Precision": "Value", "Value": "3.5", "Measure Unit": "MU999 - OTHER", "Measure Unit Description": "cu"},
            {"Clinical Size Type": "CST1 - Acidity", "Precision": "Text", "Text Value": "large"},
        ]
        _, uid = self._seed("MDR", clinical_size_rows=clinical)
        self._assert_valid("DEVICE.POST", [uid], "ClinicalSizes(Range/Value/Text)")

    def test_annex_xvi_multi(self):
        annex = [
            {"Non-Medical Device Type": "CONTACT_LENSES - Contact Lenses"},
            {"Non-Medical Device Type": "EMR - High intensity electromagnetic radiation"},
        ]
        _, uid = self._seed("MDR", annex_xvi_rows=annex)
        self._assert_valid("DEVICE.POST", [uid], "AnnexXVI(multi)")

    def test_device_certificates(self):
        certs = [{"Certificate Type": "MDR_TYPE_EXAMINATION", "Notified Body ID": "1234", "Certificate Number": "C-9", "Expiry Date": "2030-01-01"}]
        _, uid = self._seed("MDR", cert_rows=certs)
        self._assert_valid("DEVICE.POST", [uid], "DeviceCertificates")

    def test_market_multi_country(self):
        market = [
            {"Country Code": "IT", "Originally Placed on Market": "TRUE"},
            {"Country Code": "DE", "Originally Placed on Market": "FALSE"},
            {"Country Code": "FR", "Originally Placed on Market": "FALSE"},
        ]
        _, uid = self._seed("MDR", market_rows=market)
        self._assert_valid("DEVICE.POST", [uid], "Market(multi-country)")
        self._assert_valid("MARKET_INFO.PATCH", [uid], "MARKET_INFO.PATCH(multi-country)")

    def test_number_of_reuses_variants(self):
        for single, maxr in [("TRUE", ""), ("FALSE", ""), ("FALSE", "5")]:
            with self.subTest(single=single, maxr=maxr):
                _, uid = self._seed("MDR", udi_over={"Single Use Device": single, "Max Number of Reuses": maxr})
                self._assert_valid("DEVICE.POST", [uid], f"reuses(single={single},max={maxr})")

    def test_device_marking_and_base_quantity_order_for_regulation_devices(self):
        clinical = [
            {"Clinical Size Type": "CST1 - Acidity", "Precision": "Value", "Value": "3.5", "Measure Unit": "MU01 - %"},
        ]
        annex = [{"Non-Medical Device Type": "CONTACT_LENSES - Contact Lenses"}]
        market = [
            {"Country Code": "IT", "Originally Placed on Market": "TRUE"},
            {"Country Code": "DE", "Originally Placed on Market": "FALSE"},
        ]
        common = {
            "Quantity of Device": "5",
            "Direct Marking": "TRUE",
            "DM DI Same as UDI-DI": "TRUE",
            "Trade Name Applicable": "TRUE",
            "Trade Name": "Direct marked test device",
            "Trade Name Language": "en",
        }
        for profile in ["MDR", "IVDR"]:
            with self.subTest(profile=profile):
                _, uid = self._seed(
                    profile,
                    market_rows=market,
                    clinical_size_rows=clinical if profile == "MDR" else None,
                    annex_xvi_rows=annex if profile == "MDR" else None,
                    udi_over=common,
                    warning_rows=[{"Warning Type": "CW001 - Biological risk"}],
                    storage_rows=[{"Storage Condition Type": "SHC001 - Keep dry"}],
                )
                self._assert_valid("DEVICE.POST", [uid], f"{profile}(deviceMarking+baseQuantity)")

    def test_legacy_profiles_tolerate_maximal_applicable_fields(self):
        package_rows = [{
            "Package UDI-DI Code": "16942495390017",
            "Package Issuing Entity": "GS1",
            "Quantity per Package": "10",
        }]
        common = {
            "Quantity of Device": "5",
            "Secondary UDI-DI Code": "26942495390014",
            "Secondary Issuing Entity": "GS1",
            "Direct Marking": "TRUE",
            "DM DI Same as UDI-DI": "FALSE",
            "DM DI Code": "36942495390011",
            "DM Issuing Entity": "GS1",
            "Unit of Use DI Code": "46942495390018",
            "Unit of Use Issuing Entity": "GS1",
            "PI Lot/Batch Number": "TRUE",
            "PI Expiration Date": "TRUE",
            "Trade Name Applicable": "TRUE",
            "Trade Name": "Legacy maximal device",
            "Trade Name Language": "en",
        }
        for profile in ["MDD", "AIMDD", "IVDD"]:
            with self.subTest(profile=profile):
                _, uid = self._seed(
                    profile,
                    package_rows=package_rows,
                    udi_over=common,
                    warning_rows=[{"Warning Type": "CW001 - Biological risk"}],
                    storage_rows=[{"Storage Condition Type": "SHC001 - Keep dry"}],
                )
                self._assert_valid("DEVICE.POST", [uid], f"{profile}(maximal-applicable)")


class NegativePreflight(XSDValidationBase):
    """非法输入应被预检拦下（拦截逻辑不退化）。"""

    def test_invalid_reuses_blocks(self):
        _, uid = self._seed("MDR", udi_over={"Single Use Device": "FALSE", "Max Number of Reuses": "abc"})
        result = self.exporter.validate("DEVICE.POST", [uid])
        self.assertTrue(any("Reuses" in e for e in result["errors"]))

    def test_two_originally_placed_blocks(self):
        market = [
            {"Country Code": "IT", "Originally Placed on Market": "TRUE"},
            {"Country Code": "DE", "Originally Placed on Market": "TRUE"},
        ]
        _, uid = self._seed("MDR", market_rows=market)
        result = self.exporter.validate("DEVICE.POST", [uid])
        self.assertTrue(any("Originally Placed" in e or "TRUE" in e for e in result["errors"]))

    def test_pr_ignored_udi_fields_warn_without_blocking(self):
        _, uid = self._seed(
            "PR",
            udi_over={
                "Quantity of Device": "5",
                "Direct Marking": "TRUE",
                "DM DI Same as UDI-DI": "TRUE",
                "Single Use Device": "TRUE",
                "Containing Latex": "TRUE",
            },
        )
        result = self.exporter.validate("DEVICE.POST", [uid])
        self.assertFalse(result["errors"])
        self.assertTrue(any("PRUDIDIDataType" in warning and "不会写入 XML" in warning for warning in result["warnings"]))

    def test_invalid_notified_body_id_warns_before_xsd_rejection(self):
        certs = [{"Certificate Type": "MDR_TYPE_EXAMINATION", "Notified Body ID": "CN-NB-000000001"}]
        _, uid = self._seed("MDR", cert_rows=certs)
        result = self.exporter.validate("DEVICE.POST", [uid])
        self.assertFalse(result["errors"])
        self.assertTrue(any("NANDO ID" in warning and "4 位数字" in warning for warning in result["warnings"]))


class SystemProcedurePackProfile(XSDValidationBase):
    """System / Procedure Pack（PR）应输出官方 PRUDIDIDataType 允许的字段。"""

    def test_pr_device_post_is_valid(self):
        _, uid = self._seed("PR")
        self._assert_valid("DEVICE.POST", [uid], "DEVICE.POST/PR")

    def test_pr_udi_post_is_valid(self):
        _, uid = self._seed("PR")
        self._assert_valid("UDI_DI.POST", [uid], "UDI_DI.POST/PR")

    def test_pr_udi_patch_is_valid(self):
        _, uid = self._seed("PR", version="1")
        self._assert_valid("UDI_DI.PATCH", [uid], "UDI_DI.PATCH/PR")


if __name__ == "__main__":
    unittest.main()
