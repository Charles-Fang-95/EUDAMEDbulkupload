# EUDAMED 官方 XSD 双环境监控报告（2026-08-03）

- 检查时间：`2026-08-03T09:07:16+08:00`
- 判定来源：仅 EUDAMED / European Commission 官方帮助页及官方下载端点
- Production：[Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html)
- Production 交叉核验：[M2M support — Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/machine-to-machine/support/technical-documentation.html)
- Playground：[Technical documentation](https://webgate.ec.europa.eu/eudamed-play-help/en/documentation/technical-documentation.html)

## 结论

本次没有发现新的 XSD 版本、XSD 内容变化或六项维护相关伴随文件的内容变化。官方仍为双版本并存：

- Production：`XSD 3.0.30 / platform 2.27.0 / Publication date July 24, 2026`
- Playground：`XSD 3.0.32 / platform 3.31.2 / Publication date July 14, 2026`

Production 帮助页和文件端点发生了服务器元数据重发布：页面发布日期由 `May 18, 2026` 改为 `July 24, 2026`，页面与六项文件的 `Last-Modified` / `ETag` 均刷新。但下载后的六项二进制文件全部与 2026-06-15 Production 内容基线逐字节一致，XSD 文件级差异为 0。因此这是页面/HTTP 元数据更新，不是 schema 或伴随文件内容更新。

Playground 页面、HTTP 元数据及六项二进制文件均与 2026-07-27 基线一致。

另发现一个官方页面链接问题：当前帮助页 HTML 把 XSD 链接写为 `/en/documentation/XSD schemas.zip`；实测 Production 该 URL 返回 `404`。官方 `/en/files/XSD%20schemas.zip` 端点仍返回 `200`，本次使用该官方端点完成二进制核验。此项是官方帮助页下载链接可用性问题，不是本地工具 schema 漂移。

## HTTP 元数据

### Production（元数据刷新，内容未变）

| 资源 | Last-Modified | ETag | Content-Length |
|---|---|---:|---:|
| Technical documentation | Mon, 27 Jul 2026 08:51:58 GMT | `"467a-65793d5bce780"` | 18042 |
| M2M support technical documentation | Mon, 27 Jul 2026 08:51:58 GMT | `"3477-65793d5bce780"` | 13431 |
| XSD schemas.zip | Mon, 27 Jul 2026 08:51:59 GMT | `"209bd-65793d5cc29c0"` | 133565 |
| EOs - XML samples.zip | Mon, 27 Jul 2026 08:51:59 GMT | `"fcd3-65793d5cc29c0"` | 64723 |
| UDI Devices - data dictionary.xlsx | Mon, 27 Jul 2026 08:51:59 GMT | `"2263e-65793d5cc29c0"` | 140862 |
| UDI Devices - business rules.pdf | Mon, 27 Jul 2026 08:51:59 GMT | `"c984a-65793d5cc29c0"` | 825418 |
| UDI Devices - enumerations.pdf | Mon, 27 Jul 2026 08:51:59 GMT | `"11de6b1-65793d5cc29c0"` | 18736817 |
| DTX for EOs - services definition.pdf | Mon, 27 Jul 2026 08:51:58 GMT | `"983668-65793d5bce780"` | 9975400 |

### Playground（元数据未变）

| 资源 | Last-Modified | ETag | Content-Length |
|---|---|---:|---:|
| Technical documentation | Fri, 24 Jul 2026 15:25:08 GMT | `"51d9-6575cfa499d00"` | 20953 |
| XSD schemas.zip | Fri, 24 Jul 2026 15:25:09 GMT | `"20c04-6575cfa58df40"` | 134148 |
| EOs - XML samples.zip | Fri, 24 Jul 2026 15:25:08 GMT | `"102f7-6575cfa499d00"` | 66295 |
| UDI Devices - data dictionary.xlsx | Fri, 24 Jul 2026 15:25:08 GMT | `"24708-6575cfa499d00"` | 149256 |
| UDI Devices - business rules.pdf | Fri, 24 Jul 2026 15:25:08 GMT | `"b7cea-6575cfa499d00"` | 752874 |
| UDI Devices - enumerations.pdf | Fri, 24 Jul 2026 15:25:08 GMT | `"88509-6575cfa499d00"` | 558345 |
| DTX for EOs - services definition.pdf | Fri, 24 Jul 2026 15:25:08 GMT | `"e318d-6575cfa499d00"` | 930189 |

## 下载件、校验和与包清单

本次为两个环境分别下载并保留：`XSD_schemas.zip`、`EOs_XML_samples.zip`、UDI Devices data dictionary、business rules、enumerations、DTX for EOs services definition。

- Production XSD SHA-256：`e3c7621a69340b1ad01d375994a6df6a131073626e2a4ae01048e0ffa04b1c3b`
- Playground XSD SHA-256：`129f9143a146564c8f9e32fe32e2cdb8bf04dcc160421d3248edeee3c5885217`
- 两个 XSD ZIP 均为 `92` 个条目：24 个目录、67 个 XSD、1 个 sample XML
- Production 对上一内容基线：新增 `0`、删除 `0`、修改 `0`
- Playground 对 2026-07-27 基线：新增 `0`、删除 `0`、修改 `0`
- schema 结构、枚举、字段、约束变化：`无`
- 六项伴随文件内容变化：两个环境均为 `无`

完整 SHA-256、ZIP listing、解包文件 manifest、二进制比较和空的文件级 diff 均保存在本检查目录。

## 对主转换工具的影响

本次没有产生新的代码、映射、模板或校验调整点：

1. `local_beta/constants.py` 的全局 `SCHEMA_VERSION = "3.0.30"` 仍只与 Production 一致。
2. Production 仍要求 3.0.30，不能直接把全局版本改成 3.0.32。
3. Playground 仍要求 3.0.32；既有的环境感知缺口未消失，正确方向仍是显式选择目标环境，并按环境选择消息版本及 XSD 快照。
4. 本轮未发现 UDI/Device schema、枚举、字段或约束变化，不需要调整 importer、exporter、legacy validator 或 Excel 模板映射。
5. 官方页面当前 XSD href 返回 404；若工具或维护脚本将来从帮助页自动解析下载链接，应对 HTTP 状态做硬校验，并保留官方可用端点的证据，不应把 404 页面当作 ZIP。

本轮只新增官方资料监控证据，没有修改转换代码，因此未运行发布前 compile/test/template rebuild 流程。

## 留存文件

- `source_evidence.json`：来源、版本、元数据、链接状态和判定
- `raw_pages/`：Production、Production M2M support、Playground 官方页面快照
- `raw_headers/`：页面和文件端点的原始 HTTP 响应头
- `downloads/prod/`、`downloads/play/`：本次双环境 12 个官方原始下载件
- `production_official_files_checksums.sha256`、`playground_official_files_checksums.sha256`：SHA-256
- `prod_xsd_zip_listing.txt`、`play_xsd_zip_listing.txt`：ZIP 条目清单
- `prod_xsd_manifest.txt`、`play_xsd_manifest.txt`：解包文件校验清单
- `prod_xsd_file_level_diff.txt`、`play_xsd_file_level_diff.txt`：空文件表示无文件级差异
- `prod_binary_comparison.txt`、`play_binary_comparison.txt`：六项文件逐字节比较结论
- `normalized_header_comparison.txt`：与上一环境基线的规范化元数据比较
