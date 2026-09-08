# EUDAMED 官方 XSD 双环境监控报告（2026-09-07）

- 检查时间：`2026-09-07T09:03:56+08:00`
- 判定来源：仅 EUDAMED / European Commission 官方帮助页与官方下载端点
- Production：[Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html)
- Production 交叉核验：[M2M support — Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/machine-to-machine/support/technical-documentation.html)
- Playground：[Technical documentation](https://webgate.ec.europa.eu/eudamed-play-help/en/documentation/technical-documentation.html)

## 结论

本次没有发现 XSD 版本号、XSD 包内容或六项主工具维护资料的更新：

- Production：`XSD 3.0.30 / platform 2.27.0 / Publication date July 24, 2026`
- Playground：`XSD 3.0.32 / platform 3.31.2 / Publication date July 14, 2026`

三张官方页面正文与 2026-08-31 基线逐字节一致；两环境各六项 `/en/files/` 官方文件的 `Last-Modified`、`ETag`、`Content-Length` 和 `Content-Type` 也全部未变。因此按监控停止规则，本轮不重复下载大文件，复用既有校验和与 XSD manifest。这里的“包内容未变”依据是：当前 HTTP 三项元数据与页面正文均未漂移，加上此前对应环境已有实际下载、SHA-256 和解包 manifest 证据，并非只根据版本字符串推断。

## HTTP 与内容证据

- Production XSD：`Last-Modified: Thu, 27 Aug 2026 11:33:36 GMT`，`ETag: "2126e-65a05b4dd4400"`，`Content-Length: 135790`；复用 SHA-256 `22d098940ba72be23deb202b73759e8d1746b457393f3c90b560e19a4de16492`。
- Playground XSD：`Last-Modified: Fri, 24 Jul 2026 15:25:09 GMT`，`ETag: "20c04-6575cfa58df40"`，`Content-Length: 134148`；复用 SHA-256 `129f9143a146564c8f9e32fe32e2cdb8bf04dcc160421d3248edeee3c5885217`。
- Production XSD 包基线仍为 92 个条目：24 个目录、67 个 XSD、1 个 sample XML；新增 `0`、删除 `0`、修改 `0`。
- Playground XSD 包基线同为 92 个条目：24 个目录、67 个 XSD、1 个 sample XML；新增 `0`、删除 `0`、修改 `0`。
- 页面广告的 12 个 `/en/documentation/` 文件 URL 仍全部 HTTP 404；相应官方 `/en/files/` 端点全部 HTTP 200，且内容类型符合预期。两类响应均已留存。

六项资料为：`XSD schemas.zip`、`EOs - XML samples.zip`、`UDI Devices - data dictionary.xlsx`、`UDI Devices - business rules.pdf`、`UDI Devices - enumerations.pdf`、`DTX for EOs - services definition.pdf`。

## 对主转换工具的影响

1. `local_beta/constants.py` 的 `SCHEMA_VERSION = "3.0.30"` 对 Production 仍正确；Playground 继续是 3.0.32，不能全局切换。
2. 未发现 schema 结构、枚举、字段、约束、样例、业务规则、数据字典或服务定义变化；无需调整 exporter、importer、legacy validator、映射、模板或常量。
3. 现有维护事项不变：顶层 `official_docs/XSD_schemas.zip` 仍应在独立受审变更中刷新到 Production 2026-08-10 的同版本内容基线；本轮没有擅自覆盖。
4. 因官方内容和元数据均无漂移，本轮未运行 compile、单元测试或模板重建，也未修改工具代码。

## 留存文件

- `raw_pages/`：三张官方页面正文
- `raw_headers/`：页面 GET headers、广告链接 404 与 `/en/files/` 200 响应
- `normalized_header_comparison.txt`：与 2026-08-31 的白名单字段比较
- `production_official_files_checksums_reused_2026-08-31.sha256`、`playground_official_files_checksums_reused_2026-08-03.sha256`：复用校验和
- `prod_xsd_manifest_reused_2026-08-31.txt`、`play_xsd_manifest_reused_2026-08-03.txt`：复用解包清单
- `source_evidence.json`：结构化判定依据
