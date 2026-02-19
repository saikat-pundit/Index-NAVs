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

def extract_all_pages_from_har(filepath):
    """
    Finds EVERY instance of the data API in the HAR file 
    and merges all pages into one list.
    """
    all_records = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        entries = har_data.get('log', {}).get('entries', [])
        
        found_pages = 0
        for entry in entries:
            url = entry.get('request', {}).get('url', '')
            
            # Check for the specific API endpoint
            if "findEligibleElectors" in url:
                response = entry.get('response', {})
                # Ensure the request was successful
                if response.get('status') == 200:
                    content_text = response.get('content', {}).get('text', '')
                    
                    if content_text:
                        try:
                            data = json.loads(content_text)
                            elector_list = data.get('payload', {}).get('electorDetailDto', [])
                            if isinstance(elector_list, list) and len(elector_list) > 0:
                                all_records.extend(elector_list)
                                found_pages += 1
                        except json.JSONDecodeError:
                            continue
        
        if found_pages > 0:
            print(f"  - Extracted {len(all_records)} records from {found_pages} pages in {os.path.basename(filepath)}")
        return all_records, None
        
    except Exception as e:
        return None, str(e)

def main():
    # 1. Setup
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Download
    print(f"Downloading HAR files...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    # 3. Process All Files
    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(DOWNLOAD_DIR) for f in filenames if not f.startswith('.')]
    master_record_list = []

    print(f"Processing {len(all_files)} HAR files...")

    for filename in all_files:
        records, error = extract_all_pages_from_har(filename)
        if records:
            master_record_list.extend(records)
        elif error:
            print(f"⚠️  Error in {os.path.basename(filename)}: {error}")

    # 4. Create CSV
    if master_record_list:
        df = pd.json_normalize(master_record_list, sep='__')
        
        # Ensure only TARGET_COLUMNS exist and are in the correct order
        # Missing columns will be filled with NaN
        final_df = df.reindex(columns=TARGET_COLUMNS)
        
        # Remove duplicates based on EPIC Number
        initial_count = len(final_df)
        final_df = final_df.drop_duplicates(subset=['epicNo'], keep='first')
        
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*50)
        print(f"✅ FINAL SUCCESS")
        print(f"Total Raw Records Found: {initial_count}")
        print(f"Total Unique Records:    {len(final_df)}")
        print(f"Duplicates Removed:      {initial_count - len(final_df)}")
        print(f"Output: {OUTPUT_FILE}")
        print("="*50)
        
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No voter records found in any of the HAR files.")

if __name__ == "__main__":
    main()
