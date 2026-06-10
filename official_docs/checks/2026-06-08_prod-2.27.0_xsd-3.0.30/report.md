# EUDAMED 官方 XSD / 技术资料巡检报告

- 检查日期: `2026-06-08`
- 本地生成时间: `2026-06-08T09:07:35+08:00`
- 判定范围: `仅使用 EUDAMED / European Commission 官方生产环境帮助页与官方下载 URL`
- 本地工具基线: `local_beta/constants.py -> SCHEMA_VERSION = 3.0.30`
- 结论:
  - `未发现新的生产 XSD 版本；官方仍声明 XSD v3.0.30 对应平台 v2.27.0`
  - `发现官方配套资料已整体换到 2026-05-26 发布批次，本地顶层 official_docs 中 samples / data dictionary / business rules / enumerations / services definition 均已落后`

## 官方判定依据

1. 官方下载索引页  
   URL: <https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html>  
   证据:
   - 页面尾部显示 `© 2026 European Commission-v.2.27.0`
   - 页面 `Publication date: May 18, 2026`
   - 页面说明: `The XSD schemas above version (v 3.0.30) relate to the current platform release (v 2.27.0).`
2. 官方 support 页  
   URL: <https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/machine-to-machine/support/technical-documentation.html>  
   证据:
   - 页面尾部显示 `© 2026 European Commission-v.2.27.0`
   - 页面 `Publication date: May 18, 2026`
   - 页面说明技术文档集合包含 `DTX XSD / XML samples / Service Definition / Business Rules / Enumerations / Data Dictionaries`
3. 官方下载件 HTTP 元数据  
   所有本次核对的下载件 `Last-Modified` 均为 `Tue, 26 May 2026 12:19:44 GMT`

## HTTP / 下载元数据

| 官方文件 | URL | Last-Modified | ETag | Content-Length | 结论 |
| --- | --- | --- | --- | ---: | --- |
| Technical documentation page | <https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html> | `Tue, 26 May 2026 12:19:44 GMT` | `"4630-652b7829bb800"` | 17968 | 页面已切到 `v2.27.0 / XSD 3.0.30` |
| XSD schemas.zip | <https://webgate.ec.europa.eu/eudamed-help/en/files/XSD%20schemas.zip> | `Tue, 26 May 2026 12:19:44 GMT` | `"209bd-652b7829bb800"` | 133565 | 与本地 `3.0.30` 基线二进制一致 |
| EOs - XML samples.zip | <https://webgate.ec.europa.eu/eudamed-help/en/files/EOs%20-%20XML%20samples.zip> | `Tue, 26 May 2026 12:19:44 GMT` | `"fcd3-652b7829bb800"` | 64723 | 官方样例包有变更 |
| UDI Devices - data dictionary.xlsx | <https://webgate.ec.europa.eu/eudamed-help/en/files/UDI%20Devices%20-%20data%20dictionary.xlsx> | `Tue, 26 May 2026 12:19:44 GMT` | `"2263e-652b7829bb800"` | 140862 | 官方数据字典有变更 |
| UDI Devices - business rules.pdf | <https://webgate.ec.europa.eu/eudamed-help/en/files/UDI%20Devices%20-%20business%20rules.pdf> | `Tue, 26 May 2026 12:19:44 GMT` | `"c984a-652b7829bb800"` | 825418 | 官方业务规则有变更 |
| UDI Devices - enumerations.pdf | <https://webgate.ec.europa.eu/eudamed-help/en/files/UDI%20Devices%20-%20enumerations.pdf> | `Tue, 26 May 2026 12:19:44 GMT` | `"11de6b1-652b7829bb800"` | 18736817 | 官方枚举说明有变更 |
| DTX for EOs - services definition.pdf | <https://webgate.ec.europa.eu/eudamed-help/en/files/DTX%20for%20EOs%20-%20services%20definition.pdf> | `Tue, 26 May 2026 12:19:44 GMT` | `"983668-652b7829bb800"` | 9975400 | 官方服务定义有变更 |

## 本次留存目录

- 检查目录: [official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30)
- 原始下载件: [downloads](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30/downloads)
- 证据 JSON: [source_evidence.json](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30/source_evidence.json)
- 校验和: [official_files_checksums.sha256](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30/official_files_checksums.sha256)
- XSD zip 清单: [xsd_zip_entries.txt](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30/xsd_zip_entries.txt)
- XSD 文件清单: [xsd_file_manifest.tsv](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30/xsd_file_manifest.tsv)
- EO samples zip 清单: [eo_samples_zip_entries.txt](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30/eo_samples_zip_entries.txt)
- EO samples 差异: [eo_samples_diff.tsv](/Users/charles_fang/Documents/EUDAMED/official_docs/checks/2026-06-08_prod-2.27.0_xsd-3.0.30/eo_samples_diff.tsv)

