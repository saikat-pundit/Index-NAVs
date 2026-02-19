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

# ONLY these columns will be exported to the CSV
TARGET_COLUMNS = [
    "name", "epicNo", "acNo", "partNo", "partSerialNo", 
    "categoryType", "relationType", "progenyLinked", 
    "progLimitExceed", "docAnomaly", "anomalies", 
    "lastSirState", "lastSirAc", "lastSirPart", "lastSirSerialNo", 
    "recommendedByBlo", "deoApproval", "deoRemarks", 
    "miobApproval", "miobRemarks", "roobApproval", "roobRemarks"
]

def main():
    # 1. Setup
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Download from Drive
    print(f"Downloading files...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    # 3. Identify Files (No extension restriction)
    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(DOWNLOAD_DIR) for f in filenames if not f.startswith('.')]

    processed_dfs = []
    ignored_files = []

    print(f"Processing {len(all_files)} files...")

    # 4. Extract and Filter
    for filename in all_files:
        fname = os.path.basename(filename)
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            
            if elector_list and isinstance(elector_list, list):
                # Flatten the JSON
                df = pd.json_normalize(elector_list, sep='__')
                
                # Reindex ensures only TARGET_COLUMNS exist. 
                # If a column is missing in the JSON, it's added as empty.
                df_filtered = df.reindex(columns=TARGET_COLUMNS)
                processed_dfs.append(df_filtered)
            else:
                ignored_files.append(f"{fname}: Empty or missing 'electorDetailDto'")

        except (json.JSONDecodeError, ValueError):
            ignored_files.append(f"{fname}: Not a valid JSON")
        except Exception as e:
            ignored_files.append(f"{fname}: {str(e)}")

    # 5. Merge and Save
    if processed_dfs:
        # Concatenate all valid results
        final_df = pd.concat(processed_dfs, ignore_index=True, sort=False)

        # Final check to ensure columns are in the EXACT order requested
        final_df = final_df[TARGET_COLUMNS]

        # Save to CSV
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*50)
        print(f"✅ SUCCESS: {len(processed_dfs)} files merged into CSV.")
        print(f"📊 Total Records: {len(final_df)}")
        print(f"📋 Columns Exported: {len(TARGET_COLUMNS)}")
        print("="*50)

        if ignored_files:
            print(f"\n⚠️  DIAGNOSTIC - {len(ignored_files)} FILES IGNORED:")
            for note in ignored_files[:10]:
                print(f" - {note}")
        
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No data extracted. Please check the JSON structure of your files.")

if __name__ == "__main__":
    main()
