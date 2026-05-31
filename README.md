# EUDAMED Bulk Upload 助手 / EUDAMED Bulk Upload Helper

> 当前版本 **0.7.0**，对应 EUDAMED 官方 XSD **3.0.30**。
> Current version **0.7.0**, built for EUDAMED official XSD **3.0.30**.

---

# 中文

## 简介

这是一个**本地运行的网页小工具**，帮医疗器械企业把 EUDAMED 的设备数据从 Excel 转成可上传的官方 XML：

> 下载 Excel 模板 → 填写 → 导入本地工具 → 自动校验 / 管理 → 按官方 service 生成 bulk upload XML → 上传到 EUDAMED。

- 支持 **MDR / IVDR**（Regulation Device）和 **MDD / AIMDD / IVDD**（Legacy Device / EUDI）。
- 支持 6 类官方 service：`DEVICE.POST`、`UDI_DI.POST`、`Basic_UDI.PATCH`、`UDI_DI.PATCH`、`MARKET_INFO.PATCH`、`PACKAGE_UDI.PATCH`。
- 自动处理官方 **300 条/XML** 上限：超出时自动拆成多个 XML，并打包成 ZIP 附带上传顺序清单（manifest）。
- 数据只存在你自己的电脑上（本地 SQLite）。

> ⚠️ 这是**个人开发的非官方工具**，与欧盟委员会 / EUDAMED 官方无任何关联。它不替你判断合规，最终一切以 EUDAMED 官方平台为准。

## 适用对象

面向企业**法规事务（RA）人员**，不需要懂编程也能用。界面支持**中英双语**，右上角一键切换。

## 如何下载

### 方式 A：下载现成包（推荐，非技术用户）

到 GitHub Releases 页面下载最新 ZIP（含 Windows 包），解压后运行：

- 最新版本：<https://github.com/Charles-Fang-95/EUDAMEDbulkupload/releases/latest>

Windows 用户建议按这个顺序操作：

1. 打开上面的 Releases 页面。
2. 在 `Assets` 中下载 `EUDAMED_Local_Beta_Windows.zip`。
3. 右键 ZIP → 全部解压 / Extract All，不要直接在压缩包里运行。
4. 进入解压后的文件夹，双击启动程序。
5. 浏览器会打开本地地址 `http://127.0.0.1:8765`；如果没有自动打开，请手动复制这个地址到浏览器。

> 注：需要作者先在 GitHub 发布 Release，上面的下载链接才会有内容。如果页面是空的，说明还没发布正式包，请先用方式 B，或联系作者。

### 方式 B：从源码运行（开发者 / 暂无现成包时）

需要本机有 **Python 3**（建议 3.10 以上）。常用的 Excel 依赖（openpyxl 等）已随仓库内置在 `EUDAMED_TOOL_v2/lib/`，一般无需额外安装。

```bash
git clone https://github.com/Charles-Fang-95/EUDAMEDbulkupload.git
cd EUDAMEDbulkupload
python3 run_local_beta.py
```

然后用浏览器打开：

```text
http://127.0.0.1:8765
```

## 如何更新

1. 在工具的「帮助」页点 **检查更新**——它会读取 GitHub Releases，有新版会显示版本号和下载链接。
2. 下载新 ZIP，**覆盖**到原目录（或直接运行新版 exe）。
3. 你的数据（`local_beta_data/` 里的数据库和导出文件）**不会被覆盖**，会保留。也可以用环境变量 `EUDAMED_DATA_DIR` 把数据目录指到别处。

> 工具版本和官方 XSD 版本是**绑定**的：EUDAMED 升级 XSD 时必须整包更新工具，不能只替换 XSD 文件，否则生成的 XML 会不合规。

## 工具怎么用

