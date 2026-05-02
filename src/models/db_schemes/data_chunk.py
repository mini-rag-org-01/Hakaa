from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId  # id type 

class DataChunk(BaseModel):
    _id: Optional[ObjectId]
    chunk_text : str = Field (..., min_length=1)
    chunk_metadata : dict
    chunk_order : int = Field(..., gt = 0)
    chunk_project_id : ObjectId
    # Bug: the processing route was creating `DataChunk(..., chunk_asset_id=...)`,
    # but the schema had no such field.
    # Fix: add the field so each chunk can be traced back to its source asset.
    chunk_asset_id : ObjectId
   
    
    #skip any error
    class Config:
        arbitrary_types_allowed = True


    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [
                    ("chunk_project_id", 1)
                ],
                "name": "chunk_project_id_index_1",
                "unique": False
            }
        ]
    
    
