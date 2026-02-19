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

TARGET_COLUMNS = [
    "name", "epicNo", "acNo", "partNo", "partSerialNo", 
    "categoryType", "relationType", "progenyLinked", 
    "progLimitExceed", "docAnomaly", "anomalies", 
    "lastSirState", "lastSirAc", "lastSirPart", "lastSirSerialNo", 
    "recommendedByBlo", "deoApproval", "deoRemarks", 
    "miobApproval", "miobRemarks", "roobApproval", "roobRemarks"
]

def robust_json_load(filepath):
    """Attempts to read JSON files even with hidden characters or encoding issues."""
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
            if not raw:
                return None, "File is empty"
        
        # Try UTF-8 with BOM first (handles hidden Windows characters)
        try:
            content = raw.decode('utf-8-sig').strip()
            return json.loads(content), None
        except json.JSONDecodeError:
            pass
            
        # Try standard UTF-8 if that fails
        content = raw.decode('utf-8', errors='ignore').strip()
        return json.loads(content), None
        
    except json.JSONDecodeError as e:
        # Capture a snippet of the file to see why it failed
        snippet = str(raw[:50])
        return None, f"Invalid JSON format near: {snippet}"
    except Exception as e:
        return None, str(e)

def main():
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Downloading from Drive...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(DOWNLOAD_DIR) for f in filenames if not f.startswith('.')]

    processed_dfs = []
    failed_details = []

    print(f"Analyzing {len(all_files)} files...")

    for filename in all_files:
        fname = os.path.basename(filename)
        data, error = robust_json_load(filename)
        
        if data:
            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            if elector_list and isinstance(elector_list, list):
                df = pd.json_normalize(elector_list, sep='__')
                df_filtered = df.reindex(columns=TARGET_COLUMNS)
                processed_dfs.append(df_filtered)
            else:
                failed_details.append(f"{fname}: Valid JSON but 'electorDetailDto' key missing/empty")
        else:
            failed_details.append(f"{fname}: {error}")

    if processed_dfs:
        final_df = pd.concat(processed_dfs, ignore_index=True, sort=False)
        final_df = final_df[TARGET_COLUMNS] # Final column lock
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*50)
        print(f"✅ SUCCESS: {len(processed_dfs)} files merged.")
        print(f"📊 Total Records: {len(final_df)}")
        print("="*50)

        if failed_details:
            print(f"\n⚠️  STRUCTURAL ISSUES FOUND IN {len(failed_details)} FILES:")
            for issue in failed_details:
                print(f" - {issue}")
        
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No valid data extracted. Look at the issues listed above.")

if __name__ == "__main__":
    main()
