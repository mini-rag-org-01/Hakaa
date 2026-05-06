from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId  # id type 

class Project( ):
    # Bug: the codebase was using `project.id`, but the schema only exposed `_id`.
    # Fix: expose `id` in Python code and map it to Mongo's `_id` via an alias.
    id: Optional[ObjectId] = Field(None, alias="_id")
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

    @classmethod
    def get_indexes(cls):
        # Bug: `ProjectModel.init_collection()` expects `Project.get_indexes()`.
        # Fix: define the index metadata on the schema, matching the pattern used by other models.
        return [
            {
                "key": [("project_id", 1)],
                "name": "project_id_index_1",
                "unique": True,
            }
        ]



    @classmethod
    def get_indexes(cls):

        return [
            {
                "key": [
                    ("project_id", 1)
                ],
                "name": "project_id_index_1",
                "unique": True
            }
        ]    
