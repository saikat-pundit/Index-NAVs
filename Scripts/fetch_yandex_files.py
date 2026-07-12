import os
import csv
import argparse
import sys
from pathlib import Path
import requests
from datetime import datetime
import json

class YandexDiskAPI:
    """Yandex Disk REST API client"""
    
    def __init__(self, token):
        """
        Initialize Yandex Disk API client
        
        Args:
            token (str): Yandex OAuth token
        """
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {
            "Authorization": f"OAuth {self.token}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_connection(self):
        """
        Test if the OAuth token is valid
        Uses /disk endpoint to get disk info
        """
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Connection successful!")
                print(f"   User: {data.get('user', {}).get('login', 'Unknown')}")
                print(f"   Total space: {data.get('total_space', 0) / 1024**3:.2f} GB")
                print(f"   Used space: {data.get('used_space', 0) / 1024**3:.2f} GB")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def get_files_list(self, limit=10000):
        """
        Get list of all files using /resources/files endpoint
        This returns all files without recursion
        
        Args:
            limit (int): Maximum number of files to fetch
            
        Returns:
            list: List of file information dictionaries
        """
        all_files = []
        offset = 0
        
        print(f"📡 Fetching files from Yandex Disk...")
        
        while len(all_files) < limit:
            try:
                params = {
                    "limit": min(100, limit - len(all_files)),
                    "offset": offset,
                    "fields": "items.name,items.path,items.modified,items.size,items.media_type"
                }
                
                response = self.session.get(
                    f"{self.base_url}/resources/files",
                    params=params
                )
                
                if response.status_code != 200:
                    print(f"⚠️  Error: {response.status_code}")
                    print(f"   {response.text}")
                    break
                
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                
                for item in items:
                    file_info = {
                        'Date-Time': self._format_date(item.get('modified', '')),
                        'File Directory': self._get_directory(item.get('path', '')),
                        'File Name': item.get('name', ''),
                        'Size (bytes)': item.get('size', 0),
                        'Type': item.get('media_type', '')
                    }
                    all_files.append(file_info)
                
                # Check if we have all items
                if len(items) < params['limit']:
                    break
                
                offset += params['limit']
                
                # Progress indicator
                print(f"   Fetched {len(all_files)} files...", end='\r')
                
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        print(f"   ✅ Fetched {len(all_files)} files total")
        return all_files
    
    def get_files_recursive(self, path="/", limit=10000):
        """
        Get files recursively using /resources endpoint
        
        Args:
            path (str): Starting path
            limit (int): Maximum number of files to fetch
            
        Returns:
            list: List of file information dictionaries
        """
        all_files = []
        self._fetch_recursive(path, all_files, limit)
        return all_files
    
    def _fetch_recursive(self, path, all_files, limit):
        """Helper method for recursive fetching"""
        if len(all_files) >= limit:
            return
        
        try:
            params = {
                "path": path,
                "limit": min(100, limit - len(all_files)),
                "fields": "items.name,items.path,items.modified,items.size,items.type"
            }
            
            response = self.session.get(
                f"{self.base_url}/resources",
                params=params
            )
            
            if response.status_code != 200:
                return
            
            data = response.json()
            items = data.get('items', [])
            
            for item in items:
                if len(all_files) >= limit:
                    break
                
                if item.get('type') == 'file':
                    file_info = {
                        'Date-Time': self._format_date(item.get('modified', '')),
                        'File Directory': self._get_directory(item.get('path', '')),
                        'File Name': item.get('name', ''),
                        'Size (bytes)': item.get('size', 0),
                        'Type': item.get('media_type', '')
                    }
                    all_files.append(file_info)
                elif item.get('type') == 'dir':
                    # Recursively fetch subdirectory
                    self._fetch_recursive(item.get('path'), all_files, limit)
                    
        except Exception as e:
            print(f"⚠️  Error in {path}: {e}")
    
    def _format_date(self, date_string):
        """Format date string to readable format"""
        if not date_string:
            return ""
        try:
            # Yandex returns ISO format dates
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return date_string
    
    def _get_directory(self, file_path):
        """Extract directory from file path"""
        if not file_path:
            return ""
        # Remove filename from path
        path_obj = Path(file_path)
        return str(path_obj.parent)


def save_to_csv(file_data, output_file, include_headers=True):
    """
    Save file information to CSV file
    
    Args:
        file_data (list): List of dictionaries with file info
        output_file (str): Path to output CSV file
        include_headers (bool): Whether to include header row
    """
    if not file_data:
        print("⚠️  No data to save")
        return False
    
    # Create directory if it doesn't exist
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            # Only include the required columns as specified
            fieldnames = ['Date-Time', 'File Directory', 'File Name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if include_headers:
                writer.writeheader()
            
            for row in file_data:
                writer.writerow({
                    'Date-Time': row.get('Date-Time', ''),
                    'File Directory': row.get('File Directory', ''),
                    'File Name': row.get('File Name', '')
                })
        
        print(f"✅ Successfully saved {len(file_data)} files to: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Fetch file list from Yandex Disk using REST API'
    )
    parser.add_argument(
        '--token',
        '-t',
        help='Yandex OAuth token (uses YANDEX_DRIVE env var if not provided)'
    )
    parser.add_argument(
        '--path',
        '-p',
        default='/',
        help='Path in Yandex Disk to scan (default: /)'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='Data/yandex_file_list.csv',
        help='Output CSV file path (default: Data/yandex_file_list.csv)'
    )
    parser.add_argument(
        '--limit',
        '-l',
        type=int,
        default=10000,
        help='Maximum number of files to fetch (default: 10000)'
    )
    parser.add_argument(
        '--recursive',
        '-r',
        action='store_true',
        help='Recursively scan subdirectories (default: uses /files endpoint)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Yandex Disk File Fetcher")
    print("=" * 60)
    
    # Get token from args or environment
    token = args.token or os.environ.get('YANDEX_DRIVE')
    
    if not token:
        print("❌ Error: Yandex OAuth token not found")
        print("\nTo get your OAuth token:")
        print("1. Register an app at: https://oauth.yandex.com")
        print("2. Get token from: https://oauth.yandex.com/authorize?response_type=token&client_id=YOUR_CLIENT_ID")
        print("3. Or use: https://yandex.com/dev/disk/poligon/ for quick testing")
        print("\nSet the token as:")
        print("   Environment variable: export YANDEX_DRIVE='your_token_here'")
        print("   Or use --token argument")
        sys.exit(1)
    
    print(f"📁 Path: {args.path}")
    print(f"📄 Output: {args.output}")
    print(f"📊 Limit: {args.limit}")
    print(f"🔄 Recursive: {args.recursive}")
    print("-" * 60)
    
    # Initialize client
    client = YandexDiskAPI(token)
    
    # Test connection
    print("🔍 Testing connection...")
    if not client.test_connection():
        print("❌ Connection failed. Invalid OAuth token?")
        print("\n💡 Note: You need an OAuth token, not an App Password!")
        print("   App Passwords are for email, not for API access.")
        sys.exit(1)
    
    print("-" * 60)
    
    # Fetch files
    if args.recursive:
        files = client.get_files_recursive(args.path, args.limit)
    else:
        files = client.get_files_list(args.limit)
    
    if not files:
        print("⚠️  No files found")
        sys.exit(0)
    
    # Sort by date-time (newest first)
    files.sort(key=lambda x: x.get('Date-Time', ''), reverse=True)
    
    # Save to CSV
    if save_to_csv(files, args.output):
        print("-" * 60)
        print("📊 Summary:")
        print(f"   Total files: {len(files)}")
        print(f"   Output file: {args.output}")
        
        # Show sample
        print("\n📋 Sample files (first 5):")
        for i, file in enumerate(files[:5]):
            print(f"   {i+1}. {file['File Name']}")
            print(f"      📅 {file['Date-Time']}")
            print(f"      📁 {file['File Directory']}")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
