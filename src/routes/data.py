from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import aiofiles
from models import ResponseSignal
import logging
from .schemes.data import (
    ProcessRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
)
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemes.minirag.schemes import DataChunk, Asset, Project
from models.enums.AssetTypeEnum import AssetTypeEnum
from controllers import NLPController

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.post("/projects")
async def create_project(
    request: Request,
    project_request: ProjectCreateRequest,
):
    project_name = project_request.project_name.strip()

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    existing_project = await project_model.get_project_by_name(
        project_name=project_name
    )

    if existing_project is not None:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "signal": "project name already exists"
            },
        )

    description = project_request.project_description

    if description:
        description = description.strip() or None

    project_record = Project(
        project_name=project_name,
        project_description=description,
        is_public=project_request.is_public,
    )

    project = await project_model.create_project(
        project=project_record
    )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "signal": "project created successfully",
            "project": {
                "project_id": project.project_id,
                "project_uuid": str(project.project_uuid),
                "project_name": project.project_name,
                "project_description": project.project_description,
                "is_public": project.is_public,
                "project_status": project.project_status,
            },
        },
    )


@data_router.get("/projects")
async def get_projects(
    request: Request,
    page: int = 1,
    page_size: int = 100,
):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    projects, total_pages = await project_model.get_all_projects(
        page=page,
        page_size=page_size,
    )

    return {
        "projects": [
            {
                "project_id": project.project_id,
                "project_name": project.project_name,
                "project_description": project.project_description,
                "is_public": project.is_public,
                "project_status": project.project_status,
            }
            for project in projects
        ],
        "page": page,
        "total_pages": total_pages,
    }

@data_router.patch("/projects/{project_id}")
async def update_project(
    request: Request,
    project_id: int,
    project_request: ProjectUpdateRequest,
):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project_name = project_request.project_name

    if project_name is not None:
        project_name = project_name.strip()

        if not project_name:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal": "project name cannot be empty"},
            )

        existing_project = await project_model.get_project_by_name(
            project_name=project_name
        )

        if (
            existing_project is not None
            and existing_project.project_id != project_id
        ):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"signal": "project name already exists"},
            )

    description = project_request.project_description

    if description is not None:
        description = description.strip()

    project = await project_model.update_project(
        project_id=project_id,
        project_name=project_name,
        project_description=description,
        is_public=project_request.is_public,
        project_status=project_request.project_status,
    )

    if project is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": "project not found"},
        )

    return {
        "signal": "project updated successfully",
        "project": {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "project_description": project.project_description,
            "is_public": project.is_public,
            "project_status": project.project_status,
        },
    }

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: int, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):


    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    # validate the file properties
    data_controller = DataController()

    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal.value
            }
        )

    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                # Bug: the enum name is `FILE_UPLOADED_FAILED`, not `FILE_UPLOAD_FAILED`.
                # Fix: use the actual enum member name.
                "signal": ResponseSignal.FILE_UPLOADED_FAILED.value
            }
        )

    # store the assets into the database
    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )

    asset_resource = Asset(
        asset_project_id=project.project_id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset=asset_resource)

    return JSONResponse(
            content={
                # Bug: the enum name is `FILE_UPLOADED_SUCCESS`, not `FILE_UPLOAD_SUCCESS`.
                # Fix: use the correct enum member.
                "signal": ResponseSignal.FILE_UPLOADED_SUCCESS.value,
                # Bug: later processing expects the saved filename, not the Mongo asset id.
                # Fix: return the stored asset name as `file_id`, and expose the DB id separately as `asset_id`.
                "file_id": asset_record.asset_name,
                "asset_id": str(asset_record.asset_id),
            }
        )

@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id: int, process_request: ProcessRequest):

    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.generation_client,
        template_parser=request.app.template_parser,
    )
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
        )

    project_files_ids = {}

    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(
            asset_project_id=project.project_id,
            asset_name=process_request.file_id
        )
        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value,
                }
            )
        project_files_ids = {
            asset_record.asset_id: asset_record.asset_name
        }

    else:
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value,
        )

        project_files_ids = {
            record.asset_id: record.asset_name
            for record in project_files
        }

    if len(project_files_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.NO_FILES_ERROR.value,
            }
        )

    process_controller = ProcessController(project_id=project_id)

    no_records = 0
    no_files = 0

    chunk_model = await ChunkModel.create_instance(
                        db_client=request.app.db_client
                    )

    if do_reset == 1:
        # delete associated vectors collection
        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        _ = await request.app.vectordb_client.delete_collection(collection_name=collection_name)

        # delete associated chunks
        _ = await chunk_model.delete_chunks_by_project_id(
            project_id=project.project_id
        )
    for asset_id, file_id in project_files_ids.items():

        file_content = process_controller.get_file_content(file_id=file_id)

        if file_content is None:
            logger.error(f"Error while processing file: {file_id}")
            continue

        file_chunks = process_controller.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )

        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESSING_FAILED.value
                }
            )

        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i+1,
                chunk_project_id=project.project_id,
                chunk_asset_id=asset_id
            )
            for i, chunk in enumerate(file_chunks)
        ]

        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1

    return JSONResponse(
        content={
            # Note: this endpoint only processes files into chunks in Mongo.
            # The project already uses this success enum, so we keep it for compatibility even though the name is misleading.
            "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files
        }
    )
