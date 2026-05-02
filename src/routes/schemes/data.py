from pydantic import BaseModel
from typing import Optional

class ProcessRequest(BaseModel):
    # Bug: forcing `file_id` to always exist prevented the endpoint from supporting
    # the "process all files in the project" branch already present in the route.
    # Fix: allow `file_id` to be omitted.
    file_id: str = None
    chunk_size: Optional[int] = 100
    overlap_size: Optional[int] = 20
    do_reset: Optional[int] = 0

