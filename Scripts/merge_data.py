import pandas as pd
import gdown
import os
import shutil
import sys
import json

# --- CONFIGURATION ---
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1llUw5NLQXunAc3CsP51K1Hn0D8nK4X-j"
DOWNLOAD_DIR = "downloaded_files"  # Changed name to be generic
OUTPUT_DIR = "Data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "AERO.csv")

# The specific column order you need
TARGET_COLUMNS = [
    "statusCode", "refId", "message", "payload__electorDetailDto__name",
    "payload__electorDetailDto__bloDoc1back", "payload__electorDetailDto__relationOldStateCd",
    "payload__electorDetailDto__doc1FrontCitizenGrandParent", "payload__electorDetailDto__bloDoc1Type",
    "payload__electorDetailDto__rescheduleFlg", "payload__electorDetailDto__doc1BackCitizenGrandParent",
    "payload__electorDetailDto__bloDoc2Front", "payload__electorDetailDto__rescheduleDttm",
    "payload__electorDetailDto__lastSirStateCitizen", "payload__electorDetailDto__bloDoc2back",
    "payload__electorDetailDto__bloDoc4Type", "payload__electorDetailDto__lastSirAcCitizen",
    "payload__electorDetailDto__bloDoc2Type", "payload__electorDetailDto__deliveredTo",
    "payload__electorDetailDto__relationType", "payload__electorDetailDto__bloDoc3Front",
    "payload__electorDetailDto__uploadedPhoto", "payload__electorDetailDto__doc5FrontCitizen",
    "payload__electorDetailDto__bloDoc3back", "payload__electorDetailDto__deliveredToPhoto",
    "payload__electorDetailDto__doc6FrontCitizen", "payload__electorDetailDto__bloDoc3Type",
    "payload__electorDetailDto__doc1BackCitizen", "payload__electorDetailDto__bloDoc4Front",
    "payload__electorDetailDto__doc6TypeIdCitizen", "payload__electorDetailDto__bloDoc4back",
    "payload__electorDetailDto__doc1FrontCitizen", "payload__electorDetailDto__relationOldPartNo",
    "payload__electorDetailDto__progenyLinked", "payload__electorDetailDto__proof_of_relationship_progeny_1",
    "payload__electorDetailDto__docAnomaly", "payload__electorDetailDto__proof_of_relationship_progeny_2",
    "payload__electorDetailDto__oldStateCd", "payload__electorDetailDto__blo_letter_url",
    "payload__electorDetailDto__enumDoc1Front", "payload__electorDetailDto__relationOldAcNo",
    "payload__electorDetailDto__anomalies", "payload__electorDetailDto__acNo",
    "payload__electorDetailDto__relationOldPslNo", "payload__electorDetailDto__doc1TypeIdCitizen",
    "payload__electorDetailDto__partNo", "payload__electorDetailDto__doc2TypeIdCitizen",
    "payload__electorDetailDto__hearingDatetime", "payload__electorDetailDto__doc3FrontCitizen",
    "payload__electorDetailDto__doc3TypeIdCitizen", "payload__electorDetailDto__hearingRefNo",
    "payload__electorDetailDto__doc4FrontCitizen", "payload__electorDetailDto__doc4TypeIdCitizen",
    "payload__electorDetailDto__mobileNo", "payload__electorDetailDto__doc5TypeIdCitizen",
    "payload__electorDetailDto__enumDoc4Front", "payload__electorDetailDto__lastSirState",
    "payload__electorDetailDto__enumDoc4back", "payload__electorDetailDto__lastSirAc",
    "payload__electorDetailDto__doc2FrontCitizen", "payload__electorDetailDto__enumDoc4Type",
    "payload__electorDetailDto__lastSirPart", "payload__electorDetailDto__enumDoc5Type",
    "payload__electorDetailDto__lastSirSerialNo", "payload__electorDetailDto__enumDoc2Type",
    "payload__electorDetailDto__epicId", "payload__electorDetailDto__enumDoc3Front",
    "payload__electorDetailDto__rollBackDoc1TypeId", "payload__electorDetailDto__enumDoc3back",
    "payload__electorDetailDto__rollBackDoc1Front", "payload__electorDetailDto__enumDoc3Type",
    "payload__electorDetailDto__rollBackDoc1Back", "payload__electorDetailDto__enumDoc1back",
    "payload__electorDetailDto__rollBackDoc2TypeId", "payload__electorDetailDto__doc2BackCitizen",
    "payload__electorDetailDto__enumDoc1Type", "payload__electorDetailDto__rollBackDoc2Front",
    "payload__electorDetailDto__doc3BackCitizen", "payload__electorDetailDto__enumDoc2Front",
    "payload__electorDetailDto__rollBackDoc2Back", "payload__electorDetailDto__doc4BackCitizen",
    "payload__electorDetailDto__enumDoc2back", "payload__electorDetailDto__hearingPhoto",
    "payload__electorDetailDto__doc5BackCitizen", "payload__electorDetailDto__isPresent",
    "payload__electorDetailDto__doc6BackCitizen", "payload__electorDetailDto__isDocUploaded",
    "payload__electorDetailDto__lastSirPartCitizen", "payload__electorDetailDto__lastSirSerialNoCitizen",
    "payload__electorDetailDto__lastSirFrontCitizen", "payload__electorDetailDto__lastSirBackCitizen",
    "payload__electorDetailDto__deoApproval", "payload__electorDetailDto__doc1FrontCitizenParent",
    "payload__electorDetailDto__progLimitExceed", "payload__electorDetailDto__doc1BackCitizenParent",
    "payload__electorDetailDto__proof_of_relationship_parent_1", "payload__electorDetailDto__miobApproval",
    "payload__electorDetailDto__lastSirFront", "payload__electorDetailDto__roobApproval",
    "payload__electorDetailDto__lastSirBack", "payload__electorDetailDto__attendenceSheet",
    "payload__electorDetailDto__proofOfRelationshipParent1Ero", "payload__electorDetailDto__proofOfRelationshipParent2Ero",
    "payload__electorDetailDto__proofOfRelationshipProgeny1Ero", "payload__electorDetailDto__proofOfRelationshipProgeny2Ero",
    "payload__electorDetailDto__deoRemarks", "payload__electorDetailDto__isVip",
    "payload__electorDetailDto__electorType", "payload__electorDetailDto__submittedBy",
    "payload__electorDetailDto__recommendedByBlo", "payload__electorDetailDto__generateNoticeDate",
    "payload__electorDetailDto__enumDoc5Front", "payload__electorDetailDto__uploadHearingReciept",
    "payload__electorDetailDto__preRevisionVoterDocUrl", "payload__electorDetailDto__enumDoc5back",
    "payload__electorDetailDto__miobRemarks", "payload__electorDetailDto__oldAcNo",
    "payload__electorDetailDto__enumDoc6back", "payload__electorDetailDto__presentActionPending",
    "payload__electorDetailDto__oldPartNo", "payload__electorDetailDto__enumDoc6Type",
    "payload__electorDetailDto__roobRemarks", "payload__electorDetailDto__oldPslNo",
    "payload__electorDetailDto__enumDoc6Front", "payload__electorDetailDto__miobOkNotOk",
    "payload__electorDetailDto__bloDoc1Front", "payload__electorDetailDto__roobOkNotOk",
    "payload__electorDetailDto__partSerialNo", "payload__electorDetailDto__proof_of_relationship_parent_2",
    "payload__electorDetailDto__epicNo", "payload__electorDetailDto__categoryType",
    "payload__totalCount", "payload__next"
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
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=DOWNLOAD_DIR, quiet=False, use_cookies=False)
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        sys.exit(1)

    # 3. Find ALL files (ABSOLUTELY NO EXTENSION CHECK)
    all_files = [
        os.path.join(dp, f) 
        for dp, dn, filenames in os.walk(DOWNLOAD_DIR) 
        for f in filenames
    ]

    if not all_files:
        print("❌ Error: gdown finished, but no files at all were found in the folder.")
        sys.exit(1)

    print(f"✅ Found {len(all_files)} files. Listing first 5 for debug:")
    for f in all_files[:5]:
        print(f"   - {f}")
    
    processed_dfs = []

    for filename in all_files:
        try:
            # 4. Force read as JSON
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 5. Extract the specific LIST from payload
            # Structure: payload -> electorDetailDto (List)
            elector_list = data.get('payload', {}).get('electorDetailDto', [])
            
            if not isinstance(elector_list, list) or len(elector_list) == 0:
                print(f"⚠️  File {os.path.basename(filename)} is valid JSON but has no 'electorDetailDto' list. Skipping.")
                continue

            # 6. Normalize the LIST into rows
            df = pd.json_normalize(elector_list)

            # 7. Add prefix to match your column names (payload__electorDetailDto__...)
            df = df.add_prefix('payload__electorDetailDto__')

            # 8. Add top-level fields (statusCode, message) to every row
            df['statusCode'] = data.get('statusCode')
            df['refId'] = data.get('refId')
            df['message'] = data.get('message')

            # 9. Reorder columns
            df_reordered = df.reindex(columns=TARGET_COLUMNS)
            
            processed_dfs.append(df_reordered)
            print(f"Processed: {os.path.basename(filename)} ({len(df)} rows)")

        except json.JSONDecodeError:
            print(f"⚠️  Skipping {os.path.basename(filename)}: Not a valid JSON file (likely garbage or system file).")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    # 10. Merge and Save
    if processed_dfs:
        print(f"Merging {len(processed_dfs)} dataframes...")
        final_df = pd.concat(processed_dfs, ignore_index=True)
        
        final_df.to_csv(OUTPUT_FILE, index=False, sep=';')
        
        if os.path.exists(OUTPUT_FILE):
            print(f"🎉 Success! Saved merged file to: {OUTPUT_FILE}")
            print(f"Total Rows: {len(final_df)}")
        else:
            print("❌ Error: File save failed.")
            sys.exit(1)
    else:
        print("❌ Error: No valid data extracted from any file.")
        sys.exit(1)

if __name__ == "__main__":
    main()
