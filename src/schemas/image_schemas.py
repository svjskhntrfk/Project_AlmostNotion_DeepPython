from pydantic import BaseModel, HttpUrl
from uuid import UUID
from fastapi import UploadFile
import uuid
from src.db.cfg.config import settings

class ImageSchema(BaseModel):
    id: UUID
    file: str
    
    @property
    def url(self) -> str:
        return f"http://127.0.0.1:9000/{settings.MINIO_MEDIA_BUCKET}/{self.file}"
    
    class Config:
        from_attributes = True
        
class ImageCreate(BaseModel):
    file: str

class ImageUploadResponse(BaseModel):
    id: UUID
    file: str
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