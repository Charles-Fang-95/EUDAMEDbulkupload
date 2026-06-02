# 0.8.0 易用性改进计划（交给 codex 执行）

## 背景与目标

工具的网页界面本身已较成熟，但对「不懂 GitHub 的普通 RA」存在两类摩擦：
1. **进工具之前**：下载 / SmartScreen / 黑窗口 / 更新；
2. **进工具之后**：术语门槛、不知道选哪个 service、模板怎么填、EUDAMED 那边怎么传、被退回后怎么返工。

本批 9+1 项改进集中解决上述摩擦。**不动 XML 生成主路径**（exporter 的 `_build_*` 节点逻辑），只在「引导 / 校验 / 呈现 / 打包发布」侧做工作。

已确认的现状（实现前提）：
- 双语统一走 `views.t(zh, en)` + thread-local `_lang_ctx`。
- `update_checker.check_latest_release` 已支持 GitHub→Gitee 回落，返回 `assets`(name/url/size)、`asset_url`(平台优选)、`source`(github/gitee)。`constants.py` 已有 `GITEE_RELEASES_API_URL/PAGE_URL`、`_preferred_asset()`。
- `template_schema.py` 的列对象含 `header / description / example / applies / entity`；`MAIN_COLUMNS`、`RELATED_SHEETS`、`ENTRY_SHEETS`、`columns_for_entry_sheet()` 可直接复用。
- `storage.py` 有列迁移机制 `_ensure_record_columns()`（`PRAGMA table_info` + `ALTER TABLE ADD COLUMN`）。
- `basic_records` / `udi_records` 当前**没有** sample 标记列。
- `run_server()`（app.py:504）**不自动开浏览器**、**无退出路由**；打包脚本 `packaging/windows/build_windows_exe.ps1` 用 `--console`。
- `SUPPORTED_SERVICES`（views.py）已含 label/scope/requires/after；`upload_guidance(service_type)` 已存在；`EUDAMED_BULK_UPLOAD_HELP_URL` 已有。
- 导出结果面板 `export_result_panel()`、产品库 `library_page()`、导出页 `export_page()`、导入页、帮助页 `help_page()` 均在 `views.py`。

建议版本号 **0.8.0**（0.7.0 已含两个新 service）。每项都要双语、都要更新 CHANGELOG。

---

## 任务 1：首次使用引导 + 示例数据（含醒目区分 + 可清除）

**目标**：空库用户看到「快速开始」卡 + 一键载入示例数据走通全流程；示例数据**用颜色 + 文字标注**醒目区分；**随时可一键清除**；**绝不会被误传到 EUDAMED**。

### 1a. 数据层
- `storage.py` 给 `basic_records`、`udi_records` 各加列 `is_sample INTEGER NOT NULL DEFAULT 0`，在 `_ensure_record_columns()` 里按现有模式补迁移。
- 新增 `Repository.load_sample_data()`：插入一套**自洽且能通过 DEVICE.POST 预检**的最小示例——1 个 MDR Basic UDI-DI + 2 个 UDI-DI（含 market/package/trade name），全部 `is_sample=1`。编码用显眼前缀，如 `SAMPLE-BASIC-0001` / `SAMPLE-UDI-0001`，自带「这是假数据」语义，且不与真实数据冲突。重复调用要幂等（先清后插或 INSERT OR IGNORE）。
- `Repository.clear_sample_data()`：删除所有 `is_sample=1` 的 basic/udi 记录（连带其 JSON 子数据，因子数据是行内 JSON 列，删行即可）。
- `Repository.sample_data_count()`：返回示例 basic/udi 计数，供横幅与按钮状态判断。
- `list_basics/list_udis/get_filtered_ids` 的返回项要带上 `is_sample`，供视图层着色。

