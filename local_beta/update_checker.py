"""检查工具是否有新版本：从 GitHub Releases API 拉最新 release。

不做自动下载/替换；仅返回新版本元信息供帮助页展示链接。所有异常都吞掉、用 status 字段表达，
调用方不需要 try/except。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request


def check_latest_release(api_url: str, current_version: str, timeout: int = 6) -> dict:
    """请求 GitHub Releases 最新 release，与本地版本比较。

    返回 dict（永不抛异常）：
      status: "ok"          有新版本可下载
              "up_to_date"  本地已是最新
              "unconfigured" RELEASES_API_URL 留空
              "offline"     联网失败 / 超时
              "error"       JSON 解析或字段缺失
      latest_version: 远端语义化版本（去掉前缀 v）
      html_url: 用户可点开看 release 的页面
      asset_url: 第一个 asset 的下载直链（可能为空）
      published_at: ISO 时间串
      body: release notes 全文（裁剪由调用方决定）
      error: 失败时的简要描述
    """
    result = {
        "status": "unconfigured",
        "latest_version": "",
        "html_url": "",
        "asset_url": "",
        "published_at": "",
        "body": "",
        "error": "",
    }
    if not api_url:
        return result

    try:
        request = urllib.request.Request(
            api_url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "eudamed-local-beta"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", errors="ignore"))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result["status"] = "offline"
        result["error"] = str(exc)
        return result
    except (ValueError, json.JSONDecodeError) as exc:
        result["status"] = "error"
        result["error"] = f"JSON 解析失败: {exc}"
        return result

    tag = str(payload.get("tag_name") or payload.get("name") or "").strip()
    if not tag:
        result["status"] = "error"
        result["error"] = "release 缺少 tag_name"
        return result

    latest = tag.lstrip("vV").strip()
    result["latest_version"] = latest
    result["html_url"] = str(payload.get("html_url") or "")
    result["published_at"] = str(payload.get("published_at") or "")
    result["body"] = str(payload.get("body") or "")
    assets = payload.get("assets") or []
    if assets and isinstance(assets, list):
        first = assets[0] or {}
        result["asset_url"] = str(first.get("browser_download_url") or "")

    result["status"] = "ok" if compare_versions(current_version, latest) < 0 else "up_to_date"
    return result


def compare_versions(a: str, b: str) -> int:
    """语义化版本比较；解析失败时回退到字符串比较。返回 -1/0/1。"""

    def parse(version: str) -> tuple:
        clean = version.strip().lstrip("vV")
        parts = []
        for chunk in clean.split("."):
            digits = ""
            for ch in chunk:
                if ch.isdigit():
                    digits += ch
                else:
                    break
            if not digits:
                raise ValueError(version)
            parts.append(int(digits))
        return tuple(parts) if parts else (0,)

    try:
        ta, tb = parse(a), parse(b)
    except ValueError:
        if a == b:
            return 0
        return -1 if a < b else 1
    # 补齐尾部 0 以便不同长度可比较
    length = max(len(ta), len(tb))
    ta = ta + (0,) * (length - len(ta))
    tb = tb + (0,) * (length - len(tb))
    if ta == tb:
        return 0
    return -1 if ta < tb else 1
