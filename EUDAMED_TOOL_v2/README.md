# EUDAMED_TOOL_v2 目录说明

> 当前主工具已经迁移到根目录的本地网页端：`python3 run_local_beta.py`。
>
> 本目录是旧命令行转换器和 vendored 依赖目录。当前 `local_beta/` 仍复用这里的 `lib/` 和 `validator.py`，所以不能整体删除；但这里的旧 README 内容、旧模板和历史报告不代表当前 v2.11 本地网页端的使用方式。

当前推荐阅读：

- 根目录 `README.md`
- `LOCAL_BETA_README.md`
- `docs/PROJECT_STRUCTURE.md`

下面保留旧命令行工具说明，仅供追溯历史。

# EUDAMED批量注册XML转换工具 v2.0

## 📋 项目简介

EUDAMED批量注册XML转换工具是一个专为医疗器械制造商设计的自动化工具，用于将Excel格式的产品数据批量转换为符合EUDAMED（欧盟医疗器械数据库）规范的XML文件。

**版本**: 2.0.0  
**规范版本**: EUDAMED UDI Devices v3.0.25  
**适用法规**: MDR (EU 2017/745), IVDR (EU 2017/746)

---

## ✨ v2.0 主要改进

### 1. 用户体验大幅提升
- ❌ **旧版流程**: 填写Excel → 手动导出7个CSV → 运行脚本
- ✅ **新版流程**: 填写Excel → 双击批处理文件

### 2. Excel模板优化
- 新增 **16个关键字段**（Basic UDI-DI: 8个，UDI-DI: 8个）
- 字段覆盖率从 **34%** 提升至 **85%**
- 新增 **8个枚举值辅助工作表**（200+有效值）
- 数据验证规则从 **47条** 增至 **120+条**
- 所有字段添加详细批注说明

### 3. 四层数据验证引擎
1. **格式验证**: 日期、布尔值、UDI代码、URL、邮箱
2. **完整性验证**: 必填字段、条件必填、二选一必填
3. **有效性验证**: 枚举值、关联关系、跨表引用
4. **业务规则验证**: EUDAMED官方规则（如RULE-00018）

### 4. 智能报告系统
- **控制台报告**: 实时进度和错误提示
- **HTML报告**: 现代化UI，可视化数据统计
- **JSON报告**: 结构化数据，便于系统集成

---

## 🚀 快速开始

### 前置要求

- **操作系统**: Windows 7/10/11, macOS, Linux
- **Python版本**: 3.7 或更高版本
- **权限要求**: 无需管理员权限

### 安装步骤

1. **确认Python已安装**
   ```bash
   python --version
   # 或
   python3 --version
   ```

2. **下载工具包**
   - 解压到任意目录（建议路径不含中文）

3. **检查文件结构**
   ```
   EUDAMED_TOOL_v2/
   ├── eudamed_converter_integrated.py  # 主程序
   ├── validator.py                     # 验证模块
   ├── xml_builder.py                   # XML构建模块
   ├── logger.py                        # 报告模块
   ├── convert.bat                      # Windows快捷启动
   ├── lib/                             # 依赖库（已捆绑）
   │   ├── openpyxl/
   │   └── et_xmlfile/
   ├── templates/                       # 模板文件夹
   │   └── EUDAMED_Template_v2.xlsx
   └── docs/                            # 文档文件夹
       └── README.md
   ```

### 使用方法

#### 方法一：Windows用户（推荐）

1. 打开 `templates` 文件夹
2. 在 `EUDAMED_Template_v2.xlsx` 中填写产品数据
3. 保存并关闭Excel文件
4. 双击 `convert.bat` 运行转换
5. 查看生成的XML文件和HTML报告

#### 方法二：命令行（所有平台）

