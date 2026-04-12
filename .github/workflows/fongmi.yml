#!/usr/bin/env python3
"""
update_apk_versions.py
统一管理多个 APK JSON 配置文件的版本自动更新。
每个 JSON 文件对应一个 GitHub 上的 branch/目录，
通过 GitHub API 获取每个文件最新 commit message，
提取版本号后与本地 JSON 对比，若不同则仅更新 version 字段。

用法:
    python scripts/update_apk_versions.py
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from dataclasses import dataclass

# ── 版本号正则（匹配 3.2.2 / v3.2.2 / 5.0.7.1 等格式）────────────────────
VERSION_RE = re.compile(r"v?(\d+\.\d+\.\d+(?:\.\d+)?)")

# ── GitHub API 基础 URL ──────────────────────────────────────────────────────
GITHUB_REPO = "FongMi/Release"
API_BASE    = f"https://api.github.com/repos/{GITHUB_REPO}"


# ── 每个 JSON 文件的独立配置 ─────────────────────────────────────────────────
@dataclass
class JsonConfig:
    """描述一个需要维护的本地 JSON 文件及其对应的 GitHub 来源。"""
    json_path:  str   # 本地 JSON 路径（相对仓库根目录）
    branch:     str   # 对应的 GitHub branch
    remote_dir: str   # 远端仓库内的目录前缀（如 "apk"）


CONFIGS: list[JsonConfig] = [
    JsonConfig(
        json_path  = "apk/okjack.json",
        branch     = "okjack",
        remote_dir = "apk",
    ),
    JsonConfig(
        json_path  = "apk/fongmi.json",
        branch     = "fongmi",
        remote_dir = "apk",
    ),
    # 如需新增更多 JSON，在此继续追加 JsonConfig(...)
]
# ─────────────────────────────────────────────────────────────────────────────


def gh_get(url: str, retries: int = 3) -> list | dict:
    """访问 GitHub API，自动处理限速与重试。"""
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {
        "Accept":     "application/vnd.github+json",
        "User-Agent": "apk-version-updater/2.0",
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
            time.sleep(5)


def get_latest_commit(branch: str, repo_path: str) -> dict:
    """
    获取仓库内指定文件在指定 branch 上的最新 commit 信息。
    repo_path 示例: "apk/release/leanback-arm64_v8a.apk"
    返回: {"sha": str, "message": str, "date": str}
    """
    url  = f"{API_BASE}/commits?sha={branch}&path={repo_path}&per_page=1"
    data = gh_get(url)
    if not data:
        raise ValueError(f"未找到任何 commit 记录: branch={branch} path={repo_path}")
    c = data[0]["commit"]
    return {
        "sha":     data[0]["sha"],
        "message": c["message"].strip(),
        "date":    c["committer"]["date"],
    }


def extract_version(msg: str) -> str | None:
    """从 commit message 中提取版本号，未找到返回 None。"""
    m = VERSION_RE.search(msg)
    return m.group(1) if m else None


def process_json(cfg: JsonConfig) -> int:
    """处理单个 JSON 配置，返回更新条目数。"""
    json_path = Path(cfg.json_path)
    print(f"\n{'═' * 60}")
    print(f"📄 {cfg.json_path}  (branch: {cfg.branch})")
    print(f"{'═' * 60}")

    if not json_path.exists():
        print(f"  ⚠️  文件不存在，跳过: {json_path}")
        return 0

    with json_path.open(encoding="utf-8") as f:
        data: dict = json.load(f)

    print(f"  共 {len(data)} 个条目需要检查\n")
    updated_count = 0

    for file_key, entry in data.items():
        repo_path = f"{cfg.remote_dir}/{file_key}"   # e.g. apk/release/leanback-arm64_v8a.apk
        print(f"  ▶ {file_key}")

        try:
            commit_info = get_latest_commit(cfg.branch, repo_path)
        except FileNotFoundError:
            print(f"    ⚠️  GitHub 上找不到此文件，跳过\n")
            continue
        except Exception as exc:
            print(f"    ❌ 获取 commit 失败: {exc}，跳过\n")
            continue

        msg        = commit_info["message"]
        remote_ver = extract_version(msg)
        local_ver  = entry.get("version", "")

        print(f"    本地 version : {local_ver}")
        print(f"    Commit msg   : {msg[:80]}")
        print(f"    解析 version : {remote_ver or '(未识别，保留原值)'}")

        # 仅在版本号发生变化时更新
        if remote_ver and remote_ver != local_ver:
            print(f"    🔄 version: {local_ver} → {remote_ver}")
            entry["version"] = remote_ver
            updated_count += 1
            print(f"    ✅ 已标记更新")
        else:
            print(f"    ✔  无变化")

        print()
        time.sleep(0.3)   # 礼貌性延迟，避免触发 API 速率限制

    # 写回 JSON（保留原始格式：ensure_ascii=False, indent=2）
    if updated_count:
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 已写回 {cfg.json_path}，本文件共更新 {updated_count} 条")
    else:
        print(f"  ✔  {cfg.json_path} 所有条目均为最新，无需写入")

    return updated_count


def main():
    total_updated = 0

    for cfg in CONFIGS:
        total_updated += process_json(cfg)

    print(f"\n{'═' * 60}")
    print(f"🏁 全部检查完毕，共更新 {total_updated} 个条目")
    print(f"{'═' * 60}\n")

    # 输出给 GitHub Actions 后续步骤判断是否需要 commit
    env_file = os.getenv("GITHUB_OUTPUT", "")
    if env_file:
        with open(env_file, "a") as f:
            f.write(f"updated={total_updated}\n")


if __name__ == "__main__":
    main()
