# Agent Operating Notes

This file is the shared operating brief for Codex, Claude, and any future coding agent working on this repository.

## Project Purpose

This is a local EUDAMED bulk-upload helper for medical-device Regulatory Affairs users. It converts the maintained Excel template into official EUDAMED XML for supported DTX services.

The tool is not an official European Commission product. Generated XML must be verified by users in the EUDAMED Playground before production use.

## Current Release Contract

- Tool version is defined in `local_beta/constants.py`.
- Template version is defined in both `local_beta/constants.py` and `local_beta/template_schema.py`; these must stay aligned.
- The default user template is `EUDAMED_Template_v2.8.xlsx`.
- The declared official XSD version is `3.0.30`.
- Update `CHANGELOG.md` for every user-visible change.

## Important Paths

- `run_local_beta.py`: local web server entry point.
- `local_beta/`: current web app, importer, storage, exporter, template generator.
- `EUDAMED_TOOL_v2/validator.py`: legacy validator still used by importer.
- `official_docs/unpacked/xsd_production/`: bundled production XSD files.
- `local_beta_data/`: user runtime data. Treat this as private user data; never delete or reset without explicit instruction.
- `Test sample/` and `Feedback case/`: customer/sample material. Do not include in releases unless explicitly requested.

## Engineering Rules

- Do not silently change XML semantics. If changing exporter behavior, add or update tests and document the reason in `CHANGELOG.md`.
- Do not call version-string checks “XSD validation” unless the code actually validates XML against XSD.
- Do not remove customer data, local databases, official documents, generated templates, or feedback cases without explicit approval.
- Keep Excel template changes synchronized with importer, exporter, validator, docs, packaging, and release workflow.
- Prefer local-only behavior. Do not add telemetry, uploads, SaaS calls, or external AI features without explicit user approval.
- Preserve bilingual UI and RA-user wording. Official EUDAMED service names can stay in English, but user guidance should be understandable in Chinese.

## Verification Before Release

Run at least:

```bash
python3 -m compileall local_beta EUDAMED_TOOL_v2/validator.py
python3 -m unittest discover -s tests
python3 -m local_beta.build_unified_template
```

Then manually smoke-test:

- Start `python3 run_local_beta.py`.
- Open `http://127.0.0.1:8765`.
- Import a current v2.8 template sample.
- Pre-check and export at least one `DEVICE.POST` and one update service.
- Confirm generated XML/ZIP and manifest behavior.

## Release Notes

GitHub/Gitee releases are expected to carry the Windows ZIP and the current Excel template. The release workflow validates that `TOOL_VERSION` matches the requested release version.

