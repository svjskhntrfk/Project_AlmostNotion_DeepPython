from pydantic import BaseModel, HttpUrl
from uuid import UUID
from fastapi import UploadFile
import uuid

class ImageSchema(BaseModel):
    id: UUID
    file: str
    
    @property
    def url(self) -> str:
        from config import settings
        return f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{self.file}"
    
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