# EUDAMED 官方 XSD / 技术资料巡检报告

- 检查日期: `2026-06-15`
- 本地生成时间: `2026-06-15T17:03:00+08:00`
- 判定范围: `仅使用 EUDAMED / European Commission 官方生产环境帮助页与官方下载 URL`
- 本地工具基线:
  - `local_beta/constants.py -> SCHEMA_VERSION = 3.0.30`
  - `local_beta/constants.py -> BULK_UPLOAD_ENTITY_LIMIT = 300`
  - `local_beta/constants.py -> TOOL_VERSION = 0.9.4`
  - `local_beta/constants.py + local_beta/template_schema.py -> TEMPLATE_VERSION = v2.9`
- 结论:
  - `未发现新的生产 XSD 版本；官方页面仍声明 XSD v3.0.30 对应平台 v2.27.0`
  - `官方页面与下载件的 HTTP 元数据已在 2026-06-10 重新发布，但当前下载内容与 2026-06-08 快照二进制完全一致`
  - `主转换工具当前不需要因 XSD 结构变化而改码；主要维护动作仍是决定是否刷新顶层 official_docs 镜像资料`

## 官方判定依据

1. 官方下载索引页  
   URL: <https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html>  
   当前观测:
   - 页面尾部显示 `© 2026 European Commission-v.2.27.0`
   - 页面 `Publication date: May 18, 2026`
   - 页面说明: `The XSD schemas above version (v 3.0.30) relate to the current platform release (v 2.27.0).`
2. 官方 support 页  
   URL: <https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/machine-to-machine/support/technical-documentation.html>  
   当前观测:
   - 页面尾部显示 `© 2026 European Commission-v.2.27.0`
   - 页面 `Publication date: May 18, 2026`
   - 页面继续把 `DTX XSD / XML samples / Service Definition / Business Rules / Enumerations / Data Dictionaries` 列为技术资料集合
3. 官方下载件 HTTP 元数据  
   当前核对的页面与下载件 `Last-Modified` 已统一切到 `Wed, 10 Jun 2026 12:37:37/38 GMT`

## 本次留存目录

- 检查目录: [official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30)
- 原始下载件: [downloads](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/downloads)
- 证据 JSON: [source_evidence.json](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/source_evidence.json)
- 比较摘要: [comparison_summary.json](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/comparison_summary.json)
- 校验和: [official_files_checksums.sha256](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/official_files_checksums.sha256)
- XSD zip 清单: [xsd_zip_entries.txt](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/xsd_zip_entries.txt)
- XSD 文件清单: [xsd_file_manifest.tsv](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/xsd_file_manifest.tsv)
- EO samples zip 清单: [eo_samples_zip_entries.txt](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/eo_samples_zip_entries.txt)
- EO samples 差异: [eo_samples_diff.tsv](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/eo_samples_diff.tsv)

## HTTP / 下载元数据

| 官方文件 | URL | Last-Modified | ETag | Content-Length | 结论 |
| --- | --- | --- | --- | ---: | --- |
| Technical documentation page | <https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html> | `Wed, 10 Jun 2026 12:37:37 GMT` | `"4630-653e5822f0640"` | 17968 | 页面声明仍是 `v2.27.0 / XSD 3.0.30` |
| XSD schemas.zip | <https://webgate.ec.europa.eu/eudamed-help/en/files/XSD%20schemas.zip> | `Wed, 10 Jun 2026 12:37:38 GMT` | `"209bd-653e5823e4880"` | 133565 | 与 2026-06-08 快照二进制一致 |
| EOs - XML samples.zip | <https://webgate.ec.europa.eu/eudamed-help/en/files/EOs%20-%20XML%20samples.zip> | `Wed, 10 Jun 2026 12:37:37 GMT` | `"fcd3-653e5822f0640"` | 64723 | 与 2026-06-08 快照二进制一致 |
| UDI Devices - data dictionary.xlsx | <https://webgate.ec.europa.eu/eudamed-help/en/files/UDI%20Devices%20-%20data%20dictionary.xlsx> | `Wed, 10 Jun 2026 12:37:38 GMT` | `"2263e-653e5823e4880"` | 140862 | 与 2026-06-08 快照二进制一致 |
| UDI Devices - business rules.pdf | <https://webgate.ec.europa.eu/eudamed-help/en/files/UDI%20Devices%20-%20business%20rules.pdf> | `Wed, 10 Jun 2026 12:37:38 GMT` | `"c984a-653e5823e4880"` | 825418 | 与 2026-06-08 快照二进制一致 |
| UDI Devices - enumerations.pdf | <https://webgate.ec.europa.eu/eudamed-help/en/files/UDI%20Devices%20-%20enumerations.pdf> | `Wed, 10 Jun 2026 12:37:38 GMT` | `"11de6b1-653e5823e4880"` | 18736817 | 与 2026-06-08 快照二进制一致 |
| DTX for EOs - services definition.pdf | <https://webgate.ec.europa.eu/eudamed-help/en/files/DTX%20for%20EOs%20-%20services%20definition.pdf> | `Wed, 10 Jun 2026 12:37:37 GMT` | `"983668-653e5822f0640"` | 9975400 | 与 2026-06-08 快照二进制一致 |

## 与上一轮快照比较

比较对象: [official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30)

### 1. XSD schemas.zip

