from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
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

# --- User Models ---
class UserBase(BaseModel):
    username: str = Field(..., description="Unique username for the user.")
    email: Optional[str] = Field(None, description="User's email address.")

class UserCreate(UserBase):
    password: str = Field(..., description="User's password.")

class UserInDB(UserBase):
    hashed_password: str
    disabled: Optional[bool] = False
    roles: List[str] = Field(default_factory=lambda: ["user"], description="List of roles assigned to the user.")

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    disabled: Optional[bool] = False
    roles: List[str] = Field(default_factory=lambda: ["user"], description="List of roles assigned to the user.")

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
