# EUDAMED 官方 XSD / 技术资料复检报告

- 检查日期: `2026-06-29`
- 本地生成时间: `2026-06-29T09:04:04+08:00`
- 判定范围: `仅使用 EUDAMED / European Commission 官方生产环境帮助页与官方下载 URL`
- 本地工具基线:
  - `local_beta/constants.py -> SCHEMA_VERSION = 3.0.30`
  - `local_beta/constants.py -> TOOL_VERSION = 0.9.4`
  - `local_beta/constants.py + local_beta/template_schema.py -> TEMPLATE_VERSION = v2.9`
- 复检目标: `确认 2026-06-22 复检之后，生产帮助页或直链下载件是否再次发生变化`
- 结论:
  - `未发现新的生产 XSD 版本；官方仍声明 XSD v3.0.30 对应平台 v2.27.0`
  - `未发现新的官方下载件 HTTP 元数据漂移；Last-Modified / ETag / Content-Length 与 2026-06-15/2026-06-22 基线一致`
  - `因此无需重新下载或重解包 XSD；沿用 2026-06-15 已留存的原始下载件作为当前官方原始件基线`

## 官方判定依据

1. 官方下载索引页  
   URL: <https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html>  
   证据:
   - 页面 `Publication date: May 18, 2026`
   - 页面尾部仍为 `© 2026 European Commission-v.2.27.0`
   - 页面仍声明: `The XSD schemas above version (v 3.0.30) relate to the current platform release (v 2.27.0).`
2. 官方 support 页  
   URL: <https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/machine-to-machine/support/technical-documentation.html>  
   证据:
   - 页面 `Publication date: May 18, 2026`
   - 页面尾部仍为 `© 2026 European Commission-v.2.27.0`
   - 支持页仍把 `DTX XSD / XML samples / Service Definition / Business Rules / Enumerations / Data dictionaries` 作为官方技术资料集合
3. 官方下载件实时 HTTP 元数据  
   证据:
   - 本次 HEAD 采集时间集中在 `2026-06-29 01:01:58-01:02:03 GMT`
   - 所有本次核对的下载件 `Last-Modified` 仍为 `Wed, 10 Jun 2026 12:37:37/38 GMT`
   - 所有 `ETag` 与 `Content-Length` 均与 [official_docs/checks/2026-06-22_prod-2.27.0_xsd-3.0.30_recheck/report.md](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-22_prod-2.27.0_xsd-3.0.30_recheck/report.md) 和 [official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/report.md](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/report.md) 一致

## HTTP / 下载元数据

| 官方文件 | Last-Modified | ETag | Content-Length | 本次结论 |
| --- | --- | --- | ---: | --- |
| Technical documentation page | `Wed, 10 Jun 2026 12:37:37 GMT` | `"4630-653e5822f0640"` | 17968 | 页面仍是 `v2.27.0 / XSD 3.0.30` |
| Support technical documentation page | `Wed, 10 Jun 2026 12:37:37 GMT` | `"3475-653e5822f0640"` | 13429 | support 页事实未变 |
| XSD schemas.zip | `Wed, 10 Jun 2026 12:37:38 GMT` | `"209bd-653e5823e4880"` | 133565 | 与 2026-06-15/2026-06-22 基线一致 |
| EOs - XML samples.zip | `Wed, 10 Jun 2026 12:37:37 GMT` | `"fcd3-653e5822f0640"` | 64723 | 与 2026-06-15/2026-06-22 基线一致 |
| UDI Devices - data dictionary.xlsx | `Wed, 10 Jun 2026 12:37:38 GMT` | `"2263e-653e5823e4880"` | 140862 | 与 2026-06-15/2026-06-22 基线一致 |
| UDI Devices - business rules.pdf | `Wed, 10 Jun 2026 12:37:38 GMT` | `"c984a-653e5823e4880"` | 825418 | 与 2026-06-15/2026-06-22 基线一致 |
| UDI Devices - enumerations.pdf | `Wed, 10 Jun 2026 12:37:38 GMT` | `"11de6b1-653e5823e4880"` | 18736817 | 与 2026-06-15/2026-06-22 基线一致 |
| DTX for EOs - services definition.pdf | `Wed, 10 Jun 2026 12:37:37 GMT` | `"983668-653e5822f0640"` | 9975400 | 与 2026-06-15/2026-06-22 基线一致 |

## 本次留存目录