### 1b. 视图层
- **快速开始卡**：`dashboard()` 在「无任何记录」时（真实 + 示例都为 0，或仅判断真实记录为 0）显示一张卡：三步「① 下载模板 ② 填写并导入 ③ 选 service 导出」+ 按钮【下载模板】【载入示例数据】【去导入】。
- **醒目区分**（用户强调）：示例记录在产品库 / 导出表的行加类 `.is-sample`（淡琥珀底色）+ 一个 `<span class="badge sample">示例 / SAMPLE</span>` 角标；详情页顶部加同样徽章。CSS 新增 `.row-sample{background:rgba(212,156,52,.10)}` 与 `.badge.sample`。
- **常驻横幅**：只要库中存在示例数据，所有页面顶部显示醒目提示条：「当前包含**示例数据**，仅供熟悉流程，**请勿提交到 EUDAMED**。[清除示例数据]」。
- **空状态**：见任务 10。

### 1c. 路由（app.py）
- POST `/sample-data/load` → `load_sample_data()` 后重定向回概览。
- POST `/sample-data/clear` → `clear_sample_data()` 后重定向回来源页。
- 两者都用现有 POST + 重定向模式，带防重复提交。

### 1d. 安全闸（关键）
- `exporter.validate()`：若本次选中记录中**含 `is_sample=1`**，加一条**显著 warning**（不强制 block，但文案强烈）：「本次包含示例数据（SAMPLE-…），示例数据仅供练习，请勿上传到 EUDAMED」。这样即便用户载入示例后误点导出，也会被明确警告。

### 1e. 验证
- 空库进概览 → 出现快速开始卡；点【载入示例数据】→ 产品库出现带琥珀底 + 「示例」角标的记录 + 顶部横幅。
- 用示例数据走 DEVICE.POST 预检 → 通过且出现「含示例数据」warning。
- 点【清除示例数据】→ 记录与横幅消失，真实数据不受影响。

---

## 任务 2：service「人话名」+「我该选哪个」向导

**目标**：RA 不必理解 POST/PATCH；任务化标签 + 决策向导帮他选对 service。原始代码名保留（EUDAMED 仍用）。

### 2a. 人话名
- `SUPPORTED_SERVICES`（views.py）每项加 `task_zh / task_en`（任务化名），例如：
  - DEVICE.POST → 「注册新器械（Basic UDI-DI + 首个 UDI-DI）」
  - UDI_DI.POST → 「给已注册的 Basic 增加新的 UDI-DI」
  - Basic_UDI.PATCH → 「修改已注册 Basic UDI-DI 的信息」
  - UDI_DI.PATCH → 「修改已注册 UDI-DI 的信息」
  - MARKET_INFO.PATCH → 「更新已注册 UDI-DI 的市场国家 / 上市日期」
  - PACKAGE_UDI.PATCH → 「更新已注册 UDI-DI 的包装结构」
- `service_options()` 下拉项显示「人话名 — CODE」；导出页「当前 service」面板把人话名放最显眼，code 作副标题。

### 2b. 选择向导
- 导出页未选 service 时（现有「请先选择 service」分支）渲染一个「**我该选哪个？**」向导：3–4 个是非/单选问题：
  1. 这是**全新还没注册**的产品，还是改**已注册**的？
  2. （新）是新的 Basic + 首个 UDI-DI，还是给已有 Basic 加新 UDI-DI？
  3. （改）改的是 Basic 信息 / UDI-DI 信息 / 市场信息 / 包装结构？
- 纯前端 JS（沿用现有内联 `<script>` 风格、`{{ }}` 转义）即可：根据选择显示推荐结果卡 + 「用这个 service」按钮（`<a href="/export?service_type=...">`）。无需新路由。

### 2c. 验证
- 下拉显示人话名；向导按不同回答推荐到正确 service 并能跳转。

---

## 任务 3：驯服「黑窗口」（含进阶）

**目标**：非技术用户不被黑窗口吓到 / 误关；提供干净退出。用户要求**尽量做进阶**（隐藏控制台）。

### 3a. 基线（必做）
- `run_server()`：绑定成功后 `webbrowser.open(f"http://{host}:{port}/")` 自动开浏览器；用环境变量（如 `EUDAMED_NO_BROWSER=1`）在开发/reload 时关闭，避免重复弹窗。
- 新增 `/shutdown`（POST）路由：在后台线程调用 `server.shutdown()`，先返回一个「已退出，可关闭本页和后台窗口」的页面。
- 每个页面（或仅首页）顶部加一条一次性提示：「保持后台窗口开启；用完点右上角【退出工具】」。导航栏右侧加【退出工具】→ POST `/shutdown`（带确认）。

