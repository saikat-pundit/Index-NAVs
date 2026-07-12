import os
import csv
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
import time
import urllib.parse

class YandexDiskFetcher:
    """Fetches file information from Yandex Disk"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {
            "Authorization": f"OAuth {token}",
            "Accept": "application/json"
        }
    
    def get_folder_contents(self, folder_path: str = "/🏢-🖨️/", limit: int = 1000) -> List[Dict]:
        """Fetch all files from a specific folder using the resources endpoint"""
        all_items = []
        offset = 0
        
        # URL encode the folder path
        encoded_path = urllib.parse.quote(folder_path, safe='')
        
        while True:
            url = f"{self.base_url}/resources"
            params = {
                "path": folder_path,
                "limit": min(limit, 100),  # Max 100 per request
                "offset": offset
            }
            
            try:
                print(f"Fetching folder contents: {folder_path} (offset: {offset})")
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Get the embedded items (files and folders inside this folder)
                embedded = data.get("_embedded", {})
                items = embedded.get("items", [])
                
                if not items:
                    break
                
                # Filter to only files (exclude folders if needed)
                file_items = [item for item in items if item.get("type") == "file"]
                all_items.extend(file_items)
                
                # Check if we have more items
                if len(items) < params["limit"]:
                    break
                    
                offset += len(items)
                time.sleep(0.5)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching folder contents: {e}")
                if hasattr(e, 'response') and e.response:
                    print(f"Response: {e.response.text}")
                break
        
        return all_items
    
    def get_file_info(self, file_item: Dict) -> Dict:
    """Extract relevant file information"""
    # Get file path
    path = file_item.get("path", "")
    
    # Get file name from path
    name = file_item.get("name", os.path.basename(path) if path else "")
    
    # Get file size (convert to MB for readability)
    size_bytes = file_item.get("size", 0)
    size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes else 0
    
    # Get modification date
    modified = file_item.get("modified", "")
    if modified:
        try:
            # Parse ISO format date
            date_obj = datetime.fromisoformat(modified.replace('Z', '+00:00'))
            date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_str = modified
    else:
        date_str = "Unknown"
    
    # Get media type (keep this for summary)
    media_type = file_item.get("media_type", "unknown")
    
    # Get direct download link (requires additional API call)
    download_link = self.get_download_link(path) if path else ""
    
    return {
        "file_name": name,
        "file_size_mb": size_mb,
        "modified_date": date_str,
        "mime_type": file_item.get("mime_type", ""),
        "download_link": download_link,
        "media_type": media_type  # ADD THIS BACK
    }
    
    def get_download_link(self, path: str) -> str:
        """Get direct download link for a file"""
        try:
            url = f"{self.base_url}/resources/download"
            params = {"path": path}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("href", "")
            
        except requests.exceptions.RequestException:
            return ""
    
    def fetch_files_from_folder(self, folder_path: str = "/🏢-🖨️/", limit: int = 1000) -> List[Dict]:
        """Fetch and process all files from a specific folder"""
        files = self.get_folder_contents(folder_path, limit)
        files_info = []
        
        print(f"Found {len(files)} files in {folder_path}. Processing...")
        
        for i, file_item in enumerate(files, 1):
            try:
                info = self.get_file_info(file_item)
                files_info.append(info)
                
                # Print progress
                if i % 10 == 0:
                    print(f"Processed {i}/{len(files)} files")
                    
            except Exception as e:
                print(f"Error processing file {i}: {e}")
        
        print(f"Successfully processed {len(files_info)} files")
        return files_info


def save_to_csv(files_info: List[Dict], filename: str = "Data/Yandex Drive Office.csv"):
    """Save file information to CSV"""
    if not files_info:
        print("No files to save")
        return
    
    # Ensure Data directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Define CSV columns
    fieldnames = [
        "file_name",
        "file_size_mb",
        "modified_date",
        "mime_type",
        "download_link"
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(files_info)
        
        print(f"✅ Successfully saved {len(files_info)} files to {filename}")
        
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")


def main():
    """Main function to run the script"""
    print("=" * 60)
    print("Yandex Disk File Lister - Office Folder")
    print("=" * 60)
    
    # Get token from environment variable (for security)
    token = os.environ.get("YANDEX_DISK_TOKEN")
    
    if not token:
        print("❌ Error: YANDEX_DISK_TOKEN environment variable not set")
        print("Please set it using: export YANDEX_DISK_TOKEN='your_token'")
        return
    
    try:
        # Initialize fetcher
        fetcher = YandexDiskFetcher(token)
        
        # Specify the folder to scan
        folder_path = "/🏢-🖨️/"
        
        # Fetch files from the specific folder
        print(f"Fetching files from {folder_path}...")
        files_info = fetcher.fetch_files_from_folder(folder_path)
        
        # Save to CSV in Data directory
        if files_info:
            # Create Data directory if it doesn't exist
            os.makedirs("Data", exist_ok=True)
            
            # Save as "Yandex Drive Office.csv"
            filename = "Data/Yandex Drive Office.csv"
            save_to_csv(files_info, filename)
            
            # Print summary
            print("\n📊 Summary:")
            print(f"   Total files in {folder_path}: {len(files_info)}")
            
            # Calculate total size
            total_size_mb = sum(f["file_size_mb"] for f in files_info)
            print(f"   Total size: {total_size_mb:.2f} MB")
            
            # Count by media type
            media_types = {}
            for f in files_info:
                media_type = f["media_type"]
                media_types[media_type] = media_types.get(media_type, 0) + 1
            
            print("   File types:")
            for media_type, count in media_types.items():
                print(f"     {media_type}: {count}")
                
            # Show first few files as preview
            print("\n📁 Sample files:")
            for i, f in enumerate(files_info[:5], 1):
                print(f"   {i}. {f['file_name']} ({f['file_size_mb']} MB)")
                
        else:
            print(f"No files found in {folder_path}")
            print("Please check:")
            print("1. The folder name is correct (case sensitive)")
            print("2. The folder exists in your Yandex Disk")
            print("3. Your token has access to this folder")
            
    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()
