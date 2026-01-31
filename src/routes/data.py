from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os 
from models import ResponseSignal
import aiofiles
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import logging
from .schemes.data import ProcessRequest
from models.ProjectModel import ProjectModel

logger = logging.getLogger('uvicorn.error')
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1/data"],
)
# upload : recieve file and upload it on our sever.

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request ,project_id: str,file : UploadFile, 
                      app_settings: Settings = Depends(get_settings)):
    
    project_model =ProjectModel(
        db_client= request.app.db_client
    )

    
    project = await project_model.get_project_or_create_one(
        project_id = project_id 
    )



    # validate the file properties
    data_controller = DataController()

    is_valid, result_signal = data_controller.validate_uploaded_file(file = file)
    if not is_valid:
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content= {
                "signal": result_signal.value,
                "file_id" : file_id,
                "project_id": str(project_id)
            }
        )
    # access to file 
    project_dir_path = ProjectController().get_project_path(project_id= project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name = file.filename,
        project_id= project_id
    )
    try:
    # open file and write 
        async with aiofiles.open(file_path , "wb") as f:
        # read cunk by chunk
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                # write chunk 
                await f.write(chunk)
    except Exception as e:
        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value,
                "file_id" : file_id

            }
        )


    return JSONResponse(
            content= {
                "signal": ResponseSignal.FILE_UPLOADED_SUCCESS.value,
                "file_id" : file_id,
                "project_id": str(project_id)

            }
        )


@data_router.post("/process/{project_id}")
async def process_endpoint(project_id:str, process_request : ProcessRequest ):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    process_controller = ProcessController(project_id=project_id)

    file_content = process_controller.get_file_content(file_id=file_id)


    file_chunks = process_controller.process_file_content(
        file_content = file_content,
        file_id = file_id,
        chunk_size = chunk_size,
        overlap_size = overlap_size
    )


    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESSING_FAILED.value
            }
        )

    return file_chunks