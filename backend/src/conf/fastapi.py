import base64
import os
import secrets
from enum import Enum
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class ModeEnum(str, Enum):
    development = "development"
    production = "production"
    testing = "testing"


class Settings(BaseSettings):
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY")
    MINIO_DOMAIN: str = os.getenv("MINIO_DOMAIN")
    MINIO_REGION_NAME: str = os.getenv("MINIO_REGION_NAME")
    MINIO_MEDIA_BUCKET: str = os.getenv("MINIO_MEDIA_BUCKET")
    MINIO_STATIC_BUCKET: str = os.getenv("MINIO_STATIC_BUCKET")
    MINIO_DATABASE_BUCKET: str = os.getenv("MINIO_DATABASE_BUCKET")
    MINIO_USE_SSL: bool = int(os.getenv("MINIO_USE_SSL"))

    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ENCRYPT_KEY: str = os.getenv("ENCRYPT_KEY", base64.urlsafe_b64encode(os.urandom(32)).decode())

settings = Settings()