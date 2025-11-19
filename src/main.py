from fastapi import FastAPI
from routes import base 
from routes import data 
from motor.motor_asyncio import AsyncIOMotorClient

#to call database name/url
from helpers.config import get_settings

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    settings = get_settings()
    # create conniction 
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client =  app.mongo_conn [settings.MONGODB_DATABASE]


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongo_conn.close()



app.include_router(base.base_router)
app.include_router(data.data_router)