- 复检目录: [official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck)
- 证据 JSON: [official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/source_evidence.json](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/source_evidence.json)
- 原始 HEAD 响应目录: [official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/raw_headers](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/raw_headers)
- 原始官方页面 HTML: [official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/raw_pages](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/raw_pages)
- 复用校验和: [official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/official_files_checksums.sha256](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/official_files_checksums.sha256)
- 复用的 XSD zip 清单: [official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/xsd_zip_entries.txt](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/xsd_zip_entries.txt)
- 复用的 XSD 文件清单: [official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/xsd_file_manifest.tsv](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/xsd_file_manifest.tsv)
- 复用的 EO samples zip 清单: [official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/eo_samples_zip_entries.txt](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/eo_samples_zip_entries.txt)
- 复用的 EO samples 差异: [official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/eo_samples_diff.tsv](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-29_prod-2.27.0_xsd-3.0.30_recheck/eo_samples_diff.tsv)
- 复用原始下载快照: [official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30)

## 与上一版基线的比较

### 1. XSD schemas.zip

- 本次官方头信息与 `2026-06-15` 原始下载快照及 `2026-06-22` metadata-only 复检完全一致。
- 因此继续采用 `2026-06-15` 快照中的原始下载件:
  - [official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/downloads/XSD_schemas.zip](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-15_prod-2.27.0_xsd-3.0.30/downloads/XSD_schemas.zip)
  - SHA-256: `e3c7621a69340b1ad01d375994a6df6a131073626e2a4ae01048e0ffa04b1c3b`
- 已知该快照相对 `2026-06-08` 的证明仍有效:
  - XSD 文件新增: `0`
  - XSD 文件删除: `0`
  - XSD 文件修改: `0`
  - schema 结构、枚举、字段、约束均未发生变化

### 2. 相关配套资料

- `EOs - XML samples.zip`
- `UDI Devices - data dictionary.xlsx`
- `UDI Devices - business rules.pdf`
- `UDI Devices - enumerations.pdf`
- `DTX for EOs - services definition.pdf`

以上 5 个官方下载件本次头信息也全部与 `2026-06-15/2026-06-22` 基线一致，因此 `2026-06-10` 元数据重发后的那一批官方资料仍是当前最新状态，没有出现新的第二次更新。

## 对主转换工具的影响

### 当前不需要立刻修改

- [local_beta/constants.py](/Users/charles_fang/Documents/EUDAMED/local_beta/constants.py): `SCHEMA_VERSION = 3.0.30` 仍正确
- [local_beta/exporter.py](/Users/charles_fang/Documents/EUDAMED/local_beta/exporter.py): 无新的 XSD 结构变化触发 payload 调整
- [local_beta/template_schema.py](/Users/charles_fang/Documents/EUDAMED/local_beta/template_schema.py): 无新的 XSD 枚举或 requiredness 变化证据
- [local_beta/importer.py](/Users/charles_fang/Documents/EUDAMED/local_beta/importer.py): 无新的数据字典变化证据要求同步字段导入逻辑
- [EUDAMED_TOOL_v2/validator.py](/Users/charles_fang/Documents/EUDAMED/EUDAMED_TOOL_v2/validator.py): 无新的 schema 漂移要求更新校验基线

### 维护者仍应关注

1. 顶层 `official_docs/` 中的若干镜像文件仍旧落后于当前官方配套资料批次。  
   这不是 `2026-06-29` 新发生的变化，但仓库顶层镜像与当前官方原件之间的差异仍存在。
2. 如果要把顶层镜像提升到当前官方批次，应以 `2026-06-15` 已留存原件为基准。
3. 只有当未来官方再次改动页面版本文字、`Last-Modified`、`ETag` 或 `Content-Length` 时，才需要重新下载 XSD zip 并重新生成:
   - 文件清单
   - XSD 文件级增删改
   - schema 结构 / 枚举 / 字段 / 约束差异摘要

## 最终判定

截至 `2026-06-29T09:04:04+08:00`，EUDAMED 官方生产帮助页与官方直链下载件相对 `2026-06-15/2026-06-22` 没有任何可观测变化。对主转换工具维护而言，当前状态仍然是 `XSD 3.0.30 / platform 2.27.0，无需因 schema 本体而改 exporter / importer / validator / template / constants`；后续如要行动，重点仍是 `是否把仓库顶层 official_docs 配套镜像刷新到当前官方批次`。
