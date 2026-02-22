import pandas as pd
import requests
import re
import zipfile
import json
from io import BytesIO
from PIL import Image
import os

# --- CONFIGURATION ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTBuDewVgTDoc_zaWYQyaWKpBt0RwtFPhnBrpqr1v6Y5wfAmPpEYvTsaWd64bsHhH68iYNtLMSRpOQ0/pub?gid=979866094&single=true&output=csv"
MAX_IMAGE_SIZE_KB = 200
MAX_IMAGE_BYTES = MAX_IMAGE_SIZE_KB * 1024

def get_filename(file_id):
    """Get original filename from Google Drive"""
    try:
        meta_url = f"https://drive.google.com/file/d/{file_id}/view"
        resp = requests.get(meta_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        
        json_ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', resp.text, re.DOTALL)
        if json_ld:
            data = json.loads(json_ld.group(1))
            return data.get('name', f"file_{file_id}")
            
        title = re.search(r'<title>(.*?) - Google Drive</title>', resp.text)
        if title:
            return title.group(1).strip()
            
    except Exception as e:
        pass
    
    return f"file_{file_id}"

def convert_and_compress_image(image_content):
    """Convert (WEBP/etc) to JPEG and compress below 200KB"""
    try:
        img = Image.open(BytesIO(image_content))
        
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
            
        quality = 95
        output_buffer = BytesIO()
        
        while quality > 5:
            output_buffer.seek(0)
            output_buffer.truncate(0)
            img.save(output_buffer, format="JPEG", quality=quality)
            
            if output_buffer.tell() < MAX_IMAGE_BYTES:
                return output_buffer.getvalue()
                
            quality -= 5 
            
        return output_buffer.getvalue()
        
    except Exception as e:
        print(f"   ⚠️ Image conversion failed: {e}")
        return image_content

def process_and_zip_folders(df):
    """Group by Main Folder and create ZIPs with Sub Folders"""
    
    # Extract columns AN (39), AO (40), AP (41)
    # A=0, Z=25, AA=26, AN=39, AO=40, AP=41
    try:
        data = df.iloc[:, [39, 40, 41]].copy()
    except IndexError:
        print("❌ Error: Columns AN, AO, AP not found in the CSV.")
        return

    data.columns = ['MAIN_FOLDER', 'SUB_FOLDER', 'DRIVE_LINKS']
    data = data.dropna(subset=['MAIN_FOLDER', 'DRIVE_LINKS'])
    
    # Group the data by Main Folder so all subfolders go into the same ZIP
    grouped = data.groupby('MAIN_FOLDER')
    
    print(f"📊 Found {len(grouped)} unique Main Folders to process...")
    
    for main_folder, group in grouped:
        clean_main = re.sub(r'[<>:"/\\|?*]', '_', str(main_folder).strip())
        zip_filename = f"{clean_main}.zip"
        
        print(f"\n📦 Processing Main Folder: {zip_filename}")
        success_count = 0
        
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for _, row in group.iterrows():
                sub_folder = re.sub(r'[<>:"/\\|?*]', '_', str(row['SUB_FOLDER']).strip())
                if str(sub_folder).lower() == 'nan':
                    sub_folder = "Unknown_Subfolder"
                    
                links_str = row['DRIVE_LINKS']
                links = [l.strip() for l in str(links_str).split(';') if l.strip()]
                
                for link in links:
                    match = re.search(r'id=([a-zA-Z0-9_-]+)', link)
                    if not match:
                        match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
                    
                    if not match:
                        print(f"   ✗ Invalid link format: {link[:50]}...")
                        continue
                        
                    file_id = match.group(1)
                    original_filename = get_filename(file_id)
                    
                    # Download file
                    try:
                        dl_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                        session = requests.Session()
                        response = session.get(dl_url, stream=True, timeout=30)
                        
                        if "confirm=" in response.url:
                            token = re.search(r'confirm=([0-9A-Za-z_]+)', response.url).group(1)
                            response = session.get(f"{dl_url}&confirm={token}", stream=True, timeout=30)
                        
                        content = response.content

                        # Process Image
                        content = convert_and_compress_image(content)
                        
                        # Ensure filename ends with .jpg
                        original_filename = re.sub(r'\.[^.]+$', '', original_filename) # Strip old extension
                        final_filename = f"{original_filename}.jpg"
                        
                        # Set up the internal ZIP path: Subfolder/Image.jpg
                        zip_path = os.path.join(sub_folder, final_filename)
                        
                        # Write to ZIP
                        zipf.writestr(zip_path, content)
                        success_count += 1
                        print(f"   ✓ Added to {sub_folder}/ : {final_filename}")
                        
                    except Exception as e:
                        print(f"   ✗ Error downloading {file_id}: {str(e)[:50]}")
                        continue
        
        print(f"   ✅ Saved {zip_filename} with {success_count} files inside.")

def main():
    print("Fetching CSV data...")
    df = pd.read_csv(CSV_URL)
    process_and_zip_folders(df)
    print("\n🎉 All folders processed successfully!")

if __name__ == "__main__":
    main()
