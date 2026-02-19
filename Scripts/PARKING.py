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

def deep_scan_har(filepath):
    all_records = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            har_data = json.load(f)
        
        entries = har_data.get('log', {}).get('entries', [])
        
        for entry in entries:
            text = entry.get('response', {}).get('content', {}).get('text', '')
            if not text or "electorDetailDto" not in text:
                continue

            extracted_list = None
            
            # METHOD 1: Standard JSON Load
            try:
                data = json.loads(text)
                extracted_list = data.get('payload', {}).get('electorDetailDto', [])
            except:
                # METHOD 2: Handle Escaped JSON (The \" issue)
                try:
                    # Remove backslash escapes if they are literal strings
                    fixed_text = text.replace('\\"', '"').replace('\\\\', '\\')
                    data = json.loads(fixed_text)
                    extracted_list = data.get('payload', {}).get('electorDetailDto', [])
                except:
                    # METHOD 3: Regex extraction (The "Brute Force" method)
                    # This finds the list even if the surrounding JSON is totally broken
                    match = re.search(r'\"electorDetailDto\"\s*:\s*(\[.*?\])(?=\s*\}|\s*,)', text, re.DOTALL)
                    if match:
                        try:
                            extracted_list = json.loads(match.group(1))
                        except:
                            pass

            if extracted_list and isinstance(extracted_list, list):
                all_records.extend(extracted_list)
        
        return all_records, None
    except Exception as e:
        return None, str(e)

def main():
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Downloading files...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(DOWNLOAD_DIR) for f in filenames if not f.startswith('.')]
    master_list = []

    print(f"Processing {len(all_files)} files...")

    for filename in all_files:
        records, error = deep_scan_har(filename)
        if records:
            print(f"  ✅ SUCCESS: Found {len(records)} records in {os.path.basename(filename)}")
            master_list.extend(records)
        else:
            print(f"  ⚠️  FAILED: No records found in {os.path.basename(filename)}")

    if master_list:
        df = pd.json_normalize(master_list, sep='__')
        final_df = df.reindex(columns=TARGET_COLUMNS)
        
        initial_len = len(final_df)
        final_df = final_df.drop_duplicates(subset=['epicNo'], keep='first')
        
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*50)
        print(f"✅ FINAL SUCCESS")
        print(f"Total Records Found: {initial_len}")
        print(f"Total Unique Rows:    {len(final_df)}")
        print(f"Duplicates Removed:   {initial_len - len(final_df)}")
        print(f"Output: {OUTPUT_FILE}")
        print("="*50)
        
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ CRITICAL ERROR: Could not extract data. The 'text' field format is unrecognized.")

if __name__ == "__main__":
    main()