### 3b. 进阶（用户要的，作为 3 的目标形态）
- 打包出 **windowed/noconsole** 版：`build_windows_exe.ps1` 增加 `--noconsole`（或并行产出一个无控制台目标）。无控制台后**退出只能靠 Web 的【退出工具】按钮**，所以 3a 的 `/shutdown` 是前置依赖。
- 加**系统托盘**：引入 `pystray` + `Pillow`，启动时在托盘放图标，右键菜单「打开界面 / 退出」。这样既无黑窗口、又有可见的「它在运行」信号和干净退出。
  - 依赖增量评估：pystray+Pillow 会增大包体。若不想加依赖，**退而求其次**：noconsole exe + 启动自动开浏览器 + Web【退出工具】按钮（最小可行，无托盘）。
  - 实现提示：托盘需在主线程跑 icon loop、HTTP server 放子线程；或反之。注意 PyInstaller `--noconsole` 下 `print` 无输出，日志改写文件 `local_beta_data/run.log`。

### 3c. 验证
- 源码运行：启动自动开浏览器；点【退出工具】→ 服务停止、页面提示已退出。
- 打包版：双击启动无黑窗口、自动开浏览器、托盘可退出（或 Web 按钮可退出）。

---

## 任务 4：导入页瘦身

**目标**：文件选择框置顶；警告收进可折叠清单。

- `views.py` 导入页重排：把 `选择文件 + 开始导入` 放到面板**最上方**。
- 现有几段警告改为一个 `<details>`「填写须知（点击展开）」，内容用**勾选清单式**呈现（✅ 编码已设为文本、未丢前导 0；✅ 用的是当前模板；✅ Market Info 恰好一个 Originally Placed=TRUE；✅ 旧/客户模板先走迁移）。
- 「市场信息提醒」保留但收进同一 `<details>`，默认折叠。
- 不删任何信息，只重排 + 折叠。

**验证**：导入页首屏即见文件选择与导入按钮；须知默认折叠、可展开。

---

## 任务 5：术语内联解释（tooltip）

**目标**：对 jargon 提供悬浮解释，降低入门 RA 认知负担。

- `views.py` 新增 `GLOSSARY = {term: (zh_def, en_def)}`，覆盖：Basic UDI-DI、UDI-DI、EMDN Code、Manufacturer SRN、Authorised Representative SRN、Issuing Entity、Originally Placed on Market、Device Status、DTX service、以及各 service code 与「人话名」。
- 新增 helper `term_hint(term)` → 渲染 `<span class="term-tip" data-tip="...">{term}<sup>?</sup></span>`，纯 CSS tooltip（`.term-tip{...}` + `:hover::after`）。
- 接入点：`field_input()` 的字段标签（对命中 GLOSSARY 的 header 自动挂 tooltip，复用现有中文 hint 逻辑）、导出页「当前 service」面板、产品库/导出表头。
- 双语：tooltip 文案走 `t()`。

**验证**：悬停带「?」的术语出现解释；中英切换文案正确；不影响布局。

---

## 任务 6：检测到更新后，直接给出 GitHub + Gitee 的 ZIP 直链

**目标**：发现新版时，**同时**显示 GitHub 与 Gitee 的 Windows ZIP **直接下载地址**，用户点能用的那个；而不仅是 release 页链接。

现状：`check_latest_release` 走 GitHub→Gitee 回落，只返回**单一来源**的 assets。

### 6a. 数据层（update_checker.py）
- 新增 `release_download_links(github_api, gitee_api, timeout)`：**分别**请求 GitHub 与 Gitee 最新 release，各用 `_preferred_asset()` 选出 Windows `.zip` 资产，返回：
  ```
  {
    "github": {"version": "...", "zip_url": "...", "page_url": GITHUB_RELEASES_PAGE_URL, "error": ""},
    "gitee":  {"version": "...", "zip_url": "...", "page_url": GITEE_RELEASES_PAGE_URL, "error": ""},
  }
  ```
  每个来源独立 try/except，失败降级为 `zip_url=""` + 保留 page_url，互不影响。
