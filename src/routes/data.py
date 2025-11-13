from fastapi import FastAPI, APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
import os 
from models import ResponseSignal
import aiofiles
from helpers.config import get_settings, Settings
from controllers import DataControler, ProjectController
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1/data"],
)
# upload : recieve file and upload it on our sever.

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str,file : UploadFile, 
                      app_settings: Settings = Depends(get_settings)):
    
    
    # validate the file properties
    is_valid, result_signal = DataControler().validate_uploaded_file(file = file)
    if not is_valid:
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content= {
                "signal": result_signal.value
            }
        )
    # access to file 
    project_dir_path = ProjectController().get_project_path(project_id= project_id)
    file_path = os.path.join(
        project_dir_path,
        file.filename
    )
    # open file and write 
    async with aiofiles.open(file_path , "wb") as f:
       # read cunk by chunk
        while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
            # write chunk 
            await f.write(chunk)
    return JSONResponse(
            content= {
                "signal": ResponseSignal.FILE_UPLOADED_SUCCESS.value
            }
        )