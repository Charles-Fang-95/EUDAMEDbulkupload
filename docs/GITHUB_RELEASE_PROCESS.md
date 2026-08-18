# GitHub / Gitee Release 发布流程

本项目推荐用 GitHub Releases 作为主发布源，并同步一份到 Gitee Release 作为中国大陆下载镜像。用户不需要懂 Git，只需要从 Release 页面下载最新 ZIP；工具帮助页的“检查更新”优先读取 GitHub Releases API，GitHub 失败时回退到 Gitee Release API。

## 1. 仓库设置

1. 在 GitHub 新建仓库，例如 `eudamed-local-beta`。
2. 如果希望用户无需登录即可下载，仓库应设为 Public。Private 仓库的 Release asset 通常需要登录/权限，不适合普通客户下载。
3. 不要把客户 Excel、SQLite 数据库、EUDAMED response、收款码原图等隐私/个人文件提交到仓库。
4. 建议提交代码、模板、官方 XSD 包、打包脚本和文档；`local_beta_data/` 不提交。

## 2. 每次发布前

1. 更新 `local_beta/constants.py`：
   - `TOOL_VERSION`
   - `TOOL_VERSION_LABEL`
   - `TOOL_UPDATED`
2. 更新 `CHANGELOG.md`，写清楚工具、模板、XSD 或校验规则变化。
3. 重新生成模板：
   ```bash
   python3 -m local_beta.build_unified_template
   ```
4. 跑基础检查：
   ```bash
   python3 -m compileall local_beta
   ```
5. 在 Windows 机器上重新构建 Windows 包，生成 `dist/EUDAMED_Local_Beta_Windows.zip`。

## 3. GitHub Actions 自动发布

当前仓库使用 `.github/workflows/release.yml` 自动构建 Windows ZIP，并发布到 GitHub Release 和 Gitee Release。

首次使用前需要在 GitHub 仓库配置 secret：

1. 打开 GitHub 仓库 `Settings -> Secrets and variables -> Actions`。
2. 新增 repository secret：
   ```text
   GITEE_TOKEN
   ```
3. `GITEE_TOKEN` 使用 Gitee 个人访问令牌，令牌需要能管理 `Charles-Fang-95/EUDAMEDbulkupload` 的 Release。

发布步骤：

1. 打开 GitHub 仓库 `Actions`。
2. 选择 `Release` workflow。
3. 点击 `Run workflow`。
4. `version` 填不带 `v` 的版本号，例如 `0.7.1`。该版本必须与 `local_beta/constants.py` 的 `TOOL_VERSION` 和 `CHANGELOG.md` 顶部章节一致。
5. workflow 会生成 `dist/EUDAMED_Local_Beta_Windows.zip`，并把它、`EUDAMED_Template_v2.12.xlsx` 和 `EUDAMED_Template_v2.12_EN.xlsx` 上传到 GitHub Release。
6. 同一 workflow 会调用 Gitee API 创建/更新同 tag 的 Gitee Release，并尽力上传同名附件；Gitee 镜像失败不会阻断 GitHub 主发布。

Gitee Release 附件限制：普通项目单个附件不能超过 100M，仓库总附件容量普通项目不能超过 1G。GitHub runner 到 Gitee 上传 50MB 以上附件可能因跨境网络超时；如 Gitee ZIP 上传失败，GitHub Release 仍有效，Gitee 可手动补传或改用 OSS/COS/网盘等备用下载源。

## 4. 手动创建 GitHub Release（备用）

1. 打开仓库页面，进入 `Releases`。
2. 点击 `Draft a new release`。
3. 创建 tag，例如 `v0.7.0`。tag 需要和 `TOOL_VERSION` 对齐。
4. Release title 写当前版本，例如 `v0.9.8 - 公开测试版`。
5. Release notes 粘贴 `CHANGELOG.md` 中对应版本的内容。
6. 上传二进制附件，例如：
   - `EUDAMED_Local_Beta_Windows.zip`
   - `EUDAMED_Local_Beta_macOS.zip`（如有）
   - `EUDAMED_Template_v2.12.xlsx`（中文模板，方便用户单独下载）
   - `EUDAMED_Template_v2.12_EN.xlsx`（英文模板，方便海外用户单独下载）
7. 公开测试阶段可勾选 `Set as a pre-release`；稳定后取消。
8. 发布后确认 Release 页面能看到附件下载链接。

建议附件命名保持稳定。GitHub 支持 latest release 固定下载地址：

```text
https://github.com/Charles-Fang-95/EUDAMEDbulkupload/releases/latest
https://github.com/Charles-Fang-95/EUDAMEDbulkupload/releases/latest/download/EUDAMED_Local_Beta_Windows.zip
```

如果每次 Windows 包都叫 `EUDAMED_Local_Beta_Windows.zip`，这个直链不会随版本号变化，适合发给非技术用户。

## 5. 配置工具内“检查更新”

发布仓库确定后，在 `local_beta/constants.py` 填入：

```python
RELEASES_API_URL = "https://api.github.com/repos/<你的账号>/<仓库名>/releases/latest"
RELEASES_PAGE_URL = "https://github.com/<你的账号>/<仓库名>/releases"
```

工具会读取 latest release 的 `tag_name`，与本地 `TOOL_VERSION` 比较；如有新版本，会在帮助页显示下载/发布页入口。

当前工具还配置了 Gitee 镜像：

```python
GITEE_RELEASES_API_URL = "https://gitee.com/api/v5/repos/Charles-Fang-95/EUDAMEDbulkupload/releases?per_page=1"
GITEE_RELEASES_PAGE_URL = "https://gitee.com/Charles-Fang-95/EUDAMEDbulkupload/releases"
```

检查更新时优先访问 GitHub；如果 GitHub API 因网络、限流或不可达失败，会尝试读取 Gitee 最新 Release，并在帮助页标明来源。

如果 Release 上传了多个附件，帮助页会列出全部附件，并优先高亮当前系统更可能需要的安装包。Windows 用户通常应下载 `EUDAMED_Local_Beta_Windows.zip`。

如果仓库还没有任何 GitHub Release，帮助页会显示“仓库尚未发布版本”。这不是断网；需要先创建 tag + Release + 上传 ZIP，检查更新才会变成可用。

## 6. 中国大陆下载风险

GitHub Releases 可以直接分发，但中国大陆网络访问 GitHub、GitHub API、`github.com/.../releases/download/...` 可能不稳定或速度很慢。

推荐做法：

- GitHub 作为主发布源和版本记录源。
- 同步上传一份到大陆可访问镜像，例如 Gitee Release、阿里云 OSS、腾讯云 COS、蓝奏云或企业网盘。当前 workflow 已自动同步 Gitee Release。
- Release notes 中同时写 GitHub 下载链接和国内备用下载链接。
- 如果大量国内用户反馈“检查更新失败”，可进一步考虑自托管 `latest.json`，让检查更新不依赖 GitHub/Gitee API。

## 7. 用户侧说明

用户升级时只替换程序包，不要删除本机数据目录：

- 默认数据目录：程序旁边的 `local_beta_data/`
- 如使用环境变量：`EUDAMED_DATA_DIR`

推荐给用户的升级说明：

1. 打开工具的帮助页，点击“检查更新”。
2. 如果提示有新版本，下载 `EUDAMED_Local_Beta_Windows.zip`。
3. 关闭当前工具。
4. 解压新版 ZIP 到新目录，或覆盖原程序目录；不要删除 `local_beta_data/`。
5. 启动新版工具，确认帮助页版本号已更新。

生成 XML 不等于 EUDAMED 上传成功；升级工具不会自动改变本地记录的提交状态。
