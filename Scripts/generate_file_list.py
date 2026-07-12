#!/usr/bin/env python3
"""
Script to generate a CSV file with file directory information
"""

import os
import csv
import datetime
from pathlib import Path
import argparse
import sys

def get_file_info(directory_path):
    """
    Recursively walk through directory and collect file information
    
    Args:
        directory_path (str): Path to the directory to scan
    
    Returns:
        list: List of dictionaries containing file information
    """
    file_data = []
    
    # Convert to Path object for better handling
    base_path = Path(directory_path)
    
    if not base_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist.")
        return file_data
    
    if not base_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory.")
        return file_data
    
    # Walk through directory
    for root, dirs, files in os.walk(directory_path):
        # Skip hidden directories like .git
        if '/.git/' in root or '/.github/' in root:
            continue
            
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
                
            file_path = Path(root) / file
            try:
                # Get file modification time
                mod_time = datetime.datetime.fromtimestamp(
                    file_path.stat().st_mtime
                )
                
                # Get relative path from base directory
                relative_path = file_path.relative_to(base_path)
                
                file_data.append({
                    'Date-Time': mod_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'File Directory': str(file_path.parent),
                    'File Name': file
                })
            except (OSError, PermissionError) as e:
                print(f"Warning: Could not access {file_path}: {e}")
                continue
    
    return file_data

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
                writer.writerow(row)
        
        print(f"Successfully saved {len(file_data)} files to {output_file}")
    
    except IOError as e:
        print(f"Error saving CSV file: {e}")
        sys.exit(1)

def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(
        description='Generate CSV with file directory information'
    )
    parser.add_argument(
        '--directory',
        '-d',
        default='.',
        help='Directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='Data/file_list.csv',
        help='Output CSV file path (default: Data/file_list.csv)'
    )
    parser.add_argument(
        '--sort',
        '-s',
        action='store_true',
        help='Sort files by date-time'
    )
    
    args = parser.parse_args()
    
    print(f"Scanning directory: {args.directory}")
    print(f"Output file: {args.output}")
    
    # Get file information
    file_data = get_file_info(args.directory)
    
    if not file_data:
        print("No files found in the directory.")
        return
    
    # Sort by date-time if requested
    if args.sort:
        file_data.sort(key=lambda x: x['Date-Time'])
    
    # Save to CSV
    save_to_csv(file_data, args.output)
    
    # Print summary
    print(f"Total files scanned: {len(file_data)}")

if __name__ == "__main__":
    main()
