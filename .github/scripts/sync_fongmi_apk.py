import os
import requests
import json  # 确保导入了json模块，用于json.dump
from github import Github
from datetime import datetime

# 获取环境变量
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
SOURCE_REPO = os.environ.get('SOURCE_REPO', 'FongMi/Release')
SOURCE_BRANCH = os.environ.get('SOURCE_BRANCH', 'fongmi')  # 默认使用okjack分支
# 支持多个源目录，用逗号分隔
SOURCE_PATHS = os.environ.get('SOURCE_PATHS', 'apk,apk/release').split(',')
DEST_PATH = os.environ.get('DEST_PATH', 'apk')

# 确保目标目录存在
for source_path in SOURCE_PATHS:
    # 从源路径中提取子目录名（如release、kitkat、pro）
    # 如果源路径是根目录（如 'apk'），则子目录为空
    if source_path.strip() == 'apk':
        sub_dir = ''  # 根目录文件直接保存到目标分支目录
    else:
        sub_dir = os.path.basename(source_path.strip())
    
    # 创建目标目录
    if sub_dir:
        os.makedirs(os.path.join(DEST_PATH, SOURCE_BRANCH, sub_dir), exist_ok=True)
    else:
        os.makedirs(os.path.join(DEST_PATH, SOURCE_BRANCH), exist_ok=True)

# 初始化GitHub客户端
g = Github(GITHUB_TOKEN)

# 获取源仓库
source_repo = g.get_repo(SOURCE_REPO)

# 添加重试装饰器
import time
from functools import wraps

def retry(max_retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise
                    print(f"Retry {retries}/{max_retries} after error: {str(e)}")
                    time.sleep(delay)
        return wrapper
    return decorator

# 获取源仓库指定路径下的文件
@retry(max_retries=3, delay=2)
def get_source_files(repo, path):
    files = []
    contents = repo.get_contents(path, ref=SOURCE_BRANCH)
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path, ref=SOURCE_BRANCH))
        else:
            # 获取该文件的最后一次提交信息
            try:
                # 添加延迟以避免API限流
                time.sleep(0.5)
                # 获取文件的最后一次提交
                commits = repo.get_commits(path=file_content.path)
                if commits:
                    last_commit = commits[0]
                    last_commit_message = last_commit.commit.message
                    last_commit_sha = last_commit.sha
                    last_commit_date = last_commit.commit.author.date
                else:
                    last_commit_message = "No commit history"
                    last_commit_sha = ""
                    last_commit_date = None
            except Exception as e:
                print(f"Error getting commit history for {file_content.path}: {str(e)}")
                last_commit_message = "Error getting commit history"
                last_commit_sha = ""
                last_commit_date = None
            
            files.append({
                'name': file_content.name,
                'path': file_content.path,
                'sha': file_content.sha,
                'download_url': file_content.download_url,
                'last_modified': file_content.last_modified,
                'last_commit_message': last_commit_message,
                'last_commit_sha': last_commit_sha,
                'last_commit_date': last_commit_date
            })
    return files

# 获取本地文件信息
def get_local_files(path):
    files = []
    for root, _, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, path)
            try:
                with open(file_path, 'rb') as f:
                    # 使用简单的哈希来比较文件内容
                    import hashlib
                    sha = hashlib.sha1(f.read()).hexdigest()
                    files.append({
                        'name': filename,
                        'path': rel_path,
                        'sha': sha
                    })
            except Exception as e:
                print(f"Error reading local file {file_path}: {e}")
    return files

# 下载文件
@retry(max_retries=3, delay=2)
def download_file(url, dest_path):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Failed to download {os.path.basename(dest_path)}: {str(e)}")
        return False

