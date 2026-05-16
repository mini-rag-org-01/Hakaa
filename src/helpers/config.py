from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    OPEN_API_KEY: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    POSTRGRES_USERNAME:str
    POSTRGRES_PASSWORD:str
    POSTRGRES_HOST:str
    POSTRGRES_PORT:int
    POSTRGRES_MAIN_DATABASE:str

    GENERATION_BACKEND : str
    EMBEDDING_BACKEND : str

    OPENAI_API_KEY : str = None
    OPENAI_API_URL_LITERAL : List[str] = []
    OPENAI_API_URL : str = None 
    COHERE_API_KEY : str = None

    GENERATION_MODEL_ID : str = None
    GENERATION_MODEL_ID_LITERAL : List[str] = []
    EMBEDDING_MODEL_ID : str = None

    EMBEDDING_MODEL_SIZE : int = None

    INPUT_DEFAULT_MAX_CHARACTERS: int = None
    GENERATION_DEFAULT_MAX_TOKENS: int = None
    GENERATION_DEFAULT_TEMPRATURE: float = None

    VECTOR_DB_BACKEND_LITERAL:  List[str] = []
    VECTOR_DB_BACKEND : str
    VECTOR_DB_PATH : str
    VECTOR_DB_DISTANCE_METHOD: str = None
    VECTOR_DB_INDEX_THRESHOLD: int = 100


    PRIMARY_LANG: str 
    DEFAULT_LANG : str 




    class Config:
        env_file = ".env"

def get_settings():
    return Settings()