import os
import csv
import datetime
import requests
import argparse
import sys
from pathlib import Path
import json
import urllib.parse

class YandexDiskClient:
    """Client for interacting with Yandex Disk API"""
    
    def __init__(self, email, app_password):
        """
        Initialize Yandex Disk client
        
        Args:
            email (str): Yandex email address
            app_password (str): Yandex app-specific password (for API access)
        """
        self.email = email
        self.app_password = app_password
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.session = requests.Session()
        # Yandex Disk uses OAuth token
        # For app passwords, we need to use the token endpoint
        self.token = None
        
    def authenticate(self):
        """
        Authenticate with Yandex Disk
        
        For Yandex Disk, you need an OAuth token.
        If you have an app password, you can use it as the token directly
        if it's a valid OAuth token.
        """
        # Try using the app_password as an OAuth token directly
        if self.app_password:
            # Test if it's a valid token
            headers = {"Authorization": f"OAuth {self.app_password}"}
            try:
                response = self.session.get(
                    f"{self.base_url}/",
                    headers=headers
                )
                if response.status_code == 200:
                    self.token = self.app_password
                    print("✓ Successfully authenticated with Yandex Disk")
                    return True
                else:
                    print(f"⚠️  Authentication failed. Status: {response.status_code}")
                    print("Please ensure YANDEX_APP_PASSWORD contains a valid OAuth token.")
                    print("You can get one from: https://yandex.com/dev/disk/poligon/")
                    return False
            except Exception as e:
                print(f"Error: {e}")
                return False
        return False
    
    def get_files_recursive(self, path="/", limit=1000):
        """
        Recursively fetch all files from Yandex Disk
        
        Args:
            path (str): Path to start from (default: root)
            limit (int): Max files to fetch
        
        Returns:
            list: List of file information dictionaries
        """
        if not self.token:
            print("Error: Not authenticated.")
            return []
        
        all_files = []
        self._fetch_recursive(path, all_files, limit)
        return all_files
    
    def _fetch_recursive(self, path, all_files, limit):
        """Helper method for recursive fetching"""
        if len(all_files) >= limit:
            return
        
        headers = {"Authorization": f"OAuth {self.token}"}
        
        try:
            params = {
                "path": path,
                "fields": "items.name,items.path,items.modified,items.size,items.type,items.created",
                "limit": min(100, limit - len(all_files))
            }
            
            response = self.session.get(
                f"{self.base_url}/resources",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                for item in items:
                    if len(all_files) >= limit:
                        break
                    
                    if item.get('type') == 'file':
                        file_info = {
                            'Date-Time': item.get('modified', ''),
                            'File Directory': str(Path(item.get('path', '')).parent),
                            'File Name': item.get('name', '')
                        }
                        all_files.append(file_info)
                    elif item.get('type') == 'dir':
                        # Recursively fetch files from subdirectory
                        self._fetch_recursive(item.get('path', ''), all_files, limit)
            else:
                print(f"Error fetching from {path}: {response.status_code}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    def get_files_flat(self, path="/", limit=1000):
        """
        Fetch files from Yandex Disk (flat list, no recursion)
        
        Args:
            path (str): Path to start from (default: root)
            limit (int): Max files to fetch
        
        Returns:
            list: List of file information dictionaries
        """
        if not self.token:
            print("Error: Not authenticated.")
            return []
        
        all_files = []
        offset = 0
        headers = {"Authorization": f"OAuth {self.token}"}
        
        while len(all_files) < limit:
            try:
                params = {
                    "path": path,
                    "fields": "items.name,items.path,items.modified,items.size,items.type",
                    "limit": min(100, limit - len(all_files)),
                    "offset": offset
                }
                
                response = self.session.get(
                    f"{self.base_url}/resources",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    
                    if not items:
                        break
                    
                    for item in items:
                        if len(all_files) >= limit:
                            break
                        if item.get('type') == 'file':
                            file_info = {
                                'Date-Time': item.get('modified', ''),
                                'File Directory': str(Path(item.get('path', '')).parent),
                                'File Name': item.get('name', '')
                            }
                            all_files.append(file_info)
                    
                    if len(items) < params['limit']:
                        break
                    
                    offset += params['limit']
                else:
                    print(f"Error fetching files: {response.status_code}")
                    print(f"Response: {response.text}")
                    break
                    
            except Exception as e:
                print(f"Error: {e}")
                break
        
        return all_files

def save_to_csv(file_data, output_file):
    """
    Save file information to CSV file
    
    Args:
        file_data (list): List of dictionaries with file info
        output_file (str): Path to output CSV file
    """
    if not file_data:
        print("No data to save.")
        return
    
    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date-Time', 'File Directory', 'File Name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in file_data:
                writer.writerow({
                    'Date-Time': row.get('Date-Time', ''),
                    'File Directory': row.get('File Directory', ''),
                    'File Name': row.get('File Name', '')
                })
        
        print(f"✓ Successfully saved {len(file_data)} files to {output_file}")
    
    except IOError as e:
        print(f"Error saving CSV file: {e}")
        sys.exit(1)

def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(
        description='Fetch file list from Yandex Disk and save to CSV'
    )
    parser.add_argument(
        '--email',
        '-e',
        help='Yandex email address (uses YANDEX_EMAIL env var if not provided)'
    )
    parser.add_argument(
        '--password',
        '-p',
        help='Yandex OAuth token/app password (uses YANDEX_APP_PASSWORD env var if not provided)'
    )
    parser.add_argument(
        '--path',
        '-d',
        default='/',
        help='Path in Yandex Disk to scan (default: root)'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='Data/yandex_file_list.csv',
        help='Output CSV file path (default: Data/yandex_file_list.csv)'
    )
    parser.add_argument(
        '--recursive',
        '-r',
        action='store_true',
        default=True,
        help='Recursively scan subdirectories (default: True)'
    )
    parser.add_argument(
        '--limit',
        '-l',
        type=int,
        default=1000,
        help='Maximum number of files to fetch (default: 1000)'
    )
    
    args = parser.parse_args()
    
    # Get credentials from args or environment
    email = args.email or os.environ.get('YANDEX_EMAIL')
    password = args.password or os.environ.get('YANDEX_APP_PASSWORD')
    
    if not email or not password:
        print("❌ Error: Yandex credentials not found.")
        print("Please provide email and password via arguments or environment variables.")
        print("Environment variables needed:")
        print("  - YANDEX_EMAIL: Your Yandex email")
        print("  - YANDEX_APP_PASSWORD: Your Yandex OAuth token")
        sys.exit(1)
    
    print(f"📁 Fetching files from Yandex Disk: {args.path}")
    print(f"📄 Output file: {args.output}")
    print(f"📧 Using email: {email}")
    
    # Initialize client
    client = YandexDiskClient(email, password)
    
    if not client.authenticate():
        print("❌ Authentication failed.")
        print("\n💡 TIP: YANDEX_APP_PASSWORD should be an OAuth token, not an app password.")
        print("   To get an OAuth token:")
        print("   1. Go to: https://yandex.com/dev/disk/poligon/")
        print("   2. Click 'Get token'")
        print("   3. Select 'disk:read' permission")
        print("   4. Copy the token and add it as YANDEX_APP_PASSWORD in GitHub secrets")
        sys.exit(1)
    
    # Fetch files
    print("📡 Fetching files...")
    if args.recursive:
        file_data = client.get_files_recursive(args.path, args.limit)
    else:
        file_data = client.get_files_flat(args.path, args.limit)
    
    if not file_data:
        print("⚠️  No files found or error occurred.")
        return
    
    # Sort by date-time (newest first)
    file_data.sort(key=lambda x: x.get('Date-Time', ''), reverse=True)
    
    # Save to CSV
    save_to_csv(file_data, args.output)
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"  Total files fetched: {len(file_data)}")
    
    # Show sample of fetched files
    if file_data:
        print(f"\n📋 Sample of fetched files:")
        for i, file in enumerate(file_data[:5]):
            print(f"  {i+1}. {file['File Name']} - {file['Date-Time']}")
    
    print(f"\n✅ Done!")

if __name__ == "__main__":
    main()
