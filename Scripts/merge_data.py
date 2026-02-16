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

# The specific column order you need
TARGET_COLUMNS = [
    "payload__electorDetailDto__name", "payload__electorDetailDto__epicNo", 
    "payload__electorDetailDto__acNo", "payload__electorDetailDto__partNo", 
    "payload__electorDetailDto__partSerialNo", "payload__electorDetailDto__relationType", 
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
    print(f"Downloading folder from Google Drive...")
    try:
        # Note: gdown folder download requires the folder to be accessible/public or auth configured
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False)
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        sys.exit(1)

    # 3. Find ALL files
    all_files = []
    for root, dirs, files in os.walk(DOWNLOAD_DIR):
        for name in files:
            all_files.append(os.path.join(root, name))

    if not all_files:
        print("❌ Error: No files found in the download directory.")
        sys.exit(1)

    processed_dfs = []

    for filename in all_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 4. Extract list and normalize
            # We target the list directly
            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            
            if not isinstance(elector_list, list) or len(elector_list) == 0:
                continue

            # 5. Create DataFrame and Prefix Columns
            # We prefix with 'payload__electorDetailDto__' to match your TARGET_COLUMNS
            df = pd.DataFrame(elector_list)
            df = df.add_prefix('payload__electorDetailDto__')

            # 6. Reindex to ensure all TARGET_COLUMNS exist (fills missing with NaN)
            df_reordered = df.reindex(columns=TARGET_COLUMNS)
            
            processed_dfs.append(df_reordered)
            print(f"✅ Processed: {os.path.basename(filename)} ({len(df)} rows)")

        except json.JSONDecodeError:
            pass # Skip non-json files quietly
        except Exception as e:
            print(f"⚠️ Error processing {os.path.basename(filename)}: {e}")

    # 7. Merge and Save
    if processed_dfs:
        print(f"\nMerging {len(processed_dfs)} files...")
        final_df = pd.concat(processed_dfs, ignore_index=True)
        
        # Save using comma or semicolon based on your preference; you used ';' in original
        final_df.to_csv(OUTPUT_FILE, index=False, sep=';', encoding='utf-8-sig')
        
        print(f"🚀 Success! Saved merged file to: {OUTPUT_FILE}")
        print(f"Total Records: {len(final_df)}")
    else:
        print("❌ Error: No valid data was extracted.")

if __name__ == "__main__":
    main()
