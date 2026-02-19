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

# Strictly these columns will be exported
TARGET_COLUMNS = [
    "name", "epicNo", "acNo", "partNo", "partSerialNo", 
    "categoryType", "relationType", "progenyLinked", 
    "progLimitExceed", "docAnomaly", "anomalies", 
    "lastSirState", "lastSirAc", "lastSirPart", "lastSirSerialNo", 
    "recommendedByBlo", "deoApproval", "deoRemarks", 
    "miobApproval", "miobRemarks", "roobApproval", "roobRemarks"
]

def extract_from_har(filepath):
    """Parses HAR file and extracts the JSON text from the response content."""
    extracted_records = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        entries = har_data.get('log', {}).get('entries', [])
        
        for entry in entries:
            url = entry.get('request', {}).get('url', '')
            # Filter for the specific API call that contains the voter data
            if "findEligibleElectors" in url:
                content_text = entry.get('response', {}).get('content', {}).get('text', '')
                
                if content_text:
                    try:
                        # The 'text' inside a HAR is usually a stringified JSON
                        data = json.loads(content_text)
                        elector_list = data.get('payload', {}).get('electorDetailDto', [])
                        if isinstance(elector_list, list):
                            extracted_records.extend(elector_list)
                    except json.JSONDecodeError:
                        continue
                        
        return extracted_records, None
    except Exception as e:
        return None, str(e)

def main():
    # 1. Setup Workspace
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Download from Drive
    print(f"Downloading .har files from Drive...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    all_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(DOWNLOAD_DIR) for f in filenames if not f.startswith('.')]
    all_extracted_data = []

    print(f"Processing {len(all_files)} files...")

    # 3. Process each file
    for filename in all_files:
        records, error = extract_from_har(filename)
        if records:
            all_extracted_data.extend(records)
        elif error:
            print(f"⚠️  Skipping {os.path.basename(filename)}: {error}")

    # 4. Merge and Filter
    if all_extracted_data:
        # Convert to DataFrame
        df = pd.json_normalize(all_extracted_data, sep='__')
        
        # Lock to your TARGET_COLUMNS
        # reindex ensures if a column is missing in the HAR, it's created as empty
        final_df = df.reindex(columns=TARGET_COLUMNS)
        
        # Save to CSV
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*50)
        print(f"✅ SUCCESS: Data extracted from .har files.")
        print(f"📊 Total Records Found: {len(final_df)}")
        print(f"📋 File Saved: {OUTPUT_FILE}")
        print("="*50)
        
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No voter data found. Ensure the HAR files contain 'findEligibleElectors' requests.")

if __name__ == "__main__":
    main()
