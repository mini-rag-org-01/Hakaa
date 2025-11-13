from fastapi import FastAPI, APIRouter, Depends, UploadFile
from helpers.config import get_settings, Settings
from controllers import DataControler
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1/data"],
)
# upload : recieve file and upload it on our sever.

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str,file : UploadFile, 
                      app_settings: Settings = Depends(get_settings)):
    
    
    # validate the file properties
    is_valid = DataControler().validate_uploaded_file(file = file)
    return is_valid