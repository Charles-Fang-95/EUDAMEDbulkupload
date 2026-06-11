# Windows Codex Build Handoff

把本文件和项目源码交给 Windows 版 Codex。目标是在 Windows 上生成可发给企业内测的绿色版 ZIP 包。

## 任务

请在 Windows 环境中为这个项目生成 Windows 内测包，并验证 exe 能启动本地网页。

## 必须保留的项目状态

- 不要回退已有网页 UI 改动。
- 不要删除帮助页中的 Ko-fi、支付宝和微信支持入口。
- 不要修改 EUDAMED XML 导出核心逻辑，除非构建失败必须修复。
- 当前支持的 EUDAMED production XSD version 是 `3.0.30`。
- 当前默认模板是 `EUDAMED_Template_v2.9.xlsx`。
- `DEVICE.POST` 支持 Regulation Device（MDR/IVDR）、SPP，以及 Legacy Device / EUDI（MDD/AIMDD/IVDD）。不要漏测 AIMDD。

## Windows 构建命令

在项目根目录打开 PowerShell，运行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\packaging\windows\build_windows_exe.ps1
```

成功后应生成：

```text
dist\EUDAMED_Local_Beta\EUDAMED_Local_Beta.exe
dist\EUDAMED_Local_Beta_Windows.zip
```

给企业测试时发送 `dist\EUDAMED_Local_Beta_Windows.zip`，不要只发送单个 `.exe`。

## 验证步骤

1. 双击 `dist\EUDAMED_Local_Beta\EUDAMED_Local_Beta.exe`。
2. 浏览器打开 `http://127.0.0.1:8765`。
3. 确认首页、导入、产品库、导出、帮助页面能打开。
4. 打开帮助页，确认 Ko-fi 链接、支付宝收款码、微信收款码存在。
5. 下载模板，确认下载的是 `EUDAMED_Template_v2.9.xlsx`。
6. 导入一个 v2.9 模板样例，确认无 Python traceback。
7. 导出 `DEVICE.POST` XML，确认 XML 版本号为 `3.0.30`，且本地 XSD 校验仍通过。
8. 构造/复制三条 legacy 场景分别测试 `MDD`、`AIMDD`、`IVDD`，确认：
   - `MDD` 和 `AIMDD` 输出 `MDEUDeviceType` / `MDEUData` / `MDEUDI`。
   - `AIMDD` 的 Basic XML 中包含 `<eudi:applicableLegislation>AIMDD</eudi:applicableLegislation>`。
   - `IVDD` 输出 `IVDEUDeviceType` / `IVDEUData` / `IVDEUDI`。
   - 三者都通过 production XSD `3.0.30` 校验。
9. Market Info 里如有希腊，确认导出的 `<marketinfo:country>` 是 `EL`，不是 `GR`。

## 注意事项

- PyInstaller 不能可靠从 macOS 交叉生成 Windows `.exe`，所以必须在 Windows 或 Windows 虚拟机上构建。
- 未签名 exe 可能触发 Windows Defender / SmartScreen 提示，这是内测阶段的预期风险。
- 本地数据默认写入 exe 同级目录下的 `local_beta_data`，不要把该目录打进给企业的初始包。
- 如果构建失败，优先修复 Windows 路径、PyInstaller data file、资源路径问题，不要重构业务逻辑。
