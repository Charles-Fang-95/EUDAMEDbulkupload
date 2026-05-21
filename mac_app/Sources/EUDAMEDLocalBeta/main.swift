import AppKit
import Foundation
import WebKit

private let appName = "EUDAMED Local Beta"
private let serverURL = URL(string: "http://127.0.0.1:8765")!

final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate {
    private var window: NSWindow!
    private var webView: WKWebView!
    private var serverProcess: Process?
    private var ownsServer = false
    private var outputPipe: Pipe?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        buildWindow()
        startOrAttachToServer()
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    func applicationWillTerminate(_ notification: Notification) {
        if ownsServer, let process = serverProcess, process.isRunning {
            process.terminate()
        }
    }

    private func buildWindow() {
        let config = WKWebViewConfiguration()
        config.defaultWebpagePreferences.allowsContentJavaScript = true

        webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = self

        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1200, height: 780),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = appName
        window.center()
        window.contentView = webView
        window.makeKeyAndOrderFront(nil)

        showStatus("正在启动本地 EUDAMED 工具...")
    }

    private func startOrAttachToServer() {
        DispatchQueue.global(qos: .userInitiated).async {
            if self.isServerReachable() {
                self.loadApp()
                return
            }

            do {
                try self.startBundledServer()
            } catch {
                self.showError("无法启动本地服务", detail: error.localizedDescription)
                return
            }

            for _ in 0..<60 {
                if self.isServerReachable() {
                    self.loadApp()
                    return
                }
                if let process = self.serverProcess, !process.isRunning {
                    self.showError("本地服务已退出", detail: self.recentServerOutput())
                    return
                }
                Thread.sleep(forTimeInterval: 0.25)
            }

            self.showError("本地服务启动超时", detail: "请确认本机已安装 python3，并且端口 8765 未被其他程序占用。")
        }
    }

    private func startBundledServer() throws {
        guard let resourceURL = Bundle.main.resourceURL else {
            throw AppError("找不到 App Resources 目录。")
        }

        let projectRoot = resourceURL.appendingPathComponent("EUDAMEDLocalBeta", isDirectory: true)
        let entrypoint = projectRoot.appendingPathComponent("run_local_beta.py")
        guard FileManager.default.fileExists(atPath: entrypoint.path) else {
            throw AppError("找不到打包的 run_local_beta.py：\(entrypoint.path)")
        }
        let dataRoot = try applicationSupportDataDirectory()

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = ["python3", "run_local_beta.py", "--no-reload"]
        process.currentDirectoryURL = projectRoot
        process.environment = [
            "PYTHONUNBUFFERED": "1",
            "EUDAMED_DATA_DIR": dataRoot.path,
            "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        ]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        outputPipe = pipe

        try process.run()
        serverProcess = process
        ownsServer = true
    }

    private func applicationSupportDataDirectory() throws -> URL {
        let base = try FileManager.default.url(
            for: .applicationSupportDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        let directory = base
            .appendingPathComponent("EUDAMED Local Beta", isDirectory: true)
            .appendingPathComponent("local_beta_data", isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        return directory
    }

    private func loadApp() {
        DispatchQueue.main.async {
            self.webView.load(URLRequest(url: serverURL))
        }
    }

    private func isServerReachable() -> Bool {
        var request = URLRequest(url: serverURL)
        request.timeoutInterval = 1.0

        let semaphore = DispatchSemaphore(value: 0)
        var ok = false
        let task = URLSession.shared.dataTask(with: request) { _, response, _ in
            if let http = response as? HTTPURLResponse {
                ok = (200..<500).contains(http.statusCode)
            }
            semaphore.signal()
        }
        task.resume()
        _ = semaphore.wait(timeout: .now() + 1.2)
        task.cancel()
        return ok
    }

    private func showStatus(_ message: String) {
        let html = """
        <!doctype html>
        <html lang="zh">
        <head>
          <meta charset="utf-8">
          <style>
            body { margin:0; min-height:100vh; display:grid; place-items:center; background:#f3efe6; color:#20201b; font-family:-apple-system,BlinkMacSystemFont,"Songti SC",sans-serif; }
            .card { width:min(560px, calc(100vw - 48px)); padding:32px; border-radius:18px; background:#fffdf7; border:1px solid #d7cfbf; box-shadow:0 10px 30px rgba(0,0,0,.05); }
            h1 { margin:0 0 12px; font-size:24px; }
            p { margin:0; color:#6e6a60; line-height:1.6; }
          </style>
        </head>
        <body><section class="card"><h1>\(escapeHTML(message))</h1><p>首次启动可能需要几秒钟。</p></section></body>
        </html>
        """
        DispatchQueue.main.async {
            self.webView.loadHTMLString(html, baseURL: nil)
        }
    }

    private func showError(_ message: String, detail: String) {
        let html = """
        <!doctype html>
        <html lang="zh">
        <head>
          <meta charset="utf-8">
          <style>
            body { margin:0; min-height:100vh; display:grid; place-items:center; background:#f3efe6; color:#20201b; font-family:-apple-system,BlinkMacSystemFont,"Songti SC",sans-serif; }
            .card { width:min(720px, calc(100vw - 48px)); padding:32px; border-radius:18px; background:#fffdf7; border:1px solid #d7cfbf; box-shadow:0 10px 30px rgba(0,0,0,.05); }
            h1 { margin:0 0 12px; font-size:24px; color:#ae3131; }
            pre { white-space:pre-wrap; padding:14px; border-radius:12px; background:#f8f4ea; color:#514b40; overflow:auto; }
          </style>
        </head>
        <body><section class="card"><h1>\(escapeHTML(message))</h1><pre>\(escapeHTML(detail))</pre></section></body>
        </html>
        """
        DispatchQueue.main.async {
            self.webView.loadHTMLString(html, baseURL: nil)
        }
    }

    private func recentServerOutput() -> String {
        guard let pipe = outputPipe else {
            return "没有捕获到服务输出。"
        }
        let data = pipe.fileHandleForReading.availableData
        guard !data.isEmpty else {
            return "服务没有输出更多错误信息。"
        }
        return String(data: data, encoding: .utf8) ?? "服务输出无法解码。"
    }
}

struct AppError: LocalizedError {
    let message: String

    init(_ message: String) {
        self.message = message
    }

    var errorDescription: String? {
        message
    }
}

private func escapeHTML(_ value: String) -> String {
    value
        .replacingOccurrences(of: "&", with: "&amp;")
        .replacingOccurrences(of: "<", with: "&lt;")
        .replacingOccurrences(of: ">", with: "&gt;")
        .replacingOccurrences(of: "\"", with: "&quot;")
        .replacingOccurrences(of: "'", with: "&#39;")
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