## 与本地上一版官方资料比较

### 1. XSD schemas.zip

- 本地旧件: `official_docs/XSD_schemas_production_3.0.30.zip`
- 本次新件: `downloads/XSD_schemas.zip`
- SHA-256: `e3c7621a69340b1ad01d375994a6df6a131073626e2a4ae01048e0ffa04b1c3b`
- 文件大小: `133565 bytes -> 133565 bytes`
- 二进制比较: `完全一致`
- 解包比较:
  - XSD 文件新增: `0`
  - XSD 文件删除: `0`
  - XSD 文件修改: `0`
  - `MessageType.xsd`、枚举定义、约束、payload 结构均未见变化

### 2. EOs - XML samples.zip

- 本地旧件 SHA-256: `40934d2a64b9ab9e6b80008e68ee95e3349c858b8e2339d9ae41b888a381c6e8`
- 本次新件 SHA-256: `583d92b7ba59df6d4d66116cfc868fe9fe21d2abc14100d8a7ba6ce3663b7bf5`
- 文件项数量: `41 -> 40`
- 发现的文件级变化:
  - 删除: `EOs - XML samples/SAMPLE_DTX_ACT_001.02.xml`
  - 新增: `无`
  - 其他文件名: `无变化`
- 对工具的意义:
  - 当前主转换工具主要聚焦 UDI/Device，`ACT_001.02` 删除不会立刻影响 `DEVICE.POST / PATCH` 转换逻辑
  - 但本地 `official_docs/unpacked/samples` 已与现行官方样例包不一致，若后续将 samples 作为回归样本来源，应同步更新样例基线

### 3. UDI Devices - data dictionary.xlsx

- 本地旧件 SHA-256: `5a9fb37b618c173e2b097c1ac4d78213a33b9d1f74cae3d47bad1190ac3d7bb0`
- 本次新件 SHA-256: `480a170ba563712a54c6858400fb5b0b55c11e88e66de0e9fc9f54d5d9e2e6b1`
- 文件大小: `137871 -> 140862`
- 结构观察:
  - 新包新增了 `"[trash]/0000.dat"` 条目
  - `docProps/core.xml` 最后修改人从 `GLABAS Magda Teresa (SANTE-EXT)` 变为 `TRAIANIDOU Meropi (SANTE-EXT)`
  - `docProps/core.xml` 修改时间从 `2026-02-26T11:01:34Z` 变为 `2026-04-07T16:24:44Z`
  - `xl/sharedStrings.xml` 中新增版本文本:
    - `2.27.0`
    - `Release 3.25.0 PG, 2.25.0 PROD`
    - `Release 3.27.0 PG, 2.27.0 PROD`
  - 删除旧文本:
    - `Release 3.25.0 PG, 3.25.1 hotfix PG, 2.25.0 PROD`
- 初步判定:
  - 这不是单纯文件重打包，版本历史页至少已经推进到 `2.27.0`
  - 本次快速字符串比较未发现新的字段标签、sheet 名或实体页新增/删除信号
  - 更像是 `版本历史 + 文档包装/样式` 更新，而非 UDI 字段模型大改

### 4. UDI Devices - business rules.pdf

- 本地旧件: `Playground v 3.25.1`, `26 pages`, `822918 bytes`
- 本次新件: `Production v 2.27.0`, `27 pages`, `825418 bytes`
- 文本观察:
  - 新版首页已从 `Playground v 3.25.1` 切到 `Production v 2.27.0`
  - 变更日志显示:
    - `1.0  No changes  PG 3.27, PROD 2.27`
    - 保留 `PG 3.22 / PROD 2.22` 历史说明
- 判定:
  - 业务规则文档已对齐生产 2.27
  - 目前未发现需要立刻修改 `local_beta/importer.py` 或 `local_beta/exporter.py` 的新硬性约束

### 5. UDI Devices - enumerations.pdf

- 本地旧件: `Playground v 3.25.1`, `19 pages`, `5775015 bytes`
- 本次新件: `Production v 2.27.0`, `21 pages`, `18736817 bytes`
- 文本观察:
  - 新版首页已切到 `Production v 2.27.0`
  - 变更日志包含:
    - `1.1  No changes  PG 3.27.0 / PROD 2.27.0`
    - `1.1  See changes below  PG 3.25 / PROD 2.25`
