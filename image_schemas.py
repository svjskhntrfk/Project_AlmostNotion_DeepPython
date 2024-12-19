from pydantic import BaseModel, HttpUrl
from uuid import UUID
from fastapi import UploadFile
import uuid

class ImageSchema(BaseModel):
    id: UUID
    file: str
    is_main: bool

    class Config:
        from_attributes = True
        
class ImageCreate(BaseModel):
    file: str
    is_main: bool

class ImageUploadRequest(BaseModel):
    is_main: bool

class ImageUploadResponse(BaseModel):
    id: UUID
    file: str
    is_main: bool
    url: str

    class Config:
        from_attributes = True

class ImageUpdate(ImageCreate):
    id: uuid.UUID