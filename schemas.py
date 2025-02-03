# File: schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class ChatMessageBase(BaseModel):
    content: str

class ChatMessageCreate(ChatMessageBase):
    content: str
    agents: Optional[str] = None

class ChatMessageResponse(ChatMessageBase):
    id: UUID
    response: str
    timestamp: datetime
    user_id: str
    
    class Config:
        orm_mode = True

class FileBase(BaseModel):
    filename: str

class FileCreate(FileBase):
    pass

class FileResponse(FileBase):
    id: UUID
    size: int
    upload_date: datetime
    user_id: str
    blob_url: str
    
    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str
    email: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        orm_mode = True