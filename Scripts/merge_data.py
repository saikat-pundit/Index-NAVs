import pandas as pd
import gdown
import glob
import os
import shutil
import sys  # Added to force-fail the script if things go wrong

# 1. Configuration
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1llUw5NLQXunAc3CsP51K1Hn0D8nK4X-j"
OUTPUT_DIR = "downloaded_data"
MERGED_FILENAME = "merged_output.csv"

# The specific column order you requested
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
    # 2. Setup environment
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    print(f"Downloading folder from Google Drive...")
    
    # 3. Download files
    try:
        # Added quiet=False to see download progress in logs
        downloaded = gdown.download_folder(url=DRIVE_FOLDER_URL, output=OUTPUT_DIR, quiet=False, use_cookies=False)
        
        # Check if download actually returned anything
        if downloaded is None or len(downloaded) == 0:
            print("❌ Error: gdown returned no files. Download likely failed.")
            sys.exit(1) # Fail the script
            
    except Exception as e:
        print(f"❌ Critical Error downloading folder: {e}")
        sys.exit(1) # Fail the script

    # 4. Process CSVs
    all_files = glob.glob(os.path.join(OUTPUT_DIR, "**/*.csv"), recursive=True)
    
    if not all_files:
        print("❌ Error: Download finished, but NO .csv files were found in the folder.")
        # Debug: list what was actually downloaded
        print("Files found in directory:")
        for root, dirs, files in os.walk(OUTPUT_DIR):
             for file in files:
                 print(os.path.join(root, file))
        sys.exit(1) # Fail the script

    print(f"✅ Found {len(all_files)} CSV files. Processing...")
    
    processed_dfs = []

    for filename in all_files:
        try:
            df = pd.read_csv(filename)
            df_reordered = df.reindex(columns=TARGET_COLUMNS)
            processed_dfs.append(df_reordered)
            print(f"Processed: {os.path.basename(filename)}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to process {filename}: {e}")

    # 6. Merge and Save
    if processed_dfs:
        print("Merging all files...")
        final_df = pd.concat(processed_dfs, ignore_index=True)
        final_df.to_csv(MERGED_FILENAME, index=False, sep=';')
        
        # Verify file exists
        if os.path.exists(MERGED_FILENAME):
            print(f"🎉 Success! Saved merged file to: {MERGED_FILENAME}")
            print(f"File size: {os.path.getsize(MERGED_FILENAME)} bytes")
        else:
            print("❌ Error: Code finished but file was not found on disk.")
            sys.exit(1)
    else:
        print("❌ Error: No dataframes were successfully processed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
