import pandas as pd
import io
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

def download_drive_file_as_string(drive_service, file_id):
    """Download file from Google Drive and return it as a string."""
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return fh.read().decode()

def filter_duplicates(historical_data, new_data):
    """Remove duplicate entries from new data based on historical data."""
    # Assuming the first two columns can be used as a composite key for uniqueness
    historical_ids = set((row[0], row[1]) for row in historical_data)
    filtered_new_data = [row for row in new_data if (row[0], row[1]) not in historical_ids]
    return filtered_new_data

def check_and_concatenate(drive_service, folder_id, new_data, file_name):
    """Check for existing file, concatenate new data, and handle duplicates."""
    response = drive_service.files().list(q=f"name='{file_name}' and '{folder_id}' in parents").execute()
    files = response.get("files", [])

    if files:
        existing_data_str = download_drive_file_as_string(drive_service, files[0]["id"])
        existing_data = [row.split(',') for row in existing_data_str.split('\n') if row]
        filtered_new_data = filter_duplicates(existing_data, new_data)
        combined_data = existing_data + filtered_new_data
    else:
        combined_data = new_data

    combined_data_str = '\n'.join([','.join(map(str, row)) for row in combined_data])
    return combined_data_str

def save_to_drive(drive_service, folder_id, combined_data_str, file_name):
    """Upload combined data string to Google Drive."""
    fh = io.BytesIO(combined_data_str.encode())
    media = MediaIoBaseUpload(fh, mimetype="text/csv", resumable=True)
    file_metadata = {"name": file_name, "parents": [folder_id]}
    
    if files:
        drive_service.files().update(fileId=files[0]["id"], body=file_metadata, media_body=media).execute()
    else:
        drive_service.files().create(body=file_metadata, media_body=media).execute()

def cloud_function_entry_point(new_data):
    """Entry point for the cloud function to concatenate and save data."""
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    SERVICE_ACCOUNT_FILE = "gcloud_utils/id2223-finals-9544f15b0a48.json"

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    drive_service = build("drive", "v3", credentials=credentials)

    folder_id = "1fUm9njnrto7mNMirssukMpcw-VnTpEKd"
    file_name = "data_full.csv"

    combined_data_str = check_and_concatenate(
        drive_service, folder_id, new_data, file_name
    )
    save_to_drive(drive_service, folder_id, combined_data_str, file_name)

    return "Data saved successfully"
