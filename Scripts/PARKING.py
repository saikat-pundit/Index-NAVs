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

# These will be moved to the FRONT of the CSV for easy reading.
# ALL other columns found in the JSON will follow these automatically.
PRIORITY_COLUMNS = [
    "payload__electorDetailDto__name", 
    "payload__electorDetailDto__epicNo", 
    "payload__electorDetailDto__acNo", 
    "payload__electorDetailDto__partNo"
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

    # 3. Collect and Flatten Files
    all_files = []
    for dp, dn, filenames in os.walk(DOWNLOAD_DIR):
        for f in filenames:
            if f.endswith('.json'):
                all_files.append(os.path.join(dp, f))

    processed_dfs = []
    print(f"Processing {len(all_files)} files...")

    for filename in all_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Use record_path to dig into the list, and sep='__' to create readable headers
            # errors='ignore' ensures that if a key is missing in one file, it doesn't crash
            df = pd.json_normalize(
                data, 
                record_path=['payload', 'electorDetailDto'], 
                sep='__'
            )
            
            # Add a prefix so you know exactly where the data came from in the JSON tree
            df = df.add_prefix('payload__electorDetailDto__')
            
            if not df.empty:
                processed_dfs.append(df)

        except Exception as e:
            print(f"Skipping {os.path.basename(filename)}: {e}")
            continue

    # 4. Merge and Handle Jumbled Headers
    if processed_dfs:
        # pd.concat aligns columns by name. If File A has 'Age' and File B doesn't, 
        # File B's 'Age' cells will simply be empty (NaN).
        final_df = pd.concat(processed_dfs, ignore_index=True, sort=False)

        # 5. Smart Reordering (Show Priority first, then everything else)
        all_cols = list(final_df.columns)
        
        # Identify columns that exist in our priority list
        existing_priority = [c for c in PRIORITY_COLUMNS if c in all_cols]
        # Identify every other column found in the JSONs
        other_cols = [c for c in all_cols if c not in existing_priority]
        
        # Combine them: Priority first + Every other header found
        final_df = final_df[existing_priority + other_cols]

        # 6. Deduplicate and Save
        if 'payload__electorDetailDto__epicNo' in final_df.columns:
            final_df = final_df.drop_duplicates(subset=['payload__electorDetailDto__epicNo'], keep='first')
        
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("-" * 40)
        print(f"✅ Success! Generated: {OUTPUT_FILE}")
        print(f"Total Records: {len(final_df)}")
        print(f"Total Unique Headers Found: {len(final_df.columns)}")
        print("-" * 40)
        
        # Cleanup
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No data was extracted. Check your JSON structure.")

if __name__ == "__main__":
    main()
