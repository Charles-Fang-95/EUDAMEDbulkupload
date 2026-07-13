"""检查工具是否有新版本：从 GitHub / Gitee Releases API 拉最新 release。

不做自动下载/替换；仅返回新版本元信息供帮助页展示链接。所有异常都吞掉、用 status 字段表达，
调用方不需要 try/except。
"""

from __future__ import annotations

import json
import platform
import urllib.error
import urllib.request


def check_latest_release(api_url: str, current_version: str, timeout: int = 6, mirror_api_url: str = "") -> dict:
    """请求 GitHub Releases 最新 release；失败时可回退到 Gitee mirror。

    返回 dict（永不抛异常）：
      status: "ok"          有新版本可下载
              "up_to_date"  本地已是最新
              "local_newer"  本地版本高于线上最新发布版本
              "unconfigured" RELEASES_API_URL 留空
              "no_release"   仓库存在但尚未发布 Release
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
      source: github / gitee
      fallback_error: GitHub 失败但 Gitee 成功时保留原始错误
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
        "source": "",
        "fallback_error": "",
    }
    if not api_url and not mirror_api_url:
        return result

    primary = _load_release(api_url, timeout, "github") if api_url else (None, "unconfigured", "GitHub 更新源未配置。", "")
    payload, error_status, error_text, source = primary
    fallback_error = ""
    if error_status and mirror_api_url:
        fallback_error = error_text
        payload, error_status, error_text, source = _load_release(mirror_api_url, timeout, "gitee")
    if error_status:
        result["status"] = "no_release" if error_status == "not_found" else error_status
        result["error"] = error_text
        result["fallback_error"] = fallback_error
        result["source"] = source
        return result
    normalized = _normalize_release(payload, source)
    if not normalized:
        result["status"] = "error"
        result["error"] = f"{source or 'Release'} API 返回值不是 release 对象。"
        result["fallback_error"] = fallback_error
        result["source"] = source
        return result

    tag = normalized["tag"]
    if not tag:
        result["status"] = "error"
        result["error"] = "release 缺少 tag_name"
        result["fallback_error"] = fallback_error
        result["source"] = source
        return result

    latest = tag.lstrip("vV").strip()
    result["latest_version"] = latest
    result["html_url"] = normalized["html_url"]
    result["published_at"] = normalized["published_at"]
    result["body"] = normalized["body"]
    result["prerelease"] = normalized["prerelease"]
    result["source"] = source
    result["fallback_error"] = fallback_error
    assets = normalized["assets"]
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


def release_download_links(github_api: str, gitee_api: str, timeout: int = 6) -> dict:
    """分别读取 GitHub/Gitee 最新 release，返回 Windows ZIP 直链。

    与 check_latest_release 的“主源失败后回退”不同，这里两个来源独立检查：
    一个失败不影响另一个，方便帮助页同时给出国际/国内下载入口。
    """
    return {
        "github": _download_source(github_api, timeout, "github"),
        "gitee": _download_source(gitee_api, timeout, "gitee"),
    }


def _download_source(api_url: str, timeout: int, source: str) -> dict:
    data = {
        "version": "",
        "zip_url": "",
        "page_url": "",
        "error": "",
        "source": source,
    }
    if not api_url:
        data["error"] = f"{_source_label(source)} 更新源未配置。"
        return data
    payload, error_status, error_text, loaded_source = _load_release(api_url, timeout, source)
    if error_status:
        data["error"] = error_text
        data["page_url"] = _release_page_url(source)
        return data
    normalized = _normalize_release(payload, loaded_source)
    if not normalized:
        data["error"] = f"{_source_label(source)} API 返回值不是 release 对象。"
        data["page_url"] = _release_page_url(source)
        return data
    tag = normalized.get("tag", "")
    data["version"] = tag.lstrip("vV").strip()
    data["page_url"] = normalized.get("html_url") or _release_page_url(source)
    preferred = _preferred_asset(normalized.get("assets") or [])
    data["zip_url"] = preferred.get("url", "") if preferred else ""
    return data


def _load_release(url: str, timeout: int, source: str):
    payload, error_status, error_text = _fetch_json(url, timeout, source)
    if error_status == "not_found":
        fallback_url = _fallback_releases_url(url)
        if fallback_url:
            payload, error_status, error_text = _fetch_json(fallback_url, timeout, source)
        else:
            error_status = "no_release"
            error_text = f"{_source_label(source)} 仓库尚未发布 Release。"
    if error_status:
        return None, error_status, error_text, source
    if isinstance(payload, list):
        if not payload:
            return None, "no_release", f"{_source_label(source)} 仓库尚未发布 Release。", source
        payload = payload[0]
    return payload, "", "", source


def _fetch_json(url: str, timeout: int, source: str):
    try:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "eudamed-local-beta"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="ignore")), "", ""
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "not_found", f"{_source_label(source)} 仓库尚未发布 Release。"
        if exc.code in {403, 429}:
            return None, "offline", f"{_source_label(source)} API HTTP {exc.code}: {exc.reason}"
        return None, "error", f"{_source_label(source)} API HTTP {exc.code}: {exc.reason}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, "offline", str(exc)
    except (ValueError, json.JSONDecodeError) as exc:
        return None, "error", f"JSON 解析失败: {exc}"


def _fallback_releases_url(api_url: str) -> str:
    marker = "/releases/latest"
    if marker not in api_url:
        return ""
    return api_url.replace(marker, "/releases?per_page=1")


def _normalize_release(payload, source: str) -> dict:
    if not isinstance(payload, dict):
        return {}
    if source == "gitee":
        return _normalize_gitee_release(payload)
    return _normalize_github_release(payload)


def _normalize_github_release(payload: dict) -> dict:
    return {
        "tag": str(payload.get("tag_name") or payload.get("name") or "").strip(),
        "html_url": str(payload.get("html_url") or ""),
        "published_at": str(payload.get("published_at") or ""),
        "body": str(payload.get("body") or ""),
        "prerelease": bool(payload.get("prerelease")),
        "assets": _release_assets(payload.get("assets") or [], "github"),
    }


def _normalize_gitee_release(payload: dict) -> dict:
    tag = str(payload.get("tag_name") or payload.get("tag") or payload.get("name") or "").strip()
    html_url = str(payload.get("html_url") or payload.get("url") or "")
    if not html_url and tag:
        html_url = f"https://gitee.com/Charles-Fang-95/EUDAMEDbulkupload/releases/tag/{tag}"
    return {
        "tag": tag,
        "html_url": html_url,
        "published_at": str(payload.get("published_at") or payload.get("created_at") or ""),
        "body": str(payload.get("body") or payload.get("description") or ""),
        "prerelease": bool(payload.get("prerelease")),
        "assets": _release_assets(payload.get("assets") or payload.get("attach_files") or [], "gitee", tag),
    }


def _release_assets(raw_assets, source: str = "github", tag: str = "") -> list[dict]:
    if not isinstance(raw_assets, list):
        return []
    assets = []
    for item in raw_assets:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("filename") or item.get("file_name") or "")
        url = str(item.get("browser_download_url") or item.get("download_url") or item.get("url") or "")
        if source == "gitee":
            url = _normalize_gitee_asset_url(url, name, tag)
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


def _normalize_gitee_asset_url(url: str, name: str, tag: str) -> str:
    if url.startswith("http"):
        return url
    if tag and name:
        return f"https://gitee.com/Charles-Fang-95/EUDAMEDbulkupload/releases/download/{tag}/{name}"
    return url


def _source_label(source: str) -> str:
    return "Gitee" if source == "gitee" else "GitHub"


def _release_page_url(source: str) -> str:
    if source == "gitee":
        return "https://gitee.com/Charles-Fang-95/EUDAMEDbulkupload/releases"
    return "https://github.com/Charles-Fang-95/EUDAMEDbulkupload/releases"


def _preferred_asset(assets: list[dict]) -> dict:
    if not assets:
        return {}
    package_assets = [
        asset for asset in assets
        if str(asset.get("name") or "").lower().endswith((".zip", ".exe", ".dmg", ".pkg"))
    ]
    if not package_assets:
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

    return max(package_assets, key=score)


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
