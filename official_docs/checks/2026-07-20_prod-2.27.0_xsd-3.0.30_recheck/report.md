# EUDAMED 官方 XSD / 技术资料复检报告

> **2026-07-23 更正：** 本报告只证明 Production 帮助页当日仍为 XSD 3.0.30；它错误地把该结果表述成整个 EUDAMED 官方范围“未更新”。Playground 官方帮助页已于 2026-07-14 发布 XSD 3.0.32 / platform 3.31.2。详见 [2026-07-23 Playground 3.0.32 检查报告](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-07-23_play-3.31.2_xsd-3.0.32/report.md)。

- 检查日期：`2026-07-20`
- 本地生成时间：`2026-07-20T09:03:23+08:00`
- 判定范围：仅使用 EUDAMED / European Commission 官方生产帮助页与官方下载 URL
- 本地基线：`SCHEMA_VERSION = 3.0.30`、`TEMPLATE_VERSION = v2.10`、`TOOL_VERSION = 0.9.6`

## 结论

未发现官方 XSD 或相关技术资料更新。官方页面仍声明 `XSD v3.0.30` 对应平台 `v2.27.0`，发布日期仍为 `May 18, 2026`，页脚仍为 `European Commission-v.2.27.0`。两张页面与 2026-07-13 留存 HTML 逐字节一致；8 个受监控对象的 `Last-Modified / ETag / Content-Length` 也全部一致，原始 HEAD 仅响应 `Date` 改变。

因此本次按元数据停止规则复用 2026-06-15 已下载、已校验的官方原始件，不重复下载或解包。

## 官方来源

1. [Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html)
2. [M2M support — Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/machine-to-machine/support/technical-documentation.html)
3. 上述页面指向的官方 XSD、EO samples、UDI data dictionary、business rules、enumerations、EO services definition 下载件。

## HTTP 元数据

| 对象 | Last-Modified | ETag | Content-Length | 与 2026-07-13 比较 |
| --- | --- | --- | ---: | --- |
| Technical documentation page | `Wed, 10 Jun 2026 12:37:37 GMT` | `\"4630-653e5822f0640\"` | 17968 | 一致 |
| Support page | `Wed, 10 Jun 2026 12:37:37 GMT` | `\"3475-653e5822f0640\"` | 13429 | 一致 |
| XSD schemas.zip | `Wed, 10 Jun 2026 12:37:38 GMT` | `\"209bd-653e5823e4880\"` | 133565 | 一致 |
| EOs - XML samples.zip | `Wed, 10 Jun 2026 12:37:37 GMT` | `\"fcd3-653e5822f0640\"` | 64723 | 一致 |
| UDI Devices - data dictionary.xlsx | `Wed, 10 Jun 2026 12:37:38 GMT` | `\"2263e-653e5823e4880\"` | 140862 | 一致 |
| UDI Devices - business rules.pdf | `Wed, 10 Jun 2026 12:37:38 GMT` | `\"c984a-653e5823e4880\"` | 825418 | 一致 |
| UDI Devices - enumerations.pdf | `Wed, 10 Jun 2026 12:37:38 GMT` | `\"11de6b1-653e5823e4880\"` | 18736817 | 一致 |
| DTX for EOs - services definition.pdf | `Wed, 10 Jun 2026 12:37:37 GMT` | `\"983668-653e5822f0640\"` | 9975400 | 一致 |

## XSD 与配套资料比较

- 官方 XSD zip 元数据与 2026-06-15 原始快照一致；该快照 SHA-256 为 `e3c7621a69340b1ad01d375994a6df6a131073626e2a4ae01048e0ffa04b1c3b`。
- 沿用已验证的文件级结论：新增 `0`、删除 `0`、修改 `0`。
- schema 结构、枚举、字段及约束：没有新变化证据。
- EO samples、data dictionary、business rules、enumerations、services definition：HTTP 三元组均无变化，因此没有触发二进制或内容层复检。

## 对主转换工具的影响

- `local_beta/constants.py`：`SCHEMA_VERSION = 3.0.30` 仍正确。
- exporter / importer / validator / template_schema：没有 XSD 结构、字段、枚举或约束变化要求修改。
- 本次未修改代码，因此无需运行编译、单元测试或重建模板。
- 既有维护项仍在：顶层 `official_docs/` 的部分配套镜像比 2026-06-15 当前官方快照旧；这不是本次新变化。

## 留存证据

- `raw_headers/`：8 个官方对象的原始 HEAD 响应。
- `raw_pages/`：两张官方页面 HTML。
- `normalized_header_comparison.txt`：排除响应 `Date` 后的字段白名单比较。
- `source_evidence.json`：结构化来源、元数据、比较和影响结论。
- `official_files_checksums.sha256`、`xsd_zip_entries.txt`、`xsd_file_manifest.tsv`、`eo_samples_zip_entries.txt`、`eo_samples_diff.tsv`：从最近已验证基线复制的校验和与清单。

最终判定：截至 `2026-07-20T09:03:23+08:00`，EUDAMED 官方生产技术文档相对 2026-07-13 无可观测变化，主转换工具无需因官方 schema 漂移做代码、映射、模板或校验更新。
