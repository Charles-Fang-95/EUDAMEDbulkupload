# Project Structure

这份说明用于区分当前项目中的执行文件、数据库、官方文档、测试样例和历史文件。

## 1. 当前运行主线

| 路径 | 分类 | 说明 |
| --- | --- | --- |
| `run_local_beta.py` | 启动入口 | 启动本地 web server，默认端口 `8765` |
| `local_beta/` | 当前应用代码 | 本地网页端、导入、存储、导出、模板生成 |
| `local_beta/static/style.css` | UI 样式 | 本地网页端样式 |
| `EUDAMED_Template_v2.9.xlsx` | 当前用户模板 | 首页下载模板默认指向这里 |
| `EUDAMED_TOOL_v2/lib/` | 打包依赖 | 当前工具使用的 vendored Python 依赖 |
| `EUDAMED_TOOL_v2/validator.py` | 复用模块 | 当前 importer 仍调用四层验证器 |

## 2. 本地数据区

| 路径 | 分类 | 说明 |
| --- | --- | --- |
| `local_beta_data/eudamed_beta.db` | SQLite 数据库 | 保存产品库、导入记录、导出记录 |
| `local_beta_data/uploads/` | 上传缓存 | 保存用户上传到网页端的 Excel |
| `local_beta_data/exports/` | XML 输出 | 保存生成的 `DEVICE.POST`、`UDI_DI.POST`、`PATCH` XML |

`local_beta_data/` 是本地运行数据区。做代码整理时不要删除；做测试重置时应先备份。

## 3. 官方文档区

| 路径 | 说明 |
| --- | --- |
| `official_docs/XSD_schemas_production.zip` | production XSD 原始压缩包 |
| `official_docs/unpacked/xsd_production/` | 已解压 production XSD，XML 校验使用这里 |
| `official_docs/UDI_Devices_business_rules.pdf` | UDI Devices 业务规则 |
| `official_docs/UDI_Devices_data_dictionary.xlsx` | UDI Devices 数据字典 |
| `official_docs/UDI_Devices_enumerations.pdf` | 枚举说明 |
| `official_docs/DTX_for_EOs_services_definition.pdf` | DTX service definition |
| `official_docs/EOs_XML_samples.zip` | 官方 XML samples |

当前工具声明和本地 XSD 版本应保持 `3.0.30`。

## 4. 测试样例区

| 路径 | 说明 |
| --- | --- |
| `Test sample/EUDAMED_Customer_Test_Template_Unimax_v2.5.xlsx` | 历史内测样例，可用迁移工具搬到当前模板 |
| `Test sample/5432_Appendix...xlsx` | 客户原始 Basic 信息来源 |
| `Test sample/UM-QR-9.0-12-02 UDI-DI清单(1) 新 - 副本.xls` | 客户原始 UDI-DI 清单 |
| `Test sample/EUDAMED_Customer_Test_Template_Unimax*.xlsx` | 历史测试输出，可归档 |

正式测试优先使用当前 `EUDAMED_Template_v2.9.xlsx`，或使用迁移工具生成的 v2.9 样例。

## 5. 旧工具和历史文件

`EUDAMED_TOOL_v2/` 是旧命令行工具目录。当前本地网页端仍复用其中的 `lib/` 和 `validator.py`，因此不能整体删除。

可考虑后续归档：

- `EUDAMED_TOOL_v2/eudamed_report_*.html`
- `EUDAMED_TOOL_v2/eudamed_report_*.json`
- 根目录 `eudamed_report_*.html/json`
- 旧模板和备份模板
- `.DS_Store`
- `__pycache__/`

## 6. 建议的交付视角

交付给用户时，应只暴露：

- 启动器或打包后的应用
- 当前模板下载入口
- 本地网页端
- 用户数据目录说明
- 官方 XSD 版本说明

不应让普通用户直接接触 `local_beta/`、`EUDAMED_TOOL_v2/`、`official_docs/unpacked/` 这些内部目录。

> 面向用户的简介、下载、更新、使用说明已统一放到根目录 [`README.md`](../README.md)；本文件只保留维护者视角。

## 7. Windows 测试包

macOS 不能可靠直接生成 Windows `.exe`。要给企业发 Windows 内测包，请在 Windows 10/11 或 Windows 虚拟机中运行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\packaging\windows\build_windows_exe.ps1
```

生成结果在 `dist\EUDAMED_Local_Beta_Windows.zip`。发送 ZIP，不要只发送单个 `.exe`。

## 8. EUDAMED XSD 更新处理

EUDAMED 官方会随平台版本更新 XSD。工具导出 XML 时会读取本地 `official_docs/unpacked/xsd_production/service/Message/MessageType.xsd` 里的 fixed version，而不只依赖代码常量。更新流程：

1. 从 EUDAMED Technical documentation 下载最新 `XSD schemas.zip`。
2. 替换 `official_docs/XSD_schemas_production.zip`，并解压覆盖 `official_docs/unpacked/xsd_production/`。
3. 运行 `python3 -m local_beta.build_unified_template` 重新生成模板枚举下拉。
4. 运行 `python3 -m compileall local_beta`。
5. 用样例导出 XML，并用新版 `official_docs/unpacked/xsd_production/service/Message.xsd` 校验。
6. 更新 `local_beta/constants.py` 的 `SCHEMA_VERSION` / `TOOL_VERSION` / `TOOL_UPDATED` 与 `CHANGELOG.md`，重建 Windows/Mac 包发给用户；已发出的包不会自动获得新 XSD。

发包与「检查更新」配置详见 [`GITHUB_RELEASE_PROCESS.md`](GITHUB_RELEASE_PROCESS.md)。

## 9. 不要随意删除

- `local_beta/`
- `run_local_beta.py`
- `EUDAMED_Template_v2.9.xlsx`
- `EUDAMED_TOOL_v2/lib/`、`EUDAMED_TOOL_v2/validator.py`
- `official_docs/unpacked/`、`official_docs/XSD_schemas_production.zip`
- `local_beta_data/eudamed_beta.db`（用户数据，删除即清空本地库）

## 10. 可归档但不影响核心运行

- 根目录与 `EUDAMED_TOOL_v2/` 下的历史 `eudamed_report_*.html/json`
- 旧模板：`EUDAMED_Template_v2.3.xlsx`、`EUDAMED_TOOL_v2/templates/EUDAMED_Template_v2*.xlsx`
- `__pycache__/`、`.DS_Store`

归档前先复制到外部备份目录，不要直接删除客户原始样例。
