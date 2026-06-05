# Data Dictionary Field Mapping Audit

This report compares the official EUDAMED UDI Devices data dictionary with the current Excel template, importer/storage, and XML exporter.

Status meanings:

- `implemented`: collected and currently output to XML, or mapped by known exporter logic.
- `collected_not_exported`: template/importer collects the field but exporter does not currently output it.
- `not_in_template`: official field is not represented in the current template.
- `explicitly_out_of_scope`: template deliberately marks the field as not currently output or tied to a later service.
- `needs_design`: field needs a dedicated mapping design before safe XML output.

## Summary

- `implemented`: 174
- `collected_not_exported`: 0
- `not_in_template`: 113
- `explicitly_out_of_scope`: 6
- `needs_design`: 0

## Known Priority Findings

- `eIFU URL` and `Public Email` are collected or partly represented, but not safely output to XML yet.
- `Device Certificates` is implemented for Basic UDI-DI `deviceCertificateLinks`; PR/SPP certificate handling remains out of scope.
- `Clinical Sizes` and `Annex XVI Purposes` are implemented for MDR UDI-DI via structured detail sheets.
- `Is it a Kit` is unified in the template and exported where the current XSD provides `commondi:kit` (IVDR/IVDD paths).
- `Product Designer` remains out of scope until the Update product original manufacturer service is designed.
- `Presence of Medicinal Substance` remains documented-not-exported because `Medicinal Product Device` already maps to `medicinalProductCheck`.

## Field Audit

