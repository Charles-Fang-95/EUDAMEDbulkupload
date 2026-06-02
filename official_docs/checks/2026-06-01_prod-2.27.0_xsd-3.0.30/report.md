# EUDAMED 官方 XSD 巡检报告

- 检查日期: `2026-06-01`
- 本地生成时间: `2026-06-01T09:06:54+08:00`
- 判定范围: `仅使用 EUDAMED / European Commission 官方生产环境来源`
- 结论: `未发现新的生产 XSD 版本或相关文档命名变化；当前仍为平台 v2.27.0 / XSD v3.0.30`

## 官方依据

1. 官方支持页: <https://webgate.ec.europa.eu/eudamed-help/en/data-exchange/machine-to-machine/support/technical-documentation.html>
   - 页面发布日期: `2026-05-18`
   - 说明技术文档集合包含 DTX XSD、XML samples、service definition、business rules、enumerations、data dictionaries。
2. 官方下载索引页: <https://webgate.ec.europa.eu/eudamed-help/en/documentation/technical-documentation.html>
   - 页面发布日期: `2026-05-18`
   - 页面备注明确写明: `The XSD schemas above version (v 3.0.30) relate to the current platform release (v 2.27.0).`
   - 页面展示的文件标签与本地基线一致: `XSD schemas.zip`、`EOs - XML samples.zip`、`UDI Devices - business rules`、`UDI Devices - enumerations`、`UDI Devices - data dictionary`、`DTX for EOs - services definition`。
3. 官方 PDF 直接链接:
   - `UDI Devices - business rules.pdf`: <https://webgate.ec.europa.eu/eudamed-help/en/files/UDI%20Devices%20-%20business%20rules.pdf>
   - `DTX for EOs - services definition.pdf`: <https://webgate.ec.europa.eu/eudamed-help/en/files/DTX%20for%20EOs%20-%20services%20definition.pdf>
   - 业务规则 PDF 首页显示 `Production v 2.27.0`。

## HTTP / 下载元数据

- 本次运行未能在 shell 侧直接抓取 `webgate.ec.europa.eu` 的 HTTP 头。
- 失败表现: `urllib` / `curl` 本地 DNS 解析失败，无法稳定获得 `Last-Modified`、`ETag`、响应长度等头信息。
- 处理方式: 使用浏览器侧官方抓取确认页面内容与 PDF 内容；HTTP 头字段在本次报告中记为 `未获取`，避免把不可验证数据写成事实。
- 直接下载 URL:
   - `https://webgate.ec.europa.eu/eudamed-help/en/files/XSD%20schemas.zip` (`官方索引路径模式推断，未在 shell 侧重新下载`)
   - `https://webgate.ec.europa.eu/eudamed-help/en/files/EOs%20-%20XML%20samples.zip` (`官方索引路径模式推断，未在 shell 侧重新下载`)
   - `https://webgate.ec.europa.eu/eudamed-help/en/files/UDI%20Devices%20-%20data%20dictionary.xlsx` (`官方索引路径模式推断，未在 shell 侧重新下载`)

## 本地官方基线核对

- Manifest: `official_docs/official_sources_manifest.json`
- Manifest 生成日期: `2026-05-22`
- Manifest 期望 XSD 版本: `3.0.30`
- 本地 `MessageType.xsd` 固定版本: `3.0.30`
- 结论: `官方页版本 = manifest 版本 = 本地解包 XSD 固定版本 = 3.0.30`

### 已留存原始官方文件

| 文件 | 本地路径 | SHA-256 | 大小(bytes) |
|---|---|---|---:|
| XSD schemas.zip | `official_docs/XSD_schemas_production_3.0.30.zip` | `e3c7621a69340b1ad01d375994a6df6a131073626e2a4ae01048e0ffa04b1c3b` | 133565 |
| UDI Devices - data dictionary.xlsx | `official_docs/UDI_Devices_data_dictionary.xlsx` | `5a9fb37b618c173e2b097c1ac4d78213a33b9d1f74cae3d47bad1190ac3d7bb0` | 137871 |
| UDI Devices - business rules.pdf | `official_docs/UDI_Devices_business_rules.pdf` | `344fd158c2bc3a51b5a122e155bd01e12c2018eb7daa32a5512d5edd63ad9526` | 822918 |
| DTX for EOs - services definition.pdf | `official_docs/DTX_for_EOs_services_definition.pdf` | `1f66c9819a63203711c9cc2a39d30ea379927b65e4c6f304694d7b9fba65de0f` | 947381 |