```bash
# 基本用法
python eudamed_converter_integrated.py --input templates/EUDAMED_Template_v2.xlsx

# 指定输出文件名
python eudamed_converter_integrated.py --input templates/EUDAMED_Template_v2.xlsx --output my_output.xml

# 仅验证数据，不生成XML
python eudamed_converter_integrated.py --input templates/EUDAMED_Template_v2.xlsx --validate-only
```

---

## 📊 Excel模板填写指南

### 工作表说明

| 工作表名称 | 说明 | 必填 |
|-----------|------|------|
| **Basic UDI-DI** | 基本设备标识信息 | ✅ 是 |
| **UDI-DI** | 设备标识详细信息 | ✅ 是 |
| **Market Information** | 市场投放信息 | ✅ 是 |
| **Critical Warnings** | 关键警告信息 | ⚪ 可选 |
| **Storage Conditions** | 储存条件 | ⚪ 可选 |
| **CMR Substances** | CMR物质信息 | ⚪ 可选 |
| **Package Information** | 包装信息 | ⚪ 可选 |

### 填写规则

#### 1. 必填字段（标记为 *）
- **Basic UDI-DI**: Basic UDI-DI Code, Issuing Entity, Manufacturer SRN, Risk Class, Applicable Legislation, Device Type, EMDN Code, Is it a Kit, Reagent, Presence of Medicinal Substance
- **UDI-DI**: Parent Basic UDI-DI, UDI-DI Code, UDI-DI Issuing Entity, Device Status, Single Use Device, Device Labelled as Sterile, Trade Name Applicable, Nomenclature Code。Containing Latex 仅 MDR/MDD/AIMDD 适用；UDI-PI 类型字段仅 MDR/IVDR Regulation Device 或 SPP 条件适用，MDD/AIMDD/IVDD Legacy 不输出。

#### 2. 数据格式要求

| 数据类型 | 格式要求 | 示例 |
|---------|---------|------|
| 日期 | YYYY-MM-DD | 2026-12-31 |
| 布尔值 | TRUE 或 FALSE（必须大写） | TRUE |
| UDI代码 | 8-50位字母数字 | 00860000123456 |
| 邮箱 | 标准邮箱格式 | contact@example.com |
| URL | http:// 或 https:// 开头 | https://www.example.com |

#### 3. 枚举值（从下拉列表选择）

- **Issuing Entity**: GS1, HIBCC, ICCBBA
- **Risk Class**: Class I, Class IIa, Class IIb, Class III (MDR) / Class A, B, C, D (IVDR)
- **Applicable Legislation**: MDR, IVDR, MDD, AIMDD, IVDD
- **Device Type**: Regular Device, System, Procedure Pack
- **Device Status**: On the EU market, No longer placed on the EU market, Not intended for the EU market
- **Country Code**: EU/EEA国家代码（希腊按 EUDAMED 官方枚举使用 EL，不使用 GR）

#### 4. 特殊规则

- **Device Name/Model**: 与 Device Model 二选一必填，两者都可以提供
- **Authorised Representative SRN**: 非欧盟制造商必填（RULE-00018）
- **Trade Name**: 当 Trade Name Applicable 为 TRUE 时必填
- **风险等级与法规匹配**: 
  - MDR设备使用 Class I/IIa/IIb/III
  - IVDR设备使用 Class A/B/C/D

### 字段批注

所有字段都包含详细的批注说明，将鼠标悬停在表头单元格上即可查看：
- 字段的官方ID
- 强制性要求
- 详细说明
- 填写示例

---

## 🔍 验证规则详解

### 第一层：格式验证

检查数据格式是否符合要求：
- 日期必须为 YYYY-MM-DD 格式
- 布尔值必须为 TRUE 或 FALSE（大写）
- UDI代码必须为 8-50 位字母数字
- URL必须以 http:// 或 https:// 开头
- 邮箱必须符合标准格式

### 第二层：完整性验证

检查必填字段是否填写：
- 所有标记为 * 的字段必须填写
- 条件必填字段根据其他字段值判断
- 二选一必填字段至少填写一个

### 第三层：有效性验证

