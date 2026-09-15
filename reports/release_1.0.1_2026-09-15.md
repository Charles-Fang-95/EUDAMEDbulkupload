# 1.0.1 导出下载修复验证

- 工具 1.0.1，模板 v2.13，Production XSD 3.0.30。
- 根因：POST /export 返回结果后，restoreExportPageIfNeeded 根据 sessionStorage 跳转，丢弃结果。结果存在时禁止此跳转；成功生成文件后自动请求下载，手动入口放在产品列表前。
- 同秒导出文件原先可重名覆盖；增加 UUID，保持历史文件独立。
- 保留已有空选提示修复。Mac 用户取消保存不再报下载失败。

## 验证

- compileall、git diff --check 通过。
- unittest discover：112 tests，157.621 秒，全部通过，含 Node 执行实际筛选恢复函数的回归、真实 XML/ZIP 结果页与同秒导出测试。
- 中英文模板重新生成；与上一提交的解压内容比较仅 docProps/core.xml 时间元数据变化。
- 用重建中文模板填写隔离 MDR 样本：导入 1 Basic、1 UDI、1 Market，0 错误、0 警告；DEVICE.POST、MARKET_INFO.PUT 导出均通过 bundled Production XSD。
- 浏览器从选择记录到生成 XML，捕获实际 download 事件；结果和手动下载入口保留。
- 新构建 Mac 1.0.1 自动弹 NSSavePanel；取消保存后无错误弹窗，结果与下载链接仍在。
- 本地 Mac ZIP 与 app 内文件逐一一致；codesign --verify --deep --strict 通过。Mac 为 arm64 本地签名，未 Apple 公证。

## 边界

本地隔离数据验证，不使用或修改用户业务数据库。Windows 发布构建结果另见 GitHub Actions；未进行 Windows 桌面交互实测或 EUDAMED Playground 上传验收。未将此次检查等同于所有功能无 bug。
