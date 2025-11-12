from fastapi import FastAPI, APIRouter, Depends
import os
from helpers.config import get_settings
BaseRouter = APIRouter(
    prefix="/api/v1",
    tags = ["api_v1"],
)

@BaseRouter.get("/")
async def welcome(): 
     
    app_settings = get_settings()
    app_name = app_settings.APP_NAME
    app_version =app_settings.APP_VERSION
    return {
        "app_name" : app_name,
        "app_version" : app_version,

    }