| Source Sheet | Field ID | Field Label | Occurrence | Template Field | Importer Reads | Storage Saves | Exporter Outputs | XML Path | Status | Notes |
|---|---|---|---|---|---:|---:|---:|---|---|---|
| DD BASIC UDI | FLD-UDID-01 | Issuing Entity Basic UDI-DI | 1 | Basic - Issuing Entity* | Yes | Yes | Yes | basicudi:basicUDIIdentifier/issuingEntity | `implemented` |  |
| DD BASIC UDI | FLD-UDID-14 | Basic UDI- DI code | 1 | Basic UDI-DI Code* | Yes | Yes | Yes | basicudi:basicUDIIdentifier/basicUDIIdentifier | `implemented` |  |
| DD BASIC UDI | FLD-UDID-10 | Legal Manufacturer SRN | 1 | Basic - Manufacturer SRN* | Yes | Yes | Yes | manufacturerActorCode | `implemented` |  |
| DD BASIC UDI | FLD-UDID-11 | Applicable regulation | 1 | Basic - Applicable Legislation* | Yes | Yes | Yes | payload profile / applicableLegislation | `implemented` | Template uses the label Applicable Legislation. |
| DD BASIC UDI | FLD-UDID-12 | Is it a System which is a Device in itself, Procedure pack which is a Device in itself | 1 |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI | FLD-UDID-356 | Is it a Kit | 1 | Basic - Is it a Kit | Yes | Yes | Yes | commondi:kit | `implemented` | Unified template field. Exported for IVDR/IVDD paths where current XSD provides commondi:kit; MDR/MDD are not forced into XML without a safe schema location. |
| DD BASIC UDI | FLD-UDID-13 | Special Device Type | 0..1 | Basic - Special Device Type | Yes | Yes | Yes | basicudi:specialDevice | `implemented` | v2.8 template uses official MDRSpecialDeviceTypeEnum / IVDRSpecialDeviceTypeEnum dropdowns by sheet. |
| DD BASIC UDI | FLD-UDID-15 | Authorised Representative | 0..1 Applicable and mandatory only for nonEU MF | Basic - Authorised Representative SRN | Yes | Yes | Yes | basicudi:ARActorCode | `implemented` | Template stores SRN only. |
| DD BASIC UDI | FLD-UDID-16 | Risk Class | 1 | Basic - Risk Class* | Yes | Yes | Yes | riskClass | `implemented` |  |
| DD BASIC UDI | FLD-UDID-18 | Tissues and cells - Presence of animal tissues or Cells, or their derivates | 1 | Basic - Presence of Animal Tissues | Yes | Yes | Yes |  | `implemented` |  |
| DD BASIC UDI | FLD-UDID-34 | Tissues and cells - Presence of cells or substances of microbial origin | 1 | Basic - Microbial Origin (IVDR) | Yes | Yes | Yes | commondi:microbialSubstances | `implemented` | IVDR field. |
| DD BASIC UDI | FLD-UDID-23 | Tissues and cells - presence of human tissues or cells, or their derivates | 1 | Basic - Presence of Human Tissues | Yes | Yes | Yes |  | `implemented` |  |
| DD BASIC UDI | FLD-UDID-20 | Device Model | 0..1 Either Device Model or Device Name is required (both can be provided) | Basic - Device Model | Yes | Yes | Yes |  | `implemented` |  |
| DD BASIC UDI | FLD-UDID-22 | Device Name | 0..1 Either Device Model or Device Name is required (both can be provided) | Basic - Device Name* | Yes | Payload | Yes | deviceName | `implemented` | Template field is Basic - Device Name* / internal field Device Name/Model. |
| DD BASIC UDI | FLD-UDID-28 | Active Device | 1 | Basic - Active Device | Yes | Yes | Yes |  | `implemented` |  |
| DD BASIC UDI | FLD-UDID-29 | Device Intended to administer and/or Remove medicinal product | 1 | Basic - Administer Medicine | Yes | Yes | Yes | commondi:administeringMedicine | `implemented` | Template label is Administer Medicine. |
| DD BASIC UDI | FLD-UDID-30 | Implantable | 1 | Basic - Implantable | Yes | Yes | Yes |  | `implemented` |  |
| DD BASIC UDI | FLD-UDID-31 | Measuring Function | 1 | Basic - Measuring Function | Yes | Yes | Yes |  | `implemented` |  |
| DD BASIC UDI | FLD-UDID-32 | Reusable Surgical Instruments | 1 | Basic - Reusable Surgical Instrument | Yes | Yes | Yes | commondi:reusable | `implemented` | Template uses singular wording. |
| DD BASIC UDI | FLD-UDID-33 | Companion Diagnostic | 1 | Basic - Companion Diagnostic (IVDR) | Yes | Yes | Yes | commondi:companionDiagnostics | `implemented` | IVDR field. |
| DD BASIC UDI | FLD-UDID-35 | Near Patient Testing | 1 | Basic - Near Patient Testing (IVDR) | Yes | Yes | Yes | commondi:nearPatientTesting | `implemented` | IVDR field. |
| DD BASIC UDI | FLD-UDID-36 | Patient Self Testing | 1 | Basic - Self-Testing (IVDR) | Yes | Yes | Yes | commondi:selfTesting | `implemented` | IVDR field. |
| DD BASIC UDI | FLD-UDID-155 | Presence of a substance which , if used separately, may be considered to be a medicinal product derived from human blood or plasma | 1 | Basic - Medicinal Product Device | Yes | Yes | Yes | basicudi:medicinalProductCheck | `implemented` | Current exporter maps Medicinal Product Device to medicinalProductCheck. |
| DD BASIC UDI | FLD-UDID-158 | Presence of substance which, if used separately, may be considered to be a medicinal product | 1 | Basic - Medicinal Product Device | Yes | Yes | Yes | basicudi:medicinalProductCheck | `implemented` | Current exporter maps Medicinal Product Device to medicinalProductCheck. |
| DD BASIC UDI | FLD-UDID-262 | Reagent | 1 | Basic - Reagent | Yes | Yes | Yes |  | `implemented` |  |
| DD BASIC UDI | FLD-UDID-263 | Professional Testing | 1 | Basic - Professional Testing (IVDR) | Yes | Yes | Yes | commondi:professionalTesting | `implemented` | IVDR field. |
| DD BASIC UDI | FLD-UDID-264 | Instrument | 1 | Basic - Instrument (IVDR) | Yes | Yes | Yes | commondi:instrument | `implemented` | IVDR field. |
| DD BASIC UDI | FLD-UDID-265 | Is it Device a suture, staple, dental filling, dental brace (...)? | 0..1 Property is conditional mandatory only for Devices having Risk Class II b and having the property 'Implantable' | Basic - Is Suture/Staple/Filling/Brace (IIb Implant) | Yes | Payload | Yes | basicudi:IIb_implantable_exceptions | `implemented` | Conditional MDR/MDD field; v2.8 template uses TRUE/FALSE dropdown. |
| DD BASIC UDI | FLD-UDID-50 | Clinical Investigations associated to the Basic UDI | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI | FLD-UDID-39 | Device Certificate Information associated with the Device | 0..1 | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD BASIC UDI | FLD-UDID-343 | Certificates linked to the Device | 0..n | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD BASIC UDI | FLD-UDID-40 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI | FLD-UDID-51 | Clinical Investigation/Performance study reference Number | 1 Occurrence applicable if Clinical Investigations are provided (FLD-UDID-50) | UDI - Reference Number* | Yes | Yes | Yes | referenceNumber | `implemented` |  |
| DD BASIC UDI | FLD-UDID-300 | Countries outside EU where Clinical Investigation is performed | 0..n Occurrence applicable if Clinical Investigations are provided (FLD-UDID-50) |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI | FLD-UDID-54 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI | FLD-UDID-60 | Certificate Type (Technical Documentation, Type Examination, etc) | 1 Occurrence applicable if Device Certificate Inforamtion is provided (FLD-UDID-39) | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD BASIC UDI | FLD-UDID-61 | Certificate Number | 0..1 Occurrence applicable if Device Certificate Inforamtion is provided (FLD-UDID-39) | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD BASIC UDI | FLD-UDID-62 | Revision Number | 0..1 Occurrence applicable if Device Certificate Information is provided (FLD-UDID-39) | Device Certificates / Revision Number | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:certificateRevisionNumber | `implemented` | Optional revision number. |
| DD BASIC UDI | FLD-UDID-63 | Notified Body | 1 Occurrence applicable if Device Certificate Information is provided (FLD-UDID-39) | Device Certificates / Notified Body ID | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:NBActorCode | `implemented` | Stored as Notified Body ID / NBActorCode. |
| DD BASIC UDI | FLD-UDID-360 | Certificate Type | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD BASIC UDI | FLD-UDID-344 | Certificate Number | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD BASIC UDI | FLD-UDID-345 | Revision Number | 0..1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) | Device Certificates / Revision Number | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:certificateRevisionNumber | `implemented` | Optional revision number. |
| DD BASIC UDI | FLD-UDID-346 | Issue Date | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) |  | No | No | No |  | `not_in_template` | Issue date is not part of current deviceCertificateLinks output. |
| DD BASIC UDI | FLD-UDID-347 | Starting Validity Date | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) |  | No | No | No |  | `not_in_template` | Starting validity date is not part of current deviceCertificateLinks output. |
| DD BASIC UDI | FLD-UDID-348 | Expiry Date | 0..1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) | Device Certificates / Expiry Date | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:expiryDate | `implemented` | Optional for regulation devices; often required for legacy directive certificates. |
| DD BASIC UDI | FLD-UDID-349 | Notified Body | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) | Device Certificates / Notified Body ID | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:NBActorCode | `implemented` | Stored as Notified Body ID / NBActorCode. |
| DD BASIC UDI | FLD-UDID-350 | Certificate Status | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) |  | No | No | No |  | `not_in_template` | Device certificate link output does not include certificate status. |
| DD BASIC UDI | FLD-UDID-357 | Decision Date | 0..1 Occurrence applicable if Certificate Link exists (FLD-UDID-343) | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD BASIC UDI | FLD-UDID-361 | Starting Decision Applicability Date | 0..1 Occurrence applicable if Certificate Link exists (FLD-UDID-343) | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD BASIC UDI | FLD-UDID-50 | Clinical Investigations associated to the Basic UDI | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI | FLD-UDID-39 | Device Certificate Information associated with the Device | 0..1 | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD BASIC UDI | FLD-UDID-343 | Certificates linked to the Device | 0..n | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD BASIC UDI | FLD-UDID-40 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI | FLD-UDID-51 | Clinical Investigation/Performance study reference Number | 1 Occurrence applicable if Clinical Investigations are provided (FLD-UDID-50) | UDI - Reference Number* | Yes | Yes | Yes | referenceNumber | `implemented` |  |
| DD BASIC UDI | FLD-UDID-300 | Countries outside EU where Clinical Investigation is performed | 0..n Occurrence applicable if Clinical Investigations are provided (FLD-UDID-50) |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI | FLD-UDID-54 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI | FLD-UDID-60 | Certificate Type (Technical Documentation, Type Examination, etc) | 1 Occurrence applicable if Device Certificate Inforamtion is provided (FLD-UDID-39) | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD BASIC UDI | FLD-UDID-61 | Certificate Number | 0..1 Occurrence applicable if Device Certificate Inforamtion is provided (FLD-UDID-39) | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD BASIC UDI | FLD-UDID-62 | Revision Number | 0..1 Occurrence applicable if Device Certificate Information is provided (FLD-UDID-39) | Device Certificates / Revision Number | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:certificateRevisionNumber | `implemented` | Optional revision number. |
| DD BASIC UDI | FLD-UDID-63 | Notified Body | 1 Occurrence applicable if Device Certificate Information is provided (FLD-UDID-39) | Device Certificates / Notified Body ID | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:NBActorCode | `implemented` | Stored as Notified Body ID / NBActorCode. |
| DD BASIC UDI | FLD-UDID-360 | Certificate Type | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD BASIC UDI | FLD-UDID-344 | Certificate Number | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD BASIC UDI | FLD-UDID-345 | Revision Number | 0..1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) | Device Certificates / Revision Number | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:certificateRevisionNumber | `implemented` | Optional revision number. |
| DD BASIC UDI | FLD-UDID-346 | Issue Date | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) |  | No | No | No |  | `not_in_template` | Issue date is not part of current deviceCertificateLinks output. |
| DD BASIC UDI | FLD-UDID-347 | Starting Validity Date | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) |  | No | No | No |  | `not_in_template` | Starting validity date is not part of current deviceCertificateLinks output. |
| DD BASIC UDI | FLD-UDID-348 | Expiry Date | 0..1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) | Device Certificates / Expiry Date | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:expiryDate | `implemented` | Optional for regulation devices; often required for legacy directive certificates. |
| DD BASIC UDI | FLD-UDID-349 | Notified Body | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) | Device Certificates / Notified Body ID | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:NBActorCode | `implemented` | Stored as Notified Body ID / NBActorCode. |
| DD BASIC UDI | FLD-UDID-350 | Certificate Status | 1 Occurrence applicable if Certificate Link is provided (FLD-UDID-343) |  | No | No | No |  | `not_in_template` | Device certificate link output does not include certificate status. |
| DD BASIC UDI | FLD-UDID-357 | Decision Date | 0..1 Occurrence applicable if Certificate Link exists (FLD-UDID-343) | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD BASIC UDI | FLD-UDID-361 | Starting Decision Applicability Date | 0..1 Occurrence applicable if Certificate Link exists (FLD-UDID-343) | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI | FLD-UDID-178 | (Master) UDI-DI code | 1 | UDI-DI Code* | Yes | Yes | Yes | udidi:udiIdentifier/diCode | `implemented` |  |
| DD UDI-DI | FLD-UDID-291 | Issuing Entity (Master) UDI-DI | 1 | Basic - Issuing Entity* | Yes | Yes | Yes | basicudi:basicUDIIdentifier/issuingEntity | `implemented` |  |
| DD UDI-DI | FLD-UDID-136 | Secondary (Master) UDI - DI code | 0..1 | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI | FLD-UDID-293 | Issuing Entity Secondary (Master) UDI-DI | 0..1 | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI | FLD-UDID-135 | Unit of Use DI code | 0..1 | UDI - Unit of Use DI Code | Yes | Yes | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-292 | Issuing Entity Unit of Use DI | 0..1 | Basic - Issuing Entity* | Yes | Yes | Yes | basicudi:basicUDIIdentifier/issuingEntity | `implemented` |  |
| DD UDI-DI | FLD-UDID-138 | Direct Marking UDI-DI code | 0..1 | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI | FLD-UDID-294 | Issuing Entity Direct marking DI | 0..1 | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI | FLD-UDID-145 | Basic UDI-DI Identifier | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-148 | Type of UDI-PI | 1..n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-149 | Nomenclature code | 1..n | UDI - Nomenclature Code* | Yes | Yes | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-151 | Quantity of device | 1 | UDI - Quantity of Device | Yes | Yes | Yes |  | `implemented` | Output only for MDR/IVDR Regulation Device `baseQuantity`; legacy devices do not output it. |
| DD UDI-DI | FLD-UDID-156 | Containing latex | 1 | UDI - Containing Latex* | Yes | Yes | Yes |  | `implemented` | MDR/MDD/AIMDD only; not applicable to IVDR/IVDD. |
| DD UDI-DI | FLD-UDID-157 | Maximum number of reuses | 0..1 Field must be completed only if singleUse is false | Maximum | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-159 | New Device | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-163 | Reference / Catalogue number | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-164 | Reprocessed single use device | 1 | UDI - Reprocessed Single Use Device | Yes | Yes | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-167 | Labelled as single use | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-169 | Device labelled sterile | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-170 | Need for sterilisation before use | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-174 | URL for additional information | 0..1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-175 | Additional product Description | 0..1 Required for System or Procedure Packs that is a Device in itself | Description | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-179 | Trade name applicable | 1 | UDI - Trade Name Applicable* | Yes | Yes | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-176 | Trade name | 0..n | Trade Name* | Yes | Yes | Yes | tradeNames | `implemented` |  |
| DD UDI-DI | FLD-UDID-130 | UDI-DI / Device Status | 1 | UDI - Device Status* | Yes | Yes | Yes | deviceStatus | `implemented` |  |
| DD UDI-DI | FLD-UDID-256 | Device Substatus | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-147 | Intended purpose other than medical (Annex XVI) | 0..n | Annex XVI Purposes sheet | Yes | JSON payload | Yes | udidi:annexXVINonMedicalDeviceTypes/udidi:nmdType | `implemented` | Annex XVI non-medical device types are collected as 0..n rows and exported for MDR UDI-DI only. |
| DD UDI-DI | FLD-UDID-140 | List of CMR Substances associated to Device | 0..n | CMR Substances sheet | Yes | JSON payload | Yes | udidi:substances | `implemented` | CMR / endocrine / medicinal / human product substance rows are stored at Basic level and emitted on related UDI-DI XML. |
| DD UDI-DI | FLD-UDID-310 | List of Endocrine Substances associated to Device | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-311 | List of Medicinal product substances associated to the Device | 0..n | Basic - Medicinal Product Device | Yes | Yes | Yes | basicudi:medicinalProductCheck | `implemented` | Current exporter maps Medicinal Product Device to medicinalProductCheck. |
| DD UDI-DI | FLD-UDID-312 | List of Storage and handling Conditions | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-144 | List of Critical Warnings or Contraindications | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-146 | Clinical Sizes | 0..n | Clinical Sizes sheet | Yes | JSON payload | Yes | udidi:clinicalSizes/commondi:clinicalSize | `implemented` | Structured Clinical Sizes sheet is exported for MDR UDI-DI only; other profiles are warned and ignored. |
| DD UDI-DI | FLD-UDID-139 | Natural or Legal person who manufactured and desinged the Device | 0..1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-137 | Member State of the placing on the EU market of the Device | 0..1 (0 only if Device Status is ‘not intended for EU market’”; ) |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-141 | Member States where device is or is to be made available on the market | 0..n If the Device has the status Not intended for EU Market, Countries where the devices is made available are not provided (Occurrence 0) |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-180 | Related Legacy Device | 0..1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-181 | Relationship Type | 0..1 Required when Related Legacy Device is provided (when linking is performed by the Manufacturer) |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-309 | Container Packages related to UDI-DI | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-177 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-122 | Manufacturer action required | 1..n Occurrence applicable if Device Substatus (FLD-UDID-256) is provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-126 | Start date | 1 Occurrence applicable if Device Substatus (FLD-UDID-256) is provided | Start Date | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-127 | Estimated end date | 0..1 Occurrence applicable if Device Substatus (FLD-UDID-256) is provided | End Date | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-131 | UDI-DI/Device -Sub status | 1 Occurrence applicable if Device Substatus (FLD-UDID-256) is provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-190 | /Clinical Size Type | 1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided | Clinical Sizes sheet | Yes | JSON payload | Yes | udidi:clinicalSizes/commondi:clinicalSize | `implemented` | Structured Clinical Sizes sheet is exported for MDR UDI-DI only; other profiles are warned and ignored. |
| DD UDI-DI | FLD-UDID-191 | /Precizion | 1 Applicable if Clinical Size (FLD-UDID-146) is provided | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI | FLD-UDID-192 | /Maximum | 0..1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided Required when Precision has value Range | Maximum | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-193 | /Value(Minimum) | 0..1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided Required when Precision has value Range | Minimum | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-196 | /Value | 0..1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided Required when Precision has value Value | Value | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-194 | /Value(Text) | 0..1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided Required when Precision has value Text |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-195 | /Measure Unit | 0..1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided Required when the Precision value is either Value or Range | Measure Unit | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-358 | Clinical Size Type Description | 0..1 Required when the Clinical Size Type has option Other | Clinical Sizes sheet | Yes | JSON payload | Yes | udidi:clinicalSizes/commondi:clinicalSize | `implemented` | Structured Clinical Sizes sheet is exported for MDR UDI-DI only; other profiles are warned and ignored. |
| DD UDI-DI | FLD-UDID-359 | Measure Unit Description | 0..1 Required when the Measure Unit Type has option Other | Clinical Sizes / Measure Unit Description | Yes | JSON payload | Yes | udidi:clinicalSizes/commondi:clinicalSize/commondi:measureUnitDescription | `implemented` | Required when Clinical Size Measure Unit is MU999 - OTHER. |
| DD UDI-DI | FLD-UDID-200 | Category of CMR | 1 Occurrence applicable if List of CMR Substances (FLD-UDID-140) is provided | CMR Substances / Substance Type | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:type | `implemented` | v2.8 template restricts Substance Type to the 5 exporter-supported substance categories. |
| DD UDI-DI | FLD-UDID-201 | Name of Substance | 0..1 Applicable if List of CMR Substances (FLD-UDID-140) is provided In case the #CAS, #EC is provided, Name of substance must be provided without the Language | CMR Substances / Substance Name | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:names | `implemented` | Stored in CMR Substances sheet. |
| DD UDI-DI | FLD-UDID-202 | CAS# | 0..1 Applicable if List of CMR Substances (FLD-UDID-140) is provided | CMR Substances / CAS Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:CASCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI | FLD-UDID-203 | EC# | 0..1 Occurrence applicable if List of CMR Substances (FLD-UDID-140) is provided | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI | FLD-UDID-313 | Name of Substance | 0..1 Occurrence applicable if List of Endocrine Substances (FLD-UDID-310) is provided. In case the #CAS, #EC is provided, Name of substance must be provided without the Language | CMR Substances / Substance Name | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:names | `implemented` | Stored in CMR Substances sheet. |
| DD UDI-DI | FLD-UDID-314 | CAS# | 0..1 Occurrence applicable if List of Endocrine Substances (FLD-UDID-310) is provided | CMR Substances / CAS Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:CASCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI | FLD-UDID-315 | EC# | 0..1 Occurrence applicable if List of Endocrine Substances (FLD-UDID-310) is provided | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI | FLD-UDID-316 | Type of Substance (Presence of a substance which, if used separately, may be considered to be a medicinal product/ Presence of a substance which, if used separately, may be considered to be a medicinal product derived from human blood or human plasma) | 1 Occurrence applicable if List of medicinal product substances (FLD-UDID-311) is provided | Basic - Medicinal Product Device | Yes | Yes | Yes | basicudi:medicinalProductCheck | `implemented` | Current exporter maps Medicinal Product Device to medicinalProductCheck. |
| DD UDI-DI | FLD-UDID-317 | Name of Substance | 0..1 Occurrence applicable if List of medicinal product substances (FLD-UDID-311) is provided Not required in case the INN is provided | CMR Substances / Substance Name | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:names | `implemented` | Stored in CMR Substances sheet. |
| DD UDI-DI | FLD-UDID-318 | INN | 0..1 Occurrence applicable if List of medicinal product substances (FLD-UDID-311) is provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-211 | Storage/handling conditions type | 1 Applicable if Storage and handling conditions (FLD-UDID-312) are provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-213 | Storage/Handling conditions Description | 0..n Applicable if Storage and handling conditions (FLD-UDID-312) are provided Required for specific items from the list of Enumerations- where additional details are required | Description | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-212 | Critical Warnings type | 1 Occurrence applicable if Critical Warnings (FLD-UDID-144) are provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-319 | Critical warnings or contra-indications Description | 0..n Occurrence applicable if Critical Warnings (FLD-UDID-144) are provided Required for specific items from the list of Enumerations (for cases in which additional details are required) | Description | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-221 | Enter the SRN (Is the Device designed and Manufactured by another legal or natural person) | 1 if SRN otherwise 0 Occurrence applicable if the Product Designer (FLD-UDID-139) is provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-222 | Organisation (When the Product Designer is not already registered as a Manufacturer in EUAMED) | 0 if SRN otherwise 1 Occurrence applicable if the Product Designer (FLD-UDID-139) is provided | UDI - Product Designer SRN / UDI - Product Designer ID | Yes | Yes | No |  | `explicitly_out_of_scope` | Product original manufacturer/designer update service is not implemented. |
| DD UDI-DI | FLD-UDID-223 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-353 | Organisation Name | 1 Occurrence applicable if the ProductDesignerOrganisation (FLD-UDID-222) is provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-354 | Contact Details | 1 (only Public Contact details) Occurrence applicable if the ProductDesignerOrganisation (FLD-UDID-222) is provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-355 | Geographical Address | 1 Occurrence applicable if the ProductDesignerOrganisation (FLD-UDID-222) is provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-250 | Start date | 0..1 Occurrence applicable if Market Info (FLD-UDID-141) is provided | Start Date | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-251 | End date | 0..1 Occurrence applicable if Market Info (FLD-UDID-141) is provided | End Date | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD-UDID-252 | Member State where the device is or is to be made available | 1 Occurrence applicable if Market Info (FLD-UDID-141) is provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD-UDID-246 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD_EMDN.code | Code |  |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD_EMDN.term | Description of the code |  | Description | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD_EMDN.status | Code status |  |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD_EMDN.version | Code version |  |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI | FLD_EMDN.fromDate | Start date of code version |  | Start Date | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI | FLD_EMDN.action | Type of change of the code |  |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-295 | Issuing Entity for EUDAMED DI | 1 | Basic - Issuing Entity* | Yes | Yes | Yes | basicudi:basicUDIIdentifier/issuingEntity | `implemented` |  |
| DD Legacy Devices | FLD-UDID-42 | EUDAMED DI code | 1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-10 | Legal Manufacturer SRN | 1 | Basic - Manufacturer SRN* | Yes | Yes | Yes | manufacturerActorCode | `implemented` |  |
| DD Legacy Devices | FLD-UDID-11 | Applicable Legislation | 1 | Basic - Applicable Legislation* | Yes | Yes | Yes | payload entity selection | `implemented` |  |
| DD Legacy Devices | FLD-UDID-12 | Is it a System which is a Device in itself, Procedure pack which is a Device in itself | 1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-356 | Is it a Kit | 1 | Basic - Is it a Kit | Yes | Yes | Yes | commondi:kit | `implemented` | Unified template field. Exported for IVDR/IVDD paths where current XSD provides commondi:kit; MDR/MDD are not forced into XML without a safe schema location. |
| DD Legacy Devices | FLD-UDID-13 | Special Device Type | 0..1 | Basic - Special Device Type | Yes | Yes | Yes | basicudi:specialDevice | `implemented` | v2.8 template uses official MDRSpecialDeviceTypeEnum / IVDRSpecialDeviceTypeEnum dropdowns by sheet. |
| DD Legacy Devices | FLD-UDID-15 | Authorised Representative | 0..1 Applicable and mandatory only for nonEU MF | Basic - Authorised Representative SRN | Yes | Yes | Yes | basicudi:ARActorCode | `implemented` | Template stores SRN only. |
| DD Legacy Devices | FLD-UDID-16 | Risk Class | 1 | Basic - Risk Class* | Yes | Yes | Yes | riskClass | `implemented` |  |
| DD Legacy Devices | FLD-UDID-18 | Tissues and cells - Presence of animal tissues or Cells, or their derivates | 1 | Basic - Presence of Animal Tissues | Yes | Yes | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-23 | Tissues and cells - presence of human tissues or cells, or their derivates | 1 | Basic - Presence of Human Tissues | Yes | Yes | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-34 | Tissues and cells - Presence of cells or substances of microbial origin | 1 | Basic - Microbial Origin (IVDR) | Yes | Yes | Yes | commondi:microbialSubstances | `implemented` | IVDR field. |
| DD Legacy Devices | FLD-UDID-20 | Device Model | 0..1 Either Device Model or Device Name is required (both can be provided) | Basic - Device Model | Yes | Yes | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-22 | Device Name | 0..1 Either Device Model or Device Name is required (both can be provided) | Basic - Device Name* | Yes | Payload | Yes | deviceName | `implemented` | Template field is Basic - Device Name* / internal field Device Name/Model. |
| DD Legacy Devices | FLD-UDID-28 | Active Device | 1 | Basic - Active Device | Yes | Yes | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-29 | Device Intended to administer and/or Remove medicinal product | 1 | Basic - Administer Medicine | Yes | Yes | Yes | commondi:administeringMedicine | `implemented` | Template label is Administer Medicine. |
| DD Legacy Devices | FLD-UDID-30 | Implantable | 1 | Basic - Implantable | Yes | Yes | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-31 | Measuring Function | 1 | Basic - Measuring Function | Yes | Yes | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-32 | Reusable Surgical Instruments | 1 | Basic - Reusable Surgical Instrument | Yes | Yes | Yes | commondi:reusable | `implemented` | Template uses singular wording. |
| DD Legacy Devices | FLD-UDID-33 | Companion Diagnostic | 1 | Basic - Companion Diagnostic (IVDR) | Yes | Yes | Yes | commondi:companionDiagnostics | `implemented` | IVDR field. |
| DD Legacy Devices | FLD-UDID-35 | Near Patient Testing | 1 | Basic - Near Patient Testing (IVDR) | Yes | Yes | Yes | commondi:nearPatientTesting | `implemented` | IVDR field. |
| DD Legacy Devices | FLD-UDID-36 | Patient Self Testing | 1 | Basic - Self-Testing (IVDR) | Yes | Yes | Yes | commondi:selfTesting | `implemented` | IVDR field. |
| DD Legacy Devices | FLD-UDID-262 | Reagent | 1 | Basic - Reagent | Yes | Yes | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-263 | Professional Testing | 1 | Basic - Professional Testing (IVDR) | Yes | Yes | Yes | commondi:professionalTesting | `implemented` | IVDR field. |
| DD Legacy Devices | FLD-UDID-264 | Instrument | 1 | Basic - Instrument (IVDR) | Yes | Yes | Yes | commondi:instrument | `implemented` | IVDR field. |
| DD Legacy Devices | FLD-UDID-50 | Clinical Investigations associated to the EUDAMED DI | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | humanProductCheck | Presence of a substance which , if used separately, may be considered to be a medicinal product derived from human blood or plasma | 0..1 | Basic - Medicinal Product Device | Yes | Yes | Yes | basicudi:medicinalProductCheck | `implemented` | Current exporter maps Medicinal Product Device to medicinalProductCheck. |
| DD Legacy Devices | medicinalProductCheck | Presence of substance which, if used separately, may be considered to be a medicinal product | 0..1 | Basic - Medicinal Product Device | Yes | Yes | Yes | basicudi:medicinalProductCheck | `implemented` | Current exporter maps Medicinal Product Device to medicinalProductCheck. |
| DD Legacy Devices | FLD-UDID-39 | Device Certificate Information associated with the Device | 0..n Required to be provided for Legacy Devices with the exception of Devices being Class I Devices or Class IVDD General | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD Legacy Devices | FLD-UDID-40 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-51 | Clinical Investigation/Performance study reference Number | 1 Occurrence applicable if Clinical Investigations are provided (FLD-UDID-50) | UDI - Reference Number* | Yes | Yes | Yes | referenceNumber | `implemented` |  |
| DD Legacy Devices | FLD-UDID-300 | Countries outside EU where Clinical Investigation is performed | 0..n Occurrence applicable if Clinical Investigations are provided (FLD-UDID-50) |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-54 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-60 | Certificate Type | 1 Occurrence applicable if Device Certificate Information is provided (FLD-UDID-39) | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD Legacy Devices | FLD-UDID-61 | Certificate Number | 1 Occurrence applicable if Device Certificate Information is provided (FLD-UDID-39) Field is required for Legacy Devices | Device Certificates | Yes | Payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink | `implemented` | Structured certificate rows are exported as deviceCertificateLinks. PR/SPP certificate handling remains out of scope. |
| DD Legacy Devices | FLD-UDID-62 | Revision Number | 0..1 Occurrence applicable if Device Certificate Information is provided (FLD-UDID-39) | Device Certificates / Revision Number | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:certificateRevisionNumber | `implemented` | Optional revision number. |
| DD Legacy Devices | FLD-UDID-63 | Notified Body | 1 Occurrence applicable if Device Certificate Information is provided (FLD-UDID-39) | Device Certificates / Notified Body ID | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:NBActorCode | `implemented` | Stored as Notified Body ID / NBActorCode. |
| DD Legacy Devices | FLD-UDID-64 | Expiry Date | 1 Occurrence applicable if Device Certificate Information is provided (FLD-UDID-39) Field is required for Legacy Devices | Device Certificates / Expiry Date | Yes | JSON payload | Yes | basicudi:deviceCertificateLinks/links:deviceCertificateLink/links:expiryDate | `implemented` | Optional for regulation devices; often required for legacy directive certificates. |
| DD Legacy Devices | FLD-UDID-341 | Issuing Entity UDI-DI / EUDAMED ID | 1 Either UDI-DI or EUDAMED ID is required | Basic - Issuing Entity* | Yes | Yes | Yes | basicudi:basicUDIIdentifier/issuingEntity | `implemented` |  |
| DD Legacy Devices | FLD-UDID-342 | UDI-DI / EUDAMED ID code | 1 Either UDI-DI or EUDAMED ID is required |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-137 | Member State of the placing on the EU market of the Device | 1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-139 | Natural or Legal person who manufactured and designed the Device | 0..1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-311 | List of Medicinal product substances associated to the Device | 0..n | Basic - Medicinal Product Device | Yes | Yes | Yes | basicudi:medicinalProductCheck | `implemented` | Current exporter maps Medicinal Product Device to medicinalProductCheck. |
| DD Legacy Devices | FLD-UDID-141 | Member States where device is or is to be made available on the market | 1..n |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-144 | List of Critical Warnings or Contraindications or Storage and handling Conditions | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-312 | List of Storage and handling Conditions | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-145 | EUDAMED DI Identifier | 1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-146 | Clinical Sizes | 0..n | Clinical Sizes sheet | Yes | JSON payload | No |  | `explicitly_out_of_scope` | Current exporter supports structured clinicalSizes only for MDR UDI-DI; legacy / other profiles are warned and ignored. |
| DD Legacy Devices | FLD-UDID-149 | Nomenclature code | 1..n | UDI - Nomenclature Code* | Yes | Yes | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-156 | Containing latex | 1 | UDI - Containing Latex* | Yes | Yes | Yes |  | `implemented` | MDD/AIMDD legacy only; not applicable to IVDD legacy. |
| DD Legacy Devices | FLD-UDID-157 | Maximum number of reuses | 0..1 Field can be completed only if singleUse is false | Maximum | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-163 | Reference / Catalogue number | 1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-164 | Reprocessed single use device | 1 | UDI - Reprocessed Single Use Device | Yes | Yes | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-167 | Labelled as single use | 1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-169 | Device labelled sterile | 1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-170 | Need for sterilisation before use | 1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-174 | URL for additional information | 0..1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-175 | Additional product Description | 0..1 Required for System or Procedure Packs that is a Device in itself | Description | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-179 | Trade name applicable | 1 | UDI - Trade Name Applicable* | Yes | Yes | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-176 | Trade name | 0..n | Trade Name* | Yes | Yes | Yes | tradeNames | `implemented` |  |
| DD Legacy Devices | FLD-UDID-130 | Device Status | 1 | UDI - Device Status* | Yes | Yes | Yes | deviceStatus | `implemented` |  |
| DD Legacy Devices | FLD-UDID-256 | Device Substatus | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-331 | Related Regulation Device | 0,,1 |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-181 | Relationship Type | 0..1 Required when Related Legacy Device is provided (when linking is performed by the Manufacturer) |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-122 | Manufacturer action required | 1..n Occurrence applicable if Device Substatus (FLD-UDID-256) is provided |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-126 | Start date | 1 Occurrence applicable if Device Substatus (FLD-UDID-256) is provided | Start Date | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-127 | Estimated end date | 0..1 Occurrence applicable if Device Substatus (FLD-UDID-256) is provided | End Date | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-131 | UDI-DI/Device -Sub status | 1 Occurrence applicable if Device Substatus (FLD-UDID-256) is provided |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-190 | /Clinical Size Type | 1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided | Clinical Sizes sheet | Yes | JSON payload | No |  | `explicitly_out_of_scope` | Current exporter supports structured clinicalSizes only for MDR UDI-DI; legacy / other profiles are warned and ignored. |
| DD Legacy Devices | FLD-UDID-191 | /Precizion | 1 Applicable if Clinical Size (FLD-UDID-146) is provided | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD Legacy Devices | FLD-UDID-192 | /Maximum | 0..1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided Required when Precision has value Range | Maximum | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-193 | /Value(Minimum) | 0..1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided Required when Precision has value Range | Minimum | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-194 | /Value(Text) | 0..1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided Required when Precision has value Text |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-196 | /Value | 0..1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided Required when Precision has value Value | Value | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-195 | /Measure Unit | 0..1 Occurrence applicable if Clinical Size (FLD-UDID-146) is provided Required when the Precision value is either Value or Range | Measure Unit | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-358 | Clinical Size Type Description | 0..1 Required when the Clinical Size Type has option Other | Clinical Sizes sheet | Yes | JSON payload | No |  | `explicitly_out_of_scope` | Current exporter supports structured clinicalSizes only for MDR UDI-DI; legacy / other profiles are warned and ignored. |
| DD Legacy Devices | FLD-UDID-359 | Measure Unit Description | 0..1 Required when the Measure Unit Type has option Other | Clinical Sizes / Measure Unit Description | Yes | JSON payload | No |  | `explicitly_out_of_scope` | Current exporter supports structured clinicalSizes only for MDR UDI-DI; legacy / other profiles are warned and ignored. |
| DD Legacy Devices | FLD-UDID-316 | Type of Substance (Presence of a substance which, if used separately, may be considered to be a medicinal product/ Presence of a substance which, if used separately, may be considered to be a medicinal product derived from human blood or human plasma) | 1 Occurrence applicable if List of medicinal product substances (FLD-UDID-311) is provided | Basic - Medicinal Product Device | Yes | Yes | Yes | basicudi:medicinalProductCheck | `implemented` | Current exporter maps Medicinal Product Device to medicinalProductCheck. |
| DD Legacy Devices | FLD-UDID-317 | Name of Substance | 0..1 Occurrence applicable if List of medicinal product substances (FLD-UDID-311) is provided Not required in case the INN is provided | CMR Substances / Substance Name | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:names | `implemented` | Stored in CMR Substances sheet. |
| DD Legacy Devices | FLD-UDID-318 | INN | 0..1 Occurrence applicable if List of medicinal product substances (FLD-UDID-311) is provided |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-211 | Storage/handling conditions type | 1 Occurrence applicable if Storage and handling conditions (FLD-UDID-312) are provided |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-213 | Storage/Handling conditions Description | 0..n Occurrence applicable if Storage and handling conditions (FLD-UDID-312) are provided Required for specific items from the list of Enumerations- where additional details are required | Description | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-212 | Critical Warnings type | 1 Occurrence applicable if Critical Warnings (FLD-UDID-144) are provided |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-319 | Critical warnings or contra-indications Description | 0..n Occurrence applicable if Critical Warnings (FLD-UDID-144) are provided Required for specific items from the list of Enumerations- where additional details are required | Description | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-221 | Enter the SRN (Is the Device designed or Manufactured by another legal or natural person) | 0..1 Occurrence applicable if the Product Designer (FLD-UDID-139) is provided |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-222 | Organisation (When the Product Designer is not already registered as a Manufacturer in EUAMED) | 0 if SRN otherwise 1 Occurrence applicable if the Product Designer (FLD-UDID-139) is provided | UDI - Product Designer SRN / UDI - Product Designer ID | Yes | Yes | No |  | `explicitly_out_of_scope` | Product original manufacturer/designer update service is not implemented. |
| DD Legacy Devices | FLD-UDID-223 | version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-353 | Organisation Name | 1 Occurrence applicable if the ProductDesignerOrganisation (FLD-UDID-222) is provided |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-354 | Contact Details | 1 (only Public Contact details) Occurrence applicable if the ProductDesignerOrganisation (FLD-UDID-222) is provided |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-355 | Geographical Address | 1 Occurrence applicable if the ProductDesignerOrganisation (FLD-UDID-222) is provided |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-250 | Start date | 0..1 Occurrence applicable if Market Info (FLD-UDID-141) is provided | Start Date | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-251 | End date | 0..1 Occurrence applicable if Market Info (FLD-UDID-141) is provided | End Date | Yes | Payload | Yes |  | `implemented` |  |
| DD Legacy Devices | FLD-UDID-252 | Member State where the device is or is to be made available | 1..n Occurrence applicable if Market Info (FLD-UDID-141) is provided |  | No | No | No |  | `not_in_template` |  |
| DD Legacy Devices | FLD-UDID-246 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI_SPP | FLD-UDID-01 | Issuing Entity Basic UDI-DI | 1 | Basic - Issuing Entity* | Yes | Yes | Yes | basicudi:basicUDIIdentifier/issuingEntity | `implemented` |  |
| DD BASIC UDI_SPP | FLD-UDID-14 | Basic UDI- DI code | 1 | Basic UDI-DI Code* | Yes | Yes | Yes | basicudi:basicUDIIdentifier/basicUDIIdentifier | `implemented` |  |
| DD BASIC UDI_SPP | FLD-UDID-44 | System or Procedure Pack Producer Actor ID | 1 |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI_SPP | FLD-UDID-16 | Risk Class | 1 | Basic - Risk Class* | Yes | Yes | Yes | riskClass | `implemented` |  |
| DD BASIC UDI_SPP | FLD-UDID-20 | System or Procedure Pack Model | 0..1 Either SPP Model or SPP Name is required (both can be provided) |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI_SPP | FLD-UDID-22 | System/Procedure pack Name | 0..1 Either SPP Model or SPP Name is required (both can be provided) |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI_SPP | FLD-UDID-40 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI_SPP | FLD-UDID-260 | Medical Purpose of the System or Procedure Pack | 1 |  | No | No | No |  | `not_in_template` |  |
| DD BASIC UDI_SPP | FLD-UDID-261 | System or Procedure Pack | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-291 | Issuing Entity UDI-DI | 1 | Basic - Issuing Entity* | Yes | Yes | Yes | basicudi:basicUDIIdentifier/issuingEntity | `implemented` |  |
| DD UDI-DI_SPP | FLD-UDID-178 | UDI-DI code | 1 | UDI-DI Code* | Yes | Yes | Yes | udidi:udiIdentifier/diCode | `implemented` |  |
| DD UDI-DI_SPP | FLD-UDID-136 | Secondary UDI - DI code | 0..1 | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI_SPP | FLD-UDID-293 | Issuing Entity Secondary DI | 0..1 | CMR Substances / EC Code | Yes | JSON payload | Yes | udidi:substances/udidi:substance/udidi:ECCode | `implemented` | Stored in CMR Substances sheet; exported only for CMR and Endocrine substance types. |
| DD UDI-DI_SPP | FLD-UDID-144 | List of Critical Warnings or Contraindications or Storage and handling Conditions | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-312 | List of Storage and handling Conditions | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-145 | Basic UDI-DI Identifier | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-148 | Type of UDI-PI | 1..n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-149 | Nomenclature code | 1..n | UDI - Nomenclature Code* | Yes | Yes | Yes |  | `implemented` |  |
| DD UDI-DI_SPP | FLD-UDID-163 | Reference / Catalogue number | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-169 | Labelled as sterile | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-170 | Need for sterilisation before use | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-174 | URL for additional information | 0..1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-175 | Additional product Description | 1 Required for System or Procedure Packs | Description | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI_SPP | FLD-UDID-176 | Trade name | 0..n | Trade Name* | Yes | Yes | Yes | tradeNames | `implemented` |  |
| DD UDI-DI_SPP | FLD-UDID-177 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-130 | System or Procedure Pack Status | 1 |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-256 | System or Procedure Pack Substatus | 0,,n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-309 | Container Packages related to UDI-DI | 0..n |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-122 | Manufacturer action required | 1..n Occurrence applicable if Device Substatus (FLD-UDID-256) is provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-126 | Start date | 1 Occurrence applicable if Device Substatus (FLD-UDID-256) is provided | Start Date | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI_SPP | FLD-UDID-127 | Estimated end date | 0..1 Occurrence applicable if Device Substatus (FLD-UDID-256) is provided | End Date | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI_SPP | FLD-UDID-131 | UDI-DI/Device -Sub status | 1 Occurrence applicable if Device Substatus (FLD-UDID-256) is provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-211 | Storage/handling conditions type | 1 Occurrence applicable if Storage and handling conditions (FLD-UDID-312) are provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-213 | Storage/Handling conditions Description | 0..n Occurrence applicable if Storage and handling conditions (FLD-UDID-312) are provided Required for specific items from the list of Enumerations- where additional details are required | Comment | Yes | Payload | Yes |  | `implemented` |  |
| DD UDI-DI_SPP | FLD-UDID-212 | Critical Warnings type | 1 Occurrence applicable if Critical Warnings (FLD-UDID-144) are provided |  | No | No | No |  | `not_in_template` |  |
| DD UDI-DI_SPP | FLD-UDID-319 | Critical warnings or contra-indications Description | 0..n Occurrence applicable if Critical Warnings (FLD-UDID-144) are provided Required for specific items from the list of Enumerations (for cases in which additional details are required) | Comment | Yes | Payload | Yes |  | `implemented` |  |
| DD Container Pack | FLD-UDID-297 | Issuing Entity Package UDI-DI | 1 Occurrence applicable if Container Package (FLD-UDID-309 is provided | Basic - Issuing Entity* | Yes | Yes | Yes | basicudi:basicUDIIdentifier/issuingEntity | `implemented` |  |
| DD Container Pack | FLD-UDID-120 | Package UDI-DI | 1 Occurrence applicable if Container Package (FLD-UDID-309 is provided |  | No | No | No |  | `not_in_template` |  |
| DD Container Pack | FLD-UDID-121 | Quantity per package | 1 Occurrence applicable if Container Package (FLD-UDID-309 is provided | Quantity per Package* | Yes | Payload | Yes |  | `implemented` |  |
| DD Container Pack | FLD-UDID-124 | Related Package (/ UDI-DI) | 1 Occurrence applicable if Container Package (FLD-UDID-309 is provided |  | No | No | No |  | `not_in_template` |  |
| DD Container Pack | FLD-UDID-130 | Container Pack Status | 1 Occurrence applicable if Container Package (FLD-UDID-309 is provided |  | No | No | No |  | `not_in_template` |  |
| DD Container Pack | FLD-UDID-298 | Version | 1 Managed by EUDAMED |  | No | No | No |  | `not_in_template` |  |
| DD AR related | FLD-UDID-41 | Comment | 1 | Comment | Yes | Payload | Yes |  | `implemented` |  |
| DD AR related | FLD-UDID-332 | Date | 1 |  | No | No | No |  | `not_in_template` |  |
| DD AR related | FLD-UDID-43 | ARSRN | 1 |  | No | No | No |  | `not_in_template` |  |
| DD AR related | FLD-UDID-306 | Basic UDI-DI for which comment is sent | 1 | Comment | Yes | Payload | Yes |  | `implemented` |  |
