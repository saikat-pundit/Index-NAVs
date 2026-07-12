#!/usr/bin/env python3
"""
Script to fetch file list from Yandex Disk and save to CSV
"""

import os
import csv
import datetime
import requests
import argparse
import sys
from pathlib import Path
import json

class YandexDiskClient:
    """Client for interacting with Yandex Disk API"""
    
    def __init__(self, email, app_password):
        """
        Initialize Yandex Disk client
        
        Args:
            email (str): Yandex email address
            app_password (str): Yandex app-specific password
        """
        self.email = email
        self.app_password = app_password
        self.base_url = "https://cloud-api.yandex.net/v1/disk"
        self.session = requests.Session()
        # Use OAuth token authentication
        # Yandex Disk uses OAuth token, not email/password directly
        # You need to get OAuth token from Yandex
        self.token = None
        
    def authenticate(self):
        """
        Authenticate with Yandex Disk using OAuth token
        Note: You need to create an OAuth token in Yandex settings
        """
        # Yandex uses OAuth tokens, not app passwords directly
        # The app password is used for SMTP, not for API
        # For API, you need an OAuth token
        
        # If you have an OAuth token, use it
        if self.app_password and len(self.app_password) > 20:
            # Assuming app_password is actually an OAuth token
            self.token = self.app_password
            return True
        else:
            print("Warning: This appears to be an app password, not an OAuth token.")
            print("Please create an OAuth token from Yandex Disk settings.")
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
            print("Error: Not authenticated. Please provide OAuth token.")
            return []
        
        headers = {
            "Authorization": f"OAuth {self.token}"
        }
        
        all_files = []
        offset = 0
        
        while True:
            try:
                # Fetch files from Yandex Disk API
                params = {
                    "path": path,
                    "fields": "items.name,items.path,items.modified,items.size,items.type,items.created",
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
                    
                    for item in items:
                        if item.get('type') == 'file':
                            # Get file info
                            file_info = {
                                'Date-Time': item.get('modified', ''),
                                'File Directory': str(Path(item.get('path', '')).parent),
                                'File Name': item.get('name', ''),
                                'Size': item.get('size', 0),
                                'Created': item.get('created', '')
                            }
                            all_files.append(file_info)
                        elif item.get('type') == 'dir':
                            # Recursively fetch files from subdirectory
                            sub_files = self.get_files_recursive(
                                item.get('path', ''),
                                limit - len(all_files)
                            )
                            all_files.extend(sub_files)
                    
                    # Check if there are more files
                    if len(items) < params['limit'] or len(all_files) >= limit:
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
            print("Error: Not authenticated. Please provide OAuth token.")
            return []
        
        headers = {
            "Authorization": f"OAuth {self.token}"
        }
        
        all_files = []
        offset = 0
        
        while True:
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
                    
                    for item in items:
                        if item.get('type') == 'file':
                            file_info = {
                                'Date-Time': item.get('modified', ''),
                                'File Directory': str(Path(item.get('path', '')).parent),
                                'File Name': item.get('name', ''),
                                'Size': item.get('size', 0)
                            }
                            all_files.append(file_info)
                    
                    if len(items) < params['limit'] or len(all_files) >= limit:
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
                # Only write the required fields
                writer.writerow({
                    'Date-Time': row.get('Date-Time', ''),
                    'File Directory': row.get('File Directory', ''),
                    'File Name': row.get('File Name', '')
                })
        
        print(f"Successfully saved {len(file_data)} files to {output_file}")
    
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
        help='Yandex OAuth token or app password (uses YANDEX_APP_PASSWOR env var if not provided)'
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
        help='Recursively scan subdirectories'
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
    password = args.password or os.environ.get('YANDEX_APP_PASSWOR')
    
    if not email or not password:
        print("Error: Yandex credentials not found.")
        print("Please provide email and password via arguments or environment variables.")
        print("Environment variables: YANDEX_EMAIL, YANDEX_APP_PASSWOR")
        sys.exit(1)
    
    print(f"Fetching files from Yandex Disk: {args.path}")
    print(f"Output file: {args.output}")
    
    # Initialize client
    client = YandexDiskClient(email, password)
    
    if not client.authenticate():
        print("Error: Authentication failed.")
        print("Please ensure you're using a valid OAuth token.")
        print("You can create one at: https://yandex.com/dev/disk/api/doc/concepts/quickstart-docpage/")
        sys.exit(1)
    
    # Fetch files
    if args.recursive:
        file_data = client.get_files_recursive(args.path, args.limit)
    else:
        file_data = client.get_files_flat(args.path, args.limit)
    
    if not file_data:
        print("No files found or error occurred.")
        return
    
    # Sort by date-time
    file_data.sort(key=lambda x: x.get('Date-Time', ''), reverse=True)
    
    # Save to CSV
    save_to_csv(file_data, args.output)
    
    # Print summary
    print(f"Total files fetched: {len(file_data)}")
    
    # Show sample of fetched files
    if file_data:
        print("\nSample of fetched files:")
        for i, file in enumerate(file_data[:5]):
            print(f"  {i+1}. {file['File Name']} - {file['Date-Time']}")

if __name__ == "__main__":
    main()
