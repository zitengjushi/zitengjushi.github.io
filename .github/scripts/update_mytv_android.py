#!/usr/bin/env python3
"""
update_mytv_android.py
检查 mytv-android/mytv-android 仓库的最新正式 release（/releases/latest，
不含预览版），把该 release 下所有 .apk 资源同步写入 apk/tv.json。

同步规则：
  - tv.json 中所有 key 以 "mytv-android-" 开头的条目都视为本脚本管理的条目，
    每次运行会先整体移除这些旧条目，再根据最新 release 的资源重新生成，
    这样同一 APK 变体在版本升级后 key 保持稳定（做"替换"而不是不断"新增"），
    也不会残留已下架资源对应的失效条目。
  - key 由资源文件名去掉版本号后拼接而成，例如：
      mytv-android-tv-2.1.0.212-all-sdk23-original.apk
      -> mytv-android-all-sdk23-original.apk
  - 中文名称按文件名中的 original / disguised 关键字及架构、SDK 信息自动生成。

用法:
    python script/update_mytv_android.py
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── 配置 ─────────────────────────────────────────────────────────────────────
JSON_PATH   = Path("apk/tv.json")
API_BASE    = "https://api.github.com"
REPO        = "mytv-android/mytv-android"
REPO_URL    = "https://github.com/mytv-android/mytv-android"
LOGO_PATH   = "/images/dszb.jpeg"
KEY_PREFIX  = "mytv-android-"

# 资源文件名前缀，例如 "mytv-android-tv-2.1.0.212-all-sdk23-original.apk"
# 捕获组 rest = "all-sdk23-original"
ASSET_NAME_RE = re.compile(r"^mytv-android-tv-[\d.]+-(?P<rest>.+)\.apk$", re.IGNORECASE)
# ─────────────────────────────────────────────────────────────────────────────


def gh_get(url: str, retries: int = 3) -> dict | list:
    """访问 GitHub API，自动处理限速与重试。"""
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {
        "Accept":     "application/vnd.github+json",
        "User-Agent": "mytv-android-updater/1.0",
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


def build_name(rest: str) -> str:
    """根据资源文件名剩余部分（如 'all-sdk23-original'）生成中文展示名称。"""
    parts = rest.lower().split("-")

    if "disguised" in parts:
        variant = "伪装版"
    elif "original" in parts:
        variant = "正常版"
    else:
        variant = rest  # 未识别的变体，直接用原始字符串兜底

    extra = [p for p in parts if p not in ("original", "disguised", "all")]
    extra_str = "·".join(extra)

    name = f"电视直播({variant})"
    if extra_str:
        name += f" [{extra_str}]"
    return name


def build_desc(rest: str) -> str:
    """根据变体类型生成描述文案。"""
    base = "可自定义直播源，基于天光云影开发"
    if "disguised" in rest.lower():
        base += "，伪装版本，伪装成Z视介（com.chinablue.tv）。解决鸿蒙系统小窗无法横屏，支持超级桌面。"
    return base


def parse_assets(assets: list[dict], version: str) -> dict:
    """把 release 的 assets 列表转换为 tv.json 需要的条目字典。"""
    entries: dict = {}

    for asset in assets:
        filename = asset.get("name", "")
        if not filename.lower().endswith(".apk"):
            continue

        m = ASSET_NAME_RE.match(filename)
        rest = m.group("rest") if m else filename[:-4]  # 去掉 .apk 兜底

        key = f"{KEY_PREFIX}{rest}.apk"

        entries[key] = {
            "version":  version,
            "name":     build_name(rest),
            "logo":     LOGO_PATH,
            "android":  "推荐" if rest.lower() == "all-sdk23-original" else "",
            "desc":     build_desc(rest),
            "url":      REPO_URL,
            "sub_dir":  asset.get("browser_download_url", ""),
        }

    return entries


def main():
    if not JSON_PATH.exists():
        raise SystemExit(f"❌ 找不到 {JSON_PATH}，请确认脚本在仓库根目录运行")

    with JSON_PATH.open(encoding="utf-8") as f:
        data: dict = json.load(f)

    print(f"🔍 正在获取 {REPO} 的最新正式 release…")
    release = gh_get(f"{API_BASE}/repos/{REPO}/releases/latest")

    tag_name = release.get("tag_name", "")
    version  = tag_name.lstrip("Vv")  # "V2.1.0.212" -> "2.1.0.212"
    assets   = release.get("assets", [])

    print(f"    最新版本: {tag_name}（共 {len(assets)} 个资源）")

    new_entries = parse_assets(assets, version)
    apk_count   = len(new_entries)

    if apk_count == 0:
        print("⚠️  该 release 下没有找到任何 .apk 资源，保持 tv.json 不变")
        return

    # 移除旧的 mytv-android-* 条目，替换为最新的
    removed = [k for k in data if k.startswith(KEY_PREFIX)]
    for k in removed:
        del data[k]

    data.update(new_entries)

    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"💾 已同步 {apk_count} 个 APK 条目到 {JSON_PATH}")
    print(f"    移除旧条目 {len(removed)} 个，写入新条目 {apk_count} 个")
    for k in new_entries:
        print(f"      - {k}")

    # 输出给 GitHub Actions
    env_file = os.getenv("GITHUB_OUTPUT", "")
    if env_file:
        with open(env_file, "a") as f:
            f.write(f"updated={apk_count}\n")
            f.write(f"version={version}\n")


if __name__ == "__main__":
    main()
