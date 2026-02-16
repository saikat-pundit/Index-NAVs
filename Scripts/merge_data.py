import pandas as pd
import gdown
import os
import shutil
import sys
import json

# --- CONFIGURATION ---
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1llUw5NLQXunAc3CsP51K1Hn0D8nK4X-j"
DOWNLOAD_DIR = "downloaded_files"  # Changed name to be generic
OUTPUT_DIR = "Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "AERO.csv")

# The specific column order you need
TARGET_COLUMNS = [
    "payload__electorDetailDto__name", "payload__electorDetailDto__epicNo", "payload__electorDetailDto__acNo", "payload__electorDetailDto__partNo", "payload__electorDetailDto__partSerialNo", "payload__electorDetailDto__relationType", "payload__electorDetailDto__progenyLinked", "payload__electorDetailDto__progLimitExceed", "payload__electorDetailDto__docAnomaly", "payload__electorDetailDto__anomalies", "payload__electorDetailDto__lastSirState", "payload__electorDetailDto__lastSirAc", "payload__electorDetailDto__lastSirPart", "payload__electorDetailDto__lastSirSerialNo", "payload__electorDetailDto__recommendedByBlo", "payload__electorDetailDto__deoApproval", "payload__electorDetailDto__deoRemarks", "payload__electorDetailDto__miobApproval", "payload__electorDetailDto__miobRemarks", "payload__electorDetailDto__roobApproval", "payload__electorDetailDto__roobRemarks"
]

def main():
    # 1. Setup Directories
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. Download from Drive
    print(f"Downloading folder from Google Drive...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False)
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        sys.exit(1)

    # 3. Find ALL files (ABSOLUTELY NO EXTENSION CHECK)
    all_files = [
        os.path.join(dp, f) 
        for dp, dn, filenames in os.walk(DOWNLOAD_DIR) 
        for f in filenames
    ]

    if not all_files:
        print("❌ Error: gdown finished, but no files at all were found in the folder.")
        sys.exit(1)

    print(f"✅ Found {len(all_files)} files. Listing first 5 for debug:")
    for f in all_files[:5]:
        print(f"   - {f}")
    
    processed_dfs = []

    for filename in all_files:
        try:
            # 4. Force read as JSON
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 5. Extract the specific LIST from payload
            # Structure: payload -> electorDetailDto (List)
            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            
            if not isinstance(elector_list, list) or len(elector_list) == 0:
                print(f"⚠️  File {os.path.basename(filename)} is valid JSON but has no 'electorDetailDto' list. Skipping.")
                continue

            # 6. Normalize the LIST into rows
            df = pd.json_normalize(elector_list)

            # 7. Add prefix to match your column names (payload__electorDetailDto__...)
            df = df.add_prefix('payload__electorDetailDto__')

            # 8. Add top-level fields (statusCode, message) to every row
            df['statusCode'] = data.get('statusCode')
            df['refId'] = data.get('refId')
            df['message'] = data.get('message')

            # 9. Reorder columns
            df_reordered = df.reindex(columns=TARGET_COLUMNS)
            
            processed_dfs.append(df_reordered)
            print(f"Processed: {os.path.basename(filename)} ({len(df)} rows)")

        except json.JSONDecodeError:
            print(f"⚠️  Skipping {os.path.basename(filename)}: Not a valid JSON file (likely garbage or system file).")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    # 10. Merge and Save
    if processed_dfs:
        print(f"Merging {len(processed_dfs)} dataframes...")
        final_df = pd.concat(processed_dfs, ignore_index=True)
        
        final_df.to_csv(OUTPUT_FILE, index=False, sep=';')
        
        if os.path.exists(OUTPUT_FILE):
            print(f"🎉 Success! Saved merged file to: {OUTPUT_FILE}")
            print(f"Total Rows: {len(final_df)}")
        else:
            print("❌ Error: File save failed.")
            sys.exit(1)
    else:
        print("❌ Error: No valid data extracted from any file.")
        sys.exit(1)

if __name__ == "__main__":
    main()
