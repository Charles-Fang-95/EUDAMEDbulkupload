# EUDAMED Local Beta

本目录是 EUDAMED Excel to XML 本地内测工具。当前主入口是本地网页端，不是旧命令行转换器。

## 最常用文件

| 类型 | 路径 | 说明 |
| --- | --- | --- |
| 启动入口 | `run_local_beta.py` | 启动本地网页端，访问 `http://127.0.0.1:8765` |
| 主程序代码 | `local_beta/` | 本地网页端、Excel 导入、SQLite 管理、XML 导出逻辑 |
| 当前模板 | `EUDAMED_Template_v2.4.xlsx` | 给用户填写的默认 Excel 模板 |
| 本地数据库 | `local_beta_data/eudamed_beta.db` | 产品库、导入历史、导出历史，删除会清空本地数据 |
| 导出 XML | `local_beta_data/exports/` | 网页端生成的 XML 文件 |
| 官方资料 | `official_docs/` | EUDAMED XSD、业务规则、数据字典等官方文档 |
| 测试样例 | `Test sample/` | 客户样例、Unimax v2.4 测试模板、原始 Excel |
| 旧工具/依赖 | `EUDAMED_TOOL_v2/` | 旧命令行工具、vendor 依赖、历史模板；当前网页端仍复用部分 validator/lib |
| 项目结构说明 | `docs/PROJECT_STRUCTURE.md` | 更详细的目录分类和清理建议 |
| 版本记录 | `CHANGELOG.md` | 工具和模板的简要更新记录 |
| 发布流程 | `docs/GITHUB_RELEASE_PROCESS.md` | GitHub Releases 发包和检查更新配置说明 |

## 启动

```bash
cd /Users/charles_fang/Documents/EUDAMED
python3 run_local_beta.py
```

启动后打开：

```text
http://127.0.0.1:8765
```

## 推荐维护方式

建议把 `EUDAMED_Template_v2.4.xlsx` 作为主维护文件。用户日常在 Excel/WPS 中维护产品数据；需要批量校验、选择 service、生成 XML 时，再上传最新版模板到本地网页端。

本地 SQLite 数据库是工作库和导出历史库，不建议把它作为唯一真相。网页端详情页编辑适合临时修正和排错；正式维护仍建议回到 Excel template。

填写编码字段时，UDI/GTIN、Basic UDI-DI、Package UDI-DI、Reference、SRN、EMDN/Nomenclature 等必须按文本维护，避免 Excel/WPS 自动改成科学计数法或丢失前导 0。

国家/市场信息填报错误时，应优先通过 EUDAMED update/create new version 纠正，不应默认删除 UDI-DI 重新注册。只有当 UDI-DI、器械身份或 Basic UDI-DI 关联本身错误且无法更新纠正时，才考虑 discard/逻辑删除并重建。

Market Info 属于 UDI-DI 层。同一 UDI-DI 可以填写多个 made available 国家，但 `Originally Placed on Market` 必须且只能有一个 `TRUE`，其它国家应填写 `FALSE`。

当前工具支持 `DEVICE.POST` 下的 Legacy Device / Regulation Device / SPP 新上传路径。MDR/IVDR 会按 Regulation Device XML 输出；MDD/AIMDD/IVDD 会按 Legacy Device / EUDI XML 输出。

EUDAMED 官方 XSD `3.0.30` 对 bulk upload payload 有 300 条同类实体上限，且 payload 是 `xs:choice`，单个 XML 不能混放不同实体。网页端导出时会自动拆分超过 300 条的任务，并在 ZIP 包的 manifest 中列出上传顺序。对于同一 Basic UDI-DI 下超过 300 个 UDI-DI 的 `DEVICE.POST`，工具会先生成创建 Basic 的 `DEVICE.POST`，后续 UDI-DI 生成依赖该 Basic 的 `UDI_DI.POST`；用户必须先确认前序上传成功再继续。

## Windows 测试包

macOS 不能可靠直接生成 Windows `.exe`。要给企业发 Windows 内测包，请在 Windows 10/11 或 Windows 虚拟机中运行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\packaging\windows\build_windows_exe.ps1
```

生成结果在 `dist\EUDAMED_Local_Beta_Windows.zip`。发送 ZIP，不要只发送单个 `.exe`。

## EUDAMED XSD 更新处理

EUDAMED 官方会随平台版本更新 XSD。工具现在导出 XML 时会读取本地 `official_docs/unpacked/xsd_production/service/Message/MessageType.xsd` 里的 fixed version，不再只依赖代码里的版本常量。

后续更新流程：

1. 从 EUDAMED Technical documentation 下载最新 `XSD schemas.zip`。
2. 替换 `official_docs/XSD_schemas_production.zip`，并解压覆盖 `official_docs/unpacked/xsd_production/`。
3. 运行 `python3 -m local_beta.build_unified_template` 重新生成模板枚举下拉。
4. 运行 `python3 -m compileall local_beta`。
5. 用样例导出 XML，并用新版 `official_docs/unpacked/xsd_production/service/Message.xsd` 校验。
6. 重新构建 Windows/Mac 包发给用户；已经发出去的 exe 不会自动获得新版 XSD。

## 当前不要随意删除

- `local_beta/`
- `run_local_beta.py`
- `EUDAMED_Template_v2.4.xlsx`
- `EUDAMED_TOOL_v2/lib/`
- `EUDAMED_TOOL_v2/validator.py`
- `official_docs/unpacked/`
- `official_docs/XSD_schemas_production.zip`
- `local_beta_data/eudamed_beta.db`

## 旧模板处理

当前导入器默认识别新版 `MDR_MDD` / `IVDR_IVDD` 主表和 v2.4 明细 sheet。旧模板或客户自有 Excel 不建议静默兼容导入，因为字段名、含义和一对多结构可能不同，错误映射会直接生成错误 XML。

推荐做法：旧模板/客户原始表先人工或通过后续 migration/mapping 工具迁移到当前 v2.4 模板；导入器发现不支持的 workbook 时会阻止导入并提示迁移。

## 可归档但不影响核心运行

- 根目录和 `EUDAMED_TOOL_v2/` 下的历史 `eudamed_report_*.html/json`
- 旧模板：`EUDAMED_Template_v2.3.xlsx`、`EUDAMED_TOOL_v2/templates/EUDAMED_Template_v2*.xlsx`
- `__pycache__/`、`.DS_Store`

归档前建议先复制到外部备份目录，不要直接删除客户原始样例。
