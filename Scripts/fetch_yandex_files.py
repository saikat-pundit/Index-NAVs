#!/usr/bin/env python3
"""
Script to fetch file list from Yandex Disk and save to CSV
"""

import os
import csv
import argparse
import sys
from pathlib import Path
import requests
from datetime import datetime

class YandexDisk:
    """Yandex Disk API client"""
    
    def __init__(self, token):
        """
        Initialize Yandex Disk client
        
        Args:
            token (str): Yandex OAuth token
        """
        self.token = token
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.headers = {"Authorization": f"OAuth {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_connection(self):
        """
        Test if the token is valid
        
        Returns:
            bool: True if connection successful
        """
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.status_code == 200
        except:
            return False
    
    def get_all_files(self, path="/", limit=10000):
        """
        Fetch all files from Yandex Disk recursively
        
        Args:
            path (str): Starting path in Yandex Disk
            limit (int): Maximum number of files to fetch
            
        Returns:
            list: List of file information dictionaries
        """
        all_files = []
        offset = 0
        
        print(f"📁 Scanning: {path}")
        
        while len(all_files) < limit:
            try:
                params = {
                    "path": path,
                    "limit": min(100, limit - len(all_files)),
                    "offset": offset,
                    "fields": "items.name,items.path,items.modified,items.size,items.type,items.created"
                }
                
                response = self.session.get(
                    f"{self.base_url}/resources",
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
                    if len(all_files) >= limit:
                        break
                    
                    if item.get('type') == 'file':
                        # Process file
                        file_info = {
                            'Date-Time': self._format_date(item.get('modified', '')),
                            'File Directory': self._get_directory(item.get('path', '')),
                            'File Name': item.get('name', '')
                        }
                        all_files.append(file_info)
                    elif item.get('type') == 'dir':
                        # Recursively process subdirectory
                        sub_files = self.get_all_files(
                            item.get('path', ''),
                            limit - len(all_files)
                        )
                        all_files.extend(sub_files)
                
                # Check if we have all items
                if len(items) < params['limit'] or len(all_files) >= limit:
                    break
                
                offset += params['limit']
                
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        return all_files
    
    def _format_date(self, date_string):
        """Format date string to readable format"""
        if not date_string:
            return ""
        try:
            # Parse ISO format date
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return date_string
    
    def _get_directory(self, file_path):
        """Extract directory from file path"""
        if not file_path:
            return ""
        # Remove the filename from path
        path_obj = Path(file_path)
        return str(path_obj.parent)

def save_to_csv(file_data, output_file):
    """
    Save file information to CSV file
    
    Args:
        file_data (list): List of dictionaries with file info
        output_file (str): Path to output CSV file
    """
    if not file_data:
        print("⚠️  No data to save")
        return False
    
    # Create directory if it doesn't exist
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
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Fetch file list from Yandex Disk'
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
    
    args = parser.parse_args()
    
    # Get token from args or environment
    token = args.token or os.environ.get('YANDEX_DRIVE')
    
    if not token:
        print("❌ Error: Yandex token not found")
        print("Please set YANDEX_DRIVE environment variable or use --token")
        print("\nTo get a Yandex OAuth token:")
        print("1. Visit: https://yandex.com/dev/disk/poligon/")
        print("2. Click 'Get token'")
        print("3. Select 'disk:read' permission")
        print("4. Copy the token")
        sys.exit(1)
    
    print("🚀 Starting Yandex Disk file fetch")
    print("=" * 50)
    
    # Initialize client
    client = YandexDisk(token)
    
    # Test connection
    print("🔍 Testing connection...")
    if not client.test_connection():
        print("❌ Connection failed. Invalid token?")
        sys.exit(1)
    print("✅ Connection successful")
    
    # Fetch files
    print(f"📡 Fetching files from: {args.path}")
    files = client.get_all_files(args.path, args.limit)
    
    if not files:
        print("⚠️  No files found")
        sys.exit(0)
    
    # Sort by date-time (newest first)
    files.sort(key=lambda x: x['Date-Time'], reverse=True)
    
    # Save to CSV
    if save_to_csv(files, args.output):
        print("\n📊 Summary:")
        print(f"   Total files: {len(files)}")
        print(f"   Output file: {args.output}")
        
        # Show sample
        print("\n📋 Sample files:")
        for i, file in enumerate(files[:5]):
            print(f"   {i+1}. {file['File Name']}")
            print(f"      📅 {file['Date-Time']}")
            print(f"      📁 {file['File Directory']}")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
