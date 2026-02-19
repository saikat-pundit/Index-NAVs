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

# These will be moved to the FRONT. 
# They must match the names generated after normalization.
PRIORITY_COLUMNS = [
    "name", 
    "epicNo", 
    "acNo", 
    "partNo",
    "partSerialNo"
]

def main():
    # 1. Setup Directories
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Download from Drive
    print(f"Downloading data from Google Drive...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    # 3. Collect ALL Files (No extension check)
    all_files = []
    for dp, dn, filenames in os.walk(DOWNLOAD_DIR):
        for f in filenames:
            # Skip hidden system files like .DS_Store
            if not f.startswith('.'):
                all_files.append(os.path.join(dp, f))

    processed_dfs = []
    print(f"Processing {len(all_files)} files found in folder...")

    # 4. Extract and Flatten
    for filename in all_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract the list from the snippet structure
            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            
            if elector_list:
                # Normalize flattens nested keys if they exist
                df = pd.json_normalize(elector_list, sep='__')
                
                if not df.empty:
                    processed_dfs.append(df)
            else:
                print(f"⚠️  No 'electorDetailDto' list found in: {os.path.basename(filename)}")

        except (json.JSONDecodeError, ValueError):
            # This skips files that aren't actually JSON (like logs or binaries)
            continue
        except Exception as e:
            print(f"Skipping {os.path.basename(filename)}: {e}")
            continue

    # 5. Merge and Handle Jumbled Headers
    if processed_dfs:
        # Aligns all columns. If one file has a header others don't, it fills with empty values.
        final_df = pd.concat(processed_dfs, ignore_index=True, sort=False)

        # 6. Reorder: Priority first, then EVERYTHING else
        all_cols = list(final_df.columns)
        existing_priority = [c for c in PRIORITY_COLUMNS if c in all_cols]
        other_cols = [c for c in all_cols if c not in existing_priority]
        
        final_df = final_df[existing_priority + other_cols]

        # 7. Deduplicate
        if 'epicNo' in final_df.columns:
            final_df = final_df.drop_duplicates(subset=['epicNo'], keep='first')
        
        # Save to CSV
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("-" * 40)
        print(f"✅ Success! Generated: {OUTPUT_FILE}")
        print(f"Total Records: {len(final_df)}")
        print(f"Total Unique Headers Found: {len(final_df.columns)}")
        print("-" * 40)
        
        # Cleanup
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No data was extracted. Ensure the files in Drive are valid JSON format.")

if __name__ == "__main__":
    main()
