from time import timezone
from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, func, String, Boolean, Text, false
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

import uuid

class Project(SQLAlchemyBase):
    __tablename__ = "projects"
    
    # define Columns name
    project_id = Column(Integer, primary_key=True, autoincrement= True)
    project_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique= True, nullable=False) 
    project_name = Column(String(150), nullable=True)
    project_description = Column(Text, nullable=True)

    is_public = Column(
        Boolean,
        nullable=False,
        server_default=false(),
        index=True,
    )
    project_status = Column(
        String(20),
        nullable=False,
        server_default="draft",
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    chunks = relationship("DataChunk",back_populates="project")
    assets = relationship("Asset",back_populates="project")
