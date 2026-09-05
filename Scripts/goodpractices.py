import os
import csv
import requests
import zipfile
import tempfile
import shutil
import re
import textwrap
import time
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import magic
import gdown
from github import Github
from github.GithubException import GithubException

# Configuration
GIST_URL = "https://gist.githubusercontent.com/saikat-pundit/8d3eda26f337ec08ea54c8e41f936b96/raw/GoodPractices.csv"
RELEASE_NAME = "Good Practices"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def download_csv():
    """Download and parse the CSV file from Gist"""
    response = requests.get(GIST_URL)
    response.raise_for_status()
    content = response.text
    lines = content.strip().split('\n')
    header = lines[0]
    data_rows = lines[56:] if len(lines) > 56 else []
    return header, data_rows

def parse_google_drive_id(url):
    """Extract Google Drive file ID from various URL formats"""
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/uc\?export=download&id=([a-zA-Z0-9_-]+)',
        r'/open\?id=([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_file_with_retry(url, file_id, output_path, max_retries=3):
    """Download file with retry logic for handling Google Drive restrictions"""
    for attempt in range(max_retries):
        try:
            if download_file(url, file_id, output_path):
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                print(f"All {max_retries} attempts failed: {e}")
                return False
    return False

def download_file(url, file_id, output_path):
    """Enhanced download function that handles Google Drive files properly"""
    if file_id:
        try:
            # Method 1: Try gdown first
            print(f"Attempting to download Google Drive file: {file_id}")
            gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)
            return True
        except Exception as e1:
            print(f"gdown failed: {e1}")
            try:
                # Method 2: Manual download with confirmation handling
                print("Attempting manual download with confirmation handling...")
                session = requests.Session()
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                response = session.get(download_url, stream=True)
                
                # Check if we need to handle confirmation page
                if 'confirm' in response.text:
                    confirm_match = re.search(r'confirm=([^&]+)', response.text)
                    if confirm_match:
                        confirm_token = confirm_match.group(1)
                        download_url = f"https://drive.google.com/uc?export=download&confirm={confirm_token}&id={file_id}"
                        response = session.get(download_url, stream=True)
                
                response.raise_for_status()
                
                # Check if we got HTML instead of a file
                content_type = response.headers.get('content-type', '')
                if 'text/html' in content_type:
                    print("Received HTML instead of file. File may not be accessible.")
                    return False
                
                # Write the file
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"Download progress: {progress:.1f}%", end='\r')
                print()  # New line after progress
                return True
                
            except Exception as e2:
                print(f"Manual download failed: {e2}")
                
                try:
                    # Method 3: Try with alternative URL
                    print("Attempting download with alternative URL...")
                    alt_url = f"https://drive.google.com/uc?id={file_id}&export=download"
                    response = requests.get(alt_url, stream=True)
                    response.raise_for_status()
                    
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
                    
                except Exception as e3:
                    print(f"Alternative download failed: {e3}")
                    return False
    
    # Non-Google Drive URL handling
    try:
        print(f"Downloading from direct URL: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Failed to download from {url}: {e}")
        return False

def add_text_below_image(img, text):
    """Add text below an image with proper wrapping"""
    width, height = img.size
    max_width = int(width * 0.9)
    
    # Try to load a font, fall back to default
    try:
        font_size = int(height / 25)
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
        font_size = 12
    
    # Clean and wrap text
    wrapped_text = []
    for line in text.split('_'):
        if line:
            wrapped_text.append(line.strip())
    if not wrapped_text:
        wrapped_text = [text]
    
    # Word wrap the text
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
    
    # Calculate dimensions and create new image
    line_height = font_size + 5
    total_text_height = len(lines) * line_height + 20
    padding = 20
    
    new_height = height + total_text_height + padding
    new_img = Image.new('RGB', (width, new_height), (255, 255, 255))
    new_img.paste(img, (0, 0))
    
    # Draw the text
    draw = ImageDraw.Draw(new_img)
    y = height + 10
    
    for line in lines:
        text_width = font.getlength(line)
        x = (width - text_width) / 2
        draw.text((x, y), line, fill=(0, 0, 0), font=font)
        y += line_height
    
    return new_img

def compress_image(input_path, output_path, target_size_kb=100, text_below=None):
    """Compress image and optionally add text below"""
    try:
        img = Image.open(input_path)
        
        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Add text if provided
        if text_below:
            img = add_text_below_image(img, text_below)
        
        # Compress with quality adjustment
        quality = 95
        while quality > 10:
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            if len(buffer.getvalue()) / 1024 <= target_size_kb:
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                return True
            quality -= 5
        
        # Final fallback
        img.save(output_path, format='JPEG', quality=10, optimize=True)
        return True
        
    except Exception as e:
        print(f"Error compressing image {input_path}: {e}")
        return False

