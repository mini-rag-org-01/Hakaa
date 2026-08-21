from typing import Any, Dict, Optional
from pydantic import BaseModel


class RetrievedDocument(BaseModel):

    score: float
    text: str
    metadata: Optional[Dict[str, Any]] = None
    chunk_id: Optional[int] = None