def main():
    print(f"Syncing files from {SOURCE_REPO} to {DEST_PATH}...")
    print(f"SOURCE_BRANCH: {SOURCE_BRANCH}")
    print(f"SOURCE_PATHS: {SOURCE_PATHS}")
    
    # 保存所有文件的最后提交信息
    file_commit_info = {}
    
    # 比较并下载更新的文件
    total_updated_count = 0
    
    # 遍历所有源目录
    for source_path in SOURCE_PATHS:
        source_path = source_path.strip()  # 移除可能的空格
        if not source_path:  # 跳过空路径
            continue
            
        # 从源路径中提取子目录名（如release、kitkat、pro）
        if source_path.strip() == 'apk':
            sub_dir = ''  # 根目录文件直接保存到目标分支目录
        else:
            sub_dir = os.path.basename(source_path)
        
        # 构建目标目录路径
        if sub_dir:
            dest_sub_dir = os.path.join(DEST_PATH, SOURCE_BRANCH, sub_dir)
        else:
            dest_sub_dir = os.path.join(DEST_PATH, SOURCE_BRANCH)
        
        print(f"\n--- Syncing directory: {source_path} to {dest_sub_dir} ---")
        
        # 获取源文件和本地文件
        source_files = get_source_files(source_repo, source_path)
        print(f"Found {len(source_files)} source files in {source_path}")
        local_files = get_local_files(dest_sub_dir)
        print(f"Found {len(local_files)} local files in {dest_sub_dir}")
        
        # 创建本地文件字典以便快速查找
        local_files_dict = {f['name']: f for f in local_files}
        
        # 下载更新的文件
        updated_count = 0
        for source_file in source_files:
            file_name = source_file['name']
            dest_file_path = os.path.join(dest_sub_dir, file_name)
            
            # 保存文件的提交信息
            if sub_dir:
                file_key = f"{sub_dir}/{file_name}"
            else:
                file_key = file_name  # 根目录文件直接使用文件名作为key
                
            file_commit_info[file_key] = {
                'commit_message': source_file['last_commit_message'],
                'commit_sha': source_file['last_commit_sha'],
                'commit_date': str(source_file['last_commit_date']) if source_file['last_commit_date'] else None,
                'sub_dir': sub_dir
            }
            
            # 打印文件信息
            print(f"File: {file_name}")
            print(f"  Last commit: {source_file['last_commit_sha'][:7]} - {source_file['last_commit_message']}")
            
            # 检查文件是否存在或需要更新
            if file_name not in local_files_dict:
                print(f"  Action: Downloading new file")
                if download_file(source_file['download_url'], dest_file_path):
                    updated_count += 1
            else:
                # 使用SHA值比较文件是否有变化
                local_file = local_files_dict[file_name]
                if local_file['sha'] != source_file['sha']:
                    print(f"  Action: Updating file")
                    if download_file(source_file['download_url'], dest_file_path):
                        updated_count += 1
                else:
                    print(f"  Action: No changes needed")
        
        total_updated_count += updated_count
        print(f"Directory {source_path} sync completed. {updated_count} files updated.")
    
    # 将所有文件的提交信息保存为JSON文件
    json_file_path = os.path.join(os.getcwd(), '.github/scripts/fongmi_file_commit_info.json')
    print(f"\nSaving commit info to: {json_file_path}")
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(file_commit_info, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved commit info to {json_file_path}")
        # 检查文件是否存在并显示大小
        if os.path.exists(json_file_path):
            print(f"JSON file size: {os.path.getsize(json_file_path)} bytes")
            print(f"Number of files in JSON: {len(file_commit_info)}")
    except Exception as e:
        print(f"Failed to save JSON file: {str(e)}")
        # 尝试使用另一个路径保存
        alt_json_path = os.path.join(os.environ.get('GITHUB_WORKSPACE', os.getcwd()), '.github/scripts/fongmi_file_commit_info.json')
        print(f"Trying alternative path: {alt_json_path}")
        try:
            with open(alt_json_path, 'w', encoding='utf-8') as f:
                json.dump(file_commit_info, f, ensure_ascii=False, indent=2)
            print(f"Successfully saved commit info to alternative path: {alt_json_path}")
        except Exception as e2:
            print(f"Failed to save to alternative path: {str(e2)}")
    
    print(f"\nSync completed. Total {total_updated_count} files updated.")

if __name__ == "__main__":
    main()
