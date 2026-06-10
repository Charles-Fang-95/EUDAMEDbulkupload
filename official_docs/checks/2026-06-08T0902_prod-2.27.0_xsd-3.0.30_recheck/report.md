# EUDAMED 官方 XSD / 技术资料复检报告

- 检查日期: `2026-06-08`
- 本地生成时间: `2026-06-08T17:03:37+08:00`
- 判定范围: `仅使用 EUDAMED / European Commission 官方生产环境帮助页与官方下载 URL`
- 本地工具基线: `local_beta/constants.py -> SCHEMA_VERSION = 3.0.30`
- 复检目标: `确认 2026-06-08 稍早官方快照之后，生产帮助页或直链下载件是否又发生变化`
- 结论:
  - `未发现新的生产 XSD 版本；官方仍声明 XSD v3.0.30 对应平台 v2.27.0`
  - `未发现同日内新的 HTTP 元数据漂移；本次实时抓到的 Last-Modified / ETag / Content-Length 与 2026-06-08 稍早快照完全一致`
  - `因此无需重新下载或重解包 XSD；沿用 2026-06-08 稍早下载快照即可作为当前官方原始件基线`

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
   - 本次 HEAD 采集时间集中在 `2026-06-08 09:02 GMT`
   - 所有本次核对的下载件 `Last-Modified` 仍为 `Tue, 26 May 2026 12:19:44 GMT`
   - 所有 `ETag` 与 `Content-Length` 均与 [2026-06-08 首次巡检快照](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30/report.md) 一致

## HTTP / 下载元数据

| 官方文件 | Last-Modified | ETag | Content-Length | 本次结论 |
| --- | --- | --- | ---: | --- |
| Technical documentation page | `Tue, 26 May 2026 12:19:44 GMT` | `"4630-652b7829bb800"` | 17968 | 页面仍是 `v2.27.0 / XSD 3.0.30` |
| XSD schemas.zip | `Tue, 26 May 2026 12:19:44 GMT` | `"209bd-652b7829bb800"` | 133565 | 与同日稍早下载快照一致 |
| EOs - XML samples.zip | `Tue, 26 May 2026 12:19:44 GMT` | `"fcd3-652b7829bb800"` | 64723 | 与同日稍早下载快照一致 |
| UDI Devices - data dictionary.xlsx | `Tue, 26 May 2026 12:19:44 GMT` | `"2263e-652b7829bb800"` | 140862 | 与同日稍早下载快照一致 |
| UDI Devices - business rules.pdf | `Tue, 26 May 2026 12:19:44 GMT` | `"c984a-652b7829bb800"` | 825418 | 与同日稍早下载快照一致 |
| UDI Devices - enumerations.pdf | `Tue, 26 May 2026 12:19:44 GMT` | `"11de6b1-652b7829bb800"` | 18736817 | 与同日稍早下载快照一致 |
| DTX for EOs - services definition.pdf | `Tue, 26 May 2026 12:19:44 GMT` | `"983668-652b7829bb800"` | 9975400 | 与同日稍早下载快照一致 |

## 本次留存目录

- 复检目录: [official_docs/checks/2026-06-08T0902_prod-2.27.0_xsd-3.0.30_recheck](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08T0902_prod-2.27.0_xsd-3.0.30_recheck)
- 证据 JSON: [source_evidence.json](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08T0902_prod-2.27.0_xsd-3.0.30_recheck/source_evidence.json)
- 校验和: [official_files_checksums.sha256](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08T0902_prod-2.27.0_xsd-3.0.30_recheck/official_files_checksums.sha256)
- 复用的 XSD zip 清单: [xsd_zip_entries.txt](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08T0902_prod-2.27.0_xsd-3.0.30_recheck/xsd_zip_entries.txt)
- 复用的 XSD 文件清单: [xsd_file_manifest.tsv](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08T0902_prod-2.27.0_xsd-3.0.30_recheck/xsd_file_manifest.tsv)
- 复用的 EO samples zip 清单: [eo_samples_zip_entries.txt](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08T0902_prod-2.27.0_xsd-3.0.30_recheck/eo_samples_zip_entries.txt)
- 复用的 EO samples 差异: [eo_samples_diff.tsv](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08T0902_prod-2.27.0_xsd-3.0.30_recheck/eo_samples_diff.tsv)
- 同日首次下载快照: [official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30)

## 与同日首次快照的比较

### 1. XSD schemas.zip

- 本次官方头信息与 `2026-06-08` 首次快照完全一致
- 因此继续采用首次快照中的原始下载件:
  - [downloads/XSD_schemas.zip](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30/downloads/XSD_schemas.zip)
  - SHA-256: `e3c7621a69340b1ad01d375994a6df6a131073626e2a4ae01048e0ffa04b1c3b`
- 该首次快照已经证明:
  - XSD 文件新增: `0`
  - XSD 文件删除: `0`
  - XSD 文件修改: `0`
  - schema 版本、字段、枚举、约束均未较本地 `3.0.30` 基线发生变化

### 2. 相关配套资料

- `EOs - XML samples.zip`
- `UDI Devices - data dictionary.xlsx`
- `UDI Devices - business rules.pdf`
- `UDI Devices - enumerations.pdf`
- `DTX for EOs - services definition.pdf`

以上 5 个官方下载件本次头信息也全部与同日首次快照一致，因此 `2026-05-26` 那批生产版资料仍是当前最新官方状态，没有出现新的第二次更新。

## 对主转换工具的影响

### 当前不需要立刻修改

- [local_beta/constants.py](/Users/charles_fang/Documents/EUDAMED/local_beta/constants.py): `SCHEMA_VERSION = 3.0.30` 仍正确
- [local_beta/exporter.py](/Users/charles_fang/Documents/EUDAMED/local_beta/exporter.py): 无新的 XSD 结构变化触发 payload 调整
- [local_beta/template_schema.py](/Users/charles_fang/Documents/EUDAMED/local_beta/template_schema.py): 无新的 XSD 枚举/约束变化证据
- [official_docs/unpacked/xsd_production](/Users/charles_fang/Documents/EUDAMED/official_docs/unpacked/xsd_production): 仍可继续作为本地 XSD 基线

### 仍值得维护者关注

1. 顶层 `official_docs/` 中的若干镜像文件仍旧落后于官方 `2026-05-26` 生产版批次。  
   这不是“今天刚发生的新变化”，但仍是当前仓库与官方资料之间的基线差异。
2. 如果要把顶层镜像提升到现行生产版，应参考同日首次快照中的已下载原件，而不是重新猜测 URL 内容。
3. 如果未来官方再次改动 `Last-Modified`、`ETag` 或 `Content-Length`，应重新下载 XSD zip，并重新生成:
   - 文件清单
   - XSD 文件级增删改
   - schema 结构/枚举/字段/约束差异摘要

## 最终判定

截至 `2026-06-08T17:03:37+08:00`，EUDAMED 官方生产帮助页与官方直链下载件没有比 `2026-06-08` 稍早快照更新得更晚的内容。对主转换工具维护而言，当前状态仍然是 `XSD 3.0.30 / platform 2.27.0，无需因 schema 本体而改码`；后续如要行动，重点仍是 `是否把 2026-05-26 那批配套官方资料提升为仓库顶层镜像基线`。
