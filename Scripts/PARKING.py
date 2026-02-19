import pandas as pd
import gdown
import os
import shutil
import sys
import json
import re

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

def repair_and_load_json(filepath):
    """Attempts to extract the voter list even if the JSON file is broken/truncated."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Regex Strategy: Find everything between "electorDetailDto":[ and the last ]
        # This bypasses broken headers or missing closing braces at the end of the file
        match = re.search(r'\"electorDetailDto\"\s*:\s*(\[.*\])', content, re.DOTALL)
        
        if match:
            json_string = match.group(1)
            # Try to parse the extracted list
            try:
                return json.loads(json_string), None
            except json.JSONDecodeError:
                # If it's still broken (truncated), try to force-close the brackets
                try:
                    return json.loads(json_string + "]"), None
                except:
                    pass
                return None, "Truncated list could not be repaired"
        
        return None, "Could not find 'electorDetailDto' list in file"
    except Exception as e:
        return None, str(e)

def main():
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Downloading files from Drive...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(DOWNLOAD_DIR) for f in filenames if not f.startswith('.')]
    processed_dfs = []
    failed_details = []

    print(f"Repairing and analyzing {len(all_files)} files...")

    for filename in all_files:
        fname = os.path.basename(filename)
        # Use the repair function instead of standard json.load
        elector_list, error = repair_and_load_json(filename)
        
        if elector_list and isinstance(elector_list, list):
            df = pd.json_normalize(elector_list, sep='__')
            # Ensure only the columns you want exist
            df_filtered = df.reindex(columns=TARGET_COLUMNS)
            processed_dfs.append(df_filtered)
        else:
            failed_details.append(f"{fname}: {error}")

    if processed_dfs:
        final_df = pd.concat(processed_dfs, ignore_index=True, sort=False)
        final_df = final_df[TARGET_COLUMNS] 
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*50)
        print(f"✅ SUCCESS: {len(processed_dfs)} files recovered/processed.")
        print(f"📊 Total Records: {len(final_df)}")
        print("="*50)

        if failed_details:
            print(f"\n⚠️  REMAINING ISSUES ({len(failed_details)} files):")
            for issue in failed_details:
                print(f" - {issue}")
        
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No data could be recovered. The files might be severely corrupted.")

if __name__ == "__main__":
    main()
