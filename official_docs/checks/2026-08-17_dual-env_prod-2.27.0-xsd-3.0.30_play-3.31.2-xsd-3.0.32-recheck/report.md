# EUDAMED 官方 XSD 双环境监控报告（2026-08-17）

- 检查时间：`2026-08-17T09:02:33+08:00`
- 判定来源：仅 EUDAMED / European Commission 官方帮助页与官方下载端点
- Production：[Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html)
- Production 交叉核验：[M2M support — Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/machine-to-machine/support/technical-documentation.html)
- Playground：[Technical documentation](https://webgate.ec.europa.eu/eudamed-play-help/en/documentation/technical-documentation.html)

## 结论

本次未发现官方 XSD 版本号、XSD 包内容或相关六项维护资料发生更新：

- Production：`XSD 3.0.30 / platform 2.27.0 / Publication date July 24, 2026`
- Playground：`XSD 3.0.32 / platform 3.31.2 / Publication date July 14, 2026`

三张官方页面与 2026-08-10 快照逐字节一致。两环境各六项官方 `/en/files/` 资源的 `Last-Modified`、`ETag`、`Content-Length` 全部与上一基线一致，因此按元数据停止规则复用已校验的原包、SHA-256、ZIP 清单和解包 manifest，没有重复下载大文件。

这次“无更新”结论不是只看版本号得出：Production 复用的是 2026-08-10 同版本内容更新后的 XSD 基线，SHA-256 `22d098940ba72be23deb202b73759e8d1746b457393f3c90b560e19a4de16492`；Playground 复用的 XSD SHA-256 为 `129f9143a146564c8f9e32fe32e2cdb8bf04dcc160421d3248edeee3c5885217`。

## HTTP 元数据证据

### Production

| 资源 | Last-Modified | ETag | Content-Length |
|---|---|---:|---:|
| Technical documentation | Tue, 04 Aug 2026 15:03:48 GMT | `"467a-65839f63f7d00"` | 18042 |
| XSD schemas.zip | Tue, 04 Aug 2026 15:03:49 GMT | `"2126e-65839f64ebf40"` | 135790 |
| EOs - XML samples.zip | Tue, 04 Aug 2026 15:03:49 GMT | `"fcd3-65839f64ebf40"` | 64723 |
| UDI Devices - data dictionary.xlsx | Tue, 04 Aug 2026 15:03:49 GMT | `"2263e-65839f64ebf40"` | 140862 |
| UDI Devices - business rules.pdf | Tue, 04 Aug 2026 15:03:49 GMT | `"c984a-65839f64ebf40"` | 825418 |
| UDI Devices - enumerations.pdf | Tue, 04 Aug 2026 15:03:49 GMT | `"11de6b1-65839f64ebf40"` | 18736817 |
| DTX for EOs - services definition.pdf | Tue, 04 Aug 2026 15:03:49 GMT | `"983668-65839f64ebf40"` | 9975400 |

### Playground

| 资源 | Last-Modified | ETag | Content-Length |
|---|---|---:|---:|
| Technical documentation | Fri, 24 Jul 2026 15:25:08 GMT | `"51d9-6575cfa499d00"` | 20953 |
| XSD schemas.zip | Fri, 24 Jul 2026 15:25:09 GMT | `"20c04-6575cfa58df40"` | 134148 |
| EOs - XML samples.zip | Fri, 24 Jul 2026 15:25:08 GMT | `"102f7-6575cfa499d00"` | 66295 |
| UDI Devices - data dictionary.xlsx | Fri, 24 Jul 2026 15:25:08 GMT | `"24708-6575cfa499d00"` | 149256 |
| UDI Devices - business rules.pdf | Fri, 24 Jul 2026 15:25:08 GMT | `"b7cea-6575cfa499d00"` | 752874 |
| UDI Devices - enumerations.pdf | Fri, 24 Jul 2026 15:25:08 GMT | `"88509-6575cfa499d00"` | 558345 |
| DTX for EOs - services definition.pdf | Fri, 24 Jul 2026 15:25:08 GMT | `"e318d-6575cfa499d00"` | 930189 |

## 链接状态与包清单

两环境页面目前仍把上述六项文件链接写在 `/en/documentation/` 下，本次 12 个页面广告链接实测均为 HTTP 404。对应的 EC 官方 `/en/files/` 端点均为 HTTP 200，并返回预期的 ZIP、Excel 或 PDF 类型。报告分别保存两类响应头，没有静默替换来源状态。

复用的 XSD 包清单（两环境各自）：92 个 ZIP 条目 = 24 个目录 + 67 个 XSD + 1 个 sample XML。相对各自上一内容基线，本轮新增 `0`、删除 `0`、修改 `0`。

## 对主转换工具的影响

1. `local_beta/constants.py` 的 `SCHEMA_VERSION = "3.0.30"` 对 Production 仍正确；不要全局改成 Playground 的 3.0.32。
2. 本轮没有发现需要调整 exporter、importer、legacy validator、字段映射、枚举、模板或业务校验的官方变化。
3. 8 月 10 日已确认的 Production 3.0.30 同版本内容更新仍是当前基线；建议的独立维护事项仍是把打包的 Production XSD 快照刷新到该内容，而不是修改版本号。
4. 因所有漂移检测字段均未变化，本轮未运行 compile、单元测试或模板重建；这不是发布验证，也没有覆盖当前 dirty worktree 的任何用户改动。

## 留存文件

- `raw_pages/`：三张官方帮助页快照
- `raw_headers/`：页面、12 个广告 404 链接、12 个官方 `/files/` 端点响应头
- `source_evidence.json`：环境化版本、元数据、URL 状态和判定
- `normalized_header_comparison.txt`：与上一基线的规范化字段比较
- `production_official_files_checksums_reused_2026-08-10.sha256`：Production 原包校验和
- `playground_official_files_checksums_reused_2026-08-03.sha256`：Playground 原包校验和
- `*_xsd_manifest_reused_*.txt` / `*_xsd_zip_listing_reused_*.txt`：复用的包清单和文件 manifest
