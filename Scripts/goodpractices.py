import os
import csv
import requests
import zipfile
import tempfile
import shutil
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import magic
import gdown
from github import Github
from github.GithubException import GithubException
import re
import textwrap

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

def add_text_below_image(img, text):
    width, height = img.size
    max_width = int(width * 0.9)
    
    try:
        font_size = int(height / 25)
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
        font_size = 12
    
    wrapped_text = []
    for line in text.split('_'):
        if line:
            wrapped_text.append(line.strip())
    if not wrapped_text:
        wrapped_text = [text]
    
    lines = []
    for line in wrapped_text:
        if font.getlength(line) <= max_width:
            lines.append(line)
        else:
            words = line.split()
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if font.getlength(test_line) <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
    
    line_height = font_size + 5
    total_text_height = len(lines) * line_height + 20
    padding = 20
    
    new_height = height + total_text_height + padding
    new_img = Image.new('RGB', (width, new_height), (255, 255, 255))
    new_img.paste(img, (0, 0))
    
    draw = ImageDraw.Draw(new_img)
    y = height + 10
    
    for line in lines:
        text_width = font.getlength(line)
        x = (width - text_width) / 2
        draw.text((x, y), line, fill=(0, 0, 0), font=font)
        y += line_height
    
    return new_img

def compress_image(input_path, output_path, target_size_kb=100, text_below=None):
    img = Image.open(input_path)
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    if text_below:
        img = add_text_below_image(img, text_below)
    
    quality = 95
    while quality > 10:
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        if len(buffer.getvalue()) / 1024 <= target_size_kb:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            return True
        quality -= 5
    
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
                    'col1': row[5].strip() if len(row) > 5 else '',
                    'col2': row[6].strip() if len(row) > 6 else '',
                    'col3': row[7].strip() if len(row) > 7 else ''
                })
    
    zip_files = []
    temp_dir = tempfile.mkdtemp()
    
    for category, items in categories.items():
        category_dir = os.path.join(temp_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        processed_files = []
        
        for idx, item in enumerate(items, start=1):
            col_map = {1: item['col1'], 2: item['col2'], 3: item['col3']}
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
                base_name = f"{item['name']}_{category}_{col_num}"
                text_below = f"{item['name']}_{category}"
                
                if mime and mime.startswith('video'):
                    output_file = os.path.join(category_dir, f"{base_name}.mp4")
                    shutil.move(temp_file, output_file)
                    processed_files.append(output_file)
                elif mime and (mime.startswith('image') or 'webp' in mime.lower()):
                    output_file = os.path.join(category_dir, f"{base_name}.jpg")
                    compress_image(temp_file, output_file, 100, text_below)
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
        tag_name = RELEASE_NAME.replace(' ', '-').lower()
        
        try:
            release = repo.get_release(tag_name)
            for asset in release.get_assets():
                asset.delete_asset()
        except GithubException:
            release = repo.create_git_release(
                tag=tag_name,
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
