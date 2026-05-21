# official_docs

这里存放 EUDAMED 官方技术资料和本地 XML 校验用 XSD。

## 关键文件

| 路径 | 用途 |
| --- | --- |
| `XSD_schemas_production_3.0.30.zip` | production XSD 原始包 |
| `unpacked/xsd_production/` | 已解压 production XSD；本地 XML validation 使用这里 |
| `UDI_Devices_business_rules.pdf` | UDI Devices 业务规则 |
| `UDI_Devices_data_dictionary.xlsx` | UDI Devices 数据字典 |
| `UDI_Devices_enumerations.pdf` | 官方枚举说明 |
| `DTX_for_EOs_services_definition.pdf` | DTX service 定义 |
| `EOs_XML_samples.zip` | 官方 XML samples |

当前工具支持的 EUDAMED production XSD version 是 `3.0.30`。

不要删除 `unpacked/xsd_production/`，否则网页端 XSD 版本检查和 XML 校验会失效。
