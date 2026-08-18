# EUDAMED 官方 XSD 双环境监控报告（2026-07-27）

- 检查时间：`2026-07-27T09:05:17+08:00`
- 判定来源：仅 EUDAMED / European Commission 官方帮助页和官方下载端点
- Production：[Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html)
- Playground：[Technical documentation](https://webgate.ec.europa.eu/eudamed-play-help/en/documentation/technical-documentation.html)

## 结论

本次没有发现新的 XSD 内容版本或文件内容变化。官方仍为双版本并存：

- Production：`XSD 3.0.30 / platform 2.27.0 / Publication date May 18, 2026`
- Playground：`XSD 3.0.32 / platform 3.31.2 / Publication date July 14, 2026`

Production 页面和六个维护相关文件的 `Last-Modified`、`ETag`、`Content-Length` 均与 2026-07-20 基线一致。

Playground 页面和六个文件在 2026-07-24 整体刷新了 `Last-Modified` 和 `ETag`，但文件长度未变。为排除内容变化，本次重新下载全部六个文件；六个新下载件均与 2026-07-23 快照逐字节一致，SHA-256 全部一致。因此这是官方服务器元数据重发布，不是 schema、samples、data dictionary、business rules、enumerations 或 services definition 的内容更新。

## HTTP 元数据

### Production（未变化）

| 资源 | Last-Modified | ETag | Content-Length |
|---|---|---:|---:|
| Technical documentation | Wed, 10 Jun 2026 12:37:37 GMT | `"4630-653e5822f0640"` | 17968 |
| XSD schemas.zip | Wed, 10 Jun 2026 12:37:38 GMT | `"209bd-653e5823e4880"` | 133565 |
| EOs - XML samples.zip | Wed, 10 Jun 2026 12:37:37 GMT | `"fcd3-653e5822f0640"` | 64723 |
| UDI Devices - data dictionary.xlsx | Wed, 10 Jun 2026 12:37:38 GMT | `"2263e-653e5823e4880"` | 140862 |
| UDI Devices - business rules.pdf | Wed, 10 Jun 2026 12:37:38 GMT | `"c984a-653e5823e4880"` | 825418 |
| UDI Devices - enumerations.pdf | Wed, 10 Jun 2026 12:37:38 GMT | `"11de6b1-653e5823e4880"` | 18736817 |
| DTX for EOs - services definition.pdf | Wed, 10 Jun 2026 12:37:37 GMT | `"983668-653e5822f0640"` | 9975400 |

### Playground（元数据刷新，内容未变化）

| 资源 | 2026-07-23 Last-Modified | 2026-07-27 Last-Modified | 当前 ETag | Content-Length |
|---|---|---|---:|---:|
| Technical documentation | Thu, 16 Jul 2026 09:26:40 GMT | Fri, 24 Jul 2026 15:25:08 GMT | `"51d9-6575cfa499d00"` | 20953 |
| XSD schemas.zip | Thu, 16 Jul 2026 09:26:41 GMT | Fri, 24 Jul 2026 15:25:09 GMT | `"20c04-6575cfa58df40"` | 134148 |
| EOs - XML samples.zip | Thu, 16 Jul 2026 09:26:41 GMT | Fri, 24 Jul 2026 15:25:08 GMT | `"102f7-6575cfa499d00"` | 66295 |
| UDI Devices - data dictionary.xlsx | Thu, 16 Jul 2026 09:26:41 GMT | Fri, 24 Jul 2026 15:25:08 GMT | `"24708-6575cfa499d00"` | 149256 |
| UDI Devices - business rules.pdf | Thu, 16 Jul 2026 09:26:41 GMT | Fri, 24 Jul 2026 15:25:08 GMT | `"b7cea-6575cfa499d00"` | 752874 |
| UDI Devices - enumerations.pdf | Thu, 16 Jul 2026 09:26:41 GMT | Fri, 24 Jul 2026 15:25:08 GMT | `"88509-6575cfa499d00"` | 558345 |
| DTX for EOs - services definition.pdf | Thu, 16 Jul 2026 09:26:41 GMT | Fri, 24 Jul 2026 15:25:08 GMT | `"e318d-6575cfa499d00"` | 930189 |

## 下载件与校验

本次重新下载并保留：

- `XSD_schemas.zip`
- `EOs_XML_samples.zip`
- `UDI_Devices_data_dictionary.xlsx`
- `UDI_Devices_business_rules.pdf`
- `UDI_Devices_enumerations.pdf`
- `DTX_for_EOs_services_definition.pdf`

当前 SHA-256：

| 文件 | SHA-256 |
|---|---|
| XSD_schemas.zip | `129f9143a146564c8f9e32fe32e2cdb8bf04dcc160421d3248edeee3c5885217` |
| EOs_XML_samples.zip | `f2c36141283141a089cfff23611f57fe35d77a3477029158e75cf662d8161dcf` |
| UDI_Devices_data_dictionary.xlsx | `87885f08e3762a4aabf853a3f15ea6e64d1414b78b757f7995fdf45802458a95` |
| UDI_Devices_business_rules.pdf | `8b5bf94d15ebd7b4ad5bb6f10b86975f342e2e0fbea3700a83e144d52f2a3d27` |
| UDI_Devices_enumerations.pdf | `1dc2f9150184746e657c77a8d29be9c147dd4022599cbeb722d7d7712161d0f7` |
| DTX_for_EOs_services_definition.pdf | `3b27f4afdd8f52a1fc3956fab3344a3ac38403336cd1ae2ab4890a7ba187bef5` |

这些值全部与 `2026-07-23_play-3.31.2_xsd-3.0.32` 基线一致。

## XSD 文件级与结构级比较

- Playground XSD ZIP：与 2026-07-23 官方快照二进制一致
- ZIP 条目数：`92`（24 个目录、67 个 XSD、1 个示例 XML）
- XSD 文件数：`67`
- 新增 XSD：`0`
- 删除 XSD：`0`
- 修改 XSD：`0`
- 未修改 XSD：`67`
- schema 结构、枚举、字段、约束变化：`无`

3.0.30 → 3.0.32 的既有差异仍保持 2026-07-23 的实质结论：两个 ZIP 均有 68 个非目录文件（67 个 XSD、1 个示例 XML），新增 0、删除 0、修改 9；Device/UDI schema 未变，消息固定版本由 3.0.30 变为 3.0.32，其他变化位于 Actor、Certificate、SSCP、Vigilance 范围。此前报告把 68 个非目录文件简称为“68 个 XSD”，本报告纠正该计数口径。

## 对主转换工具的影响

本次元数据刷新不产生新的代码、映射、模板或校验调整点。现有维护缺口仍未消失：

1. `local_beta/constants.py` 仍只有全局 `SCHEMA_VERSION = "3.0.30"`。
2. Production 仍要求 3.0.30，不能直接把全局值覆盖成 3.0.32。
3. Playground 已要求 3.0.32；正确方向仍是显式区分目标环境，并按环境选择消息版本和 XSD 快照。
4. 在环境感知改造完成前，主工具导出的 3.0.30 XML 不能被描述为符合当前 Playground XSD 版本。
5. 后续改造应分别对 Production 3.0.30 与 Playground 3.0.32 smoke-test `DEVICE.POST` 和至少一个 update service。

本轮没有修改转换代码，因此未运行发布前 compile/test/template rebuild 流程。

## 留存文件

- `source_evidence.json`：来源、版本、元数据和判定
- `raw_headers/`：Production 与 Playground 原始 HEAD 响应
- `raw_pages/`：两套官方 Technical documentation 页面
- `downloads/play/`：2026-07-27 Playground 六个官方原始下载件
- `playground_official_files_checksums.sha256`：当前下载件校验和
- `playground_checksum_comparison.diff`：与 2026-07-23 的规范化校验和比较（空文件表示无差异）
- `playground_xsd_zip_listing.txt`、`playground_xsd_manifest.txt`：XSD 包清单
- `playground_eo_samples_zip_listing.txt`、`playground_eo_samples_manifest.txt`：EO samples 包清单
- `xsd_3.0.30_to_3.0.32_file_changes_baseline.txt`：既有版本差异基线
