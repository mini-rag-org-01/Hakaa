from enum import Enum


class DataBaseEnum(Enum):
    
    COLLECTION_PROJECT_NAME = "projects"
    COLLECTION_CHUNK_NAME = "chunks"
    # Bug: AssetModel referenced `COLLECTION_ASSET_NAME`, but the enum did not define it.
    # Fix: add the missing collection name used for uploaded file metadata.
    COLLECTION_ASSET_NAME = "assets"



