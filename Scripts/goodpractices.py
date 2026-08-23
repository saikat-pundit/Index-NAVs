import os
import csv
import requests
import zipfile
import tempfile
import shutil
from io import BytesIO
from PIL import Image
import magic
import gdown
from github import Github
from github.GithubException import GithubException
import re
from pathlib import Path

GIST_URL = "https://gist.githubusercontent.com/saikat-pundit/8d3eda26f337ec08ea54c8e41f936b96/raw/GoodPractices.csv"
RELEASE_NAME = "Good Practices"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def download_csv():
    response = requests.get(GIST_URL)
    response.raise_for_status()
    content = response.text
    lines = content.strip().split('\n')
    header = lines[0]
    data_rows = lines[56:] if len(lines) > 56 else []
    return header, data_rows

def parse_google_drive_id(url):
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/uc\?export=download&id=([a-zA-Z0-9_-]+)',
        r'/open\?id=([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_file(url, file_id, output_path):
    if file_id:
        gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=True)
        return True
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except:
        return False

def compress_image(input_path, output_path, target_size_kb=100):
    img = Image.open(input_path)
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    quality = 95
    while quality > 10:
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        size_kb = len(buffer.getvalue()) / 1024
        if size_kb <= target_size_kb:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            return True
        quality -= 5
    
    if quality <= 10:
        img.save(output_path, format='JPEG', quality=10, optimize=True)
    return True

def process_media():
    header, data_rows = download_csv()
    reader = csv.reader(data_rows)
    categories = {}
    
    for row in reader:
        if len(row) >= 8:
            category = row[2].strip()
            if category:
                if category not in categories:
                    categories[category] = []
                categories[category].append({
                    'name': row[1].strip(),
                    'col5': row[5].strip() if len(row) > 5 else '',
                    'col6': row[6].strip() if len(row) > 6 else '',
                    'col7': row[7].strip() if len(row) > 7 else ''
                })
    
    zip_files = []
    temp_dir = tempfile.mkdtemp()
    
    for category, items in categories.items():
        category_dir = os.path.join(temp_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        processed_files = []
        
        for idx, item in enumerate(items, start=1):
            col_map = {5: item['col5'], 6: item['col6'], 7: item['col7']}
            for col_num, url in col_map.items():
                if not url:
                    continue
                
                file_id = parse_google_drive_id(url)
                if not file_id:
                    continue
                
                temp_file = os.path.join(category_dir, f"temp_{col_num}")
                if not download_file(url, file_id, temp_file):
                    continue
                
                mime = magic.from_file(temp_file, mime=True)
                base_name = f"{item['name']}_{col_num}"
                
                if mime and mime.startswith('video'):
                    ext = '.mp4'
                    output_file = os.path.join(category_dir, f"{base_name}{ext}")
                    shutil.move(temp_file, output_file)
                    processed_files.append(output_file)
                elif mime and (mime.startswith('image') or 'webp' in mime.lower()):
                    if mime == 'image/webp' or temp_file.lower().endswith('.webp'):
                        output_file = os.path.join(category_dir, f"{base_name}.jpg")
                        compress_image(temp_file, output_file)
                        os.remove(temp_file)
                        processed_files.append(output_file)
                    else:
                        ext = '.jpg'
                        output_file = os.path.join(category_dir, f"{base_name}{ext}")
                        compress_image(temp_file, output_file)
                        os.remove(temp_file)
                        processed_files.append(output_file)
                else:
                    os.remove(temp_file)
        
        if processed_files:
            zip_path = os.path.join(temp_dir, f"{category}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                seen_names = set()
                for file_path in processed_files:
                    base_name = os.path.basename(file_path)
                    if base_name in seen_names:
                        name, ext = os.path.splitext(base_name)
                        counter = 1
                        while f"{name}_{counter}{ext}" in seen_names:
                            counter += 1
                        base_name = f"{name}_{counter}{ext}"
                    seen_names.add(base_name)
                    zipf.write(file_path, base_name)
            zip_files.append(zip_path)
    
    if zip_files and GITHUB_TOKEN:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(os.environ.get('GITHUB_REPOSITORY', ''))
        
        try:
            release = repo.get_release(RELEASE_NAME)
            for asset in release.get_assets():
                asset.delete_asset()
        except GithubException:
            release = repo.create_git_release(
                tag=RELEASE_NAME.replace(' ', '-').lower(),
                name=RELEASE_NAME,
                message=f"Release {RELEASE_NAME}",
                draft=False,
                prerelease=False
            )
        
        for zip_path in zip_files:
            release.upload_asset(
                zip_path,
                name=os.path.basename(zip_path),
                content_type='application/zip'
            )
    
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    process_media()
