# Changelog

本文件记录本地内测工具和 Excel template 的关键变更，便于对外发包、排查客户问题和回溯 EUDAMED 规则变化。

## 0.5.0 - 2026-05-25

- 新增 `Device Certificates` sheet，按 Basic UDI-DI 采集 product certificate 信息。
- 支持在 `DEVICE.POST` / `Basic_UDI.PATCH` 的 Basic UDI-DI XML 中输出 `deviceCertificateLinks`。
- 新增高风险 / legacy 证书信息预检 warning：MDR Class III/部分 IIb、IVDR D/C/部分 B、MDD/AIMDD/IVDD 无证书信息时提示人工确认。
- 移除主表孤立的 `Basic - Certificate Number` 字段，避免误导为单一证书号即可提交。
- 模板、README 和网页导出指引增加 NB / product certificate validation 说明。

## 0.4.2 - 2026-05-22

- 修正 GitHub Releases API 返回 404 时的提示：显示“仓库尚未发布版本”，不再误判为断网。
- 更新 template 特殊下拉值说明：`ANY` language、`CW999`、`SHC099`、`EL`、`EUDAMED`、`IFA`。
- 标注当前收集但尚未输出 XML 的复杂字段，避免用户误以为填写后一定提交到 EUDAMED。
- 新增 GitHub Actions 官方文档/XSD 更新监控脚本，发现官方资料变化时生成报告并创建 issue。
- 新增 Data Dictionary 字段映射审计报告，作为后续补充 XML 字段输出的依据。
- 新增网页端“迁移模板”工具：把旧版/已填写的 EUDAMED template 搬到当前 v2.4 模板，并生成 Migration Report。

## 0.4.1 - 2026-05-21

- 更新 Trade Name 语言规则：`UDI - Trade Name Language` 和 `Trade Names` sheet 的 `Language` 下拉允许 `ANY`，符合官方 `LanguageEnum`。
- 修正 Trade Names 导入校验：不再禁止 `ANY`，只要求填写官方语言代码或 `ANY`。
- 更新 Market Info 规则说明和校验：同一 UDI-DI 可有多个 made available 国家，但 `Originally Placed on Market` 必须且只能有一个 `TRUE`。
- 更新国家代码规则：希腊使用 XSD 官方代码 `EL`，并保留对旧输入 `GR` 的导出映射。
- 重新生成 `EUDAMED_Template_v2.4.xlsx` 和工具包内默认模板。

## 0.4.0 - 2026-05-21

- 将工具自身版本拆分为 `TOOL_VERSION` 和 `TOOL_VERSION_LABEL`，为后续 GitHub Releases 检查更新做准备。
- 增加帮助页“检查更新”模块，支持 GitHub Releases API；未配置时安全显示“未配置更新源”。
- 增加 EUDAMED bulk upload 300 条限制提示和自动拆分逻辑。
- 支持 `DEVICE.POST` 超过 300 条时按 Basic UDI-DI 分组，并为同一 Basic 后续批次生成依赖的 `UDI_DI.POST`。
- 更新官方 XSD 到 production `3.0.30`，导出 XML 的 message version 跟随本地 XSD fixed version。

## 0.3.x - 2026-05

- 新增本地网页端工作流：导入 Excel、产品库管理、service 向导、预检、XML 导出、导出历史。
- 新增 v2.4 Excel template：`MDR_MDD` / `IVDR_IVDD` 主 sheet，独立 `Trade Names`、`Market Info`、`Package Info`、`Critical Warnings`、`Storage Conditions`、`CMR Substances` sheet。
- 增加 Legacy Device / EUDI 新上传路径，支持 MDD、AIMDD、IVDD。
- 增加 Windows 打包脚本和内测交付说明。