- 复用现有 `_load_release` / `_normalize_*` / `_release_assets` / `_preferred_asset`。

### 6b. 视图层（views.py `update_check_block`）
- 当 status==`ok`（或同时在 up_to_date 也展示，便于重装）时，渲染两个清晰按钮：
  - 「⬇ 从 GitHub 下载 Windows 包 (vX.Y.Z)」→ `github.zip_url`（无则退化为 page_url）
  - 「⬇ 从 Gitee 下载 Windows 包（国内推荐）」→ `gitee.zip_url`（无则退化为 page_url）
- 文案注明：国内访问优先 Gitee；两个包内容一致。
- 失败来源只显示「打开 release 页」回退链接，不报错中断。

### 6c. 验证
- 临时把本地 `TOOL_VERSION` 调低 → 检查更新出现 GitHub 与 Gitee 两个直链按钮，指向真实 `.zip` 资产 URL。
- 断网 GitHub（或改坏其 API URL）→ GitHub 退化为 page 链接，Gitee 仍给直链；反之亦然。

---

## 任务 7：工具内置「模板怎么填」页

**目标**：把每个 sheet、每列的填写说明放进工具，用户不用对着 Excel 猜。

- 新路由 GET `/template-guide` + 导航（放二级组，挨着「下载模板」）。
- `views.py` `template_guide_page()`：**自动**从 `template_schema` 生成——
  - 对每个 `ENTRY_SHEETS`（MDR_MDD / IVDR_IVDD）：用 `columns_for_entry_sheet()` 列出列的 `header / description / example`，并标注必填。
  - 对每个 `RELATED_SHEETS`（Trade Names / Market Info / Package Info / Device Certificates / Critical Warnings / Storage Conditions / CMR Substances）：同样列出列说明 + 靠哪个 code 关联主表。
  - 顶部「常见错误」清单：科学计数法/丢前导 0、希腊用 `EL` 不是 `GR`、`Originally Placed on Market` 恰好一个 TRUE、数据从第 4 行开始、前三行锁定勿改、明细表靠 `UDI-DI Code`/`Basic UDI-DI Code` 关联。
- 纯展示页，零新增数据；description/example 已是中文，英文侧用 `t()` 包裹固定文案 + 原 header。

**验证**：页面列出所有 sheet 与列说明；与模板实际列一致（因同源 `template_schema`）；链接从导航可达。

---

## 任务 8：每个 service 配「去 EUDAMED 哪里上传」指引

**目标**：生成 XML 后，明确告诉用户去 EUDAMED 的哪里、按什么顺序传。

- `SUPPORTED_SERVICES` 每项的 `after` 扩成结构化上传指引（双语）：进入 EUDAMED 的哪个菜单（Devices / Data exchange / Bulk upload）、选与本工具一致的 service、按 `manifest` 顺序（先 DEVICE.POST 再 UDI_DI.POST）、上传后看 acknowledgement（`PROCESSED` / `PROCESSED_WITH_ERRORS`）。
- `views.upload_guidance(service_type)`（已存在）扩展：渲染上述步骤 + 指向 `EUDAMED_BULK_UPLOAD_HELP_URL` 的链接 + 「先 Playground TEST 验收」提醒 + 指引到任务 9 的「上传后被退回？点这里解析报告」。
- 纯内容/文案工作，不动生成逻辑。

**验证**：生成 XML 后的结果面板出现该 service 的上传步骤与官方链接；多文件 ZIP 时强调 manifest 顺序。

---

## 任务 9：EUDAMED 退回报告解析 + 只重导被拒记录

**目标**：用户把 EUDAMED 的 acknowledgement/response XML 传进来，工具解析出哪些实体被拒、为什么、对应本地哪条记录，并一键「只重新导出被拒的」。直接降低返工成本。

