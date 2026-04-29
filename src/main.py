from fastapi import FastAPI
from routes import base, data, nlp
from motor.motor_asyncio import AsyncIOMotorClient
#to call database name/url
from helpers.config import get_settings
from stores.LLM.LLMProviderFActory import LLMProviderfactory
#import provider factory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory


app = FastAPI()

@app.on_event("startup")
async def startup_span():
    settings = get_settings()
    # create conniction 
    app.mongo_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client =  app.mongo_conn [settings.MONGODB_DATABASE]

    llm_provider_factory = LLMProviderfactory(settings)
    vectordb_provider_factory = VectorDBProviderFactory(settings)

    #generate client
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

    # embedding client 
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                             embedding_size=settings.EMBEDDING_MODEL_SIZE)
    

    # vectordb client 
    app.vectordb_client = vectordb_provider_factory.create(
        provider=settings.VECTOR_DB_BACKEND
    )
    app.vectordb_client.connect()



@app.on_event("shutdown")
async def shutdown_span():
    app.mongo_conn.close()
    app.vectordb_client.disconnect()



app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
