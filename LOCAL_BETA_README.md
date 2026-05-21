# EUDAMED 本地内测版

这是一个本地运行的 Web 工具：

- 导入统一版 Excel 模版（当前默认 `EUDAMED_Template_v2.4.xlsx`）
- 把数据写入本地 SQLite
- 浏览和编辑 Basic UDI-DI / UDI-DI
- 按 4 类 service 生成 XML
- 保存导出历史

## 推荐维护方式

建议用户长期维护 `EUDAMED_Template_v2.4.xlsx`。本地网页端用于批量导入、校验、筛选、选择 service 和导出 XML；`local_beta_data/eudamed_beta.db` 是工作库和历史库，不建议作为唯一主数据源。

网页端详情页编辑适合临时修正和排错。正式维护仍建议回到 Excel template，避免 Excel 和本地库出现两个版本。

填写 UDI/GTIN、Basic UDI-DI、Package UDI-DI、Reference、SRN、EMDN/Nomenclature 等编码字段时，必须按文本维护，避免 Excel/WPS 自动转成科学计数法或丢失前导 0。

如果需要先区分执行文件、数据库、官方文档和测试样例，请先看：

- `README.md`
- `docs/PROJECT_STRUCTURE.md`

## 启动

```bash
python3 run_local_beta.py
```

默认会开启代码自动重载。后续修改 `local_beta/` 下的 Python 或 CSS 文件时，终端会自动重启本地服务，不需要手动停掉再运行。

启动后访问：

```text
http://127.0.0.1:8765
```

可以在页面顶部进入 `XSD 版本`，检查工具当前 XSD 版本、本地官方 XSD 包版本、官方技术文档页版本是否一致。

如需重新生成统一版 Excel 模版：

```bash
python3 -m local_beta.build_unified_template
```

## 当前范围

- 适合内测和流程验证
- 数据默认只保存在本机 `local_beta_data/`
- 支持 Excel 重复导入并按编码覆盖本地记录
- 支持在详情页直接修改主字段
- 支持检查 EUDAMED 官方 XSD 版本一致性
- 按 EUDAMED 官方 XSD `3.0.30` 的 bulk upload 300 条同类实体上限自动拆分 XML，并在 ZIP manifest 中列出上传顺序
- 新模板使用 `MDR_MDD` 和 `IVDR_IVDD` 两个主录入 sheet，正式数据从第 4 行开始
- 模板第 1 行是字段名，第 2 行是中文说明，第 3 行是示例，前三行已锁定防止误改
- 多语言 Trade Name 在 `Trade Names` sheet 中录入；主表 Trade Name 只作为快捷输入
- Market Info 属于 UDI-DI 层，不属于 BUDI 层；独立 Update market information service 后续实现
- Legacy Device / EUDI 新上传已开放；MDD/AIMDD/IVDD 会按 legacy XML 结构输出
- Market Info 中同一 UDI-DI 可以有多个 made available 国家，但 `Originally Placed on Market` 必须且只能有一个 `TRUE`
- 市场信息、警告、储存条件、包装、CMR 物质分别在独立明细 sheet 中录入，不再使用 `|` 分隔格式
- Storage/Critical Warning 类型使用官方 XSD 枚举下拉，模板显示 `CODE - English label`，导出 XML 时只输出官方代码
- 导入后，一对多子表在详情页仍以 JSON 文本区域编辑

## 工具升级流程

EUDAMED 官方 XSD 经常更新，工具版本和支持的 XSD 版本是绑死的——直接换 XSD 不换代码会让 XML 不合规。所以升级走「发新版本」的路。

**用户侧**：
1. 帮助页（`/help`）的「检查更新」区点击按钮。
2. 若提示有新版本，点下载（或打开发布页），下载 zip/exe。
3. 关闭当前工具，把 zip 解压覆盖到原目录（或运行新 exe）。`local_beta_data/` 用户数据目录会保留，不会被覆盖；也可以通过环境变量 `EUDAMED_DATA_DIR` 指向其他位置。
4. 重新启动 `python3 run_local_beta.py` 或新版 exe。

**作者侧**（发新版本时）：
1. 替换 `official_docs/unpacked/xsd_production/` 为最新官方 XSD。
2. 跑回归：`python3 -m local_beta.build_unified_template` 重新生成 Excel 模板；用 `Test sample/` 跑一遍导入 + 导出，对比 `official_docs/unpacked/samples/` 中的样例 XML。
3. 改 `local_beta/constants.py`：`SCHEMA_VERSION`（XSD 版本）、`TOOL_VERSION` / `TOOL_VERSION_LABEL`（语义化）、`TOOL_UPDATED`（发布日期）。
4. git tag `vX.Y.Z`，在 GitHub Releases 上传打包好的 zip/exe + 简要 changelog（中文即可，会被「检查更新」展开显示）。
5. 把 `RELEASES_API_URL` 和 `RELEASES_PAGE_URL` 在 `constants.py` 中填入正式仓库地址（一次性配置）。

## 当前限制

- 未做登录权限
- 未做桌面打包
- `PATCH` 类 XML 为内测版生成逻辑，仍建议在 EUDAMED TEST 环境先验收
- 旧模板和客户原始 Excel 不做默认静默兼容；需要先迁移/映射到当前 v2.4 模板后再导入
