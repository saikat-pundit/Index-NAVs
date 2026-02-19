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

# These will appear as the first few columns. 
# ALL other headers found in the JSONs will automatically follow these.
PRIORITY_COLUMNS = ["source_json_file", "name", "epicNo", "acNo", "partNo", "partSerialNo"]

def main():
    # 1. Setup
    if os.path.exists(DOWNLOAD_DIR): shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Download
    print(f"Downloading from Google Drive...")
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False, remaining_ok=True)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    # 3. Identify Files
    all_files = []
    for dp, dn, filenames in os.walk(DOWNLOAD_DIR):
        for f in filenames:
            if not f.startswith('.'):
                all_files.append(os.path.join(dp, f))

    processed_dfs = []
    ignored_files = []

    print(f"Scanning {len(all_files)} files...")

    # 4. Extract EVERYTHING
    for filename in all_files:
        fname = os.path.basename(filename)
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Look for the list of voters
            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            
            if elector_list and isinstance(elector_list, list):
                # Flatten the JSON. This creates columns for every key found.
                df = pd.json_normalize(elector_list, sep='__')
                
                # Tag the source
                df['source_json_file'] = fname
                processed_dfs.append(df)
            else:
                reason = "List 'electorDetailDto' is empty" if 'payload' in data else "Non-standard JSON structure"
                ignored_files.append(f"{fname}: {reason}")

        except json.JSONDecodeError:
            ignored_files.append(f"{fname}: Not a valid JSON")
        except Exception as e:
            ignored_files.append(f"{fname}: Error -> {str(e)}")

    # 5. Merge and Reveal All Headers
    if processed_dfs:
        # pd.concat merges all unique headers found across all files.
        # If File A has 'age' and File B has 'gender', the result has BOTH.
        final_df = pd.concat(processed_dfs, ignore_index=True, sort=False)

        # Reorder to keep it clean, but include 100% of discovered columns
        all_cols = list(final_df.columns)
        existing_priority = [c for c in PRIORITY_COLUMNS if c in all_cols]
        other_cols = [c for c in all_cols if c not in existing_priority]
        
        # This list contains EVERY column found
        final_df = final_df[existing_priority + other_cols]

        # 6. Save
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*50)
        print(f"✅ SUCCESS: {len(processed_dfs)} files merged.")
        print(f"📊 Total Records: {len(final_df)}")
        print(f"📋 Total Headers: {len(final_df.columns)} (All headers preserved)")
        print("="*50)

        if ignored_files:
            print(f"\n⚠️  REASON FOR MISSING DATA ({len(ignored_files)} files ignored):")
            for note in ignored_files[:15]:
                print(f" - {note}")
        
        shutil.rmtree(DOWNLOAD_DIR)
    else:
        print("❌ No data could be extracted from any file.")

if __name__ == "__main__":
    main()
