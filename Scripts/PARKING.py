import pandas as pd
import gdown
import os
import shutil
import sys
import json

# --- CONFIGURATION ---
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1Kmm-SqnMGL0V2tLXQc4GyEGGKYtD_XUf"
DOWNLOAD_DIR = "downloaded_files"
OUTPUT_DIR = "Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "AERO_parking.csv")

# These columns will be moved to the far left (Columns A, B, C...)
# Every other header found in the JSONs will follow these automatically.
PRIORITY_COLUMNS = [
    "source_json_file",
    "name", 
    "epicNo", 
    "acNo", 
    "partNo",
    "partSerialNo"
]

def main():
    # 1. Setup Workspace
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Download from Google Drive
    print(f"Connecting to Google Drive...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    # 3. Identify all files (ignoring extensions)
    all_files = []
    for dp, dn, filenames in os.walk(DOWNLOAD_DIR):
        for f in filenames:
            if not f.startswith('.'): # Skip hidden system files
                all_files.append(os.path.join(dp, f))

    processed_dfs = []
    print(f"Scanning {len(all_files)} files for voter data...")

    # 4. Processing Loop
    for filename in all_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Target the specific list in your JSON structure
            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            
            if elector_list:
                # json_normalize flattens nested dictionaries into columns
                df = pd.json_normalize(elector_list, sep='__')
                
                # Tag the source file so you can audit the data
                df['source_json_file'] = os.path.basename(filename)
                
                if not df.empty:
                    processed_dfs.append(df)
            else:
                print(f"⚠️  No data found in 'electorDetailDto' for file: {os.path.basename(filename)}")

        except (json.JSONDecodeError, ValueError):
            # Skip files that aren't valid JSON
            continue
        except Exception as e:
            print(f"Error reading {os.path.basename(filename)}: {e}")
            continue

    # 5. Combine and Reorganize
    if processed_dfs:
        # Filter out empty or all-NA dataframes to avoid the FutureWarning
        valid_dfs = [df for df in processed_dfs if not df.empty and not df.isna().all().all()]
        
        if not valid_dfs:
            print("❌ All processed files were empty.")
            return

        # Merge all files. Pandas aligns jumbled headers automatically.
        final_df = pd.concat(valid_dfs, ignore_index=True, sort=False)

        # 6. Column Management: Priority First + All Others
        all_cols = list(final_df.columns)
        existing_priority = [c for c in PRIORITY_COLUMNS if c in all_cols]
        other_cols = [c for c in all_cols if c not in existing_priority]
        
        final_df = final_df[existing_priority + other_cols]

        # 7. Final Cleanup and Export
        # Removing duplicates based on EPIC Number to ensure unique records
        if 'epicNo' in final_df.columns:
            initial_len = len(final_df)
            final_df = final_df.drop_duplicates(subset=['epicNo'], keep='first')
            dupes_removed = initial_len - len(final_df)
        else:
            dupes_removed = 0
        
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("-" * 45)
        print(f"✅ PROCESS COMPLETE")
        print(f"Output File:    {OUTPUT_FILE}")
        print(f"Total Files:    {len(valid_dfs)}")
        print(f"Total Records:  {len(final_df)}")
        print(f"Total Headers:  {len(final_df.columns)}")
        print(f"Dupes Removed:  {dupes_removed}")
        print("-" * 45)
        
        # Cleanup downloaded raw files
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No valid JSON data was found in the downloaded folder.")

if __name__ == "__main__":
    main()
