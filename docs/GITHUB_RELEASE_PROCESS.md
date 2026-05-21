# GitHub Release 发布流程

本项目推荐用 GitHub Releases 分发 Windows/Mac 内测包。用户不需要懂 Git，只需要从 Release 页面下载最新 ZIP；工具帮助页的“检查更新”可以读取 GitHub Releases API。

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

## 3. 创建 GitHub Release

1. 打开仓库页面，进入 `Releases`。
2. 点击 `Draft a new release`。
3. 创建 tag，例如 `v0.4.1`。tag 需要和 `TOOL_VERSION` 对齐。
4. Release title 写 `v0.4.1 - 内测版`。
5. Release notes 粘贴 `CHANGELOG.md` 中对应版本的内容。
6. 上传二进制附件，例如：
   - `EUDAMED_Local_Beta_Windows.zip`
   - `EUDAMED_Local_Beta_macOS.zip`（如有）
   - `EUDAMED_Template_v2.4.xlsx`（可选，方便用户单独下载模板）
7. 内测阶段可勾选 `Set as a pre-release`；稳定后取消。
8. 发布后确认 Release 页面能看到附件下载链接。

## 4. 配置工具内“检查更新”

发布仓库确定后，在 `local_beta/constants.py` 填入：

```python
RELEASES_API_URL = "https://api.github.com/repos/<你的账号>/<仓库名>/releases/latest"
RELEASES_PAGE_URL = "https://github.com/<你的账号>/<仓库名>/releases"
```

工具会读取 latest release 的 `tag_name`，与本地 `TOOL_VERSION` 比较；如有新版本，会在帮助页显示下载/发布页入口。

## 5. 中国大陆下载风险

GitHub Releases 可以直接分发，但中国大陆网络访问 GitHub、GitHub API、`github.com/.../releases/download/...` 可能不稳定或速度很慢。

推荐做法：

- GitHub 作为主发布源和版本记录源。
- 同步上传一份到大陆可访问镜像，例如 Gitee Release、阿里云 OSS、腾讯云 COS、蓝奏云或企业网盘。
- Release notes 中同时写 GitHub 下载链接和国内备用下载链接。
- 如果大量国内用户反馈“检查更新失败”，可以在工具里后续增加 `MIRROR_RELEASES_PAGE_URL` 或自托管 `latest.json`，让检查更新不依赖 GitHub API。

## 6. 用户侧说明

用户升级时只替换程序包，不要删除本机数据目录：

- 默认数据目录：程序旁边的 `local_beta_data/`
- 如使用环境变量：`EUDAMED_DATA_DIR`

生成 XML 不等于 EUDAMED 上传成功；升级工具不会自动改变本地记录的提交状态。
