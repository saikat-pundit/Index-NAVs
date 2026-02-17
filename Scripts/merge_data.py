import pandas as pd
import gdown
import os
import shutil
import sys
import json

# --- CONFIGURATION ---
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1llUw5NLQXunAc3CsP51K1Hn0D8nK4X-j"
DOWNLOAD_DIR = "downloaded_files"
OUTPUT_DIR = "Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "AERO_MERGED.csv")

def main():
    # 1. Setup Directories
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. Download from Drive (with bypass for 50+ files)
    print(f"Connecting to Google Drive...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, 
                              use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        sys.exit(1)

    # 3. Find all files
    all_files = [os.path.join(root, f) for root, dirs, files in os.walk(DOWNLOAD_DIR) for f in files]

    if not all_files:
        print("❌ Error: No files found.")
        sys.exit(1)

    processed_dfs = []

    # 4. Simple Merge: Load everything "as is"
    print(f"Merging {len(all_files)} files...")
    for filename in all_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # We target the list directly to ensure each entry in the list becomes a row
            # But we use record_path to keep the top-level info (statusCode, etc.) attached
            if 'payload' in data and 'electorDetailDto' in data['payload']:
                # This flattens the list while keeping top-level keys as columns
                df = pd.json_normalize(
                    data, 
                    record_path=['payload', 'electorDetailDto'],
                    meta=['statusCode', 'refId', 'message'],
                    errors='ignore'
                )
            else:
                # If the structure is different, just flatten the whole object
                df = pd.json_normalize(data)

            processed_dfs.append(df)

        except Exception:
            continue # Skip files that aren't valid JSON

    # 5. Combine, Remove Duplicates, and Save
    if processed_dfs:
        # Sort=False keeps columns in the order they appear
        final_df = pd.concat(processed_dfs, ignore_index=True, sort=False)
        
        # Remove duplicates
        initial_count = len(final_df)
        final_df = final_df.drop_duplicates()
        
        # Save to CSV
        final_df.to_csv(OUTPUT_FILE, index=False, sep=',', encoding='utf-8-sig')
        
        print("-" * 30)
        print(f"🎉 SUCCESS!")
        print(f"File Saved: {OUTPUT_FILE}")
        print(f"Original Rows: {initial_count}")
        print(f"Unique Rows: {len(final_df)}")
        print("-" * 30)
        
        # Cleanup
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No valid data found.")

if __name__ == "__main__":
    main()
