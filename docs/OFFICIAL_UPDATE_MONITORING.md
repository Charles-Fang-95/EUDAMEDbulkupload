# Official EUDAMED Update Monitoring

本项目不让用户端 exe 自动修改代码或模板。官方 XSD / data dictionary / business rules 更新时，由 GitHub Actions 定时检查并创建人工审查 issue；维护者确认后再发布新版 Release。

## How It Works

- Workflow: `.github/workflows/official-docs-check.yml`
- Script: `scripts/check_official_updates.py`
- Baseline: `official_docs/official_sources_manifest.json`
- Schedule: 每周一 UTC 02:00，也可在 GitHub Actions 页面手动运行。

检查内容：

- `XSD schemas.zip`
- `UDI Devices - data dictionary.xlsx`
- `UDI Devices - business rules.pdf`
- `DTX for EOs - services definition.pdf`
- XSD `MessageType.xsd` fixed version
- 关键枚举数量：language、country、issuing entity、storage、critical warning

## Review Flow

1. GitHub Actions 生成 `official-update-report` artifact。
2. 如 hash、XSD version 或关键枚举变化，workflow 创建或更新 issue。
3. 维护者下载报告，判断是否需要更新模板、校验器、导出器或文档。
4. 修改完成后更新 `official_sources_manifest.json`、`CHANGELOG.md`、`TOOL_VERSION`。
5. 打 tag、创建 GitHub Release、上传 Windows/Mac 包。

## Field Mapping Audit

字段映射审计报告由下面命令生成：

```bash
python3 scripts/audit_data_dictionary_mapping.py --output docs/DATA_DICTIONARY_FIELD_AUDIT.md
```

报告只用于审查，不会自动生成 XML 映射。复杂字段例如 eIFU、Public Email、Product Designer 需要先确认官方 XML 结构和业务规则，再决定是否实现；Basic UDI-DI 的 `deviceCertificateLinks`、MDR `clinicalSizes` 和 MDR `annexXVINonMedicalDeviceTypes` 已实现，但 PR/SPP 证书结构仍需单独审计。
