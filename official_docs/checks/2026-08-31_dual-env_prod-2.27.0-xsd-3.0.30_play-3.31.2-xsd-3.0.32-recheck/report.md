# EUDAMED 官方 XSD 双环境监控报告（2026-08-31）

- 检查时间：`2026-08-31T09:08:32+08:00`
- 判定来源：仅 EUDAMED / European Commission 官方帮助页与官方下载端点
- Production：[Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html)
- Production 交叉核验：[M2M support — Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/machine-to-machine/support/technical-documentation.html)
- Playground：[Technical documentation](https://webgate.ec.europa.eu/eudamed-play-help/en/documentation/technical-documentation.html)

## 结论

本次没有发现 XSD 版本号、XSD 包内容或六项主工具维护资料的内容更新：

- Production：`XSD 3.0.30 / platform 2.27.0 / Publication date July 24, 2026`
- Playground：`XSD 3.0.32 / platform 3.31.2 / Publication date July 14, 2026`

Production 在 2026-08-27 发生了整批 HTTP 元数据刷新：两张页面及六项 `/en/files/` 文件的 `Last-Modified` 和 `ETag` 改变，但页面正文与 2026-08-24 逐字节一致。为排除同版本内容更新，本次重新下载全部六项 Production 文件；完整下载后的大小和 SHA-256 均与既有内容基线一致。因此这是元数据重发布，不是 schema 或配套资料内容变化。

Playground 页面正文及六项文件的 `Last-Modified`、`ETag`、`Content-Length` 均未变化，按停止规则复用 2026-08-03 的校验和与 manifest。

## Production 下载与内容比较

| 文件 | 2026-08-31 SHA-256 | 内容判定 |
|---|---|---|
| `XSD_schemas.zip` | `22d098940ba72be23deb202b73759e8d1746b457393f3c90b560e19a4de16492` | 与 2026-08-10 基线相同 |
| `EOs_XML_samples.zip` | `583d92b7ba59df6d4d66116cfc868fe9fe21d2abc14100d8a7ba6ce3663b7bf5` | 相同 |
| `UDI_Devices_data_dictionary.xlsx` | `480a170ba563712a54c6858400fb5b0b55c11e88e66de0e9fc9f54d5d9e2e6b1` | 相同 |
| `UDI_Devices_business_rules.pdf` | `b836cd8c8a32690244335eb6a1a38136ff77aa7149077906c79ffd9c062b39a3` | 相同 |
| `UDI_Devices_enumerations.pdf` | `e3a6a544fb3c404a208e87b13aeacdacb0e3c106d57d6b19653a3a742e23170b` | 相同 |
| `DTX_for_EOs_services_definition.pdf` | `3ba4058f14827e856d4c2d1600e8d655c93f7160350ed52c4c67e16ef6491257` | 相同；PDF 提取文本 diff 为空 |

Production XSD ZIP 仍为 92 个条目：24 个目录、67 个 XSD、1 个 sample XML。相对 2026-08-10 内容基线，XSD 文件新增 `0`、删除 `0`、修改 `0`；解包 manifest diff 为空。

## HTTP 元数据摘要

Production 页面为 `Last-Modified: Thu, 27 Aug 2026 11:33:35 GMT`；XSD 为 `Thu, 27 Aug 2026 11:33:36 GMT / ETag "2126e-65a05b4dd4400" / Content-Length 135790`。其余五项的完整值见 `normalized_header_comparison.txt` 与原始 headers。

Playground 页面仍为 `Fri, 24 Jul 2026 15:25:08 GMT / ETag "51d9-6575cfa499d00"`；XSD 仍为 `Fri, 24 Jul 2026 15:25:09 GMT / ETag "20c04-6575cfa58df40" / Content-Length 134148`。

两环境页面广告的 12 个 `/en/documentation/` 文件 URL 仍全部返回 HTTP 404；对应 EC 官方 `/en/files/` 端点全部返回 HTTP 200 和预期内容类型。两类响应均已分别留存。

## 对主转换工具的影响

1. `local_beta/constants.py` 的 `SCHEMA_VERSION = "3.0.30"` 对 Production 仍正确；不能因 Playground 为 3.0.32 而全局切换。
2. 未发现 schema 结构、枚举、字段、约束、样例、业务规则、数据字典或服务定义内容变化；无需调整 exporter、importer、legacy validator、映射、模板或常量。
3. 现有维护事项不变：应在独立受审变更中确认打包的 Production XSD 已刷新到 2026-08-10 同版本内容基线，同时保持环境区分。
4. 因所有下载二进制与页面正文均未漂移，本轮未运行 compile、单元测试或模板重建；未修改主工具代码，也未覆盖工作区已有文件。

## 留存文件

- `downloads/production/`：本轮重新下载的六项 Production 官方原件
- `unpacked/production_xsd/`：Production XSD 解包快照
- `raw_pages/`、`raw_headers/`：三张官方页面、广告 404 与官方 `/files/` 200 响应证据
- `production_official_files_checksums_2026-08-31.sha256`：本轮完整下载校验和
- `prod_xsd_zip_listing_2026-08-31.txt`、`prod_xsd_manifest_2026-08-31.txt`：包清单与解包 manifest
- `analysis/`：XSD manifest diff、服务定义 PDF 信息与文本比较
- `source_evidence.json`、`normalized_header_comparison.txt`：结构化判定与基线比较
