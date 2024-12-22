from pydantic import BaseModel, HttpUrl
from uuid import UUID
from fastapi import UploadFile
import uuid

class ImageSchema(BaseModel):
    id: UUID
    file: str
    is_main: bool
    
    @property
    def url(self) -> str:
        from config import settings
        return f"http://127.0.0.1:9000/{settings.MINIO_MEDIA_BUCKET}/{self.file}"
    
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

class ImageDAOResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    # Add any other fields that you need for the response