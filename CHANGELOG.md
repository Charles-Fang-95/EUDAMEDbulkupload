# Changelog

本文件记录本地内测工具和 Excel template 的关键变更，便于对外发包、排查客户问题和回溯 EUDAMED 规则变化。

## 0.9.2 - 2026-06-05

- 概览首页新增轻量更新提示：检测到 GitHub/Gitee 有新版本时引导用户到帮助页下载，检查结果缓存 12 小时以避免频繁请求。
- 旧模板导入/迁移增加 v2.7 字段风险提示：自动归一 Special Device Type / Substance Type 时显示 warning，无法归一时继续报错，提醒用户重点核对 v2.6-v2.7 后变化字段。
- 修复 Special Device Type 归一警告误报：当前模板下拉值（`代码 - 标签` 格式）剥离为代码属正常操作，不再误报「已自动归一」；只有真正的旧写法/别名才提示核对。
- 修正 Maximum number of reuses 导出逻辑：一次性使用器械始终按官方 XSD 输出 `0`；可重复使用但未声明最大重复使用次数时输出 `-1`，不再默认输出 `1`；模板说明同步补充 `0 / -1 / 正整数` 的填写规则。
- 新增必填布尔字段留空提示（同类问题）：Implantable、Active Device、Measuring Function 等官方必填布尔留空时仍按 false 输出，但导出预检会按法规给出 warning「该字段留空，将按 false 处理，请确认」，避免漏填被无声声明为 FALSE。
- 默认模板升级为 `EUDAMED_Template_v2.8.xlsx`：IVDR/IVDD 主表新增人源/动物源字段，Market Info 明确同一 UDI-DI 多国家应逐行填写。
- 修复 IVD 字段适用性：IVDR/IVDD 不再要求 `Containing Latex`，`New Device (IVDR)` 仅 IVDR Regulation Device 输出，Legacy Device 不再输出 `baseQuantity`。

## 0.9.1 - 2026-06-04

- 默认模板升级为 `EUDAMED_Template_v2.7.xlsx`，把 `Basic - Special Device Type` 改为法规专属官方枚举下拉。
- `CMR Substances / Substance Type` 改为当前工具可安全输出的 5 类下拉，并在导入/导出预检中拦截不支持类型。
- `Basic - Is Suture/Staple/Filling/Brace (IIb Implant)` 改为 TRUE/FALSE 下拉，并在导入/导出预检中拦截非布尔值。
- 导入器、导出器和模板迁移工具增加旧值兼容：可识别 `CODE - label`、官方 code 以及部分旧模板英文标签。
- How to Use、Glossary、README、字段映射审计和打包/Release 配置同步到 v2.7 / 0.9.1。
- 启动健壮性修复：8765 端口被占时自动改用 8766-8776 第一个可用端口，并让浏览器打开真正绑定到的地址（不再固定打开打不开的 8765）。
- 新增启动日志 `local_beta_data/logs/run.log`，记录端口选择与启动成功/失败；无控制台打包版崩溃也能事后排查。
- 启动彻底失败（无可用端口等）时在程序目录写出「启动失败_STARTUP_ERROR.txt」，并在 Windows 上弹原生消息框，提示可能的端口占用 / 防火墙拦截原因。

## 0.9.0 - 2026-06-03

- 默认模板升级为 `EUDAMED_Template_v2.6.xlsx`，新增 `Clinical Sizes` 和 `Annex XVI Purposes` 明细表。
- 支持 MDR UDI-DI 输出结构化 `clinicalSizes`，包含 Range / Value / Text 三种 precision、Clinical Size Type、Measure Unit 和 OTHER 描述规则。
- 支持 MDR Annex XVI 非医疗目的产品输出 `annexXVINonMedicalDeviceTypes`，一个 UDI-DI 可填写多个 Non-Medical Device Type。
- 统一 Kit 模板字段：旧 `Basic - Kit (IVDR)` 迁移到 `Basic - Is it a Kit`；导出时按当前 XSD 在 IVDR / IVDD kit 路径输出，不向 MDR/MDD 强行写入无安全位置的节点。
- 迁移工具支持把旧 Clinical Size Value/Unit、旧 Purpose Other Than Medical 布尔值和旧 Kit 字段搬到 v2.6 结构，并在 Migration Report 中提示需要人工补充的字段。
- 模板、README、字段映射审计报告和打包脚本同步到 v2.6；`eIFU URL`、`Public Email`、`Product Designer` 等仍明确标注为当前不输出到普通 UDI-DI XML。

