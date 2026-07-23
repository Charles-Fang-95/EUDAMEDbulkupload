# EUDAMED Playground XSD 3.0.32 更正检查报告

- 检查时间：`2026-07-23T23:09:32+08:00`
- 来源范围：仅使用 EUDAMED / European Commission 官方页面及官方下载件
- 更正对象：`2026-07-20_prod-2.27.0_xsd-3.0.30_recheck`

## 更正结论

2026-07-20 的检查只覆盖了 Production，不能推出“EUDAMED 官方没有更新”。当前官方状态是双版本并存：

- Production：`XSD 3.0.30 / platform 2.27.0 / Publication date May 18, 2026`
- Playground：`XSD 3.0.32 / platform 3.31.2 / Publication date July 14, 2026`

Playground 官方 XSD 包的 `MessageType.xsd` 明确固定 `version="3.0.32"`。因此，本地工具继续统一输出 3.0.30 将无法代表当前 Playground schema。

## 官方证据

- Production：[Technical documentation](https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html)
- Playground：[Technical documentation](https://webgate.ec.europa.eu/eudamed-play-help/en/documentation/technical-documentation.html)
- Playground 页面：`Last-Modified: Thu, 16 Jul 2026 09:26:40 GMT`
- Playground XSD ZIP：`Last-Modified: Thu, 16 Jul 2026 09:26:41 GMT`
- XSD ZIP：`ETag "20c04-656b709a3d640"`、`Content-Length 134148`
- XSD ZIP SHA-256：`129f9143a146564c8f9e32fe32e2cdb8bf04dcc160421d3248edeee3c5885217`

## XSD 3.0.30 → 3.0.32

- 文件总数：`68 → 68`
- 新增：`0`
- 删除：`0`
- 修改：`9`
- 未修改：`59`

修改文件见 `xsd_file_changes.txt`。主要结构变化：

1. `service/Message/MessageType.xsd`：固定版本由 `3.0.30` 改为 `3.0.32`。
2. Actor：修正 `statusFromDate ` 尾随空格，并新增 `PostCertificateActorBaseType`。
3. Certificate：新增 quality procedure、post CECP、scrutiny、refused scope 等结构，并调整部分 requiredness。
4. SSCP：以必填 `status` 取代 `validated / sscpUpload / certificateID`，新增三项状态枚举，并修正 `certificateIdentitfier` 拼写。
5. Vigilance：调整国家枚举、字段名和部分必填性，新增输出状态字段。

与本工具当前 DEVICE / UDI 主转换范围直接相关的 Device/RegulationDevice XSD 文件未变化。当前最直接影响是消息版本属性；Certificate、SSCP、Vigilance 变化暂不应映射进本工具，除非扩展服务范围。

## 配套资料

已下载并留存 Playground 当前批次的：

- `EOs_XML_samples.zip`
- `UDI_Devices_data_dictionary.xlsx`
- `UDI_Devices_business_rules.pdf`
- `UDI_Devices_enumerations.pdf`
- `DTX_for_EOs_services_definition.pdf`

六个文件（含 XSD ZIP）的 SHA-256 均不同于 3.0.30 Production 基线，不能视为旧资料的元数据重发。

## 对主转换工具的建议

不要直接把全局 `SCHEMA_VERSION` 从 3.0.30 覆盖为 3.0.32，因为 Production 官方页仍声明 3.0.30。正确方向是：

1. 把 Production 3.0.30 与 Playground 3.0.32 作为显式环境版本处理。
2. 引入 3.0.32 XSD 快照，并让预检查按目标环境选择 XSD。
3. 对 Playground 导出把根消息版本改为 3.0.32。
4. 用当前 v2.11 模板分别 smoke-test `DEVICE.POST` 和至少一个 update service。
5. 在修改代码前继续审查 3.0.32 data dictionary、business rules、enumerations 和 EO samples 的 UDI/Devices 实质差异。

本报告只完成官方版本确认和 XSD 文件级影响定位，未修改用户现有代码。
