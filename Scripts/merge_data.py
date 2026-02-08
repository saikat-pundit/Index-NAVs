import pandas as pd
import gdown
import glob
import os
import shutil

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
    
    # 3. Download files using gdown (handles public drive folders)
    # Note: If the folder is huge, this might take time.
    try:
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=OUTPUT_DIR, quiet=False, use_cookies=False)
    except Exception as e:
        print(f"Error downloading folder: {e}")
        return

    # 4. Process CSVs
    all_files = glob.glob(os.path.join(OUTPUT_DIR, "*.csv"))
    
    if not all_files:
        print("No CSV files found in the downloaded folder.")
        return

    print(f"Found {len(all_files)} CSV files. Processing...")
    
    processed_dfs = []

    for filename in all_files:
        try:
            # Read CSV
            df = pd.read_csv(filename)
            
            # 5. Rearrange Columns
            # reindex(columns=...) does two things:
            # a. Reorders the columns to match the list.
            # b. If a column is missing in the file, it adds it with NaN (blank) values.
            # c. If the file has extra columns not in the list, they are dropped.
            df_reordered = df.reindex(columns=TARGET_COLUMNS)
            
            processed_dfs.append(df_reordered)
            print(f"Processed: {os.path.basename(filename)}")
            
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

    # 6. Merge and Save
    if processed_dfs:
        print("Merging all files...")
        final_df = pd.concat(processed_dfs, ignore_index=True)
        
        final_df.to_csv(MERGED_FILENAME, index=False, sep=';') # Using semi-colon separator based on your input style, change to ',' if needed
        print(f"Success! Saved merged file to: {MERGED_FILENAME}")
    else:
        print("No dataframes to merge.")

if __name__ == "__main__":
    main()
