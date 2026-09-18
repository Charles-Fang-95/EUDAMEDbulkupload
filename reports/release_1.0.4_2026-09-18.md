# 1.0.4 / v2.14 Orthopedic 特殊类型修复

## 官方依据与根因

- Production 2.15.0（2025）第 3.2 节：Orthopaedic 已从特殊器械类型列表移除。
  https://webgate.ec.europa.eu/eudamed-help/en/files/EUDAMED%20-%20release%20notes%20v%202-15.pdf
- Playground 3.9（2024）第 3.2 节：不再允许注册 Orthopaedic 特殊类型。
  https://webgate.ec.europa.eu/eudamed-play-help/en/files/EUDAMED%20-%20release%20notes%20v%203-9.pdf
- Production 官方索引中的 /en/documentation/ PDF 链接返回 404；从官方 /en/files/ 路径取得 PDF。Production PDF SHA-256：410f4d080cb3e8279a8ae1a6c1417d98643e6837dc8d57400882b849d92826b8。
- 本地 Production XSD 3.0.30 仍包含 MDR_ORTHOPEDIC、MDD_ORTHOPEDIC、AIMDD_ORTHOPEDIC。原工具直接从 XSD 枚举生成模板，遗漏了注册业务限制。官方 XSD 文件保持原样，不把这一问题解释为“骨科器械不能注册”或新的风险分类规则。

## 修改

- v2.14 中英文模板去掉三个骨科选项，更新字段说明；主表 3000 行、高频明细 10000 行容量不变。
- 导入和迁移识别两种英文拼写、法规前缀、代码加说明形式；明确提示核对并清空旧值，保留输入用于追溯，不静默删除。
- 导出预检同样覆盖已有数据库记录，防止绕过新模板继续生成有问题的 XML。
- 软件和其他 XSD 枚举保持不变；更新源、Windows 打包、Mac 包、模板副本和文档同步使用 v2.14。

## 验证

- 专项回归：历史数据库记录的 DEVICE.POST / Basic_UDI.PATCH 被阻止；迁移保留原值并警告；空值及软件正常导出并通过 XSD；枚举差集严格为三个骨科代码。
- 实际 v2.14 模板样本导入：骨科旧值产生明确错误，无法生成 XML；清空后重新导入无错误，DEVICE.POST 通过 Production XSD，XML 无 specialDevice 元素。
- Mac 源码/应用/ZIP 文件逐一一致，中英文根目录和打包模板一致，codesign --verify --deep --strict 通过。
- compileall、git diff --check 和完整 122 项测试通过（144.897 秒）。未使用客户数据；未上传 EUDAMED Playground/Production，未进行 Windows 桌面交互验收。
