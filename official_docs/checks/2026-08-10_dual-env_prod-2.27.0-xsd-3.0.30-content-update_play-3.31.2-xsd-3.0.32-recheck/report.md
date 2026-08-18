# EUDAMED 官方 XSD 双环境监控报告（2026-08-10）

- 检查时间：`2026-08-10T09:07:09+08:00`
- 判定来源：仅 EUDAMED / European Commission 官方帮助页及官方下载端点
- Production：[Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html)
- Production 交叉核验：[M2M support — Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/machine-to-machine/support/technical-documentation.html)
- Playground：[Technical documentation](https://webgate.ec.europa.eu/eudamed-play-help/en/documentation/technical-documentation.html)

## 结论

本次**没有出现新的版本号**，官方仍为双版本并存：

- Production：`XSD 3.0.30 / platform 2.27.0 / Publication date July 24, 2026`
- Playground：`XSD 3.0.32 / platform 3.31.2 / Publication date July 14, 2026`

但 Production 官方 XSD ZIP 在版本号仍为 `3.0.30` 的情况下发生了**实质内容更新**。新包 SHA-256 为 `22d098940ba72be23deb202b73759e8d1746b457393f3c90b560e19a4de16492`，与 2026-08-03 基线不同；67 个 XSD 中新增 `0`、删除 `0`、修改 `4`。因此本轮不能归类为单纯 HTTP 元数据重发布。

Production 其余五项维护资料虽然 Last-Modified / ETag 同步刷新，但下载后二进制均与 2026-08-03 基线一致。Playground 页面、版本文字和 HTTP 元数据均未变化，复用 2026-08-03 的已校验原包证据。

## Production XSD 文件级变化

| 文件 | 官方变化 | 对主转换工具的判断 |
|---|---|---|
| `data/Entity/Certificate/RefusedCertificateType.xsd` | `NBActorCode` 类型由 `stringNBActorCodeType` 改为 `stringSRNType` | 当前主工具不导出拒绝证书实体；无直接影响。若以后支持该服务，应按完整 SRN 类型处理。 |
| `data/Entity/Device/RegulationDevice/UDIDIType.xsd` | `numberOfReuses` 注释由“未定义时用 -1”改为“未定义时用 1” | 只改了 `xs:documentation`，没有改 XML 类型或数值约束。当前 exporter/validator 对正数重用次数的逻辑仍能通过新 XSD，但业务含义应结合后续 business rules/Playground 再确认，不能仅凭注释把 `1` 自动解释成“不适用”。 |
| `service/Message/MessageType.xsd` | `conversationID`、`correlationID`、`messageID` 由内联 `xs:string + maxLength 255` 简化为无长度上限的 `xs:string` | 约束放宽；当前工具输出 UUID，不受影响。消息固定版本仍为 `3.0.30`，payload 上限仍为 `300`。 |
| `service/Service/ServiceType.xsd` | UDI 搜索条件新增四个可选 dateTime 字段与可选 `SearchId` | 影响查询/分页型 M2M 服务能力，不影响当前六类 POST/PATCH bulk-upload 导出。若未来实现搜索服务，应新增字段映射、日期时间序列化和跨页 SearchId 保持。 |

新增的可选搜索字段是：

- `BasicUDIVersionDateTimeFrom` / `BasicUDIVersionDateTimeTo`（`xs:dateTime`）
- `UDIDIVersionDateTimeFrom` / `UDIDIVersionDateTimeTo`（`xs:dateTime`）
- `SearchId`（可选字符串，`maxLength=255`，用于翻页时保持同一搜索条件下的数据一致性）

没有发现枚举新增/删除，也没有发现当前 Device/UDI POST/PATCH payload 结构或 `maxOccurs=300` 改变。

## HTTP 与下载证据

### Production

| 资源 | Last-Modified | ETag | Content-Length | 与基线内容 |
|---|---|---:|---:|---|
| Technical documentation | Tue, 04 Aug 2026 15:03:48 GMT | `"467a-65839f63f7d00"` | 18042 | 页面正文逐字节一致 |
| XSD schemas.zip | Tue, 04 Aug 2026 15:03:49 GMT | `"2126e-65839f64ebf40"` | 135790 | **已改变** |
| EOs - XML samples.zip | Tue, 04 Aug 2026 15:03:49 GMT | `"fcd3-65839f64ebf40"` | 64723 | 一致 |
| UDI Devices - data dictionary.xlsx | Tue, 04 Aug 2026 15:03:49 GMT | `"2263e-65839f64ebf40"` | 140862 | 一致 |
| UDI Devices - business rules.pdf | Tue, 04 Aug 2026 15:03:49 GMT | `"c984a-65839f64ebf40"` | 825418 | 一致 |
| UDI Devices - enumerations.pdf | Tue, 04 Aug 2026 15:03:49 GMT | `"11de6b1-65839f64ebf40"` | 18736817 | 一致 |
| DTX for EOs - services definition.pdf | Tue, 04 Aug 2026 15:03:49 GMT | `"983668-65839f64ebf40"` | 9975400 | 一致 |

### Playground

Playground 继续保持页面 `Last-Modified: Fri, 24 Jul 2026 15:25:08 GMT`、XSD `Last-Modified: Fri, 24 Jul 2026 15:25:09 GMT`，ETag、Content-Length、页面正文及版本文字均与 2026-08-03 基线一致。XSD SHA-256 仍为 `129f9143a146564c8f9e32fe32e2cdb8bf04dcc160421d3248edeee3c5885217`。

### 官方页面链接缺陷

两个环境的当前页面仍把六项文件链接写在 `/en/documentation/` 下；本次逐项实测均返回 HTTP 404。Production 和 Playground 的官方 `/en/files/XSD%20schemas.zip` 端点返回 HTTP 200 且 Content-Type 为 `application/zip`。报告把页面所示 404 与用于验证的官方 `/files/` 端点分别留证，没有静默替换。

## 包清单与验证

- Production XSD ZIP：92 个条目 = 24 个目录 + 67 个 XSD + 1 个 sample XML
- 文件级差异：新增 `0`、删除 `0`、修改 `4`、未改 `64`（非目录文件合计 68）
- 当前转换工具对新 Production XSD 的完整导出矩阵：`25` 项通过
- `python3 -m compileall local_beta EUDAMED_TOOL_v2/validator.py`：通过
- `python3 -m unittest discover -s tests`：`58` 项通过
- 未运行模板重建：工作区在本轮开始前已有未提交的模板/代码改动，为避免覆盖用户工作，不执行会改写模板资产的构建命令。

## 对主转换工具的维护建议

1. **建议刷新打包的 Production XSD 快照，但不要改版本号。** `SCHEMA_VERSION = "3.0.30"` 仍正确；应把 `official_docs/unpacked/xsd_production/` 更新为本次同版本新内容，并让 XSD 回归测试使用新快照。
2. 该刷新应作为单独、可审查的维护改动进行；本轮只归档官方证据，没有覆盖当前 dirty worktree 中的用户修改。
3. 当前 exporter/importer/legacy validator/Excel 模板无需因这四处变化立即调整；新 XSD 已验证现有导出矩阵全部通过。
4. 对 `numberOfReuses` 的官方注释改动保持审慎：它与既有“正数代表有限重用次数”的同段文字存在语义张力。除非 business rules 或 Playground 行为进一步支持，不建议把数值 `1` 自动映射成“未定义/不适用”。
5. 若未来实现 UDI 搜索服务，再加入四个 dateTime 范围字段和 `SearchId` 的映射、输入校验与分页一致性测试。
6. 继续保留环境感知：Production 仍是 3.0.30，Playground 仍是 3.0.32，不能把全局常量直接改成 3.0.32。

## 留存文件

- `source_evidence.json`：来源、版本、元数据、链接状态、校验结论
- `raw_pages/`：Production、Production M2M support、Playground 官方页面快照
- `raw_headers/`：页面、页面所示 404 链接及官方 `/files/` 下载响应头
- `downloads/prod/`：本次 Production 六项官方原始下载件
- `unpacked/prod_xsd/`：本次 Production XSD 解包快照
- `unpacked/prior_prod_xsd/`：用于文件级比较的上一 Production 基线
- `production_official_files_checksums.sha256`：本次六项 SHA-256
- `prod_xsd_zip_listing.txt` / `prod_xsd_manifest.txt`：包清单与解包 manifest
- `prod_xsd_file_level_diff.txt` / `prod_xsd_modified_files.diff`：文件级及逐行差异
- `prod_binary_comparison.txt`：六项文件逐字节比较
- `playground_*_reused_2026-08-03.*`：Playground 未漂移时复用的校验和、manifest 与 ZIP listing
- `normalized_header_comparison.txt`：与 2026-08-03 基线的规范化比较
