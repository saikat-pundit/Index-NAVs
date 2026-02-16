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

# The specific column order required for the CSV
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
    # 1. Setup Directories: Clean old downloads and create output folder
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. Download folder from Google Drive
    print(f"Connecting to Google Drive...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False)
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        sys.exit(1)

    # 3. Collect all files from the downloaded folder
    all_files = []
    for root, dirs, files in os.walk(DOWNLOAD_DIR):
        for name in files:
            all_files.append(os.path.join(root, name))

    if not all_files:
        print("❌ Error: No files were found in the download directory.")
        sys.exit(1)

    processed_dfs = []

    # 4. Process each file
    print(f"Processing {len(all_files)} files...")
    for filename in all_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Access the specific list in the JSON structure
            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            
            if not isinstance(elector_list, list) or len(elector_list) == 0:
                continue

            # Convert the list of dictionaries to a DataFrame
            df = pd.DataFrame(elector_list)
            
            # Apply the prefix to match TARGET_COLUMNS
            df = df.add_prefix('payload__electorDetailDto__')

            # Reorder columns and fill missing ones with empty strings
            df_reordered = df.reindex(columns=TARGET_COLUMNS).fillna('')
            
            processed_dfs.append(df_reordered)

        except json.JSONDecodeError:
            # Skip non-JSON files (like system files)
            continue
        except Exception as e:
            print(f"⚠️ Warning: Could not process {os.path.basename(filename)}: {e}")

    # 5. Combine and Save to CSV
    if processed_dfs:
        final_df = pd.concat(processed_dfs, ignore_index=True)
        
        # Save as COMMA SEPARATED using sep=','
        # utf-8-sig helps Excel handle special characters/languages correctly
        final_df.to_csv(OUTPUT_FILE, index=False, sep=',', encoding='utf-8-sig')
        
        print("-" * 30)
        print(f"🎉 SUCCESS!")
        print(f"File Saved: {OUTPUT_FILE}")
        print(f"Total Rows: {len(final_df)}")
        print("-" * 30)
    else:
        print("❌ Error: No valid data found to export.")

if __name__ == "__main__":
    main()
