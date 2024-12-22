import os
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(BASE_DIR)

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

    #MODE : str
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
    MINIO_BUCKET_NAME:str

    #SECRET_KEY: str
    #ENCRYPT_KEY: str
    API_SECRET: str
    HASH_SALT: str
    JWT_SECRET: str 
    ACCESS_TOKEN_TTL: int
    REFRESH_TOKEN_TTL: int  
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env")
    )
    def get_db_url(self):
        print('\n pomjnijnilnininpn;pn \n\n',self.DB_USER, self.DB_PASSWORD)
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")

settings = Settings()