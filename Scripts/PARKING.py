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

def main():
    # 1. Setup Directories
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. Download from Drive
    print(f"Downloading data...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    # 3. Collect Files
    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(DOWNLOAD_DIR) for f in filenames]

    processed_dfs = []

    # 4. Extract and Normalize
    for filename in all_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if filename.lower().endswith('.har'):
                # Handle .har files
                entries = data.get('log', {}).get('entries', [])
                for entry in entries:
                    content_text = entry.get('response', {}).get('content', {}).get('text', '')
                    if content_text:
                        try:
                            # The text is an escaped JSON string, load it again
                            inner_data = json.loads(content_text)
                            elector_list = inner_data.get('payload', {}).get('electorDetailDto', [])
                            if elector_list:
                                df = pd.DataFrame(elector_list)
                                df = df.add_prefix('payload__electorDetailDto__')
                                processed_dfs.append(df)
                        except json.JSONDecodeError:
                            continue
            else:
                # Handle standard .json files
                elector_list = data.get('payload', {}).get('electorDetailDto', [])
                if elector_list:
                    df = pd.DataFrame(elector_list)
                    df = df.add_prefix('payload__electorDetailDto__')
                    processed_dfs.append(df)

        except (json.JSONDecodeError, Exception):
            continue

    # 5. Merge and Remove Duplicates
    if processed_dfs:
        final_df = pd.concat(processed_dfs, ignore_index=True).fillna('')
        
        initial_count = len(final_df)

        # --- DUPLICATE REMOVAL LOGIC ---
        if 'payload__electorDetailDto__epicNo' in final_df.columns:
            final_df = final_df.drop_duplicates(subset=['payload__electorDetailDto__epicNo'], keep='first')
        else:
            final_df = final_df.drop_duplicates(keep='first')
        
        removed_count = initial_count - len(final_df)

        # 6. Save to CSV (Comma Separated)
        final_df.to_csv(OUTPUT_FILE, index=False, sep=',', encoding='utf-8-sig')
        
        print("-" * 35)
        print(f"✅ Success! File: {OUTPUT_FILE}")
        print(f"Total Rows: {len(final_df)}")
        print(f"Duplicates Removed: {removed_count}")
        print("-" * 35)
        
        # Cleanup: Delete the download folder to keep workspace clean
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No valid data found.")

if __name__ == "__main__":
    main()
