#!/usr/bin/env python3
"""
update_tvbox.py
o0HalfLife0o/TVBoxOSC 仓库的 release 由 takagen99 和 q215613905 两位作者的
构建交替发布（同一个 release 只会 Credit 其中一位），因此不能直接用
/releases/latest（那只返回整个仓库最新的一条，会漏掉另一位作者）。

本脚本会翻页扫描 release 列表，分别找到两位作者各自最新的一条 release，
把其中所有 .apk 资源同步写入 apk/tvbox.json。

同步规则：
  - tvbox.json 中 key 前缀为 "tvbox-t"（takagen99）或 "tvbox-q"（q215613905）
    的条目视为本脚本管理，每次运行按作者分别整体移除旧条目、重新生成，
    避免残留旧版本的失效链接。
  - 资源文件名形如：
        TVBox_takagen99_20251127-1156-arm64-generic-python.apk
        TVBox_q215613905_20251016-2311-python.apk
    去掉作者、tag、结尾的 "-python" 后剩余部分即为变体（如 "arm64-generic"），
    q215613905 目前只有单一构建（无变体后缀）。
  - key 规则： tvbox-t-{variant}  /  tvbox-q(-{variant})？
    与仓库里已有的 tvbox-t-arm64-generic / tvbox-q 等 key 保持一致。

用法:
    python script/update_tvbox.py
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── 配置 ─────────────────────────────────────────────────────────────────────
JSON_PATH  = Path("apk/tvbox.json")
API_BASE   = "https://api.github.com"
REPO       = "o0HalfLife0o/TVBoxOSC"
REPO_URL   = "https://github.com/o0HalfLife0o/TVBoxOSC"
MAX_PAGES  = 5     # 最多翻 5 页（每页 30 条）查找两位作者的最新 release
PER_PAGE   = 30

AUTHORS = {
    "takagen99":    "t",
    "q215613905":   "q",
}

CREDIT_RE = re.compile(r"Credit:\s*([A-Za-z0-9_-]+)", re.IGNORECASE)
# 资源文件名: TVBox_<author>_<tag>(-<variant>)?(-python)?.apk
ASSET_NAME_RE = re.compile(
    r"^TVBox_(?P<author>[A-Za-z0-9_-]+)_(?P<tag>\d{8}-\d{4})(?:-(?P<rest>.+))?\.apk$",
    re.IGNORECASE,
)

# 已知变体的展示信息，未识别的变体会用通用模板兜底
KNOWN_VARIANTS = {
    ("t", None): {
        "name": "tvbox(t版 黑盒)", "logo": "/images/tvbox-t.jpeg",
        "android": "", "desc": "tvbox系列的黑盒，支持自定义源，界面更加美观",
    },
    ("t", "arm64-generic"): {
        "name": "tvbox(t版 黑盒) arm64-generic", "logo": "/images/tvbox-t.jpeg",
        "android": "", "desc": "tvbox系列的黑盒通用版，arm64版本适合手机平板等新设备安装，界面更加美观",
    },
    ("t", "arm64-hisense"): {
        "name": "tvbox(t版 黑盒) arm64-hisense", "logo": "/images/tvbox-t.jpeg",
        "android": "海信", "desc": "tvbox系列的黑盒，64位的海信版本",
    },
    ("t", "armeabi-generic"): {
        "name": "tvbox(t版 黑盒) armeabi-generic", "logo": "/images/tvbox-t.jpeg",
        "android": "", "desc": "tvbox系列的黑盒32位通用版，适合电视安装",
    },
    ("t", "armeabi-hisense"): {
        "name": "tvbox(t版 黑盒) armeabi-hisense", "logo": "/images/tvbox-t.jpeg",
        "android": "海信", "desc": "tvbox系列的黑盒32位海信版本",
    },
    ("q", None): {
        "name": "tvbox(q版 白盒)", "logo": "/images/tvbox.jpg",
        "android": "安卓4.X", "desc": "tvbox系列的白盒，兼容安卓4版本，一直保持更新",
    },
}
# ─────────────────────────────────────────────────────────────────────────────


def gh_get(url: str, retries: int = 3) -> dict | list:
    """访问 GitHub API，自动处理限速与重试。"""
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {
        "Accept":     "application/vnd.github+json",
        "User-Agent": "tvbox-updater/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                reset = int(e.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait  = max(reset - int(time.time()), 10)
                print(f"    [API限速] 等待 {wait}s 后重试…")
                time.sleep(wait)
            elif e.code == 404:
                raise FileNotFoundError(f"404 Not Found: {url}") from e
            else:
                raise
        except Exception as exc:
            if attempt == retries - 1:
                raise
            print(f"    [重试 {attempt + 1}/{retries}] {exc}")
            time.sleep(3)


def find_latest_release_per_author() -> dict:
    """翻页扫描 release 列表，返回 {author: release_json} 各自最新的一条。"""
    found: dict = {}
    for page in range(1, MAX_PAGES + 1):
        if len(found) == len(AUTHORS):
            break
        url = f"{API_BASE}/repos/{REPO}/releases?per_page={PER_PAGE}&page={page}"
        releases = gh_get(url)
        if not releases:
            break

        for release in releases:
            body = release.get("body", "") or ""
            m = CREDIT_RE.search(body)
            if not m:
                continue
            author = m.group(1)
            if author in AUTHORS and author not in found:
                found[author] = release
                print(f"    找到 {author} 最新 release: {release.get('tag_name')}")

        if len(found) == len(AUTHORS):
            break

    return found


def build_entries(author: str, release: dict) -> dict:
    """把某个作者的 release 转换为 tvbox.json 需要的条目字典。"""
    letter = AUTHORS[author]
    tag    = release.get("tag_name", "")
    version = tag[:8]  # "20251127-1156" -> "20251127"
    entries: dict = {}

    for asset in release.get("assets", []):
        filename = asset.get("name", "")
        if not filename.lower().endswith(".apk"):
            continue

        m = ASSET_NAME_RE.match(filename)
        if not m:
            print(f"    ⚠️  无法解析的资源文件名，跳过: {filename}")
            continue

        rest = m.group("rest")
        variant = None
        if rest:
            # 去掉结尾的 "-python"（不区分大小写）
            variant = re.sub(r"-python$", "", rest, flags=re.IGNORECASE)
            if variant.lower() == "python" or variant == "":
                variant = None

        key = f"tvbox-{letter}" + (f"-{variant}" if variant else "")

        info = KNOWN_VARIANTS.get((letter, variant))
        if info is None:
            # 未知变体，使用通用模板兜底
            label = variant or ""
            base_name = "tvbox(t版 黑盒)" if letter == "t" else "tvbox(q版 白盒)"
            info = {
                "name":    f"{base_name} {label}".strip(),
                "logo":    "/images/tvbox-t.jpeg" if letter == "t" else "/images/tvbox.jpg",
                "android": "",
                "desc":    f"tvbox系列，{author} 构建版本{(' ' + label) if label else ''}",
            }

        entries[key] = {
            "version": version,
            "name":    info["name"],
            "logo":    info["logo"],
            "android": info["android"],
            "desc":    info["desc"],
            "url":     REPO_URL,
            "sub_dir": asset.get("browser_download_url", ""),
        }

    return entries


def main():
    if not JSON_PATH.exists():
        raise SystemExit(f"❌ 找不到 {JSON_PATH}，请确认脚本在仓库根目录运行")

    with JSON_PATH.open(encoding="utf-8") as f:
        data: dict = json.load(f)

    print(f"🔍 正在扫描 {REPO} 的 release 列表，查找 takagen99 / q215613905 各自最新版本…")
    latest = find_latest_release_per_author()

    if not latest:
        print("⚠️  没有找到任何匹配 Credit 的 release，保持 tvbox.json 不变")
        return

    total_added = 0
    for author, release in latest.items():
        letter = AUTHORS[author]
        entries = build_entries(author, release)
        if not entries:
            print(f"⚠️  {author} 的 release {release.get('tag_name')} 未找到 .apk 资源，跳过")
            continue

        # 移除该作者旧的 tvbox-{letter}* 条目，替换为最新的
        prefix = f"tvbox-{letter}"
        removed = [k for k in data if k == prefix or k.startswith(prefix + "-")]
        for k in removed:
            del data[k]

        data.update(entries)
        total_added += len(entries)
        print(f"    {author}（{release.get('tag_name')}）：移除旧条目 {len(removed)} 个，写入新条目 {len(entries)} 个")
        for k in entries:
            print(f"      - {k}")

    if total_added == 0:
        print("⚠️  没有任何条目被更新，保持 tvbox.json 不变")
        return

    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"💾 已同步 {total_added} 个 APK 条目到 {JSON_PATH}")

    # 输出给 GitHub Actions
    env_file = os.getenv("GITHUB_OUTPUT", "")
    if env_file:
        with open(env_file, "a") as f:
            f.write(f"updated={total_added}\n")


if __name__ == "__main__":
    main()
