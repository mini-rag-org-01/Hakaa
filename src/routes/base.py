from fastapi import FastAPI, APIRouter, Depends, Request
from models.ProjectModel import ProjectModel
import os
from helpers.config import get_settings, Settings
from datetime import datetime

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)

@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):

    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION

    return {
        "app_name": app_name,
        "app_version": app_version,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
@base_router.get("/projects")
async def get_public_projects(request: Request):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    projects = await project_model.get_public_projects()

    return {
        "projects": [
            {
                "project_id": project.project_id,
                "project_name": project.project_name,
                "project_description": project.project_description,
            }
            for project in projects
        ]
    }