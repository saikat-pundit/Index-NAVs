import os
import csv
import requests
from datetime import datetime
from typing import List, Dict
import time
import urllib.parse

class YandexDiskFetcher:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {
            "Authorization": f"OAuth {token}",
            "Accept": "application/json"
        }
    
    def get_folder_contents(self, folder_path: str = "/🏢-🖨️/") -> List[Dict]:
        all_items = []
        offset = 0
        
        while True:
            params = {"path": folder_path, "limit": 100, "offset": offset}
            response = requests.get(f"{self.base_url}/resources", headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("_embedded", {}).get("items", [])
            
            if not items:
                break
            
            all_items.extend([item for item in items if item.get("type") == "file"])
            
            if len(items) < 100:
                break
                
            offset += len(items)
            time.sleep(0.5)
        
        return all_items
    
    def get_file_info(self, file_item: Dict) -> Dict:
        path = file_item.get("path", "")
        name = file_item.get("name", os.path.basename(path) if path else "")
        
        size_bytes = file_item.get("size", 0)
        size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes else 0
        
        modified = file_item.get("modified", "")
        try:
            date_str = datetime.fromisoformat(modified.replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_str = modified if modified else "Unknown"
        
        # Get download link
        try:
            dl_response = requests.get(
                f"{self.base_url}/resources/download",
                headers=self.headers,
                params={"path": path}
            )
            download_link = dl_response.json().get("href", "") if dl_response.status_code == 200 else ""
        except:
            download_link = ""
        
        return {
            "file_name": name,
            "file_size_mb": size_mb,
            "modified_date": date_str,
            "mime_type": file_item.get("mime_type", ""),
            "download_link": download_link,
            "media_type": file_item.get("media_type", "unknown")  # For summary
        }
    
    def fetch_files_from_folder(self, folder_path: str = "/🏢-🖨️/") -> List[Dict]:
        files = self.get_folder_contents(folder_path)
        print(f"Found {len(files)} files. Processing...")
        
        files_info = []
        for i, file_item in enumerate(files, 1):
            try:
                files_info.append(self.get_file_info(file_item))
                if i % 10 == 0:
                    print(f"Processed {i}/{len(files)} files")
            except Exception as e:
                print(f"Error processing file {i}: {e}")
        
        print(f"Successfully processed {len(files_info)} files")
        return files_info


def save_to_csv(files_info: List[Dict], filename: str = "Data/Yandex Drive Office.csv"):
    if not files_info:
        print("No files to save")
        return
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    fieldnames = ["file_name", "file_size_mb", "modified_date", "mime_type", "download_link"]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(files_info)
    
    print(f"✅ Saved {len(files_info)} files to {filename}")


def main():
    print("=" * 60)
    print("Yandex Disk File Lister - Office Folder")
    print("=" * 60)
    
    token = os.environ.get("YANDEX_DISK_TOKEN")
    if not token:
        print("❌ Error: YANDEX_DISK_TOKEN not set")
        return
    
    try:
        fetcher = YandexDiskFetcher(token)
        folder_path = "/🏢-🖨️/"
        
        print(f"Fetching files from {folder_path}...")
        files_info = fetcher.fetch_files_from_folder(folder_path)
        
        if files_info:
            filename = "Data/Yandex Drive Office.csv"
            save_to_csv(files_info, filename)
            
            # Summary
            print(f"\n📊 Summary:")
            print(f"   Total files: {len(files_info)}")
            print(f"   Total size: {sum(f['file_size_mb'] for f in files_info):.2f} MB")
            
            # File types
            media_types = {}
            for f in files_info:
                media_types[f["media_type"]] = media_types.get(f["media_type"], 0) + 1
            print("   File types:")
            for media_type, count in media_types.items():
                print(f"     {media_type}: {count}")
            
            # Sample files
            print("\n📁 Sample files:")
            for i, f in enumerate(files_info[:5], 1):
                print(f"   {i}. {f['file_name']} ({f['file_size_mb']} MB)")
        else:
            print(f"No files found in {folder_path}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