## 0.8.0 - 2026-06-02

- 新增首次使用快速开始卡和一键载入 / 清除示例数据；示例记录在产品库、导出页和详情页有醒目标识，导出预检会提示不要上传到 EUDAMED。
- 导出页新增 service 人话名和“我该选哪个 service”向导，帮助法规人员区分新注册、追加 UDI-DI、Basic 更新、UDI-DI 更新、市场信息更新和包装结构更新。
- 新增模板指南页，自动从当前 template schema 展示主表和明细表每个字段的说明、示例和必填状态。
- 导入页改为上传控件置顶，填写须知默认折叠；产品库、导出页、历史页增加更明确的空状态引导。
- 新增术语 tooltip、EUDAMED response XML 解析页、只重导被拒记录入口，并在 bulk upload 指引中提醒保存官方 response。
- 检查更新结果同时展示 GitHub / Gitee 下载入口；Windows 打包默认使用无控制台模式，并通过网页“退出工具”关闭本地服务。
- 反馈错误 / 发送测试结果与 EUDAMED response 解析页增加互相跳转和邮件引导，明确要求附上官方 response XML。
- 默认模板升级为 `EUDAMED_Template_v2.5.xlsx`，强化 Market Info、Package Info、Critical Warnings、Storage Conditions、CMR、证书和 Trade Names 明细表的条件必填说明。
- 版本展示从“内测版”调整为“公开测试版 / Public Beta”，适合对外发给企业试用，但仍保留非官方和正式提交前 Playground 验证提示。

## 0.7.2 - 2026-06-01

- 帮助页下载/更新区新增 Gitee Releases 国内镜像入口，用户可在 GitHub 访问失败时使用 Gitee 下载 Windows ZIP 和模板。
- 检查更新逻辑新增 Gitee 回退：优先读取 GitHub Releases API，GitHub 网络失败、限流或不可达时自动尝试 Gitee Release API。
- 更新结果显示来源 GitHub / Gitee；若使用 Gitee 回退，会提示 GitHub 检查失败原因。
- 发布流程文档补充 GitHub + Gitee 双发布与检查更新回退说明。

## 0.7.1 - 2026-06-01

- 修复产品库和导出任务页面的全选 / 取消勾选按钮失效问题。
- 修复导出任务页面在切换页面后丢失 service、筛选条件和已勾选记录的问题。
- 增加导出任务页面状态保留：已选择的 service、selection mode 和 record_ids 会保存在 URL / 浏览器会话中，返回导出页时自动恢复。

## 0.7.0 - 2026-05-31

- 新增 `MARKET_INFO.PATCH` service，支持为已注册 UDI-DI 独立更新市场国家、开始/结束日期和首次投放成员国。
- 新增 `PACKAGE_UDI.PATCH` service，支持为已注册 UDI-DI 独立更新 container package / 包装层级结构。
- 导出页 service 下拉和帮助指引开放 Update market information、Update container package，并保留 Update product original manufacturer 为暂未开放。
- 两个新增 PATCH service 复用现有 300 条拆分、ZIP manifest 和导出历史逻辑；不要求 EUDAMED version 字段。

## 0.6.1 - 2026-05-31

- 优化产品库 freshness 过滤，避免重复全表扫描。
- 改进产品库导出入口：先选择 service，再明确导出勾选记录或全部筛选结果。
- 导出页通过 URL 保留勾选记录和筛选模式，刷新后不丢选择。
- 合并帮助页下载/更新与检查更新区块，并修正本地版本高于 GitHub release 时的提示。
- 错误反馈说明增加 EUDAMED response XML 附件要求。

## 0.6.0 - 2026-05-31

