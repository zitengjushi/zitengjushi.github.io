import os
import requests
import json  # 确保导入了json模块，用于json.dump
from github import Github
from datetime import datetime

# 获取环境变量
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
SOURCE_REPO = os.environ.get('SOURCE_REPO', 'FongMi/Release')
SOURCE_BRANCH = os.environ.get('SOURCE_BRANCH', 'okjack')  # 默认使用okjack分支
SOURCE_PATH = os.environ.get('SOURCE_PATH', 'apk/release')
DEST_PATH = os.environ.get('DEST_PATH', 'apk')

# 确保目标目录存在
os.makedirs(DEST_PATH, exist_ok=True)

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
    print(f"Syncing files from {SOURCE_REPO}/{SOURCE_PATH} to {DEST_PATH}...")
    
    # 获取源文件和本地文件
    source_files = get_source_files(source_repo, SOURCE_PATH)
    local_files = get_local_files(DEST_PATH)
    
    # 创建本地文件字典以便快速查找
    local_files_dict = {f['name']: f for f in local_files}
    
    # 保存所有文件的最后提交信息
    file_commit_info = {}
    
    # 比较并下载更新的文件
    updated_count = 0
    for source_file in source_files:
        file_name = source_file['name']
        dest_file_path = os.path.join(DEST_PATH, file_name)
        
        # 保存文件的提交信息
        file_commit_info[file_name] = {
            'commit_message': source_file['last_commit_message'],
            'commit_sha': source_file['last_commit_sha'],
            'commit_date': str(source_file['last_commit_date']) if source_file['last_commit_date'] else None
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
    
    # 将所有文件的提交信息保存为JSON文件
    with open('.github/scripts/okjack_file_commit_info.json', 'w', encoding='utf-8') as f:
        json.dump(file_commit_info, f, ensure_ascii=False, indent=2)
    
    print(f"Sync completed. {updated_count} files updated.")
    print("File commit information saved to .github/scripts/okjack_file_commit_info.json")

if __name__ == "__main__":
    main()
