import json
import os
import re
import urllib.request

# 配置参数
REPO_API_URL = "https://api.github.com/repos/j4Uq/TVBoxOSC/releases/latest"
TVBOX_T_PATH = "apk/tvboxt.json"
TVBOX_Q_PATH = "apk/tvboxq.json"


def fetch_latest_release():
  """通过 GitHub API 获取最新 Release 信息"""
  req = urllib.request.Request(
      REPO_API_URL, headers={"User-Agent": "Mozilla/5.0"}
  )
  try:
    with urllib.request.urlopen(req) as response:
      data = json.loads(response.read().decode("utf-8"))
      return data
  except Exception as e:
    print(f"获取 GitHub Release 失败: {e}")
    return None


def parse_version_from_tag(tag_name):
  """从 tag 中提取版本号（例如 20260217-1327）"""
  return tag_name.strip()


def generate_display_name(raw_name, credit_type):
  """根据文件名自动生成好看的显示名称"""
  # 去掉后缀 .apk 和前缀
  name_no_ext = raw_name[:-4] if raw_name.endswith(".apk") else raw_name

  if credit_type == "takagen99":
    # 例如：TVBox_takagen99_20260217-1327-arm64-generic-java -> arm64-generic-java(t版 黑盒)
    # 提取中间的架构或特性部分
    match = re.search(r"takagen99_[^_]+-(.+)", name_no_ext)
    suffix = match.group(1) if match else name_no_ext
    return f"{suffix}(t版 黑盒)"
  elif credit_type == "q215613905":
    # 例如：TVBox_q215613905_20260610-1758-java32 -> java32(q版 白盒)
    match = re.search(r"q215613905_[^_]+-(.+)", name_no_ext)
    suffix = match.group(1) if match else name_no_ext
    return f"{suffix}(q版 白盒)"
  return name_no_ext


def update_json_file(file_path, new_entries, credit_type):
  """更新指定的 JSON 文件，保持原有结构不变，只替换对应项"""
  # 读取现有 JSON（如果不存在则使用空字典）
  existing_data = {}
  if os.path.exists(file_path):
    try:
      with open(file_path, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
    except Exception as e:
      print(f"读取 {file_path} 失败，将创建新文件: {e}")

  # 模板：如果文件为空，提供一个默认的结构参考模板
  template_item = {
      "version": "",
      "name": "",
      (
          "logo"
          if credit_type == "takagen99"
          else "logo"  # 可根据需要区分 /images/tvbox-t.jpeg 或 /images/tvbox.jpg
      ): (
          "/images/tvbox-t.jpeg"
          if credit_type == "takagen99"
          else "/images/tvbox.jpg"
      ),
      "android": "" if credit_type == "takagen99" else "安卓4.X",
      (
          "desc"
          if credit_type == "takagen99"
          else "desc"
      ): (
          "tvbox系列的黑盒通用版，arm64版本适合手机平板等新设备安装，界面更加美观"
          if credit_type == "takagen99"
          else "tvbox系列的白盒，兼容安卓4版本，一直保持更新"
      ),
      "url": "https://github.com/o0HalfLife0o/TVBoxOSC",
      "sub_dir": "",
  }

  # 如果旧文件有数据，提取第一个作为模板克隆其公共字段（保持原样）
  if existing_data:
    first_key = list(existing_data.keys())[0]
    template_item = existing_data[first_key].copy()

  # 构造新的 JSON 数据对象
  updated_data = {}
  for item in new_entries:
    key_name = item["key"]
    version = item["version"]
    download_url = item["download_url"]
    file_name = item["file_name"]

    # 复用模板并更新改变的字段
    item_obj = template_item.copy()
    item_obj["version"] = version
    item_obj["name"] = generate_display_name(file_name, credit_type)
    item_obj["sub_dir"] = download_url

    updated_data[key_name] = item_obj

  # 写入文件
  os.makedirs(os.path.dirname(file_path), exist_ok=True)
  with open(file_path, "w", encoding="utf-8") as f:
    json.dump(updated_data, f, ensure_ascii=False, indent=2)
  print(f"成功更新文件: {file_path}，写入了 {len(updated_data)} 个应用项。")


def main():
  print("正在检查 GitHub 最新 Release...")
  release_data = fetch_latest_release()
  if not release_data:
    return

  tag_name = release_data.get("tag_name")
  version = parse_version_from_tag(tag_name)
  assets = release_data.get("assets", [])

  t_entries = []
  q_entries = []

  for asset in assets:
    file_name = asset.get("name")
    download_url = asset.get("browser_download_url")

    if not file_name.endswith(".apk"):
      continue

    # 分类：takagen99 还是 q215613905
    if "takagen99" in file_name:
      # 去掉 .apk 后缀作为字典的 key
      key_name = file_name[:-4] if file_name.endswith(".apk") else file_name
      t_entries.append({
          "key": key_name,
          "version": version,
          "download_url": download_url,
          "file_name": file_name,
      })
    elif "q215613905" in file_name:
      key_name = file_name[:-4] if file_name.endswith(".apk") else file_name
      q_entries.append({
          "key": key_name,
          "version": version,
          "download_url": download_url,
          "file_name": file_name,
      })

  # 更新 t 版 (takagen99)
  if t_entries:
    update_json_file(TVBOX_T_PATH, t_entries, "takagen99")
  else:
    print("未在 Release 中找到 takagen99 相关的 apk 文件。")

  # 更新 q 版 (q215613905)
  if q_entries:
    update_json_file(TVBOX_Q_PATH, q_entries, "q215613905")
  else:
    print("未在 Release 中找到 q215613905 相关的 apk 文件。")


if __name__ == "__main__":
  main()