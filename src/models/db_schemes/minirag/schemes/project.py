from time import timezone
from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, string, DateTime, func
from sqlalchemy.dialects.postgres import UUID
from sqlalchemy.orm import relationship

import uuid

class Project(SQLAlchemyBase):
    __tablename__ = "projects"
    
    # define Columns name
    project_id = Column(Integer, primary_key=True, autoincrement= True)
    project_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique= True, nullable=False) 

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdated=func.now(), nullable=True)