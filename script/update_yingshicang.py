import json
import os
import re

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "requests"])
    import requests

# GitHub API 目录地址
API_URL = "https://api.github.com/repos/youhunwl/TVAPP/contents/%E5%BD%B1%E8%A7%86/%E5%BD%B1%E8%A7%86%E4%BB%93"
JSON_PATH = "apk/ysc.json"

def get_github_files():
    """获取 GitHub 目录下的文件列表（忽略系统代理干扰）"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    # 创建 Session 并禁用 trust_env，避免本地错误的环境变量代理干扰
    session = requests.Session()
    session.trust_env = False 
    
    # 如果你必须通过特定的代理才能访问 GitHub，可以在这里指定：
    # session.proxies = {"http": "http://127.0.0.1:你的代理端口", "https": "http://127.0.0.1:你的代理端口"}

    response = session.get(API_URL, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()

def extract_version(filename):
    """从文件名中提取版本号（如 6.1.7 或 3.0.32）"""
    match = re.search(r'(\d+\.\d+(?:\.\d+)?)', filename)
    return match.group(1) if match else "1.0.0"

def main():
    # 确保目标文件夹存在
    os.path.dirname(JSON_PATH) and os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    
    # 读取原有的 json 文件（如果存在）
    old_data = {}
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        except Exception:
            old_data = {}

    try:
        files = get_github_files()
    except Exception as e:
        print(f"获取 GitHub 目录失败: {e}")
        return

    new_data = {}
    
    for file in files:
        if file.get('type') == 'file' and file.get('name', '').endswith('.apk'):
            filename = file['name']
            base_name = os.path.splitext(filename)[0]  # 去掉 .apk 后缀作为主键
            download_url = file['download_url']
            
            # 提取版本号
            version = extract_version(filename)
            
            # 尝试从旧数据中匹配已有的字段（如 logo, name, desc 等）
            existing_item = old_data.get(base_name, {})
            if not existing_item:
                for k, v in old_data.items():
                    if base_name in k or k in base_name:
                        existing_item = v
                        break

            # 填充对应字段
            name = existing_item.get('name', base_name)
            logo = existing_item.get('logo', '/images/ysc.jpeg')
            android = existing_item.get('android', '')
            desc = existing_item.get('desc', f"{base_name}的影视仓，支持多仓")

            new_data[base_name] = {
                "version": version,
                "name": name,
                "logo": logo,
                "android": android,
                "desc": desc,
                "sub_dir": download_url
            }

    # 比较新旧数据是否一致
    old_json_str = json.dumps(old_data, sort_keys=True, ensure_ascii=False)
    new_json_str = json.dumps(new_data, sort_keys=True, ensure_ascii=False)

    if old_json_str == new_json_str:
        print("检测到 APK 文件无改动，ysc.json 保持不变。")
    else:
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        print("apk/ysc.json 已成功更新！")

if __name__ == '__main__':
    main()