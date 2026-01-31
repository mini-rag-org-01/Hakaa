from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId  # id type 

class Project(BaseModel):
    _id: Optional[ObjectId]
    project_id : str = Field (..., min_length=1)

    # create validator manualy
    @validator("project_id")
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError("project_id must be alphanumeric")
        
        return value
    
    #skip any error
    class Config:
        arbitrary_types_allowed = True


    