### 9a. 解析模块（新 `local_beta/ack_parser.py`）
- 解析 response Message XML（`service/Message/MessageType.xsd` 的 `ResponseEntitiesType` / `ResponseEntityType`：`entityCode`、`responseCode`(ProcessStatusCodeEnum)、`report`/`elementReport`、`operationErrorCode`/`operationErrorDetail`/`operationDetail`）。
- 输出每实体：`{entity_code, status, errors:[{code, detail}], matched_record:{type, id, code} | None}`。
- 映射：`entity_code` 去 `basic_records.basic_code` / `udi_records.udi_code` 匹配（兼容大小写/前后空格）。
- 容错：非预期 XML、空文件、非 response 报文都要优雅报「无法识别的报文」。

### 9b. 路由 + 视图
- GET `/ack`：上传表单（multipart，复用 import 的 `parse_multipart`）+ 说明「在 EUDAMED 下载 acknowledgement XML 后上传到这里」。
- POST `/ack`：解析 → 渲染结果表：实体 / 状态（PROCESSED 绿、PROCESSED_WITH_ERRORS 红）/ 错误明细 / 匹配到的本地记录（带详情页链接）。
- 结果页底部按钮「**只重新导出被拒的记录**」：带 `record_ids`（被拒且匹配到的）跳到 `/export?service_type=...&record_ids=...`（预选）。service_type 从报文的 service 节点推断，推断不出就让用户在导出页选。
- 导航/帮助页 + 任务 8 的上传指引里都给入口。

### 9c. 验证
- 用真实的 `PROCESSED_WITH_ERRORS` 应答（用户手上有历史 ACK，如 `APP-DTX-…`）解析 → 正确列出被拒实体 + 错误 + 匹配本地记录；「只重导被拒」能带正确 record_ids 跳转。
- 全 `PROCESSED` 的应答 → 显示「全部成功，无需返工」。
- 畸形/空 XML → 优雅提示，不崩。

---

## 任务 10（轻量）：空状态文案

**目标**：空表格替换成友好引导 + 按钮。

- 产品库为空 → 「还没有产品记录。先【下载模板】填写，再【导入 Excel】」+ 按钮（与任务 1 快速开始卡呼应；若有筛选条件且无结果 → 「没有符合条件的记录，[清除筛选]」）。
- 导出页记录为空 → 「没有可导出的记录，检查筛选或先去导入」。
- 导出历史为空 → 「还没有导出记录，去【导出任务】生成第一个 XML」。
- 复用现有 `alert_block` / 空判断；纯文案 + 按钮。

**验证**：空库/空筛选下各页显示引导而非空白表。

---

## 建议实施顺序（按性价比）

1. **第一批（高性价比、低风险，建议先做）**：任务 7（模板指引，纯展示、零风险）、任务 10（空状态）、任务 4（导入页瘦身）、任务 5（术语 tooltip）、任务 2（service 人话名 + 向导）。
2. **第二批**：任务 1（示例数据，含迁移列 + 安全闸）、任务 6（双源 ZIP 直链）、任务 8（上传指引）。
3. **第三批（最重 / 最novel）**：任务 9（ACK 解析返工闭环）、任务 3 进阶（noconsole + 托盘）。

## 不在本批范围
- 不动 exporter 的 XML 节点生成逻辑。
- 不引入后端外发网络（除已有的 GET 检查更新 / ZIP 直链探测）。
- 自动更新（自动下载替换）暂不做，仍是「给直链让用户手动下」。

## 收尾
- `constants.py`：`TOOL_VERSION = "0.8.0"`、`TOOL_VERSION_LABEL`、`TOOL_UPDATED`。
- `CHANGELOG.md` 顶部加 `## 0.8.0` 章节，逐条列本批改动（关系到 release workflow 抓取，格式照旧 `## 0.8.0 - YYYY-MM-DD`）。
- 全部新文案中英双语；新页面/按钮跑一遍中英切换无漏译硬编码中文。
- 启动 `python3 run_local_beta.py` 跑任务各自的验证清单；ACK 解析用真实应答验证。
