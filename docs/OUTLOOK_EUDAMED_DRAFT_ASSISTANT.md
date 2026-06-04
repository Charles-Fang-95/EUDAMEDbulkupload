# Outlook EUDAMED 草稿助手

这个脚本用于半自动处理 Outlook 中包含 `EUDAMED` 或 `XML` 字眼的邮件：读取邮件正文和附件，分析 EUDAMED response XML 常见错误，并生成回复草稿。它不会自动发送邮件。

脚本位置：

```bash
python3 scripts/outlook_eudamed_draft_assistant.py
```

## 推荐流程

先 dry-run，只生成本地草稿文本：

```bash
python3 scripts/outlook_eudamed_draft_assistant.py --dry-run --limit 10 --days 14
```

输出会保存到：

```text
local_beta_data/outlook_draft_assistant/
```

同时，匹配邮件的附件会按 case 保存到：

```text
Feedback case/
```

脚本会读取现有目录编号，例如已有 `1# feedback`、`2# feedback` 时，下一封匹配邮件会创建：

```text
Feedback case/3# feedback/
```

附件按邮件中的顺序加前缀保存，例如：

```text
01_APP-DTX-000061870.xml
02_EUDAMED_Template_v2.7.xlsx
```

每封邮件一个 case 文件夹。若从 `.eml` 或 Outlook 邮件读取，还会保存 `email_context.txt`，包含主题、发件人和正文，便于后续复查。

确认内容格式没问题后，再创建 Outlook 草稿：

```bash
python3 scripts/outlook_eudamed_draft_assistant.py --create-drafts --limit 10 --days 14
```

创建后请打开 Outlook 草稿箱，人工确认后再发送。

## 它会判断什么

脚本会优先解析 XML 附件，尤其是 EUDAMED acknowledgement / response XML。当前可识别的常见情况包括：

- EUDAMED 页面选择的 service 与 XML 内 service 不一致，例如用 `UDI_DI.PATCH` 上传了 `UDI_DI.POST` 文件。
- `Special Device Type` 填入了产品名称或型号，而不是官方枚举值。
- PATCH 类服务疑似缺少 EUDAMED 当前 version。
- Basic UDI-DI / UDI-DI 已存在，可能应改用追加或 PATCH 服务。
- XML schema 校验错误，例如枚举、日期、数字格式或字段位置不符合 XSD。
- ZIP 分片包未按 manifest 顺序上传，或依赖的 `UDI_DI.POST` 早于对应 `DEVICE.POST` 上传。

## Outlook 权限

首次运行 Outlook 模式时，macOS 可能会提示允许 Terminal / Codex 自动控制 Microsoft Outlook。必须允许后，脚本才能读取匹配邮件、保存附件和创建草稿。

如果你使用的是新版 Outlook for Mac，AppleScript 支持可能不完整。此时可以手动把邮件或附件导出到一个文件夹，再运行：

```bash
python3 scripts/outlook_eudamed_draft_assistant.py --source-dir /path/to/exported/files --dry-run
```

`--source-dir` 支持：

- `.eml` 邮件文件
- `.xml` response 文件

## 安全边界

- 脚本只匹配包含 `eudamed` 或 `xml` 的邮件。
- 默认只生成本地草稿文本，不写 Outlook。
- 即使用 `--create-drafts`，也只保存到 Outlook 草稿箱，不会发送。
- 建议发送前检查客户名称、附件分析、错误解释和工具待更新项。
