from pydantic import BaseModel, Field


class RetrievedDocument(BaseModel):
    score: float 
    text: str 
