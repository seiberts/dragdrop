from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from azure.storage.blob import BlobServiceClient
import uuid
import os
import asyncio
import ssl

# Ensure SSL is available
try:
    ssl.create_default_context()
except AttributeError:
    raise ImportError("The ssl module is required but not available in your environment.")

# Azure Storage Configuration
AZURE_STORAGE_CONNECTION_STRING = "your_connection_string_here"
CONTAINER_NAME = "your_container_name_here"

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

app = FastAPI()

def upload_file_to_blob(file: UploadFile, folder: str):
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=f"{folder}/{file.filename}")
    blob_client.upload_blob(file.file.read(), overwrite=True)

def trigger_aml_pipeline(guid: str):
    # Fire-and-forget AML REST call
    print(f"AML pipeline triggered for GUID: {guid}")

@app.post("/upload/")
async def upload_files(background_tasks: BackgroundTasks, files: list[UploadFile] = File(...)):
    guid = str(uuid.uuid4())
    folder = guid  # Use GUID as folder name in Azure Storage
    
    for file in files:
        upload_file_to_blob(file, folder)
    
    # Fire off AML pipeline
    background_tasks.add_task(trigger_aml_pipeline, guid)
    
    return {"guid": guid, "message": "Files uploaded successfully."}

@app.get("/retrieve/{guid}")
def retrieve_files(guid: str):
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    blobs = container_client.list_blobs(name_starts_with=guid)
    
    file_names = [blob.name.split("/")[-1] for blob in blobs]
    if not file_names:
        raise HTTPException(status_code=404, detail="No files found for the provided GUID.")
    
    return {"guid": guid, "files": file_names}
