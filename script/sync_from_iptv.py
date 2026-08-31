#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_from_iptv.py

每天检查上游仓库 xisohi/CHINA-IPTV 的 Multicast 和 Unicast 两个目录，
如果上游文件的大小 > 当前仓库对应文件的大小，则用上游内容覆盖当前仓库文件。

依赖: requests
    pip install requests

环境变量:
    GITHUB_TOKEN      - 有写权限的 token（GitHub Actions 里自动提供 secrets.GITHUB_TOKEN 即可，
                         需要给 workflow 设置 permissions: contents: write）
    GITHUB_REPOSITORY - 目标仓库，格式 "owner/repo"（GitHub Actions 会自动注入，
                         本地运行时需要自己设置，例如 export GITHUB_REPOSITORY=youruser/yourrepo）
    TARGET_BRANCH     - 目标仓库分支，默认 main
    SOURCE_REPO       - 上游仓库，默认 xisohi/CHINA-IPTV
    SOURCE_BRANCH     - 上游仓库分支，默认 main
    SYNC_DIRS         - 要同步的目录，逗号分隔，默认 "Multicast,Unicast"
"""

import base64
import os
import sys
import time
import requests

API_BASE = "https://api.github.com"

SOURCE_REPO = os.environ.get("SOURCE_REPO", "xisohi/CHINA-IPTV")
SOURCE_BRANCH = os.environ.get("SOURCE_BRANCH", "main")

TARGET_REPO = os.environ.get("GITHUB_REPOSITORY")  # owner/repo
TARGET_BRANCH = os.environ.get("TARGET_BRANCH", "main")

SYNC_DIRS = [d.strip() for d in os.environ.get("SYNC_DIRS", "Multicast,Unicast").split(",") if d.strip()]

TOKEN = os.environ.get("GITHUB_TOKEN")

if not TARGET_REPO:
    print("错误: 未设置 GITHUB_REPOSITORY 环境变量（owner/repo）", file=sys.stderr)
    sys.exit(1)

if not TOKEN:
    print("错误: 未设置 GITHUB_TOKEN 环境变量", file=sys.stderr)
    sys.exit(1)

SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "china-iptv-sync-script",
})


def get_tree(repo: str, branch: str) -> dict:
    """获取仓库某分支的完整 git tree（递归），返回 {path: {"sha":..., "size":...}}"""
    url = f"{API_BASE}/repos/{repo}/git/trees/{branch}"
    resp = SESSION.get(url, params={"recursive": "1"})
    resp.raise_for_status()
    data = resp.json()
    if data.get("truncated"):
        print(f"警告: {repo} 的 tree 被截断了，超大仓库可能需要分批处理", file=sys.stderr)

    result = {}
    for item in data.get("tree", []):
        if item.get("type") != "blob":
            continue
        result[item["path"]] = {"sha": item["sha"], "size": item.get("size", 0)}
    return result


def filter_by_dirs(tree: dict, dirs: list) -> dict:
    """只保留指定目录（含子目录）下的文件"""
    prefixes = tuple(d.rstrip("/") + "/" for d in dirs)
    return {path: info for path, info in tree.items() if path.startswith(prefixes)}


def get_blob_content(repo: str, sha: str) -> bytes:
    """通过 blob sha 获取文件原始内容（bytes）"""
    url = f"{API_BASE}/repos/{repo}/git/blobs/{sha}"
    resp = SESSION.get(url)
    resp.raise_for_status()
    data = resp.json()
    encoding = data.get("encoding")
    content = data.get("content", "")
    if encoding == "base64":
        return base64.b64decode(content)
    # 理论上 blobs API 总是 base64，兜底处理
    return content.encode("utf-8")


def update_file(repo: str, branch: str, path: str, content_bytes: bytes, existing_sha: str, message: str):
    """通过 Contents API 创建/更新目标仓库文件"""
    url = f"{API_BASE}/repos/{repo}/contents/{path}"
    payload = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode("ascii"),
        "branch": branch,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    resp = SESSION.put(url, json=payload)
    if resp.status_code not in (200, 201):
        print(f"更新失败: {path} -> {resp.status_code} {resp.text}", file=sys.stderr)
        return False
    return True


def main():
    print(f"上游仓库: {SOURCE_REPO}@{SOURCE_BRANCH}")
    print(f"目标仓库: {TARGET_REPO}@{TARGET_BRANCH}")
    print(f"同步目录: {SYNC_DIRS}")

    source_tree_full = get_tree(SOURCE_REPO, SOURCE_BRANCH)
    target_tree_full = get_tree(TARGET_REPO, TARGET_BRANCH)

    source_files = filter_by_dirs(source_tree_full, SYNC_DIRS)
    target_files = filter_by_dirs(target_tree_full, SYNC_DIRS)

    print(f"上游相关文件数: {len(source_files)}")
    print(f"目标相关文件数: {len(target_files)}")

    updated = 0
    skipped = 0
    created = 0
    failed = 0

    for path, src_info in source_files.items():
        src_size = src_info["size"]
        tgt_info = target_files.get(path)

        if tgt_info is None:
            # 目标仓库里没有这个文件，视为需要新建
            need_update = True
            reason = "目标不存在，新建"
        elif src_size > tgt_info["size"]:
            need_update = True
            reason = f"上游更大 ({src_size} > {tgt_info['size']})"
        else:
            need_update = False
            reason = f"无需更新 ({src_size} <= {tgt_info['size']})"

        if not need_update:
            skipped += 1
            continue

        print(f"[同步] {path}: {reason}")

        try:
            content = get_blob_content(SOURCE_REPO, src_info["sha"])
        except requests.HTTPError as e:
            print(f"获取上游内容失败: {path} -> {e}", file=sys.stderr)
            failed += 1
            continue

        existing_sha = tgt_info["sha"] if tgt_info else None
        ok = update_file(
            TARGET_REPO,
            TARGET_BRANCH,
            path,
            content,
            existing_sha,
            message=f"sync: update {path} from {SOURCE_REPO}",
        )

        if ok:
            if existing_sha:
                updated += 1
            else:
                created += 1
        else:
            failed += 1

        # 避免触发 GitHub API 速率限制
        time.sleep(0.5)

    print("=" * 40)
    print(f"完成。更新: {updated}, 新建: {created}, 跳过: {skipped}, 失败: {failed}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
