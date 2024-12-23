import os
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


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
    

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_ENDPOINT: str
    S3_REGION: str
    S3_BUCKET: str

    API_SECRET: str
    HASH_SALT: str
    JWT_SECRET: str 
    ACCESS_TOKEN_TTL: int
    REFRESH_TOKEN_TTL: int  

    GMAIL_USERNAME: str
    GMAIL_FROM: str
    GMAIL_PASSWORD: str
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    )

    def get_db_url(self):
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")

settings = Settings()