- SHA-256: `e3c7621a69340b1ad01d375994a6df6a131073626e2a4ae01048e0ffa04b1c3b`
- 文件大小: `133565 bytes -> 133565 bytes`
- 二进制比较: `完全一致`
- 解包比较:
  - XSD 文件新增: `0`
  - XSD 文件删除: `0`
  - XSD 文件修改: `0`
- 结论:
  - `schema 结构 / 枚举 / 字段 / 顺序 / 约束均未变化`
  - `local_beta/constants.py` 中 `SCHEMA_VERSION = 3.0.30` 继续正确

### 2. EOs - XML samples.zip

- SHA-256: `583d92b7ba59df6d4d66116cfc868fe9fe21d2abc14100d8a7ba6ce3663b7bf5`
- 文件大小: `64723 bytes -> 64723 bytes`
- 文件项比较:
  - 新增: `0`
  - 删除: `0`
  - 修改: `0`
- 结论:
  - `2026-06-08` 已确认的官方样例删除状态保持不变
  - 本次没有新的样例包变化

### 3. Data dictionary / business rules / enumerations / services definition

- 当前四个文件与 `2026-06-08` 快照 `SHA-256` 全部一致
- 结论:
  - `2026-06-08` 时已经观测到的 `Production v2.27.0` 文档批次仍然有效
  - `2026-06-10` 这次更像是页面/资源元数据重发，而不是文档内容再更新

## 与顶层 official_docs 基线比较

| 资料 | 顶层基线状态 | 当前官方状态 | 是否一致 |
| --- | --- | --- | --- |
| XSD schemas.zip | `official_docs/XSD_schemas_production_3.0.30.zip` | `3.0.30` | `是` |
| EOs - XML samples.zip | `official_docs/EOs_XML_samples.zip` | `64723 bytes / 583d92...` | `否` |
| UDI data dictionary.xlsx | `official_docs/UDI_Devices_data_dictionary.xlsx` | `140862 bytes / 480a17...` | `否` |
| UDI business rules.pdf | `official_docs/UDI_Devices_business_rules.pdf` | `825418 bytes / b836cd...` | `否` |
| UDI enumerations.pdf | `official_docs/UDI_Devices_enumerations.pdf` | `18736817 bytes / e3a6a5...` | `否` |
| EO services definition.pdf | `official_docs/DTX_for_EOs_services_definition.pdf` | `9975400 bytes / 3ba405...` | `否` |

说明:

- 顶层 `official_docs` 中的 XSD 主包仍是当前官方版本
- 顶层 `samples / data dictionary / business rules / enumerations / services definition` 仍然落后于当前官方镜像
- 由于本次当前官方件与 `2026-06-08` 快照完全一致，顶层漂移结论与上一轮相比没有新增差异，只是证据时间更新到了 `2026-06-15`

## 对主转换工具的影响清单

### 当前不需要立刻修改的部分

- `local_beta/constants.py`
  - `SCHEMA_VERSION = 3.0.30` 仍正确
  - `BULK_UPLOAD_ENTITY_LIMIT = 300` 仍可继续沿用
- `local_beta/exporter.py`
  - 当前没有因 XSD 新增字段、顺序变化或约束变化而必须调整的导出逻辑
- `local_beta/template_schema.py`
  - 当前没有来自 XSD 本体变化的新枚举或 requiredness 变动信号
- `tests/test_xsd_validation.py`
  - 当前 XSD 验证基线不需要因本轮官方检查而改动

### 维护者应关注的更新点

1. `official_docs/official_sources_manifest.json` 仍是旧镜像摘要  
   当前官方件与顶层旧镜像不一致的文件，manifest 尚未反映
2. 顶层官方资料是否要提升为现行镜像  
   如果后续要把仓库根目录下的 `official_docs/*.pdf/*.xlsx/*.zip` 作为团队共享基线，建议明确一次提升动作
3. 如果后续人工复读 `v2.27.0` 文档并发现语义性规则变化，再同步以下位置:
   - `local_beta/template_schema.py`
   - `local_beta/importer.py`
   - `local_beta/exporter.py`
   - `EUDAMED_TOOL_v2/validator.py`
   - `tests/`

## 建议的后续动作

1. 把本次检查结论视为 `无新的 XSD 内容更新，但官方元数据已在 2026-06-10 重发`
2. 若要减少后续人工判断成本，可新增一个本地巡检脚本，固定输出:
   - 页面 `Publication date / footer version`
   - 下载件 `Last-Modified / ETag / Content-Length`
   - `SHA-256`
   - zip 文件项增删
   - XSD 文件级增删改
3. 若要让仓库根目录官方资料保持“当前官方镜像”，下一步应是资料基线刷新，而不是 schema 适配改码

## 最终判定

截至 `2026-06-15`，官方生产帮助页仍声明 `XSD v3.0.30 / platform v2.27.0`。虽然页面和下载件的 HTTP 元数据已经更新到 `2026-06-10`，但当前下载到的 `XSD schemas.zip`、`EOs XML samples.zip`、`data dictionary`、`business rules`、`enumerations`、`services definition` 与 `2026-06-08` 巡检快照全部二进制一致。  

因此，这一轮对主转换工具的维护结论仍然是: `没有新的 schema 内容变化，不需要立刻改 exporter / importer / validator；仍只需要关注顶层 official_docs 镜像资料是否要刷新。`
