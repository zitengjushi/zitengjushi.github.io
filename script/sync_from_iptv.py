#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_from_source.py

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
import re
import sys
import time
import requests

API_BASE = "https://api.github.com"

SOURCE_REPO = os.environ.get("SOURCE_REPO", "xisohi/CHINA-IPTV")
SOURCE_BRANCH = os.environ.get("SOURCE_BRANCH", "main")

TARGET_REPO = os.environ.get("GITHUB_REPOSITORY")  # owner/repo
TARGET_BRANCH = os.environ.get("TARGET_BRANCH", "main")

SYNC_DIRS = [d.strip() for d in os.environ.get("SYNC_DIRS", "Multicast,Unicast").split(",") if d.strip()]

# iptv.html 所在路径（相对仓库根目录），以及需要处理的"暂无"占位文本
IPTV_HTML_PATH = os.environ.get("IPTV_HTML_PATH", "iptv.html")
PLACEHOLDER_TEXT = os.environ.get("PLACEHOLDER_TEXT", "🌐暂无")
UNICAST_ICON = os.environ.get("UNICAST_ICON", "🔗单播")
MULTICAST_ICON = os.environ.get("MULTICAST_ICON", "🛰️组播")

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


def get_file_contents_api(repo: str, path: str, branch: str):
    """通过 Contents API 获取文件（返回 dict: sha, size, decoded text），不存在返回 None"""
    url = f"{API_BASE}/repos/{repo}/contents/{path}"
    resp = SESSION.get(url, params={"ref": branch})
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    data = resp.json()
    content = data.get("content", "")
    encoding = data.get("encoding")
    if encoding == "base64":
        raw = base64.b64decode(content)
    else:
        raw = content.encode("utf-8")
    return {"sha": data["sha"], "size": data.get("size", 0), "text": raw.decode("utf-8", errors="replace"), "raw": raw}


def has_stream_url(text: str) -> bool:
    """
    判断文件内容里是否存在真实的播放地址。
    文件格式类似:
        央视,#genre#
        CCTV1,
        CCTV2,http://xxx.xxx.xxx.xxx/xxx.m3u8
    只有"频道名,"（逗号后面为空）的行，视为没有真实地址；
    逗号后面出现包含 "://" 的内容，才算真正有播放地址。
    """
    for line in text.splitlines():
        line = line.strip()
        if not line or line.endswith("#genre#"):
            continue
        if "," not in line:
            continue
        _, _, rest = line.partition(",")
        rest = rest.strip()
        if "://" in rest:
            return True
    return False


def update_iptv_html(synced_content_cache: dict):
    """
    检查 iptv.html 中所有指向 Unicast/Multicast 目录、且当前显示为"暂无"占位符的链接，
    如果对应文件此刻已经有真实播放地址了，就把占位符替换成对应的"单播/组播"图标文字。
    只处理形如 href="/Unicast/xxx/yyy.txt" 或 href="/Multicast/xxx/yyy.txt" 的相对路径链接，
    其它形式（例如指向别的域名的绝对链接）一律跳过，不做任何修改。
    """
    print("=" * 40)
    print(f"开始检查并更新 {IPTV_HTML_PATH} 中的占位符...")

    html_info = get_file_contents_api(TARGET_REPO, IPTV_HTML_PATH, TARGET_BRANCH)
    if html_info is None:
        print(f"未找到 {IPTV_HTML_PATH}，跳过 html 更新", file=sys.stderr)
        return

    html_text = html_info["text"]

    # 只匹配相对路径的 Unicast/Multicast 链接，避免误伤指向其他域名的绝对链接
    anchor_pattern = re.compile(
        r'<a\s+href="(/(?:Unicast|Multicast)/[^"]+\.txt)"([^>]*)>(.*?)</a>',
        re.DOTALL,
    )

    changed = 0
    checked = 0

    for match in list(anchor_pattern.finditer(html_text)):
        href, attrs, text = match.group(1), match.group(2), match.group(3)

        if text.strip() != PLACEHOLDER_TEXT:
            continue  # 不是"暂无"占位符，跳过

        checked += 1
        path = href.lstrip("/")  # "Unicast/heilongjiang/unicom.txt"

        if path.startswith("Unicast/"):
            new_icon = UNICAST_ICON
        elif path.startswith("Multicast/"):
            new_icon = MULTICAST_ICON
        else:
            continue  # 理论上不会走到这里

        # 优先用本次同步过程中已经取到的内容，避免重复请求
        content_text = synced_content_cache.get(path)
        if content_text is None:
            file_info = get_file_contents_api(TARGET_REPO, path, TARGET_BRANCH)
            if file_info is None:
                continue  # 文件不存在，保持"暂无"
            content_text = file_info["text"]

        if not has_stream_url(content_text):
            continue  # 依然只是频道名单模板，没有真实播放地址，不修改

        old_anchor = match.group(0)
        new_anchor = f'<a href="{href}"{attrs}>{new_icon}</a>'
        # 用 count=1 避免影响其它相同文本的 anchor（href 本身在文件里是唯一的，足够安全）
        html_text = html_text.replace(old_anchor, new_anchor, 1)
        changed += 1
        print(f"[html更新] {path}: {PLACEHOLDER_TEXT} -> {new_icon}")

    print(f"检查了 {checked} 个占位符，更新了 {changed} 个")

    if changed == 0:
        print("iptv.html 无需更新")
        return

    ok = update_file(
        TARGET_REPO,
        TARGET_BRANCH,
        IPTV_HTML_PATH,
        html_text.encode("utf-8"),
        html_info["sha"],
        message=f"sync: update {changed} placeholder badge(s) in {IPTV_HTML_PATH}",
    )
    if ok:
        print(f"{IPTV_HTML_PATH} 更新成功")
    else:
        print(f"{IPTV_HTML_PATH} 更新失败", file=sys.stderr)


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

    # 记录本次同步中，每个被更新过的文件的最新内容（文本形式），
    # 后面更新 iptv.html 徽标时可以直接复用，不用再多发一次请求
    synced_content_cache = {}

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
            synced_content_cache[path] = content.decode("utf-8", errors="replace")
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

    # 无论本轮是否有文件被同步，都检查一下 iptv.html 里的占位符
    # （因为之前某一天同步过的文件，可能今天才第一次真正有播放地址）
    try:
        update_iptv_html(synced_content_cache)
    except requests.HTTPError as e:
        print(f"更新 iptv.html 时出错: {e}", file=sys.stderr)
        failed += 1

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