1. **下载模板**：顶栏「下载模板」，或直接用仓库里的 `EUDAMED_Template_v2.4.xlsx`。
2. **填写 Excel**：在 Excel / WPS 里填数据（填写规则见下一节）。
3. **导入 Excel**：在「导入 Excel」页上传，系统立即校验并显示新增 / 已更新 / 错误行。
4. **产品库**：浏览、搜索、按 Manufacturer SRN 切换不同 actor；详情页可做临时修正（正式维护建议回到 Excel）。
5. **导出任务**：选择 service → 载入并勾选记录 → 先「预检」→ 再「生成 XML」。超过 300 条会自动拆分成多个 XML 并打成 ZIP，里面的 manifest 会标明**上传顺序**。
6. **上传 EUDAMED**：按页面 / manifest 指引上传。**先在 Playground TEST 环境验收**，通过后再上生产。

辅助功能：
- **迁移模板**（`/migrate-template`）：把旧版或客户自有的 EUDAMED Excel 搬到当前 v2.4 模板，并生成迁移报告；能确指的字段才自动搬，搬不准的列会列在报告里。
- **XSD 版本**页：核对工具内置 XSD、本地 XSD 包、官方文档页版本是否一致。

## 模板怎么用

模板 `EUDAMED_Template_v2.4.xlsx` 的结构：

- **两个主录入表**：`MDR_MDD`（医疗器械）、`IVDR_IVDD`（体外诊断）。
  - 第 1 行 = 字段名，第 2 行 = 中文说明，第 3 行 = 示例（前三行已锁定，请勿改）。
  - **正式数据从第 4 行开始填**。
- **7 个明细表**：`Trade Names`、`Market Info`、`Package Info`、`Device Certificates`、`Critical Warnings`、`Storage Conditions`、`CMR Substances`，通过 `UDI-DI Code` / `Basic UDI-DI Code` 与主表关联。
- 下拉选项（语言、国家、签发机构、储存 / 警告类型等）直接来自官方 XSD，会随 XSD 升级自动更新。

**关键填写规则：**
- 编码类字段（UDI / GTIN、Basic UDI-DI、Package UDI-DI、Reference、SRN、EMDN）必须按**文本**维护，避免 Excel / WPS 把它变成科学计数法或丢掉前导 0。
- `Market Info`：同一个 UDI-DI 可以填多个上市国家，但 `Originally Placed on Market`（首个投放成员国）**必须且只能有一个 `TRUE`**，其余填 `FALSE`。
- 多语言 / 多个商品名请用 `Trade Names` 明细表；主表的 Trade Name 只是快捷输入。
- 触发 MDR Art. 29(3) / IVDR Art. 26(2) 或 legacy 指令证书场景时，请在 `Device Certificates` 明细表填写 product certificate 信息；工具会输出 `deviceCertificateLinks`，但 NB 确认仍发生在 EUDAMED 官方流程中。

## 注意事项

- **非官方软件**，与欧盟委员会 / EUDAMED 无关联；按「现状」提供，不保证生成的 XML 一定符合 EUDAMED 要求；**数据准确性与合规责任由使用者承担**。正式提交前请务必在 EUDAMED Playground（测试环境）验收：<https://webgate.training.ec.europa.eu/eudamed-play/landing-page#/>
- **DTX 规则（重要）**：一次 `DEVICE.POST` 里，每个 Basic UDI-DI 只能创建一次（随它的第 1 个 UDI-DI 一起）；同一个 Basic 下的其余 UDI-DI 必须走 `UDI_DI.POST` 追加。工具已自动这样拆分；若重复在 DEVICE.POST 里带同一个 Basic，EUDAMED 会报「already exists」。
- 部分官方字段当前**只收集、暂不输出到 XML**（如 eIFU URL、Public Email 等）。填了不等于已提交。完整清单见 [`docs/DATA_DICTIONARY_FIELD_AUDIT.md`](docs/DATA_DICTIONARY_FIELD_AUDIT.md)。
- 数据默认只保存在本机 `local_beta_data/`；工具**没有登录权限控制**，请勿在共享电脑上保存敏感数据。

## 版本历史

当前 **0.7.0 / XSD 3.0.30**。完整变更记录见 [`CHANGELOG.md`](CHANGELOG.md)。

## 作者与授权

