import os
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModeEnum(str, Enum):
    development = "development"
    production = "production"
    testing = "testing"

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    MODE : str
    MINIO_ROOT_USER : str
    MINIO_ROOT_PASSWORD : str

    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_DOMAIN: str
    MINIO_REGION_NAME: str
    MINIO_MEDIA_BUCKET: str
    MINIO_STATIC_BUCKET: str
    MINIO_DATABASE_BUCKET: str
    MINIO_USE_SSL: bool

    SECRET_KEY: str
    ENCRYPT_KEY: str
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    )

    def get_db_url(self):
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")

settings = Settings()