### XSD 包概况

- 生产 XSD zip: `official_docs/XSD_schemas_production_3.0.30.zip`
- zip SHA-256: `e3c7621a69340b1ad01d375994a6df6a131073626e2a4ae01048e0ffa04b1c3b`
- zip 文件项总数: `92`
- 其中 XSD 文件数: `67`
- 解包后 XSD 文件数: `67`
- 额外非 XSD 内容: zip 内含 `data/Entity/Vigilance/v1/Dossier_Sample.xml`

### 关键枚举 / 约束快照

| 项目 | 本地值 | Manifest 基线 |
|---|---:|---:|
| XSD version | 3.0.30 | 3.0.30 |
| LanguageEnum | 28 | 28 |
| EUCountryWithSpecialEnum | 32 | 32 |
| IssuingEntityTypeEnum | 5 | 5 |
| StorageHandlingConditionEnum | 33 | 33 |
| CriticalWarningEnum | 423 | 423 |

## 与上一版基线比较

- XSD 文件级新增: `0`
- XSD 文件级删除: `0`
- XSD 文件级修改: `0`
- 文件名 / 命名变化: `未发现`
- schema 结构、枚举、字段、约束变化摘要: `由于官方生产页未显示高于 3.0.30 的新版本，本次未识别到新的结构性变化。`
- samples / business rules / data dictionary / service definition: `官方索引页仍显示相同文档标签；业务规则 PDF 仍对应生产版 2.27.0。`

## 对主转换工具的影响

- 当前需要调整的代码: `无`
- 当前需要调整的映射: `无`
- 当前需要调整的校验: `无`
- 当前风险判断: `低`，因为版本号、关键枚举计数和本地 pinned 官方包一致。

## 下次若官方更新时优先检查的代码点

1. `local_beta/constants.py` 与 `local_beta/xsd_version.py`
   - 更新 `SCHEMA_VERSION`、帮助页版本判定和本地固定版本提示。
2. `local_beta/exporter.py`
   - 复核 `Message` 版本字段、`schemaLocation`、payload 结构和 300 entity 限制是否仍与新 `MessageType.xsd` 一致。
3. `local_beta/template_schema.py`
   - 重新生成或验证语言、国家、签发机构、storage condition、critical warning、certificate type 等下拉枚举。
4. `scripts/audit_data_dictionary_mapping.py` 与 `docs/DATA_DICTIONARY_FIELD_AUDIT.md`
   - 复核 data dictionary / business rules 对字段 requiredness、名称、约束的影响，特别是 `eIFU URL`、`Clinical Size`、`Product Designer`、`Purpose Other Than Medical`。
5. `official_docs/official_sources_manifest.json`
   - 更新新包的 `sha256`、`size`、`expected_xsd_version` 和枚举基线。
6. 样例与校验
   - 用新版 `official_docs/unpacked/xsd_production/service/Message.xsd` 回归校验现有导出 XML；如官方 samples 更新，优先补充覆盖 `DEVICE.POST`、`UDI_DI.POST`、`Basic_UDI.PATCH`、`MARKET_INFO.PATCH`、`PACKAGE_UDI.PATCH`。

## 本次留档文件

- `source_evidence.json`: 官方证据与判定 JSON
- `official_files_checksums.sha256`: 当前保留的官方原始文件校验和
- `xsd_zip_entries.txt`: 生产 XSD zip 包文件清单
- `xsd_file_manifest.tsv`: 解包后每个 XSD 的路径、SHA-256、大小

## 判定

本次检查未发现 `2026-06-01` 时点上官方生产 EUDAMED XSD 有高于 `3.0.30` 的更新，也未发现相关生产技术文档标签发生命名变化。现有主转换工具基于 `official_docs/unpacked/xsd_production` 的实现可继续维持当前版本，无需立即改码；下次只要官方页从 `v 3.0.30 / v 2.27.0` 发生变化，就应按上述 watchlist 启动代码和映射复核。