检查数据值是否有效：
- 枚举值必须从预定义列表中选择
- 关联字段必须引用已存在的记录
- 跨表引用必须保持一致性

### 第四层：业务规则验证

检查是否符合EUDAMED业务规则：
- **RULE-00018**: 非欧盟制造商必须有授权代表
- **风险等级匹配**: 风险等级必须与适用法规匹配
- **IIb类植入物**: 需要特殊声明

---

## 📈 输出文件说明

### 1. XML文件
- **文件名**: `eudamed_upload_YYYYMMDD_HHMMSS.xml`
- **用途**: 上传到EUDAMED系统
- **规范**: 符合 EUDAMED UDI Devices v3.0.25

### 2. HTML报告
- **文件名**: `eudamed_report_YYYYMMDD_HHMMSS.html`
- **用途**: 可视化查看处理结果
- **内容**: 
  - 数据统计
  - 验证结果
  - 错误和警告详情
  - 处理时间

### 3. JSON报告
- **文件名**: `eudamed_report_YYYYMMDD_HHMMSS.json`
- **用途**: 系统集成和自动化处理
- **内容**: 结构化的处理结果数据

---

## ❓ 常见问题

### Q1: 提示"未检测到Python"怎么办？

**A**: 需要先安装Python：
1. 访问 https://www.python.org/downloads/
2. 下载Python 3.7或更高版本
3. 安装时勾选"Add Python to PATH"
4. 安装完成后重启命令行

### Q2: 为什么有些字段没有下拉列表？

**A**: 下拉列表仅对枚举值字段有效。自由文本字段（如设备名称、描述等）不提供下拉列表。

### Q3: 如何查看字段的详细说明？

**A**: 将鼠标悬停在Excel表头单元格上，会显示包含字段说明、示例和要求的批注。

### Q4: 验证失败后如何修复？

**A**: 
1. 打开生成的HTML报告
2. 查看错误详情，包含行号、字段名和修复建议
3. 在Excel中定位到对应行和字段
4. 按照建议修复
5. 重新运行转换

### Q5: 可以在没有管理员权限的电脑上使用吗？

**A**: 可以！本工具已捆绑所有依赖库，无需安装额外软件或库，无需管理员权限。

### Q6: 支持批量处理多个Excel文件吗？

**A**: 当前版本每次处理一个Excel文件。如需批量处理，可以：
1. 将所有产品数据合并到一个Excel文件中
2. 或编写脚本循环调用转换器

### Q7: 生成的XML文件可以直接上传到EUDAMED吗？

**A**: 可以。生成的XML文件完全符合EUDAMED v3.0.25规范。但建议先在EUDAMED测试环境验证。

---

## 🛠️ 技术支持

### 错误报告

如遇到问题，请提供以下信息：
1. 操作系统和Python版本
2. 错误截图或错误信息
3. 生成的JSON报告文件
4. 脱敏后的Excel文件（如可能）

### 版本更新

工具会根据EUDAMED规范更新和用户反馈持续改进。建议定期检查是否有新版本。

---

## 📄 许可证

本工具仅供内部使用，请勿未经授权分发或商业使用。

---

## 📝 更新日志

### v2.0.0 (2026-02-05)
- ✨ 新增直接读取Excel功能，取消CSV导出步骤
- ✨ 新增四层数据验证引擎
- ✨ 新增16个关键字段
- ✨ 新增8个枚举值辅助工作表
- ✨ 新增HTML和JSON报告生成
- ✨ 增强数据验证规则（47→120+条）
- ✨ 优化用户界面和错误提示
- 🐛 修复日期格式处理问题
- 🐛 修复布尔值大小写敏感问题

### v1.0.0 (2025-XX-XX)
- 🎉 初始版本发布
- ✅ 基本CSV到XML转换功能
- ✅ 支持Basic UDI-DI和UDI-DI

---

**祝您使用愉快！如有任何问题，请随时联系技术支持团队。**
