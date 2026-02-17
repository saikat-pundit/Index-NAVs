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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "AERO_SIMPLE_MERGE.csv")
EXPECTED_FILE_COUNT = 56

def main():
    # 1. Setup Directories
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. Download from Drive
    print(f"📥 Connecting to Google Drive...")
    try:
        # Note: gdown may still stop at 50 despite 'remaining_ok'. 
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, 
                              use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download Error: {e}")
        sys.exit(1)

    # 3. VERIFICATION: Check file count
    all_files = [os.path.join(root, f) for root, dirs, files in os.walk(DOWNLOAD_DIR) for f in files]
    actual_count = len(all_files)
    
    print(f"\n📊 VERIFICATION: Found {actual_count} files locally.")
    if actual_count < EXPECTED_FILE_COUNT:
        print(f"⚠️ WARNING: Only {actual_count}/{EXPECTED_FILE_COUNT} files were fetched.")
        print("Google Drive API limits often block gdown at 50 files.")
    
    processed_dfs = []

    # 4. Merge "As Is"
    print(f"🔄 Merging files one after another...")
    for filename in all_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract the voter list and flatten it entirely
            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            if elector_list:
                # No filtering, no cherry-picking. Just turn JSON to Table.
                df = pd.json_normalize(elector_list)
                processed_dfs.append(df)
        except Exception as e:
            print(f"⏩ Skipping {os.path.basename(filename)} due to error: {e}")

    # 5. Final Concatenation
    if processed_dfs:
        # 'sort=False' ensures headers are NOT rearranged alphabetically
        final_df = pd.concat(processed_dfs, ignore_index=True, sort=False)
        
        # Save with standard comma separator
        final_df.to_csv(OUTPUT_FILE, index=False, sep=',', encoding='utf-8-sig')
        
        print("-" * 40)
        print(f"🎉 SUCCESS! Merged {len(processed_dfs)} files.")
        print(f"📁 Output: {OUTPUT_FILE}")
        print(f"🔝 Total Rows: {len(final_df)}")
        print("-" * 40)
    else:
        print("❌ No valid data was found to merge.")

if __name__ == "__main__":
    main()
