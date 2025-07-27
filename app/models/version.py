from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class VersionBase(BaseModel):
    name: str = Field(..., description="A unique name for the AI artifact version.")
    description: Optional[str] = Field(None, description="A brief description of this version.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Arbitrary key-value metadata for the version (JSON format).")

class VersionCreate(VersionBase):
    pass

class Version(VersionBase):
    id: int = Field(..., description="The unique identifier for the version.")
    artifact_path: str = Field(..., description="The internal path where the artifact file is stored.")
    created_at: datetime = Field(..., description="Timestamp when the version was created.")

    class Config:
        from_attributes = True