- 作者：**Xiongfei Fang** · 邮箱：<qecslan@hotmail.com>
- 如果这个工具帮到你，欢迎在「帮助」页通过支付宝 / 微信 / Ko-fi 请作者喝杯咖啡。
- **版权所有 © 2026 Xiongfei Fang，保留所有权利。本软件非开源**：未经作者书面许可，不得复制、修改、分发或用于商业用途。
- 免责声明：本工具按「现状」提供，作者不对因使用或无法使用本工具造成的任何直接或间接损失负责。

> 维护者 / 目录结构 / 发布流程等内部文档见 [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) 与 [`docs/GITHUB_RELEASE_PROCESS.md`](docs/GITHUB_RELEASE_PROCESS.md)。

---

# English

## Introduction

This is a **local web tool** that helps medical device companies turn EUDAMED device data from Excel into upload-ready official XML:

> Download the Excel template → fill it in → import into the tool → automatic validation / management → generate bulk-upload XML per official service → upload to EUDAMED.

- Supports **MDR / IVDR** (Regulation Device) and **MDD / AIMDD / IVDD** (Legacy Device / EUDI).
- Supports the 6 official services: `DEVICE.POST`, `UDI_DI.POST`, `Basic_UDI.PATCH`, `UDI_DI.PATCH`, `MARKET_INFO.PATCH`, `PACKAGE_UDI.PATCH`.
- Handles the official **300-entities-per-XML** limit automatically: oversized jobs are split into multiple XML files and packed into a ZIP with an upload-order manifest.
- Data stays only on your own computer (local SQLite).

> ⚠️ This is an **unofficial, individually developed tool** with no affiliation to the European Commission or EUDAMED. It does not make compliance decisions for you — the official EUDAMED platform is always authoritative.

## Who it's for

Built for company **Regulatory Affairs (RA)** staff — no programming needed. The UI is **bilingual (中文 / English)**, switchable from the top-right corner.

## Download

### Option A: Download a ready package (recommended for non-technical users)

Download the latest ZIP (with the Windows package) from GitHub Releases and unzip:

- Latest release: <https://github.com/Charles-Fang-95/EUDAMEDbulkupload/releases/latest>

Recommended Windows steps:

1. Open the Releases page above.
2. Under `Assets`, download `EUDAMED_Local_Beta_Windows.zip`.
3. Right-click the ZIP and choose Extract All; do not run it from inside the compressed folder.
4. Open the extracted folder and double-click the launcher.
5. The browser should open `http://127.0.0.1:8765`; if it does not, copy this address into your browser manually.

> Note: the author must publish a GitHub Release first for that link to contain anything. If the page is empty, no official package has been published yet — use Option B or contact the author.

### Option B: Run from source (developers / when no package exists yet)

Requires **Python 3** (3.10+ recommended). Common Excel dependencies (openpyxl, etc.) are vendored under `EUDAMED_TOOL_v2/lib/`, so usually no extra install is needed.

```bash
git clone https://github.com/Charles-Fang-95/EUDAMEDbulkupload.git
cd EUDAMEDbulkupload
python3 run_local_beta.py
```

Then open in a browser:

```text
http://127.0.0.1:8765
```

## Update

1. On the tool's **Help** page, click **Check for updates** — it reads GitHub Releases and shows the new version and download link if available.
2. Download the new ZIP and **overwrite** the old folder (or run the new exe).
3. Your data (the database and exports under `local_beta_data/`) is **kept, not overwritten**. You can also point the data folder elsewhere with the `EUDAMED_DATA_DIR` environment variable.

> The tool version and the official XSD version are **coupled**: when EUDAMED upgrades the XSD, update the whole tool package — do not just swap the XSD files, or the generated XML will be non-compliant.

## Using the tool

1. **Download the template**: top-bar "Download Template", or use `EUDAMED_Template_v2.4.xlsx` from the repo.
2. **Fill in the Excel** (rules in the next section).
3. **Import Excel**: upload on the "Import Excel" page; it validates immediately and shows created / updated / error rows.
4. **Product Library**: browse, search, switch actor by Manufacturer SRN; the detail page allows quick fixes (for real maintenance, go back to Excel).
5. **Export**: choose a service → load and tick records → run "Pre-check" → then "Generate XML". Jobs over 300 entities are split into multiple XML files and packed into a ZIP whose manifest lists the **upload order**.
6. **Upload to EUDAMED** following the page / manifest. **Validate in the Playground TEST environment first**, then go to production.

