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
import urllib.request

# GitHub API 地址（获取 FongMi/Release 最新发布版本）
API_URL = "https://api.github.com/repos/FongMi/Release/releases/latest"
JSON_PATH = "apk/fongmi.json"


def get_latest_release():
  req = urllib.request.Request(
      API_URL, headers={"User-Agent": "Mozilla/5.0 (Python Script)"}
  )
  try:
    with urllib.request.urlopen(req) as response:
      data = json.loads(response.read().decode("utf-8"))
      tag_name = data.get("tag_name", "").strip()
      # 去除版本号前面的 'v'，如果您的版本号需要保留 v，可以去掉 .lstrip('v')
      version = tag_name.lstrip("v")

      # 遍历 Release 附件，寻找目标 APK 下载地址
      download_url = ""
      for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(".apk"):
          download_url = asset.get("browser_download_url", "")
          break

      # 如果没有找到附件，则退回到 Release 页面地址
      if not download_url:
        download_url = data.get("html_url", "")

      return version, download_url
  except Exception as e:
    print(f"获取 GitHub Release 失败: {e}")
    return None, None


def update_json(version, download_url):
  if not version or not download_url:
    print("版本号或下载地址为空，跳过更新。")
    return

  # 读取现有的 JSON 文件以保留原有数据结构
  data = {}
  if os.path.exists(JSON_PATH):
    try:
      with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    except Exception as e:
      print(f"读取 {JSON_PATH} 失败: {e}")

  # 仅更新指定的两个字段，其余原有字段和结构保持不变
  data["version"] = version
  data["sub_dir"] = download_url

  # 写回 JSON 文件
  os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
  with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

  print(f"成功更新 {JSON_PATH} -> version: {version}, sub_dir: {download_url}")


if __name__ == "__main__":
  version, download_url = get_latest_release()
  if version and download_url:
    update_json(version, download_url)
