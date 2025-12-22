import os
import requests
import json
from github import Github, Auth
from datetime import datetime

# 获取环境变量
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
SOURCE_REPO = os.environ.get('SOURCE_REPO')
SOURCE_PATH = os.environ.get('SOURCE_PATH')
DEST_PATH = os.environ.get('DEST_PATH')
SOURCE_BRANCH = 'okjack'  # 指定分支名称

# 确保目标目录存在
os.makedirs(DEST_PATH, exist_ok=True)

# 初始化GitHub客户端
auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)

# 获取源仓库
source_repo = g.get_repo(SOURCE_REPO)

# 获取源仓库指定路径下的文件
def get_source_files(repo, path):
    files = []
    contents = repo.get_contents(path, ref=SOURCE_BRANCH)  # 指定分支
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path, ref=SOURCE_BRANCH))  # 指定分支
        else:
            files.append({
                'name': file_content.name,
                'path': file_content.path,
                'sha': file_content.sha,
                'download_url': file_content.download_url,
                'last_modified': file_content.last_modified
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
def download_file(url, dest_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return True
    return False

def main():
    print(f"Syncing files from {SOURCE_REPO}/{SOURCE_PATH} to {DEST_PATH}...")
    
    # 获取源文件和本地文件
    source_files = get_source_files(source_repo, SOURCE_PATH)
    local_files = get_local_files(DEST_PATH)
    
    # 创建本地文件字典以便快速查找
    local_files_dict = {f['name']: f for f in local_files}
    
    # 比较并下载更新的文件
    updated_count = 0
    for source_file in source_files:
        file_name = source_file['name']
        dest_file_path = os.path.join(DEST_PATH, file_name)
        
        # 检查文件是否存在或需要更新
        if file_name not in local_files_dict:
            print(f"Downloading new file: {file_name}")
            if download_file(source_file['download_url'], dest_file_path):
                updated_count += 1
        else:
            # 使用SHA值比较文件是否有变化
            local_file = local_files_dict[file_name]
            if local_file['sha'] != source_file['sha']:
                print(f"Updating file: {file_name}")
                if download_file(source_file['download_url'], dest_file_path):
                    updated_count += 1
    
    print(f"Sync completed. {updated_count} files updated.")

if __name__ == "__main__":
    main()
