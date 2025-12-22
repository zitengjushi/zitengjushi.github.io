import os
import requests
import json
from github import Github, Auth
from datetime import datetime
from base64 import b64encode

# 获取环境变量
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
SOURCE_REPO = os.environ.get('SOURCE_REPO')
SOURCE_PATH = os.environ.get('SOURCE_PATH')
DEST_PATH = os.environ.get('DEST_PATH')
SOURCE_BRANCH = 'okjack'  # 指定分支名称

# 获取当前仓库信息
CURRENT_REPO = os.environ.get('GITHUB_REPOSITORY')

# 确保目标目录存在
os.makedirs(DEST_PATH, exist_ok=True)

# 初始化GitHub客户端
auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)

# 获取源仓库和当前仓库
source_repo = g.get_repo(SOURCE_REPO)
current_repo = g.get_repo(CURRENT_REPO)

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

# 下载文件
def download_file(url, dest_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return True
    return False

# 使用GitHub API上传文件
def upload_file(repo, path, content, message):
    try:
        # 检查文件是否存在
        file = repo.get_contents(path)
        # 更新文件
        repo.update_file(
            path=file.path,
            message=message,
            content=b64encode(content).decode('utf-8'),
            sha=file.sha
        )
    except Exception as e:
        # 创建新文件
        repo.create_file(
            path=path,
            message=message,
            content=b64encode(content).decode('utf-8')
        )

def main():
    print(f"Syncing files from {SOURCE_REPO}/{SOURCE_PATH} to {DEST_PATH}...")
    
    # 获取源文件
    source_files = get_source_files(source_repo, SOURCE_PATH)
    
    # 获取当前仓库的main分支
    main_branch = current_repo.get_branch("main")
    
    # 下载并上传文件
    updated_count = 0
    for source_file in source_files:
        file_name = source_file['name']
        dest_file_path = os.path.join(DEST_PATH, file_name)
        repo_file_path = f"{DEST_PATH}/{file_name}"
        
        # 下载文件到本地
        if download_file(source_file['download_url'], dest_file_path):
            print(f"Downloaded file: {file_name}")
            
            # 读取文件内容
            with open(dest_file_path, 'rb') as f:
                file_content = f.read()
            
            # 上传文件到当前仓库
            message = f"Update {file_name} from source repository"
            upload_file(current_repo, repo_file_path, file_content, message)
            print(f"Uploaded file: {file_name}")
            updated_count += 1
    
    print(f"Sync completed. {updated_count} files updated.")

if __name__ == "__main__":
    main()