def process_media():
    """Main function to process all media files"""
    print("Starting media processing...")
    
    # Download and parse CSV
    try:
        header, data_rows = download_csv()
        print(f"Downloaded CSV with {len(data_rows)} rows")
    except Exception as e:
        print(f"Failed to download CSV: {e}")
        return
    
    # Parse CSV data
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
    
    print(f"Found {len(categories)} categories")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    zip_files = []
    
    try:
        # Process each category
        for category, items in categories.items():
            print(f"\nProcessing category: {category} ({len(items)} items)")
            category_dir = os.path.join(temp_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            processed_files = []
            
            # Process each item in the category
            for idx, item in enumerate(items, start=1):
                print(f"  Processing item {idx}/{len(items)}: {item['name']}")
                col_map = {1: item['col1'], 2: item['col2'], 3: item['col3']}
                
                for col_num, url in col_map.items():
                    if not url:
                        continue
                    
                    file_id = parse_google_drive_id(url)
                    if not file_id:
                        print(f"    No Google Drive ID found in URL: {url}")
                        continue
                    
                    temp_file = os.path.join(category_dir, f"temp_{col_num}_{idx}")
                    
                    # Download the file with retry
                    if not download_file_with_retry(url, file_id, temp_file):
                        print(f"    Failed to download file: {file_id}")
                        continue
                    
                    # Determine file type and process
                    try:
                        mime = magic.from_file(temp_file, mime=True)
                        base_name = f"{item['name']}_{category}_{col_num}"
                        # Clean filename for filesystem
                        base_name = re.sub(r'[^\w\s-]', '', base_name)
                        base_name = re.sub(r'[-\s]+', '_', base_name)
                        text_below = f"{item['name']}_{category}"
                        
                        if mime and mime.startswith('video'):
                            output_file = os.path.join(category_dir, f"{base_name}.mp4")
                            shutil.move(temp_file, output_file)
                            processed_files.append(output_file)
                            print(f"    Processed video: {os.path.basename(output_file)}")
                            
                        elif mime and (mime.startswith('image') or 'webp' in mime.lower()):
                            output_file = os.path.join(category_dir, f"{base_name}.jpg")
                            if compress_image(temp_file, output_file, 100, text_below):
                                os.remove(temp_file)
                                processed_files.append(output_file)
                                print(f"    Processed image: {os.path.basename(output_file)}")
                            else:
                                print(f"    Failed to compress image: {temp_file}")
                                os.remove(temp_file)
                        else:
                            print(f"    Unsupported file type: {mime}")
                            os.remove(temp_file)
                            
                    except Exception as e:
                        print(f"    Error processing file: {e}")
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
            
            # Create zip file for the category
            if processed_files:
                zip_path = os.path.join(temp_dir, f"{category}.zip")
                print(f"  Creating zip file: {os.path.basename(zip_path)} with {len(processed_files)} files")
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    seen_names = set()
                    for file_path in processed_files:
                        base_name = os.path.basename(file_path)
                        # Handle duplicate filenames
                        if base_name in seen_names:
                            name, ext = os.path.splitext(base_name)
                            counter = 1
                            while f"{name}_{counter}{ext}" in seen_names:
                                counter += 1
                            base_name = f"{name}_{counter}{ext}"
                        seen_names.add(base_name)
                        zipf.write(file_path, base_name)
                
                zip_files.append(zip_path)
                print(f"  Created zip: {os.path.basename(zip_path)}")
        
        # Upload to GitHub release
        if zip_files and GITHUB_TOKEN:
            print(f"\nUploading {len(zip_files)} zip files to GitHub release...")
            try:
                g = Github(GITHUB_TOKEN)
                repo = g.get_repo(os.environ.get('GITHUB_REPOSITORY', ''))
                tag_name = RELEASE_NAME.replace(' ', '-').lower()
                
                # Check if release exists, create if not
                try:
                    release = repo.get_release(tag_name)
                    print(f"Found existing release: {tag_name}")
                    # Delete existing assets
                    for asset in release.get_assets():
                        asset.delete_asset()
                        print(f"  Deleted existing asset: {asset.name}")
                except GithubException:
                    print(f"Creating new release: {tag_name}")
                    release = repo.create_git_release(
                        tag=tag_name,
                        name=RELEASE_NAME,
                        message=f"Release {RELEASE_NAME} - {time.strftime('%Y-%m-%d %H:%M:%S')}",
                        draft=False,
                        prerelease=False
                    )
                
                # Upload each zip file
                for zip_path in zip_files:
                    try:
                        asset_name = os.path.basename(zip_path)
                        print(f"  Uploading: {asset_name}")
                        release.upload_asset(
                            zip_path,
                            name=asset_name,
                            content_type='application/zip'
                        )
                        print(f"  Uploaded: {asset_name}")
                    except Exception as e:
                        print(f"  Failed to upload {asset_name}: {e}")
                        
            except Exception as e:
                print(f"GitHub upload failed: {e}")
        else:
            if not zip_files:
                print("No zip files created to upload")
            if not GITHUB_TOKEN:
                print("GITHUB_TOKEN not set, skipping GitHub upload")
        
        print(f"\nProcessing complete. Created {len(zip_files)} zip files.")
        
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            print("Cleaned up temporary files")
        except Exception as e:
            print(f"Warning: Could not clean up temp directory: {e}")

if __name__ == "__main__":
    process_media()
