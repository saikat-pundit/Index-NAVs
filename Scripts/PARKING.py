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

def deep_scan_har(filepath):
    """
    Scans every entry in a HAR file for voter data, 
    ignoring URL filters to ensure no data is missed.
    """
    all_records = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        entries = har_data.get('log', {}).get('entries', [])
        
        for entry in entries:
            response = entry.get('response', {})
            content = response.get('content', {})
            text = content.get('text', '')
            
            if text and "electorDetailDto" in text:
                try:
                    # Parse the stringified JSON inside the HAR
                    data = json.loads(text)
                    
                    # Dig into the payload
                    # We use a recursive search or direct path
                    payload = data.get('payload', {})
                    if isinstance(payload, dict):
                        elector_list = payload.get('electorDetailDto', [])
                        if isinstance(elector_list, list):
                            all_records.extend(elector_list)
                except Exception:
                    continue
        
        return all_records, None
    except Exception as e:
        return None, str(e)

def main():
    # 1. Setup
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Download
    print(f"Downloading files...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    # 3. Process All Files
    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(DOWNLOAD_DIR) for f in filenames if not f.startswith('.')]
    master_list = []

    print(f"Processing {len(all_files)} HAR files...")

    for filename in all_files:
        records, error = deep_scan_har(filename)
        if records:
            print(f"  ✅ Found {len(records)} records in {os.path.basename(filename)}")
            master_list.extend(records)
        else:
            print(f"  ⚠️  No records found in {os.path.basename(filename)}")

    # 4. Save to CSV
    if master_list:
        df = pd.json_normalize(master_list, sep='__')
        
        # Ensure all requested columns exist
        final_df = df.reindex(columns=TARGET_COLUMNS)
        
        # Deduplicate by EPIC number
        initial_len = len(final_df)
        final_df = final_df.drop_duplicates(subset=['epicNo'], keep='first')
        
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*50)
        print(f"✅ FINAL SUCCESS")
        print(f"Total Rows Extracted: {initial_len}")
        print(f"Total Unique Rows:    {len(final_df)}")
        print(f"Output File: {OUTPUT_FILE}")
        print("="*50)
        
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ FAILED: No 'electorDetailDto' keys were found in any file.")

if __name__ == "__main__":
    main()
