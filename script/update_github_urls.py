#!/usr/bin/env python3
"""
update_github_urls.py
读取 github.json 中每个 url 条目，去掉代理前缀后访问 GitHub API
获取目标文件的最后修改时间（年月日），将 name 字段更新为：
  原始 name（去掉上次附加的日期部分）+ 新日期，例如：
  "大而全的配置" → "大而全的配置 2025-04-10"
  "大而全的配置 2025-04-10" → "大而全的配置 2025-04-15"（再次运行时）

用法:
    python scripts/update_github_urls.py
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── 配置 ─────────────────────────────────────────────────────────────────────
JSON_PATH    = Path("github.json")
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

    输入示例:
      https://raw.githubusercontent.com/qist/tvbox/master/0821.json
    返回:
      ("qist/tvbox", "master", "0821.json")

    对于带 refs/heads/ 的路径也能正确处理：
      https://raw.githubusercontent.com/maoystv/6/refs/heads/main/000.json
    返回:
      ("maoystv/6", "main", "000.json")
    """
    prefix = "https://raw.githubusercontent.com/"
    if not raw_url.startswith(prefix):
        return None

    rest  = raw_url[len(prefix):]          # owner/repo/branch/...path
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
    通过 GitHub Commits API 获取文件最后一次提交的日期（YYYY-MM-DD）。
    """
    url  = f"{API_BASE}/repos/{repo}/commits?sha={branch}&path={file_path}&per_page=1"
    data = gh_get(url)
    if not data:
        return None
    date_str = data[0]["commit"]["committer"]["date"]  # e.g. "2025-04-10T08:23:11Z"
    return date_str[:10]                               # 取 YYYY-MM-DD


def strip_date_suffix(name: str) -> str:
    """去掉 name 末尾上次追加的日期（如 ' 2025-04-10'），返回原始 name。"""
    return DATE_SUFFIX_RE.sub("", name)


def main():
    if not JSON_PATH.exists():
        raise SystemExit(f"❌ 找不到 {JSON_PATH}，请确认脚本在仓库根目录运行")

    with JSON_PATH.open(encoding="utf-8") as f:
        data: dict = json.load(f)

    entries: list[dict] = data.get("urls", [])
    print(f"🔍 共 {len(entries)} 个 URL 需要检查\n")

    updated_count = 0

    for entry in entries:
        raw_proxy_url = entry.get("url", "")
        original_name = entry.get("name", "")

        # 去掉代理前缀，还原真实 raw URL
        if raw_proxy_url.startswith(PROXY_PREFIX):
            real_url = raw_proxy_url[len(PROXY_PREFIX):]
        else:
            real_url = raw_proxy_url

        print(f"  ▶ {original_name}")
        print(f"    URL: {real_url}")

        parsed = parse_raw_url(real_url)
        if not parsed:
            print(f"    ⚠️  无法解析为 GitHub raw URL，跳过\n")
            continue

        repo, branch, file_path = parsed

        try:
            last_date = get_file_last_modified(repo, branch, file_path)
        except FileNotFoundError:
            print(f"    ⚠️  GitHub 上找不到此文件（{repo}/{file_path}），跳过\n")
            continue
        except Exception as exc:
            print(f"    ❌ 获取失败: {exc}，跳过\n")
            continue

        if not last_date:
            print(f"    ⚠️  未能获取最后修改时间，跳过\n")
            continue

        # 构造新 name：去掉旧日期后缀 + 新日期
        base_name = strip_date_suffix(original_name)
        new_name  = f"{base_name} {last_date}"

        print(f"    最后修改: {last_date}")

        if new_name != original_name:
            print(f"    🔄 name: {original_name!r} → {new_name!r}")
            entry["name"] = new_name
            updated_count += 1
            print(f"    ✅ 已更新")
        else:
            print(f"    ✔  无变化")

        print()
        time.sleep(0.3)  # 礼貌性延迟

    # 有变更时写回文件
    if updated_count:
        with JSON_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"💾 已写回 {JSON_PATH}，共更新 {updated_count} 个条目")
    else:
        print(f"✔  所有条目均为最新，无需写入")

    # 输出给 GitHub Actions
    env_file = os.getenv("GITHUB_OUTPUT", "")
    if env_file:
        with open(env_file, "a") as f:
            f.write(f"updated={updated_count}\n")


if __name__ == "__main__":
    main()
