# 1.0.5 / v2.14 验证记录 — 2026-10-15

## 官方依据与范围

核对 [Production UDI/Devices business rules](https://webgate.ec.europa.eu/eudamed-help/en/files/UDI%20Devices%20-%20business%20rules.pdf)，PDF 第 26 页 RULE-00185（旧 BR-UDID-131）。System/Procedure Pack、作为器械的 System/Procedure Pack 和 Kit 要求附加产品描述；其他普通 Regulation/Legacy 可选，描述须指定语言。本次按当前模板的 Device Type 与 Is it a Kit 表达该条件，不增改内部字段 key。

客户反馈仅用作问题背景，未将客户 Response、真实 SRN 或 UDI 数据纳入测试或提交，也未据此认定客户的具体分类。回归和页面测试均用人工构造的 SYNTH 标识。

## 修复与关联检查

- 导入与导出使用同一规则函数，避免行为分叉；通过 Parent Basic UDI-DI 读取父记录。
- 导入保存记录，缺描述/语言返回 CONDITIONAL_REQUIRED_MISSING；既有错误面板显示红色。
- DEVICE.POST、UDI_DI.POST、UDI_DI.PATCH 缺项均阻止生成；XML 构造处也进行防御检查。
- UDI 描述语言不再默认 EN；不复制 Basic 描述、名称/型号或编号，不修改 Kit，不切换 service。
- Excel bool FALSE 不再被旧 Kit (IVDR) 别名覆盖，也不再误报为布尔字段留空。
- PATCH 的当前 version 必填仍生效；Response 页增加远端已存在记录的核对与 PATCH/version 指引，不做远端重复查询。
- 中英文 v2.14 条件必填说明同步，主表和明细表容量不变。
- 检查了其他语言输出路径：Basic PR medicinalPurpose、Trade Names、Clinical Sizes 有各自的字段和历史处理，本次未改变它们的语义。此记录不代表所有 EUDAMED 业务规则已完整实现。

## 本地验证

- `python3 -m compileall local_beta EUDAMED_TOOL_v2/validator.py`：通过。
- `python3 -m unittest discover -s tests`：131 tests 全部通过，140.771 秒；新增 9 项测试，内部子用例覆盖法规、布尔形式和三个服务的组合。
- `python3 -m local_beta.build_unified_template`：通过，根目录与 EUDAMED_TOOL_v2/templates 中英文副本分别字节一致。
- 中文模板 SHA-256：`f6425349a9df6996ea2c78e2c46b6de822c717c1ed8bbac714686aa49d536c40`。
- 英文模板 SHA-256：`9c4edc2a921f5411fdf5546e0af29f11b7a9b01524615e11172d98f24e1f179b`。
- Mac arm64 本地构建完成，codesign --verify --deep --strict 通过；隔离导入打包模块成功，源码和模板副本一致。

## 实际浏览器 smoke test

隔离数据目录 `/tmp/eudamed-br131-smoke/data`、端口 18766，不接触正式本地数据库。

1. 上传匿名 IVDD Legacy Kit（Excel TRUE），描述空白：保存 1 Basic + 1 UDI，显示 1 个错误；点击生成 XML 被 BR-UDID-131 阻止，错误红色、警告黄色。
2. 同一记录填写 `Synthetic IVDD diagnostic kit` 和语言 `en` 后重新上传：0 错误，记录更新。
3. DEVICE.POST 页面导出成功，XML 包含 udidi:additionalDescription 及 EN/填写的文本；manifest 表显示 1 条实体。
4. 页面为匿名记录填写测试 version=1，选择 UDI_DI.PATCH，生成 XML 成功。
5. 两份实际网页生成的 XML 均用 lxml.XMLSchema 对打包 Production 3.0.30 的 service/Message.xsd 完整校验通过。
6. 多文件 ZIP / manifest 行为沿用全套自动测试覆盖。

截图：[空描述拦截](release_1.0.5/blocked-export.png)、[补齐后导出](release_1.0.5/success-export.png)。截图来自布尔提示修复前的页面进程，包含已另行修复的 FALSE 空白提示；对应修复已进入最终源码、测试及 Mac 包。

## 验证边界

本地业务预检、Production XSD 结构校验均通过。不代表在线接受；**未实际上传 EUDAMED Playground，线上验收尚未完成**。Windows Runner 和发布附件状态以新 v1.0.5 Release workflow 为准，不能用 Mac 本地构建代替 Windows 运行验证。

## GitHub 发布核验

- 发布提交 `7895211`，标签 `v1.0.5`；[Release](https://github.com/Charles-Fang-95/EUDAMEDbulkupload/releases/tag/v1.0.5)。
- [新发布流水线](https://github.com/Charles-Fang-95/EUDAMEDbulkupload/actions/runs/38754665123) 中 Mac 构建与 Windows 打包步骤均成功，GitHub 发布完成。
- 实际下载 Mac 与 Windows ZIP，检查 ZIP 完整性、发布 SHA-256 以及包内 exporter.py、validator.py、版本和两个模板，均与本次提交匹配（Windows 文本按 CRLF/LF 归一化比较）。
- 发布清单中的四项文件 SHA-256 全部核对通过。Windows GUI 未在本机运行；Windows Runner 打包成功不等于 Windows 手工验收。

- Gitee [v1.0.5 镜像](https://gitee.com/Charles-Fang-95/EUDAMEDbulkupload/releases/tag/v1.0.5) 的中英文模板、Windows ZIP、Mac ZIP、SHA256SUMS 共五个附件均已实际下载，与 GitHub SHA-256 完全一致。源码自动压缩包不属于本次安装包核验范围。
- 发布 workflow 最终为 completed / success。旧版 1.0.4 调用工具检查更新能发现 GitHub 1.0.5，并返回对应平台安装包。
