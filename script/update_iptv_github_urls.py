#!/usr/bin/env python3
"""
update_iptv_github_urls.py
读取 iptv-github.json 中每个条目的 url，去掉代理前缀后访问 GitHub API
获取目标文件的最后修改时间（北京时间 YYYY-MM-DD），
将日期更新到对应 name 的末尾（自动覆盖旧日期），
最后按最后修改时间对所有条目倒序重新排序并写回。

用法:
    python script/update_iptv_github_urls.py
"""

from datetime import datetime, timezone, timedelta
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── 配置 ─────────────────────────────────────────────────────────────────────
JSON_PATH    = Path("apk/iptv-github.json")
PROXY_PREFIX = "https://gh-proxy.org/"
API_BASE     = "https://api.github.com"

# name 末尾的日期格式（用于识别并替换上一次追加的日期）
DATE_SUFFIX_RE = re.compile(r"\s+\d{4}-\d{2}-\d{2}$")
# ─────────────────────────────────────────────────────────────────────────────


def gh_get(url: str, retries: int = 3) -> dict | list:
    """访问 GitHub API，自动处理限速与重试。"""
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {
        "Accept":     "application/vnd.github+json",
        "User-Agent": "github-url-updater/1.0",
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


def parse_raw_url(raw_url: str) -> tuple[str, str, str] | None:
    """
    从 raw.githubusercontent.com URL 中解析出 owner/repo、branch、文件路径。
    支持带 refs/heads/ 的路径。
    """
    prefix = "https://raw.githubusercontent.com/"
    if not raw_url.startswith(prefix):
        return None

    rest  = raw_url[len(prefix):]
    parts = rest.split("/")
    if len(parts) < 4:
        return None

    owner = parts[0]
    repo  = parts[1]

    # 处理 refs/heads/<branch> 格式
    if parts[2] == "refs" and parts[3] == "heads" and len(parts) >= 6:
        branch    = parts[4]
        file_path = "/".join(parts[5:])
    else:
        branch    = parts[2]
        file_path = "/".join(parts[3:])

    return (f"{owner}/{repo}", branch, file_path)


def get_file_last_modified(repo: str, branch: str, file_path: str) -> str | None:
    """
    通过 GitHub Commits API 获取文件最后一次提交的日期（转换为北京时间 YYYY-MM-DD）。
    """
    url  = f"{API_BASE}/repos/{repo}/commits?sha={branch}&path={file_path}&per_page=1"
    data = gh_get(url)
    if not data:
        return None
    
    utc_date_str = data[0]["commit"]["committer"]["date"]  # e.g. "2026-04-10T23:30:00Z"
    
    # 转换成 datetime 对象并转为北京时间 (UTC+8)
    dt_utc = datetime.strptime(utc_date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    tz_beijing = timezone(timedelta(hours=8))
    dt_bj = dt_utc.astimezone(tz_beijing)
    
    return dt_bj.strftime("%Y-%m-%d")


def strip_date_suffix(name: str) -> str:
    """去掉 name 末尾上次追加的日期（如 ' 2026-04-10'），返回原始 name。"""
    return DATE_SUFFIX_RE.sub("", name)


def main():
    if not JSON_PATH.exists():
        raise SystemExit(f"❌ 找不到 {JSON_PATH}，请确认脚本在仓库根目录运行")

    with JSON_PATH.open(encoding="utf-8") as f:
        data: dict = json.load(f)

    print(f"🔍 共 {len(data)} 个源需要检查\n")
    checked_count = 0

    # 用于暂存带有最后修改时间的数据，以便后续排序
    # 每个元素格式为：(key, item_dict, last_modified_date)
    processed_items = []

    for key, item in data.items():
        raw_proxy_url = item.get("url", "")
        original_name = item.get("name", "")

        # 去掉代理前缀，还原真实 raw URL
        if raw_proxy_url.startswith(PROXY_PREFIX):
            real_url = raw_proxy_url[len(PROXY_PREFIX):]
        else:
            real_url = raw_proxy_url

        print(f"  ▶ [{key}] {original_name}")
        print(f"    URL: {real_url}")

        parsed = parse_raw_url(real_url)
        if not parsed:
            print(f"    ⚠️  无法解析为 GitHub raw URL，跳过\n")
            processed_items.append((key, item, None))
            continue

        repo, branch, file_path = parsed

        try:
            last_date = get_file_last_modified(repo, branch, file_path)
        except FileNotFoundError:
            print(f"    ⚠️  GitHub 上找不到此文件（{repo}/{file_path}），跳过\n")
            processed_items.append((key, item, None))
            continue
        except Exception as exc:
            print(f"    ❌ 获取失败: {exc}，跳过\n")
            processed_items.append((key, item, None))
            continue

        if not last_date:
            print(f"    ⚠️  未能获取最后修改时间，跳过\n")
            processed_items.append((key, item, None))
            continue

        print(f"    最后修改 (北京时间): {last_date}")
        checked_count += 1

        # 构造新 name：去掉旧日期后缀 + 新日期
        base_name = strip_date_suffix(original_name)
        new_name  = f"{base_name} {last_date}"

        if new_name != original_name:
            print(f"    🔄 name: {original_name!r} → {new_name!r}")
            item["name"] = new_name
            print(f"    ✅ 已更新")
        else:
            print(f"    ✔  无变化")

        print()
        processed_items.append((key, item, last_date))
        time.sleep(0.3)  # 礼貌性延迟

    # ── 按最后修改时间排序 ─────────────────────────────────────────────────────
    # 分为 有日期的项 和 无日期的项
    dated = [x for x in processed_items if x[2] is not None]
    undated = [x for x in processed_items if x[2] is None]

    # 按时间倒序（最新的在最前面）
    dated.sort(key=lambda x: x[2], reverse=True)

    # 重新组装成有序的字典
    new_data = {}
    for key, item, _ in dated + undated:
        new_data[key] = item

    # 写回文件
    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)

    print(
        f"💾 已更新 name 日期并按最后修改时间重新排序，写回 {JSON_PATH} "
        f"（成功获取时间 {checked_count}/{len(data)} 个）"
    )

    # 输出给 GitHub Actions（如果有需要）
    env_file = os.getenv("GITHUB_OUTPUT", "")
    if env_file:
        with open(env_file, "a") as f:
            f.write(f"updated={checked_count}\n")


if __name__ == "__main__":
    main()
