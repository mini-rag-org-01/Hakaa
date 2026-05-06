from pydantic import BaseModel


class RetrievedDocument(BaseModel):
    score: float 
    text: str 
