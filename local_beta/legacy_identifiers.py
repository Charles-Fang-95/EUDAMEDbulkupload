"""Official Legacy Device EUDAMED DI/ID calculation and resolution.

The character/value tables and the checksum procedure are defined by the
EUDAMED Production help document "Format of the Unique Device Identifiers for
the Legacy Devices".  Keep this module independent from Excel, storage and XML
so importer, pre-check and exporter use exactly the same decision path.
"""

from dataclasses import dataclass


LEGACY_LEGISLATIONS = {"MDD", "AIMDD", "IVDD"}
METHOD_DERIVED_FROM_UDI = "derived_from_udi"
METHOD_GENERATED_FROM_INPUT = "generated_from_input"
METHOD_EXISTING_EUDAMED_PAIR = "existing_eudamed_pair"

# Official reference-character table, values 0..81 in the published order.
REFERENCE_CHARACTERS = (
    "!\"%&'()*+,-./0123456789:;<=>?"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
)
REFERENCE_VALUES = {character: value for value, character in enumerate(REFERENCE_CHARACTERS)}

# The right-most manufacturer character is multiplied by 2, then the weights
# progress leftwards through the first 21 prime numbers.
PRIME_WEIGHTS = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73)
CHECK_CHARACTERS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


class LegacyIdentifierError(ValueError):
    """A Legacy identifier path cannot be resolved without guessing."""


@dataclass(frozen=True)
class LegacyIdentifierResolution:
    has_assigned_udi: bool
    eudamed_di_input: str
    eudamed_di: str
    eudamed_id: str
    identifier_code: str
    identifier_issuing_entity: str
    method: str

    def audit_payload(self) -> dict[str, str]:
        return {
            "Legacy Has Assigned UDI-DI": "TRUE" if self.has_assigned_udi else "FALSE",
            "Legacy EUDAMED DI Input": self.eudamed_di_input,
            "Legacy EUDAMED DI": self.eudamed_di,
            "Legacy EUDAMED ID": self.eudamed_id,
            "Legacy Identifier Method": self.method,
        }


def is_legacy_legislation(value) -> bool:
    return str(value or "").strip().upper() in LEGACY_LEGISLATIONS


def _text(value) -> str:
    return str(value or "").strip()


def _exact_text(value) -> str:
    """Preserve manufacturer input exactly so illegal whitespace is rejected."""
    return "" if value is None else str(value)


def parse_required_boolean(value) -> bool:
    if isinstance(value, bool):
        return value
    text = _text(value).upper()
    if text == "TRUE":
        return True
    if text == "FALSE":
        return False
    raise LegacyIdentifierError("Legacy - Has Assigned UDI-DI? 必须选择 TRUE 或 FALSE。")


