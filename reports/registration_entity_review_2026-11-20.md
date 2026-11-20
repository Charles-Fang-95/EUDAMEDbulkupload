# Basic 注册类别修复审查记录

2026-11-20。基线提交 `15968a1`，工具 1.0.5、模板 v2.14。候选版本为 1.0.6 / v2.15，目标 Production XSD 3.0.30。以下结果来自虚构数据和隔离数据库。客户远端 Basic 类别仍待核实，线上验收尚未完成。

## 分类依据

| Basic 的注册类别 | Applicable Legislation | Device Type | XML 路径 |
| --- | --- | --- | --- |
| Device | MDR | Regular Device、System、Procedure Pack | MDRBasicUDIType / MDRUDIDIDataType |
| Device | MDD、AIMDD | Regular Device、System、Procedure Pack | MDEU，使用 Legacy 标识 |
| Device | IVDR、IVDD | Regular Device | IVDR 或 IVDEU |
| PR/SPP | MDR | System、Procedure Pack | PRBasicUDIType / PRUDIDIDataType |

打包 XSD 的 `BasicUDIType.xsd` 对 MDR 的 type 定义了 DEVICE、SYSTEM、PROCEDURE_PACK，对 PR 的 type 只定义了后两项。`UDIDIType.xsd` 中 PR 继承共用的 UDIDIDataType，MDR 继承带 numberOfReuses、marketInfos 等字段的 DeviceUDIDIDataType，再增加 latex、reprocessed 等字段。Legacy 的 MDEUDIType 继承 MDRBasicUDIType。官方业务规则的 FLD-UDID-12 适用于 MDR、MDD、AIMDD，独立 PR/SPP 使用另一个属性 FLD-UDID-261。描述检查沿用 RULE-00185 / BR-UDID-131。[Production 技术文档](https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html) · [UDI Devices business rules](https://webgate.ec.europa.eu/eudamed-help/en/files/UDI%20Devices%20-%20business%20rules.pdf)

DTX 服务定义第 2–4 节分别列出 Device、BasicUDI、UDIDI 的请求类型与 actor 一致性检查。BR-DTX-UDI-079 和 080 区分制造商与独立系统或组合包生产者。PR Basic 的 medicinalPurpose、PRActorCode、type 均必填。本工具复用 Manufacturer SRN 列填生产者 PR Actor ID，复用 Basic - Additional Description 填医疗目的，新增 PR Medical Purpose Language 供选择。UDI 自己的 Additional Description 和语言单独保存。[DTX for EOs services definition](https://webgate.ec.europa.eu/eudamed-help/en/files/DTX%20for%20EOs%20-%20services%20definition.pdf)

## 本地业务预检与浏览器验证

通过 `EUDAMED_DATA_DIR` 指定新临时库，运行 `python3 run_local_beta.py --port 18765 --no-reload`，以 Chrome 实际操作表单。测试结束后关闭临时浏览器和服务。

| 操作 | 观察结果 |
| --- | --- |
| 在完整 v2.14 模板副本中填写同一 Basic 的两条 MDR + Procedure Pack，导入 | 两条 UDI 均保存。红色错误显示 MDR 第 4 行、Basic 编码及 Registration Entity Type。直接生成 UDI_DI.POST 被拦截，无下载链接。 |
| 在 Basic 详情选择 Device，分别预检、下载 DEVICE.POST 和 UDI_DI.PATCH | 两次均为 0 错误、1 项既有 Basic 布尔值留空警告。下载 XML 中 numberOfReuses=0、baseQuantity=3、latex=false、reprocessed=false；市场国家 DE，首次投放为 true，附加描述语言 EN。 |
| 导入 v2.15 的独立 PR/SPP，在 Basic 详情明确选择 PR/SPP，再预检和下载 DEVICE.POST | 0 错误、1 项虚构样例共用 Reference Number 的警告。XML 使用生产者 actor，输出 PROCEDURE_PACK、医疗目的和 DE 语言，保留 UDI 描述。 |
| 选择上述三个 UDI 导出 DEVICE.POST | 默认阻止跨服务生成；“全选”也不会勾选追加服务。明确勾选 UDI_DI.POST 后预检为 0 错误、4 项提示，涉及前述布尔值、共用 Reference Number、分片与上传顺序。 |
| 下载混合 ZIP，核对 manifest.csv、manifest.html 和 XML | 3 条 UDI 各出现一次。制造商的首条 DEVICE.POST 位于第 1 份，追加 UDI_DI.POST 依赖第 1 份。生产者的独立 DEVICE.POST 使用自己的 actor。 |

## 实际 XSD 校验

对上述 3 个单独下载的 XML 及 ZIP 内的 3 个 XML，使用 lxml.etree.XMLSchema / assertValid，从 service/Message.xsd 编译整套 schema。以下两套分别通过 6/6。

- 仓库打包的 `official_docs/unpacked/xsd_production/`。
- 本地留存的欧委会 Production 3.0.30 原包，SHA-256 为 `22d098940ba72be23deb202b73759e8d1746b457393f3c90b560e19a4de16492`。原包与仓库打包目录存在先前记录的四个文件差异，因此分别执行校验。[Production XSD 原包](https://webgate.ec.europa.eu/eudamed-help/en/files/XSD%20schemas.zip)

匿名回归还复原了历史错误的 PR 子树形状。省略已填 Device 字段的旧形状仍通过 XSD，因此测试逐项断言了新 XML 的实际值、Basic 关联及类型。

## 模板与打包资源

已运行 `python3 -m local_beta.build_unified_template`。逐表核对中英文主表的字段顺序、注册类别下拉范围、示例和 Glossary。MDR 提供两种类别，其余法规主表只提供 Device。根目录与 templates 镜像分别逐字节一致。

| v2.15 资源 | SHA-256 |
| --- | --- |
| 中文模板 | `36556c47f7d45c8e944600fb4e862ecc6f59e6756b8369a44f9a70bd4e0fbfde` |
| 英文模板 | `60d54057ae97b7ac41ce4cebe4ef01886d2807bd635d3cb10f1d1b928beb7e93` |

实际生成了含歧义 MDR 行及 Legacy 行的规范化 v2.15 副本。MDR 保留空白注册类别、Procedure Pack 属性和 UDI 描述，Legacy 保留最终 B- 标识。已核对 Windows 打包和 Release workflow 的模板文件名、macOS 打包脚本引用的版本常量，以及网页的两种语言下载入口。本次未构建或发布平台安装包。

## 命令验证

- `python3 -m compileall local_beta EUDAMED_TOOL_v2/validator.py`
- `python3 -m unittest discover -s tests`（隔离数据目录，141 项全部通过，0 跳过）
- `python3 -m local_beta.build_unified_template`
