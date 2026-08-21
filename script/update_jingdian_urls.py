#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能：
1. 读取根目录下的 jingdian.json 文件
2. 并发检测里面每个 url 是否可以正常访问，同时获取其内容的 MD5
3. 把每个 url 的 MD5 和"最后更新日期"记录在固定文件 jingdian_md5.json 里
   （与 jingdian.json 同目录），用于下次运行时比对：
     - 该 url 之前没有记录（首次见到，没有基准可比） -> 日期写 1970-01-01
     - MD5 与上次不同（内容变化了）                   -> 日期写今天
     - MD5 与上次相同（内容没变）                     -> 沿用上次记录的日期
     - 本次请求失败/不可访问                          -> 不更新 MD5，
                                                          日期沿用旧记录（没有则 1970-01-01）
4. 把上面得到的日期拼进 name 里：原name + " [日期]" + ✓/✗
   能访问的：在末尾加 "✓"；不能访问的：在末尾加 "✗"
5. 能访问的排在前面，不能访问的排在后面
6. 重新写回 jingdian.json（覆盖原文件），并保存 jingdian_md5.json

用法：
    python check_jingdian.py
    python check_jingdian.py /path/to/jingdian.json   # 也可以指定文件路径
"""

import concurrent.futures
import hashlib
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

# ------------------- 配置 -------------------
JINGDIAN_JSON_PATH = Path("jingdian.json")
MD5_STORE_FILENAME = "jingdian_md5.json"   # 固定文件名，存放在 jingdian.json 同目录
TIMEOUT = 8              # 单个请求超时时间（秒）
MAX_WORKERS = 20         # 并发线程数
MAX_READ_BYTES = 20 * 1024 * 1024  # 计算 MD5 时最多读取的字节数，避免超大文件拖慢/占内存
OK_MARK = "✓"            # 可访问标记
FAIL_MARK = "✗"          # 不可访问标记
DEFAULT_DATE = "1970-01-01"  # 没有历史 MD5 可比对时使用的占位日期
USER_AGENT = (
    "okhttp/4.9.3"
)
# ---------------------------------------------

# 忽略证书校验，避免部分自签证书站点报错（仅用于检测可达性）
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# 匹配 name 末尾的 " [YYYY-MM-DD]" 日期标记
DATE_TAG_RE = re.compile(r"\s*\[\d{4}-\d{2}-\d{2}\]\s*$")


def strip_mark(name: str) -> str:
    """去掉 name 末尾已有的 ✓ / ✗ / X / x 状态标记，避免重复检测时叠加。"""
    if not name:
        return name
    name = name.strip()
    for mark in (OK_MARK, FAIL_MARK, "X", "x"):
        if name.endswith(mark):
            name = name[: -len(mark)].rstrip()
    return name


def strip_date_tag(name: str) -> str:
    """去掉 name 末尾已有的 " [YYYY-MM-DD]" 日期标记，避免重复检测时叠加。"""
    if not name:
        return name
    return DATE_TAG_RE.sub("", name).rstrip()


def clean_base_name(name: str) -> str:
    """反复去掉状态标记和日期标记，直到不再变化，得到最干净的原始名字。
    循环处理是为了兼容标记/日期顺序异常（比如手动编辑过）的情况。
    """
    prev = None
    while prev != name:
        prev = name
        name = strip_date_tag(strip_mark(name))
    return name


def fetch_and_hash(url: str) -> tuple[bool, str | None]:
    """
    请求 url，返回 (是否可访问, 内容MD5)。
    统一用 GET（而不是 HEAD），因为算 MD5 必须拿到响应体。
    """
    if not url:
        return False, None

    headers = {"User-Agent": USER_AGENT}
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CONTEXT) as resp:
            status = resp.getcode()
            if not status or status >= 400:
                return False, None
            content = resp.read(MAX_READ_BYTES)
            md5 = hashlib.md5(content).hexdigest()
            return True, md5
    except Exception:
        return False, None


def load_md5_store(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # 固定文件损坏或不可读，视为没有历史记录，重新开始累积
        return {}


def save_md5_store(path: Path, store: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def process_item(item: dict, md5_store: dict, today_str: str) -> dict:
    """
    检测单个条目：请求 -> 算MD5 -> 和 md5_store 比对决定日期 -> 拼装新 name。
    返回 {"item": 新条目, "ok": 是否可访问, "url": url,
          "store_update": None 或 {"md5":..., "date":...}}
    """
    url = item.get("url", "")
    raw_name = clean_base_name(item.get("name", ""))

    ok, md5 = fetch_and_hash(url)
    prev = md5_store.get(url)
    store_update = None

    if ok and md5:
        if prev is None:
            # 首次记录，没有历史可比对
            date_str = DEFAULT_DATE
        elif prev.get("md5") != md5:
            # 内容变化了
            date_str = today_str
        else:
            # 内容没变，沿用旧日期
            date_str = prev.get("date", DEFAULT_DATE)
        store_update = {"md5": md5, "date": date_str}
    else:
        # 请求失败，拿不到内容，不更新 md5，日期沿用旧记录
        date_str = prev.get("date", DEFAULT_DATE) if prev else DEFAULT_DATE

    new_name = f"{raw_name} [{date_str}]{OK_MARK if ok else FAIL_MARK}"
    new_item = dict(item)
    new_item["name"] = new_name

    return {"item": new_item, "ok": ok, "url": url, "store_update": store_update}


def main():
    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else JINGDIAN_JSON_PATH
    md5_store_path = json_path.parent / MD5_STORE_FILENAME

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：未找到文件 {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误：JSON 格式解析失败 - {e}")
        sys.exit(1)

    md5_store = load_md5_store(md5_store_path)
    today_str = date.today().isoformat()

    urls_list = data.get("urls", [])
    total = len(urls_list)
    print(f"共读取到 {total} 条链接，开始检测（并发数：{MAX_WORKERS}）...\n")

    results = [None] * total
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_index = {
            executor.submit(process_item, item, md5_store, today_str): idx
            for idx, item in enumerate(urls_list)
        }
        done_count = 0
        for future in concurrent.futures.as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                result = future.result()
            except Exception:
                # 极端异常兜底，标记为不可访问
                item = dict(urls_list[idx])
                raw_name = clean_base_name(item.get("name", ""))
                item["name"] = f"{raw_name} [{DEFAULT_DATE}]{FAIL_MARK}"
                result = {"item": item, "ok": False, "url": item.get("url", ""), "store_update": None}
            results[idx] = result
            done_count += 1
            status = "可访问" if result["ok"] else "不可访问"
            print(f"[{done_count}/{total}] {result['item']['name']}  -> {status}")

    # 把本轮的 MD5/日期更新写回 md5_store（只更新有 store_update 的条目）
    for r in results:
        if r["store_update"] is not None and r["url"]:
            md5_store[r["url"]] = r["store_update"]

    # 按可访问状态排序：可访问的在前，不可访问的在后；组内保持原相对顺序（稳定排序）
    ok_items = [r["item"] for r in results if r["ok"]]
    fail_items = [r["item"] for r in results if not r["ok"]]

    data["urls"] = ok_items + fail_items

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    save_md5_store(md5_store_path, md5_store)

    print(f"\n检测完成！可访问：{len(ok_items)} 条，不可访问：{len(fail_items)} 条。")
    print(f"结果已写回：{json_path}")
    print(f"MD5记录已写回：{md5_store_path}")


if __name__ == "__main__":
    main()