- 新增跨记录一致性提示：Manufacturer SRN、Reference Number、EMDN/Risk Class、父子 Basic/UDI 关系出现可疑漂移时给出 warning/info。
- 新增导出新鲜度：区分从未导出、导出后有更新、已导出且未变化，并支持产品库按导出状态筛选。
- 增强证书预检：已填写 Device Certificates 时，检查 Certificate Type 是否明显匹配当前法规和风险等级。
- 详情页新增单条记录导入变更历史，便于追溯某条 Basic UDI-DI / UDI-DI 是在哪次 Excel 导入中新增或更新。
- 帮助页新增 Windows 下载/更新说明、EUDAMED bulk upload 操作步骤和邮件错误报告入口；检查更新支持 GitHub prerelease fallback。

## 0.5.0 - 2026-05-25

- 新增 `Device Certificates` sheet，按 Basic UDI-DI 采集 product certificate 信息。
- 支持在 `DEVICE.POST` / `Basic_UDI.PATCH` 的 Basic UDI-DI XML 中输出 `deviceCertificateLinks`。
- 新增高风险 / legacy 证书信息预检 warning：MDR Class III/部分 IIb、IVDR D/C/部分 B、MDD/AIMDD/IVDD 无证书信息时提示人工确认。
- 移除主表孤立的 `Basic - Certificate Number` 字段，避免误导为单一证书号即可提交。
- 模板、README 和网页导出指引增加 NB / product certificate validation 说明。

## 0.4.2 - 2026-05-22

- 修正 GitHub Releases API 返回 404 时的提示：显示“仓库尚未发布版本”，不再误判为断网。
- 更新 template 特殊下拉值说明：`ANY` language、`CW999`、`SHC099`、`EL`、`EUDAMED`、`IFA`。
- 标注当前收集但尚未输出 XML 的复杂字段，避免用户误以为填写后一定提交到 EUDAMED。
- 新增 GitHub Actions 官方文档/XSD 更新监控脚本，发现官方资料变化时生成报告并创建 issue。
- 新增 Data Dictionary 字段映射审计报告，作为后续补充 XML 字段输出的依据。
- 新增网页端“迁移模板”工具：把旧版/已填写的 EUDAMED template 搬到当前 v2.4 模板，并生成 Migration Report。

## 0.4.1 - 2026-05-21

- 更新 Trade Name 语言规则：`UDI - Trade Name Language` 和 `Trade Names` sheet 的 `Language` 下拉允许 `ANY`，符合官方 `LanguageEnum`。
- 修正 Trade Names 导入校验：不再禁止 `ANY`，只要求填写官方语言代码或 `ANY`。
- 更新 Market Info 规则说明和校验：同一 UDI-DI 可有多个 made available 国家，但 `Originally Placed on Market` 必须且只能有一个 `TRUE`。
- 更新国家代码规则：希腊使用 XSD 官方代码 `EL`，并保留对旧输入 `GR` 的导出映射。
- 重新生成 `EUDAMED_Template_v2.4.xlsx` 和工具包内默认模板。

## 0.4.0 - 2026-05-21

- 将工具自身版本拆分为 `TOOL_VERSION` 和 `TOOL_VERSION_LABEL`，为后续 GitHub Releases 检查更新做准备。
- 增加帮助页“检查更新”模块，支持 GitHub Releases API；未配置时安全显示“未配置更新源”。
- 增加 EUDAMED bulk upload 300 条限制提示和自动拆分逻辑。
- 支持 `DEVICE.POST` 超过 300 条时按 Basic UDI-DI 分组，并为同一 Basic 后续批次生成依赖的 `UDI_DI.POST`。
- 更新官方 XSD 到 production `3.0.30`，导出 XML 的 message version 跟随本地 XSD fixed version。

## 0.3.x - 2026-05

- 新增本地网页端工作流：导入 Excel、产品库管理、service 向导、预检、XML 导出、导出历史。
- 新增 v2.4 Excel template：`MDR_MDD` / `IVDR_IVDD` 主 sheet，独立 `Trade Names`、`Market Info`、`Package Info`、`Critical Warnings`、`Storage Conditions`、`CMR Substances` sheet。
- 增加 Legacy Device / EUDI 新上传路径，支持 MDD、AIMDD、IVDD。
- 增加 Windows 打包脚本和内测交付说明。
