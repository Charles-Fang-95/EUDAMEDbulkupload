"""检查工具是否有新版本：从 GitHub Releases API 拉最新 release。

不做自动下载/替换；仅返回新版本元信息供帮助页展示链接。所有异常都吞掉、用 status 字段表达，
调用方不需要 try/except。
"""

from __future__ import annotations

import json
import platform
import urllib.error
import urllib.request


def check_latest_release(api_url: str, current_version: str, timeout: int = 6) -> dict:
    """请求 GitHub Releases 最新 release，与本地版本比较。

    返回 dict（永不抛异常）：
      status: "ok"          有新版本可下载
              "up_to_date"  本地已是最新
              "local_newer"  本地版本高于 GitHub 最新发布版本
              "unconfigured" RELEASES_API_URL 留空
              "no_release"   仓库存在但尚未发布 GitHub Release
              "offline"     联网失败 / 超时
              "error"       JSON 解析或字段缺失
      latest_version: 远端语义化版本（去掉前缀 v）
      html_url: 用户可点开看 release 的页面
      asset_url: 第一个 asset 的下载直链（可能为空）
      assets: release 中所有 asset 的 name/url/size 列表
      prerelease: 是否 GitHub pre-release
      published_at: ISO 时间串
      body: release notes 全文（裁剪由调用方决定）
      error: 失败时的简要描述
    """
    result = {
        "status": "unconfigured",
        "latest_version": "",
        "html_url": "",
        "asset_url": "",
        "assets": [],
        "prerelease": False,
        "published_at": "",
        "body": "",
        "error": "",
    }
    if not api_url:
        return result

    payload, error_status, error_text = _fetch_json(api_url, timeout)
    if error_status == "not_found":
        fallback_url = _fallback_releases_url(api_url)
        if fallback_url:
            payload, error_status, error_text = _fetch_json(fallback_url, timeout)
            if isinstance(payload, list):
                payload = payload[0] if payload else None
                if payload is None:
                    error_status = "no_release"
                    error_text = "GitHub 仓库尚未发布 Release。"
        else:
            error_status = "no_release"
            error_text = "GitHub 仓库尚未发布 Release。"
    if error_status:
        result["status"] = "no_release" if error_status == "not_found" else error_status
        result["error"] = error_text
        return result
    if not isinstance(payload, dict):
        result["status"] = "error"
        result["error"] = "GitHub API 返回值不是 release 对象。"
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
    result["prerelease"] = bool(payload.get("prerelease"))
    raw_assets = payload.get("assets") or []
    assets = _release_assets(raw_assets)
    result["assets"] = assets
    preferred = _preferred_asset(assets)
    if preferred:
        result["asset_url"] = preferred.get("url", "")

    comparison = compare_versions(current_version, latest)
    if comparison < 0:
        result["status"] = "ok"
    elif comparison == 0:
        result["status"] = "up_to_date"
    else:
        result["status"] = "local_newer"
    return result


def _fetch_json(url: str, timeout: int):
    try:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "eudamed-local-beta"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="ignore")), "", ""
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "not_found", "GitHub 仓库尚未发布 Release。"
        return None, "error", f"GitHub API HTTP {exc.code}: {exc.reason}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, "offline", str(exc)
    except (ValueError, json.JSONDecodeError) as exc:
        return None, "error", f"JSON 解析失败: {exc}"


def _fallback_releases_url(api_url: str) -> str:
    marker = "/releases/latest"
    if marker not in api_url:
        return ""
    return api_url.replace(marker, "/releases?per_page=1")


def _release_assets(raw_assets) -> list[dict]:
    if not isinstance(raw_assets, list):
        return []
    assets = []
    for item in raw_assets:
        if not isinstance(item, dict):
            continue
        url = str(item.get("browser_download_url") or "")
        name = str(item.get("name") or "")
        if not url or not name:
            continue
        assets.append(
            {
                "name": name,
                "url": url,
                "size": item.get("size") or 0,
                "content_type": str(item.get("content_type") or ""),
            }
        )
    return assets


def _preferred_asset(assets: list[dict]) -> dict:
    if not assets:
        return {}
    system = platform.system().lower()
    if system == "windows":
        keywords = ("windows", "win", ".exe")
    elif system == "darwin":
        keywords = ("macos", "mac", ".dmg", ".pkg", ".app")
    else:
        keywords = ("linux",)

    def score(asset: dict) -> tuple[int, int]:
        name = str(asset.get("name") or "").lower()
        platform_score = 1 if any(keyword in name for keyword in keywords) else 0
        package_score = 1 if name.endswith((".zip", ".exe", ".dmg", ".pkg")) else 0
        return (platform_score, package_score)

    return max(assets, key=score)


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
