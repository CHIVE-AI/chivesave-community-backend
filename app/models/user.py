from pydantic import BaseModel, Field
from typing import Optional, List

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
