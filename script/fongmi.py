#!/usr/bin/env python3
"""
update_apk_versions.py
检查 https://github.com/FongMi/Release/releases 的最新发布，
更新 apk/fongmi.json 中每个 apk 条目的:
    version  -> release 的版本号（tag，如 5.7.4）
    sub_dir  -> release 附件的下载地址
                （https://github.com/FongMi/Release/releases/download/<tag>/<文件名>）
其余字段与 JSON 结构保持不变。

用法:
    python scripts/update_apk_versions.py
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

VERSION_RE = re.compile(r"v?(\d+\.\d+\.\d+(?:\.\d+)?)")

GITHUB_REPO  = "FongMi/Release"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases?per_page=30"


@dataclass
class JsonConfig:
    json_path:   str
    tag_keyword: str = ""   # 可选：只在 tag/name 含该关键字的 release 中查找


CONFIGS: list[JsonConfig] = [
    JsonConfig(json_path="apk/fongmi.json"),
]


def gh_get(url: str, retries: int = 3):
    """访问 GitHub API，自动处理限速与重试。"""
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {
        "Accept":     "application/vnd.github+json",
        "User-Agent": "apk-version-updater/3.2",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt < retries - 1:
                reset = int(e.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = min(max(reset - int(time.time()), 10), 120)
                print(f"  [API限速] 等待 {wait}s 后重试…")
                time.sleep(wait)
            else:
                raise
        except Exception as exc:
            if attempt == retries - 1:
                raise
            print(f"  [重试 {attempt + 1}/{retries}] {exc}")
            time.sleep(5)


def extract_version(*texts: str) -> str | None:
    for t in texts:
        if t:
            m = VERSION_RE.search(t)
            if m:
                return m.group(1)
    return None


def fetch_releases(tag_keyword: str = "") -> list[dict]:
    """获取 release 列表（跳过 draft，按发布时间从新到旧）。"""
    releases = [r for r in gh_get(RELEASES_URL) if not r.get("draft")]
    kw = tag_keyword.lower()
    if kw:
        releases = [r for r in releases
                    if kw in f"{r.get('tag_name', '')} {r.get('name', '')}".lower()]
    releases.sort(key=lambda r: r.get("published_at") or r.get("created_at") or "",
                  reverse=True)
    return releases


def find_asset(releases: list[dict], file_name: str):
    """从新到旧找到第一个含有同名附件的 release，返回 (release, asset)。"""
    for rel in releases:
        for asset in rel.get("assets", []):
            if asset["name"].lower() == file_name.lower():
                return rel, asset
    return None, None


def process_json(cfg: JsonConfig) -> int:
    json_path = Path(cfg.json_path)
    print(f"\n{'═' * 60}\n📄 {cfg.json_path}\n{'═' * 60}")

    if not json_path.exists():
        print(f"  ⚠️  文件不存在，跳过: {json_path}")
        return 0

    releases = fetch_releases(cfg.tag_keyword)
    if not releases:
        print("  ❌ 没有找到可用的 release，跳过")
        return 0
    print(f"  最新 release : {releases[0]['tag_name']} ({releases[0].get('published_at')})")

    with json_path.open(encoding="utf-8") as f:
        data: dict = json.load(f)

    print(f"  共 {len(data)} 个条目需要检查\n")
    updated_count = 0

    for file_key, entry in data.items():
        file_name = file_key.rsplit("/", 1)[-1]
        print(f"  ▶ {file_key}")

        rel, asset = find_asset(releases, file_name)
        if not asset:
            print("    ⚠️  最近的 release 附件中找不到此文件，跳过\n")
            continue

        remote_ver = extract_version(rel.get("tag_name", ""), rel.get("name", ""))
        remote_url = asset["browser_download_url"]
        changed = False

        if remote_ver and remote_ver != entry.get("version", ""):
            print(f"    🔄 version: {entry.get('version', '')} → {remote_ver}")
            entry["version"] = remote_ver
            changed = True
        if remote_url != entry.get("sub_dir", ""):
            print(f"    🔄 sub_dir: {entry.get('sub_dir', '')} → {remote_url}")
            entry["sub_dir"] = remote_url
            changed = True

        if changed:
            updated_count += 1
            print("    ✅ 已标记更新\n")
        else:
            print("    ✔  无变化\n")

    if updated_count:
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"  💾 已写回 {cfg.json_path}，本文件共更新 {updated_count} 条")
    else:
        print(f"  ✔  {cfg.json_path} 所有条目均为最新，无需写入")
    return updated_count


def main():
    total_updated = sum(process_json(cfg) for cfg in CONFIGS)

    print(f"\n{'═' * 60}\n🏁 全部检查完毕，共更新 {total_updated} 个条目\n{'═' * 60}\n")

    env_file = os.getenv("GITHUB_OUTPUT", "")
    if env_file:
        with open(env_file, "a") as f:
            f.write(f"updated={total_updated}\n")


if __name__ == "__main__":
    main()
