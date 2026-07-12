#!/usr/bin/env python3
"""
Script to fetch file list from Yandex Disk using REST API
"""

import os
import csv
import argparse
import sys
from pathlib import Path
import requests
from datetime import datetime

class YandexDiskAPI:
    """Yandex Disk REST API client"""
    
    def __init__(self, token):
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {"Authorization": f"OAuth {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_connection(self):
        """Test if the OAuth token is valid"""
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
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def get_all_files(self, limit=10000):
        """
        Get all files using /resources/files endpoint
        """
        all_files = []
        offset = 0
        
        print(f"📡 Fetching files from Yandex Disk...")
        
        while len(all_files) < limit:
            try:
                params = {
                    "limit": min(100, limit - len(all_files)),
                    "offset": offset,
                    "fields": "items.name,items.path,items.modified,items.size"
                }
                
                response = self.session.get(
                    f"{self.base_url}/resources/files",
                    params=params
                )
                
                if response.status_code != 200:
                    print(f"⚠️  Error: {response.status_code}")
                    break
                
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                
                for item in items:
                    file_info = {
                        'Date-Time': self._format_date(item.get('modified', '')),
                        'File Directory': self._get_directory(item.get('path', '')),
                        'File Name': item.get('name', '')
                    }
                    all_files.append(file_info)
                
                if len(items) < params['limit']:
                    break
                
                offset += params['limit']
                print(f"   Fetched {len(all_files)} files...", end='\r')
                
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        print(f"   ✅ Fetched {len(all_files)} files total")
        return all_files
    
    def _format_date(self, date_string):
        """Format date string"""
        if not date_string:
            return ""
        try:
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return date_string
    
    def _get_directory(self, file_path):
        """Extract directory from file path"""
        if not file_path:
            return ""
        path_obj = Path(file_path)
        return str(path_obj.parent)


def save_to_csv(file_data, output_file):
    """Save file information to CSV"""
    if not file_data:
        print("⚠️  No data to save")
        return False
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date-Time', 'File Directory', 'File Name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in file_data:
                writer.writerow(row)
        
        print(f"✅ Successfully saved {len(file_data)} files to: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Fetch file list from Yandex Disk')
    parser.add_argument(
        '--token',
        '-t',
        help='Yandex OAuth token (uses YANDEX_DRIVE env var)'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='Data/yandex_file_list.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--limit',
        '-l',
        type=int,
        default=10000,
        help='Maximum files to fetch'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Yandex Disk File Fetcher")
    print("=" * 60)
    
    # Get token
    token = args.token or os.environ.get('YANDEX_DRIVE')
    
    if not token:
        print("❌ Error: Yandex OAuth token not found")
        print("Please set YANDEX_DRIVE environment variable")
        sys.exit(1)
    
    print(f"📄 Output: {args.output}")
    print(f"📊 Limit: {args.limit}")
    print("-" * 60)
    
    # Initialize client
    client = YandexDiskAPI(token)
    
    # Test connection
    print("🔍 Testing connection...")
    if not client.test_connection():
        print("❌ Connection failed. Invalid OAuth token?")
        sys.exit(1)
    
    print("-" * 60)
    
    # Fetch files
    files = client.get_all_files(args.limit)
    
    if not files:
        print("⚠️  No files found")
        sys.exit(0)
    
    # Sort by date-time
    files.sort(key=lambda x: x.get('Date-Time', ''), reverse=True)
    
    # Save to CSV
    if save_to_csv(files, args.output):
        print("-" * 60)
        print("📊 Summary:")
        print(f"   Total files: {len(files)}")
        
        print("\n📋 Sample files:")
        for i, file in enumerate(files[:5]):
            print(f"   {i+1}. {file['File Name']}")
            print(f"      📅 {file['Date-Time']}")
            print(f"      📁 {file['File Directory']}")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
