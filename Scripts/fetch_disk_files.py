import os
import csv
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
import time

class YandexDiskFetcher:
    """Fetches file information from Yandex Disk"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {
            "Authorization": f"OAuth {token}",
            "Accept": "application/json"
        }
    
    def get_all_files(self, limit: int = 1000) -> List[Dict]:
        """Fetch all files from Yandex Disk with pagination"""
        all_files = []
        offset = 0
        
        while True:
            url = f"{self.base_url}/resources/files"
            params = {
                "limit": min(limit, 100),  # Max 100 per request
                "offset": offset
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                items = data.get("items", [])
                if not items:
                    break
                
                all_files.extend(items)
                
                # Check if we have more items
                if len(items) < params["limit"]:
                    break
                    
                offset += len(items)
                time.sleep(0.5)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching files: {e}")
                break
        
        return all_files
    
    def get_file_info(self, file_item: Dict) -> Dict:
        """Extract relevant file information"""
        # Get file path
        path = file_item.get("path", "")
        
        # Get file name from path
        name = os.path.basename(path) if path else file_item.get("name", "")
        
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
        
        # Get media type
        media_type = file_item.get("media_type", "unknown")
        
        # Get direct download link (requires additional API call)
        download_link = self.get_download_link(path) if path else ""
        
        return {
            "file_name": name,
            "file_path": path,
            "file_size_mb": size_mb,
            "file_size_bytes": size_bytes,
            "modified_date": date_str,
            "media_type": media_type,
            "download_link": download_link,
            "mime_type": file_item.get("mime_type", ""),
            "created": file_item.get("created", "")
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
    
    def fetch_all_files_info(self, limit: int = 1000) -> List[Dict]:
        """Fetch and process all files"""
        files = self.get_all_files(limit)
        files_info = []
        
        print(f"Found {len(files)} files. Processing...")
        
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


def save_to_csv(files_info: List[Dict], filename: str = "Data/yandex_disk_files_latest.csv"):
    """Save file information to CSV"""
    if not files_info:
        print("No files to save")
        return
    
    # Ensure Data directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Define CSV columns
    fieldnames = [
        "file_name",
        "file_path", 
        "file_size_mb",
        "file_size_bytes",
        "modified_date",
        "media_type",
        "download_link",
        "mime_type",
        "created"
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
    print("Yandex Disk File Lister")
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
        
        # Fetch files
        print("Fetching files from Yandex Disk...")
        files_info = fetcher.fetch_all_files_info()
        
        # Save to CSV in Data directory
        if files_info:
            # Create Data directory if it doesn't exist
            os.makedirs("Data", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Data/yandex_disk_files_{timestamp}.csv"
            save_to_csv(files_info, filename)
            
            # Also save as latest in Data directory
            save_to_csv(files_info, "Data/yandex_disk_files_latest.csv")
            
            # Print summary
            print("\n📊 Summary:")
            print(f"   Total files: {len(files_info)}")
            
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
        else:
            print("No files found or error occurred")
            
    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()
