# 0.9.9 更新与检查记录（2026-09-08）

范围：本地 0.9.8 工作区 → 0.9.9，模板 v2.12 → v2.13，生产 XSD 仍为 3.0.30。保留原有未跟踪官方核查目录和所有历史模板、客户文件、运行数据库；没有发布 GitHub/Gitee Release。

## 已修复

- Mac 打包仍引用 v2.6 模板、Info.plist 版本固定 0.4：现取当前工具版本，打包 v2.13 中英文模板。
- Mac WebKit 缺少上传文件面板及附件下载代理：新增 NSOpenPanel / NSSavePanel，已在实际窗口验证。
- Mac 后端输出管道没有持续消费：现持续读取并保留最近 64 KiB，避免长时间运行堵塞。
- Mac 直接附着 8765 任意现有 HTTP 服务：改为本次应用独立端口，启动随包后端，避免新版窗口连接旧服务。
- Windows 本地构建只安装 PyInstaller，缺少静态分析所需 openpyxl / et_xmlfile；缺少原生命令退出码检查：已补齐，编译和打包失败时拒绝继续归档。
- 两平台原脚本复制整个 official_docs 和旧工具目录：改为运行必需模块和生产 XSD，Mac ZIP 已确认不含用户库、反馈资料和核查目录。

## Original manufacturer

- 注册与 UDI 更新：DEVICE.POST / UDI_DI.POST / UDI_DI.PATCH 输出 productDesignerActor。
- 独立更新：PRODUCT_DESIGNER.PUT → pd:DTXProductDesigner，带 UDI 标识和 pda:productDesignerActor。操作为 PUT，不是 PATCH。
- 支持制造商 Actor ID/SRN，或组织名称及国家、邮编、城市、街道、门牌号，二选一。
- 地址填写时国家及邮编必填。组织名称语言为 ANY；冲突、非法 SRN/国家、旧内部 Product Designer ID、空白独立更新均阻止导出。
- PR/SPP 暂不支持；本版不提供联系人字段或删除原始制造商操作。提交组织更新前必须核对期望的完整信息。
- 依据：本地官方 SAMPLE_DTX_UDI_015.01.xml / 015.02.xml、生产 XSD ProductDesignerType.xsd / UDIDIType.xsd；官方 [M2M 用户指南](https://webgate.ec.europa.eu/eudamed-help/en/files/M2M%20-%20user%20guide.pdf) 列出该服务和两类样例。

## 发布前复核修正

- 官方 Production 2.27.0 服务定义要求 Market Information 和 Container Package 更新使用 `PUT`。工具原先把两者的 recipient operation 错写为 `PATCH`，现已改为 `MARKET_INFO.PUT` / `PACKAGE_UDI.PUT`；旧 `.PATCH` 本地链接仍兼容并自动规范化。
- Market Information 页面不再误导用户通过 `MARKET_INFO.PUT` 修改首次投放成员国：该标记必须与 EUDAMED 当前值一致，如需修改应使用 `UDI_DI.PATCH`。首页和导出页已移除空白的“暂未开放”区域。
- 历史 `MDR_MDD` / `IVDR_IVDD` 混合主表仍按 Applicable Legislation 精确拆分。空白或无法识别的法规值不再写入产品库，迁移报告会保留待修正行并明确提示，避免法规不明记录被误认作目标 sheet 的法规。
- GitHub Release run 34213112404 固定在旧提交 7568315（0.9.8）；重新运行同一 run 仍使用旧 SHA。0.9.9 需要在包含本报告和 `TOOL_VERSION = "0.9.9"` 的新提交上重新 dispatch。
- 已在上述修正后重新构建 `dist/EUDAMED Local Beta.app` 和 `dist/EUDAMED_Local_Beta_Mac_arm64.zip`；包内 `local_beta` 与当前工作树逐文件一致，v2.13 中英文模板逐字节一致。构建脚本现会同步重写 `SHA256SUMS-0.9.9.txt`，避免重建后校验文件仍指向旧产物。
- Mac 启动器设置 `PYTHONDONTWRITEBYTECODE=1`，避免运行时在已签名 `.app` 内生成 `__pycache__` 并破坏资源封印；重建后的包在隔离服务烟测前后均通过严格签名校验。

## 验证

最终结果：`compileall`、`git diff --check` 通过；最终完整测试 **104 项通过**（162.635 秒，0 失败）。模板已重新生成并完成包内一致性验证。

- 在原 95 项发布测试基础上新增服务矩阵/真实 PUT operation、版本契约、空白法规迁移阻断、PR 的 Basic UDI / Container Package 更新，以及本轮 UI 和 Mac 签名保护测试，最终 104 项通过。
- 原始制造商两种信息形式 × MDR/IVDR/MDD/AIMDD/IVDD × 四种服务通过生产 XSD 结构校验。
- 中英文 v2.13 实际导入、保存字段、独立 PUT 导出通过；根目录、旧工具 templates 目录和 Mac 包内对应文件逐字节一致。
- Mac release 编译、ad-hoc 签名验证、ZIP 完整性通过。实际窗口显示 0.9.9；系统面板下载的模板与根目录模板逐字节一致。
- Mac 系统文件面板选择合成 Excel 并导入成功，1 Basic + 1 UDI，导入错误 0；临时库中的 DEVICE.POST 与 PRODUCT_DESIGNER.PUT HTTP 预检、导出、下载通过，生成文件再次通过生产 XSD。
- 当前 v2.13 合成工作簿通过隔离本地 HTTP 服务导入（0 错误、0 警告）；DEVICE.POST 与 MARKET_INFO.PUT 均成功导出并通过生产 XSD 3.0.30，MARKET_INFO recipient operation 实际为 PUT。
- 原生 Mac 应用及包内 HTTP 服务均使用 `/tmp/eudamed-099-mac-app-smoke` 等隔离目录测试；没有向 EUDAMED 上传合成记录，也没有读写用户正式产品库。

## 交付及边界

- dist/EUDAMED Local Beta.app；dist/EUDAMED_Local_Beta_Mac_arm64.zip。
- EUDAMED_Template_v2.13.xlsx；EUDAMED_Template_v2.13_EN.xlsx。
- Mac 包为 Apple Silicon arm64，本机需要 Python 3.10+；本地 ad-hoc 签名，未进行 Developer ID 公证，未验证 Intel Mac。
- Windows 完成共享代码/模板测试和构建脚本静态检查；本机没有执行 Windows 原生 PyInstaller 打包和 EXE 冒烟，不能据此宣称 Windows 成品已验证。
- 未做 Excel/WPS 原生全工作簿视觉回归；模板已按现有生成器保持样式并通过结构及导入检查。
- 未在 Playground/Production 执行业务上传；生产 XSD 通过不等于官方业务接受。本次不改变生产/Playground XSD 版本基线。
