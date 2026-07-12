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
        if size_bytes >= 1024 * 1024:
            size_str = f"{round(size_bytes / (1024 * 1024), 1)}MB"
        else:
            size_str = f"{round(size_bytes / 1024, 1)}KB"
        
        modified = file_item.get("modified", "")
        try:
            date_obj = datetime.fromisoformat(modified.replace('Z', '+00:00'))
            date_str = date_obj.strftime("%d %B %Y")
        except:
            date_str = modified if modified else "Unknown"
        
        mime_type = file_item.get("mime_type", "")
        if mime_type:
            file_type = mime_type.split('/')[-1].upper()
        else:
            file_type = "UNKNOWN"
        
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
            "File Name": name,
            "File Size": size_str,
            "Created Date": date_str,
            "File Type": file_type,
            "Download Link": download_link
        }
    
    def fetch_files_from_folder(self, folder_path: str = "/🏢-🖨️/") -> List[Dict]:
        files = self.get_folder_contents(folder_path)
        files_info = []
        for file_item in files:
            try:
                files_info.append(self.get_file_info(file_item))
            except:
                pass
        return files_info


def save_to_csv(files_info: List[Dict], filename: str = "Data/Yandex Drive Office.csv"):
    if not files_info:
        return
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fieldnames = ["File Name", "File Size", "Created Date", "File Type", "Download Link"]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(files_info)


def main():
    token = os.environ.get("YANDEX_DISK_TOKEN")
    if not token:
        print("❌ Error: YANDEX_DISK_TOKEN not set")
        return
    
    try:
        fetcher = YandexDiskFetcher(token)
        folder_path = "/🏢-🖨️/"
        files_info = fetcher.fetch_files_from_folder(folder_path)
        
        if files_info:
            filename = "Data/Yandex Drive Office.csv"
            save_to_csv(files_info, filename)
            print(f"✅ Saved {len(files_info)} files to {filename}")
        else:
            print(f"No files found in {folder_path}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