def calculate_check_characters(body: str) -> str:
    """Return the two official check characters for a 1..21 character body."""
    body = _exact_text(body)
    if not 1 <= len(body) <= 21:
        raise LegacyIdentifierError("Legacy - EUDAMED DI Input 主体长度必须为 1 到 21 个字符。")
    invalid = [character for character in body if character not in REFERENCE_VALUES]
    if invalid:
        display = "、".join(repr(character) for character in dict.fromkeys(invalid))
        raise LegacyIdentifierError(f"Legacy - EUDAMED DI Input 含官方字符表之外的字符：{display}。")
    total = sum(
        REFERENCE_VALUES[character] * PRIME_WEIGHTS[index]
        for index, character in enumerate(reversed(body))
    )
    checksum = total % 1021
    return CHECK_CHARACTERS[checksum // 32] + CHECK_CHARACTERS[checksum % 32]


def generate_eudamed_pair(body: str) -> tuple[str, str]:
    body = _exact_text(body)
    check = calculate_check_characters(body)
    suffix = f"{body}{check}"
    return f"B-{suffix}", f"D-{suffix}"


def validate_eudamed_pair(eudamed_di: str, eudamed_id: str) -> tuple[str, str, str]:
    eudamed_di = _text(eudamed_di)
    eudamed_id = _text(eudamed_id)
    if not eudamed_di or not eudamed_id:
        raise LegacyIdentifierError("没有 UDI-DI 时必须同时提供合法的 B- EUDAMED DI 和 D- EUDAMED ID。")
    if not eudamed_di.startswith("B-") or not eudamed_id.startswith("D-"):
        raise LegacyIdentifierError("EUDAMED DI 必须以 B- 开头，EUDAMED ID 必须以 D- 开头。")
    if eudamed_di[2:] != eudamed_id[2:]:
        raise LegacyIdentifierError("B- EUDAMED DI 与 D- EUDAMED ID 的主体和校验字符必须完全一致。")
    value = eudamed_di[2:]
    if len(value) < 3:
        raise LegacyIdentifierError("B-/D- 标识缺少制造商主体或两个校验字符。")
    body, supplied_check = value[:-2], value[-2:]
    expected_check = calculate_check_characters(body)
    if supplied_check != expected_check:
        raise LegacyIdentifierError(
            f"B-/D- 标识校验字符错误：应为 {expected_check}，实际为 {supplied_check}。"
        )
    return body, eudamed_di, eudamed_id


def _inferred_path(basic: dict, udi: dict) -> bool:
    udi_code = _text(udi.get("UDI-DI Code"))
    udi_entity = _text(udi.get("UDI-DI Issuing Entity")).upper()
    basic_code = _text(basic.get("Basic UDI-DI Code"))
    basic_entity = _text(basic.get("Issuing Entity")).upper()
    if udi_code and udi_entity and udi_entity != "EUDAMED":
        return True
    if basic_code.startswith("B-") and udi_code.startswith("D-") and basic_entity == udi_entity == "EUDAMED":
        return False
    raise LegacyIdentifierError(
        "旧模板无法判断 Legacy 标识路径：请迁移到 v2.12，选择是否已有 UDI-DI；"
        "如没有 UDI-DI，请填写生成主体或合法的 B-/D- 对。"
    )


def resolve_legacy_identifiers(
    basic: dict,
    udi: dict,
    *,
    allow_v211_inference: bool = True,
) -> LegacyIdentifierResolution | None:
    """Resolve a Legacy row; return None for MDR/IVDR/PR-SPP rows."""
    if not is_legacy_legislation(basic.get("Applicable Legislation")):
        return None
    if _text(basic.get("Device Type")).lower() in {"system", "procedure pack"}:
        return None

    raw_path = udi.get("Legacy Has Assigned UDI-DI")
    if raw_path in (None, ""):
        if not allow_v211_inference:
            raise LegacyIdentifierError("Legacy - Has Assigned UDI-DI? 为 Legacy Device 条件必填。")
        has_assigned_udi = _inferred_path(basic, udi)
    else:
        has_assigned_udi = parse_required_boolean(raw_path)

    body = _exact_text(udi.get("Legacy EUDAMED DI Input"))
    result_di = _text(udi.get("Legacy EUDAMED DI"))
    result_id = _text(udi.get("Legacy EUDAMED ID"))
    udi_code = _text(udi.get("UDI-DI Code"))
    udi_entity = _text(udi.get("UDI-DI Issuing Entity"))
    basic_code = _text(basic.get("Basic UDI-DI Code"))
    basic_entity = _text(basic.get("Issuing Entity"))

    if has_assigned_udi:
        if not udi_code:
            raise LegacyIdentifierError("选择已有 UDI-DI 时，UDI - UDI-DI Code 必须填写真实 UDI-DI。")
        if not udi_entity or udi_entity.upper() == "EUDAMED":
            raise LegacyIdentifierError("选择已有 UDI-DI 时，必须填写非 EUDAMED 的真实 issuing entity。")
        if body:
            raise LegacyIdentifierError("已有 UDI-DI 路径不得填写 Legacy - EUDAMED DI Input。")
        expected_di = f"B-{udi_code}"
        if result_di and result_di != expected_di:
            raise LegacyIdentifierError(f"Legacy - EUDAMED DI 应为 {expected_di}。")
        if result_id:
            raise LegacyIdentifierError("已有真实 UDI-DI 时，Legacy - EUDAMED ID 必须留空。")
        return LegacyIdentifierResolution(
            has_assigned_udi=True,
            eudamed_di_input="",
            eudamed_di=expected_di,
            eudamed_id="",
            identifier_code=udi_code,
            identifier_issuing_entity=udi_entity,
            method=METHOD_DERIVED_FROM_UDI,
        )

    # No assigned UDI-DI: v2.12 result columns take precedence; v2.11 stores
    # the same official pair in the historical Basic/UDI fields.
    if udi_code and udi_entity.upper() != "EUDAMED":
        raise LegacyIdentifierError(
            "选择没有 UDI-DI 时，不得保留非 EUDAMED 的 UDI-DI Code / issuing entity；"
            "如该代码是真实 UDI-DI，请把 Legacy 路径改为 TRUE。"
        )
    if udi_entity and udi_entity.upper() != "EUDAMED":
        raise LegacyIdentifierError("没有 UDI-DI 路径的 identifier issuing entity 必须为 EUDAMED。")
    if basic_code and (not basic_code.startswith("B-") or basic_entity.upper() != "EUDAMED"):
        raise LegacyIdentifierError(
            "没有 UDI-DI 路径不得使用普通 Basic/本地标识；请留空让工具生成，"
            "或提供 EUDAMED 签发的合法 B- 标识。"
        )
    if result_di and basic_code and result_di != basic_code:
        raise LegacyIdentifierError("Legacy - EUDAMED DI 与 Basic - Basic UDI-DI Code 不一致。")
    if result_id and udi_code and result_id != udi_code:
        raise LegacyIdentifierError("Legacy - EUDAMED ID 与 UDI - UDI-DI Code 不一致。")
    existing_di = result_di or (basic_code if basic_entity.upper() == "EUDAMED" else "")
    existing_id = result_id or (udi_code if udi_entity.upper() == "EUDAMED" else "")
    if body:
        if bool(existing_di) != bool(existing_id):
            raise LegacyIdentifierError("填写计算主体并同时提供现有标识时，必须同时提供完整的 B-/D- 对。")
        generated_di, generated_id = generate_eudamed_pair(body)
        if existing_di and existing_di != generated_di:
            raise LegacyIdentifierError(
                f"输入主体重新计算得到 {generated_di}，与现有 EUDAMED DI {existing_di} 不一致。"
            )
        if existing_id and existing_id != generated_id:
            raise LegacyIdentifierError(
                f"输入主体重新计算得到 {generated_id}，与现有 EUDAMED ID {existing_id} 不一致。"
            )
        method = METHOD_GENERATED_FROM_INPUT
        final_di, final_id = generated_di, generated_id
    else:
        body, final_di, final_id = validate_eudamed_pair(existing_di, existing_id)
        method = METHOD_EXISTING_EUDAMED_PAIR

    return LegacyIdentifierResolution(
        has_assigned_udi=False,
        eudamed_di_input=body if _exact_text(udi.get("Legacy EUDAMED DI Input")) else "",
        eudamed_di=final_di,
        eudamed_id=final_id,
        identifier_code=final_id,
        identifier_issuing_entity="EUDAMED",
        method=method,
    )


def legacy_fields_present(payload: dict) -> bool:
    return any(
        _text(payload.get(field))
        for field in (
            "Legacy Has Assigned UDI-DI",
            "Legacy EUDAMED DI Input",
            "Legacy EUDAMED DI",
            "Legacy EUDAMED ID",
        )
    )