Helpers:
- **Migrate template** (`/migrate-template`): move an old or customer-specific EUDAMED Excel into the current v2.4 template and produce a migration report. Only confidently mappable fields are moved; unmapped columns are listed in the report.
- **XSD version** page: check that the tool's built-in XSD, local XSD package, and the official documentation version are consistent.

## Using the template

Structure of `EUDAMED_Template_v2.4.xlsx`:

- **Two main entry sheets**: `MDR_MDD` (medical devices), `IVDR_IVDD` (in-vitro diagnostics).
  - Row 1 = field name, Row 2 = description, Row 3 = example (first three rows are locked — do not edit).
  - **Real data starts at Row 4.**
- **Seven detail sheets**: `Trade Names`, `Market Info`, `Package Info`, `Device Certificates`, `Critical Warnings`, `Storage Conditions`, `CMR Substances`, linked to the main sheets via `UDI-DI Code` / `Basic UDI-DI Code`.
- Dropdown options (languages, countries, issuing entities, storage / warning types, etc.) come straight from the official XSD and update automatically when the XSD is upgraded.

**Key rules:**
- Code fields (UDI / GTIN, Basic UDI-DI, Package UDI-DI, Reference, SRN, EMDN) must be kept as **text**, to avoid Excel / WPS turning them into scientific notation or dropping leading zeros.
- `Market Info`: one UDI-DI may have several market countries, but `Originally Placed on Market` **must have exactly one `TRUE`**; the rest should be `FALSE`.
- For multiple / multilingual trade names, use the `Trade Names` sheet; the main-sheet Trade Name is only a shortcut.
- For MDR Art. 29(3) / IVDR Art. 26(2) or legacy directive certificate scenarios, fill product certificate information in `Device Certificates`; the tool writes `deviceCertificateLinks`, while NB confirmation still happens in the official EUDAMED flow.

## Important notes

- **Unofficial software**, not affiliated with the European Commission / EUDAMED; provided "as is" with no warranty that the generated XML fully meets EUDAMED requirements; **the user is responsible for data accuracy and compliance**. Always validate in the EUDAMED Playground (test) before any production submission: <https://webgate.training.ec.europa.eu/eudamed-play/landing-page#/>
- **DTX rule (important)**: within one `DEVICE.POST`, each Basic UDI-DI can be created only once (together with its first UDI-DI); the remaining UDI-DIs of that Basic must be added via `UDI_DI.POST`. The tool splits this automatically; repeating the same Basic inside one DEVICE.POST makes EUDAMED return "already exists".
- Some official fields are currently **collected but not yet written to XML** (e.g. eIFU URL, Public Email). Filling them does not mean they were submitted. Full list: [`docs/DATA_DICTIONARY_FIELD_AUDIT.md`](docs/DATA_DICTIONARY_FIELD_AUDIT.md).
- Data is stored only on your machine under `local_beta_data/`; the tool has **no login / access control**, so do not keep sensitive data on a shared computer.

## Version history

Current **0.7.0 / XSD 3.0.30**. Full changelog: [`CHANGELOG.md`](CHANGELOG.md).

## Author & license

- Author: **Xiongfei Fang** · Email: <qecslan@hotmail.com>
- If this tool helps you, feel free to support the author via Alipay / WeChat / Ko-fi on the Help page.
- **Copyright © 2026 Xiongfei Fang. All rights reserved. This software is NOT open source**: it may not be copied, modified, distributed or used commercially without the author's written permission.
- Disclaimer: provided "as is"; the author is not liable for any direct or indirect loss arising from the use of, or inability to use, this tool.

> Maintainer / project-structure / release docs: [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) and [`docs/GITHUB_RELEASE_PROCESS.md`](docs/GITHUB_RELEASE_PROCESS.md).
