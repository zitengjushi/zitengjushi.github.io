#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能：
1. 读取根目录下的 jingdian.json 文件
2. 并发检测里面每个 url 是否可以正常访问
3. 能访问的：在原 name 后面加 "✓"
   不能访问的：在原 name 后面加 "✗"
4. 能访问的排在前面，不能访问的排在后面
5. 重新写回 jingdian.json 文件（覆盖原文件）

用法：
    python check_jingdian.py
    python check_jingdian.py /path/to/jingdian.json   # 也可以指定文件路径
"""

import json
import sys
import concurrent.futures
import urllib.request
import urllib.error
import ssl
from pathlib import Path

# ------------------- 配置 -------------------
JINGDIAN_JSON_PATH    = Path("jingdian.json")
TIMEOUT = 8            # 单个请求超时时间（秒）
MAX_WORKERS = 20        # 并发线程数
OK_MARK = "✓"           # 可访问标记
FAIL_MARK = "✗"          # 不可访问标记
USER_AGENT = (
    "okhttp/4.9.3"
)
# ---------------------------------------------

# 忽略证书校验，避免部分自签证书站点报错（仅用于检测可达性）
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


def strip_mark(name: str) -> str:
    """去掉 name 末尾已有的 ✓ / ✗ / X / x 标记，避免重复检测时叠加。"""
    if not name:
        return name
    name = name.strip()
    for mark in (OK_MARK, FAIL_MARK, "X", "x"):
        if name.endswith(mark):
            name = name[: -len(mark)].rstrip()
    return name


def check_url(url: str) -> bool:
    """判断 url 是否可以正常访问。先尝试 HEAD，失败再尝试 GET。"""
    if not url:
        return False

    headers = {"User-Agent": USER_AGENT}

    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CONTEXT) as resp:
                status = resp.getcode()
                # 只要能拿到响应，且状态码小于 400，就算可访问
                if status and status < 400:
                    return True
        except urllib.error.HTTPError as e:
            # 有些站点不支持 HEAD 会返回 405，换 GET 再试
            if e.code == 405 and method == "HEAD":
                continue
            # 其他 HTTP 错误码（4xx/5xx）视为不可访问，但也可能只是拒绝了 HEAD
            if method == "HEAD":
                continue
            return False
        except Exception:
            # 超时、DNS 失败、连接被拒绝等，换 GET 再试一次
            if method == "HEAD":
                continue
            return False

    return False


def process_item(item: dict) -> dict:
    """检测单个条目，返回带标记结果的新条目 + 可访问状态。"""
    url = item.get("url", "")
    raw_name = strip_mark(item.get("name", ""))
    ok = check_url(url)
    new_name = f"{raw_name}{OK_MARK if ok else FAIL_MARK}"
    new_item = dict(item)
    new_item["name"] = new_name
    return {"item": new_item, "ok": ok}


def main():
    json_path = sys.argv[1] if len(sys.argv) > 1 else JINGDIAN_JSON_PATH

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：未找到文件 {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误：JSON 格式解析失败 - {e}")
        sys.exit(1)

    urls_list = data.get("urls", [])
    total = len(urls_list)
    print(f"共读取到 {total} 条链接，开始检测（并发数：{MAX_WORKERS}）...\n")

    results = [None] * total
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_index = {
            executor.submit(process_item, item): idx
            for idx, item in enumerate(urls_list)
        }
        done_count = 0
        for future in concurrent.futures.as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                result = future.result()
            except Exception as e:
                # 极端异常兜底，标记为不可访问
                item = dict(urls_list[idx])
                item["name"] = f"{strip_mark(item.get('name', ''))}{FAIL_MARK}"
                result = {"item": item, "ok": False}
            results[idx] = result
            done_count += 1
            status = "可访问" if result["ok"] else "不可访问"
            print(f"[{done_count}/{total}] {result['item']['name']}  -> {status}")

    # 按可访问状态排序：可访问的在前，不可访问的在后；组内保持原相对顺序（稳定排序）
    ok_items = [r["item"] for r in results if r["ok"]]
    fail_items = [r["item"] for r in results if not r["ok"]]

    data["urls"] = ok_items + fail_items

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"\n检测完成！可访问：{len(ok_items)} 条，不可访问：{len(fail_items)} 条。")
    print(f"结果已写回：{json_path}")


if __name__ == "__main__":
    main()
