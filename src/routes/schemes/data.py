from pydantic import BaseModel, Field
from typing import Optional, Literal

class ProjectCreateRequest(BaseModel):
    project_name: str = Field(min_length=1, max_length=150)
    project_description: Optional[str] = None
    is_public: bool = False
class ProjectUpdateRequest(BaseModel):
    project_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    project_description: Optional[str] = None
    is_public: Optional[bool] = None
    project_status: Optional[
        Literal["draft", "processing", "ready", "failed"]
    ] = None

class ProcessRequest(BaseModel):
    # Bug: forcing `file_id` to always exist prevented the endpoint from supporting
    # the "process all files in the project" branch already present in the route.
    # Fix: allow `file_id` to be omitted.
    file_id: str = None
    chunk_size: int = Field(default=400, gt=0)
    overlap_size: int = Field(default=60, ge=0)
    do_reset: int = Field(default=0, ge=0, le=1)

