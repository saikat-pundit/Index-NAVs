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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "AERO.csv")

TARGET_COLUMNS = [
    "payload__electorDetailDto__name", "payload__electorDetailDto__epicNo", 
    "payload__electorDetailDto__acNo", "payload__electorDetailDto__partNo", 
    "payload__electorDetailDto__partSerialNo", "payload__electorDetailDto__categoryType" ,"payload__electorDetailDto__relationType", 
    "payload__electorDetailDto__progenyLinked", "payload__electorDetailDto__progLimitExceed", 
    "payload__electorDetailDto__docAnomaly", "payload__electorDetailDto__anomalies", 
    "payload__electorDetailDto__lastSirState", "payload__electorDetailDto__lastSirAc", 
    "payload__electorDetailDto__lastSirPart", "payload__electorDetailDto__lastSirSerialNo", 
    "payload__electorDetailDto__recommendedByBlo", "payload__electorDetailDto__deoApproval", 
    "payload__electorDetailDto__deoRemarks", "payload__electorDetailDto__miobApproval", 
    "payload__electorDetailDto__miobRemarks", "payload__electorDetailDto__roobApproval", 
    "payload__electorDetailDto__roobRemarks"
]

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

            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            if not elector_list:
                continue

            df = pd.DataFrame(elector_list)
            df = df.add_prefix('payload__electorDetailDto__')
            df_reordered = df.reindex(columns=TARGET_COLUMNS).fillna('')
            processed_dfs.append(df_reordered)

        except (json.JSONDecodeError, Exception):
            continue

    # 5. Merge and Remove Duplicates
    if processed_dfs:
        final_df = pd.concat(processed_dfs, ignore_index=True)
        
        initial_count = len(final_df)

        # --- DUPLICATE REMOVAL LOGIC ---
        # Option A: Remove rows where the EPIC number is the same (Safest for voter data)
        final_df = final_df.drop_duplicates(subset=['payload__electorDetailDto__epicNo'], keep='first')
        
        # Option B: Use this instead if you only want to remove 100% identical rows:
        # final_df = final_df.drop_duplicates(keep='first')
        
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