- 判定:
  - 官方枚举说明文档已更新并重制版式
  - 但 XSD 本体未变，本地依赖 `unpacked/xsd_production` 读取的枚举值集当前仍可视为有效

### 6. DTX for EOs - services definition.pdf

- 本地旧件: `Playground v 3.25.1`, `13 pages`, `947381 bytes`
- 本次新件: `Production v 2.27.0`, `14 pages`, `9975400 bytes`
- 文本观察:
  - 旧件标题页是 `Playground v 3.25.1`
  - 新件标题页是 `Production v 2.27.0`
  - 新件 change log 明确写:
    - `No changes from 3.25.0  -> PG 3.27.0, PROD 2.27.0`
    - `DEVICE.GET: MFs, PRs should be able to download submitted, registered, discarded - but only own devices -> PG 3.25.0`
  - 新件正文仍写明 `max 300 items per response`
- 判定:
  - 这强化了本地 `BULK_UPLOAD_ENTITY_LIMIT = 300` 的依据仍然成立
  - 也说明现有工具在下载/筛选相关的未来扩展上，应以 `MF/PR only own devices` 的服务定义为准

## 对主转换工具的直接影响

### 当前不需要立刻修改的部分

- `local_beta/constants.py`
  - `SCHEMA_VERSION = 3.0.30` 仍正确
  - `BULK_UPLOAD_ENTITY_LIMIT = 300` 仍被现行服务定义支持
- `official_docs/unpacked/xsd_production/`
  - 仍可继续作为本地 XML 验证基线
- `local_beta/exporter.py`
  - 暂无因 XSD 结构变更导致的 payload / schema version / element order 调整需求
- `local_beta/template_schema.py`
  - 暂无来自 XSD 的新枚举集变化信号

### 建议尽快处理的资料基线更新

1. 刷新本地官方资料镜像  
   建议把本次 `downloads/` 下的以下文件经人工确认后提升为顶层基线:
   - `EOs_XML_samples.zip`
   - `UDI_Devices_data_dictionary.xlsx`
   - `UDI_Devices_business_rules.pdf`
   - `UDI_Devices_enumerations.pdf`
   - `DTX_for_EOs_services_definition.pdf`
2. 更新 `official_docs/official_sources_manifest.json`  
   目前 manifest 只记录旧版哈希，已不能代表最新官方配套资料状态
3. 复核样例基线  
   本地 `official_docs/unpacked/samples` 仍多出 `SAMPLE_DTX_ACT_001.02.xml`
4. 文档比对后再决定是否需要代码变更  
   如果维护者后续人工阅读 `2.27` 版 data dictionary / business rules，发现 requiredness 或说明语义变化，再按以下位置补代码:
   - `local_beta/template_schema.py`
   - `local_beta/importer.py`
   - `local_beta/exporter.py`
   - `tests/test_core_contracts.py`

## 建议的后续维护检查点

1. 复核 `data dictionary` 的版本历史页与字段页是否仅更新 release 文案，还是对字段 requiredness / 描述做了隐性修订。
2. 复核 `business rules` / `enumerations` 新 PDF 是否只做生产版对齐，还是存在对 RA 用户输入约束的重要补充。
3. 若决定把新资料提升为顶层基线，顺带补一个脚本化巡检流程，自动报告:
   - HTTP `Last-Modified` / `ETag`
   - zip 文件项新增/删除
   - XSD 哈希差异
   - samples 删除/新增
   - data dictionary sharedStrings 版本差异

## 本次执行的本地验证

```bash
python3 -m compileall local_beta EUDAMED_TOOL_v2/validator.py
python3 -m unittest discover -s tests
python3 -m local_beta.build_unified_template
```

结果:

- `compileall`: 通过
- `unittest`: `Ran 7 tests ... OK`
- `build_unified_template`: 成功生成 `EUDAMED_Template_v2.8.xlsx`

## 最终判定

截至 `2026-06-08`，官方生产帮助页和官方 `XSD schemas.zip` 仍显示 `XSD v3.0.30 / platform v2.27.0`，因此主转换工具当前没有因为 schema 本体变化而必须修改的代码。  

但本地仓库保存的多份官方配套资料仍停留在较早的 `Playground v3.25.1 / PROD 2.25` 批次，而官方已经在 `2026-05-26` 发布了对应 `Production v2.27.0` 的 samples、data dictionary、business rules、enumerations、services definition。对维护者来说，当前最需要处理的是 `官方资料基线刷新`，而不是 `XSD 结构适配改码`。
