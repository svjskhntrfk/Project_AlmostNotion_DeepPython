import io
import mimetypes
import os
from typing import List

import aioboto3
import aiohttp
import filetype
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from backend.src.conf import settings

class S3AsyncClient:
    _cached_session = None

    def __init__(self):
        self.endpoint_domain = settings.MINIO_DOMAIN
        self.use_ssl = settings.MINIO_USE_SSL
        if S3AsyncClient._cached_session is None:
            S3AsyncClient._cached_session = aioboto3.Session(
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
                region_name=settings.MINIO_REGION_NAME
            )
        self.endpoint_url = self._get_endpoint_url()

    @property
    def client(self):
        return S3AsyncClient._cached_session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            use_ssl=self.use_ssl
        )

    def _get_endpoint_url(self) -> str:
        if self.endpoint_domain.startswith("http"):
            raise ValueError(
                "settings.MINIO_DOMAIN should not start with 'http' or 'https'. Please use just the domain name.")

        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.endpoint_domain}"

    async def __aenter__(self):
        self.s3_client = await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.s3_client.__aexit__(exc_type, exc_val, exc_tb)


class S3StorageManager(S3AsyncClient):
    bucket_name = None
    default_acl = None
    custom_domain = None
    use_ssl = False

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        cls._validate_class_attributes()
        return instance

    @classmethod
    def _validate_class_attributes(cls):
        required_attributes = ("bucket_name", "default_acl")

        for attr in required_attributes:
            value = getattr(cls, attr)
            if value is None:
                raise ValueError(f"The '{attr}' class attribute is required and cannot be None.")

    async def put_object(self, file: UploadFile, path: str = "", file_type: str = "image") -> str:
        logger.info("Начало загрузки файла: %s", file.filename)

        async with self.client as s3_client:
            try:
                file_content, file_name = await self._read_file(file)
                path = self._prepare_path(path)

                kind = filetype.guess(file_content)
                is_image = kind is not None and kind.mime.startswith("image")

                if file_type == "image":
                    if not is_image:
                        logger.error("Файл %s не является допустимым изображением", file.filename)
                        raise HTTPException(status_code=400, detail="Invalid image file")
                    file_content, content_type = self._convert_to_webp(file_content)
                    file_name = os.path.splitext(file_name)[0] + ".webp"
                else:
                    content_type = kind.mime if kind else 'application/octet-stream'

                key = await self._generate_unique_key(s3_client, path + file_name)
                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_content,
                    ContentType=content_type,
                    ACL=self.default_acl
                )

                logger.info("Файл успешно загружен в S3: %s", key)
                return key

            except ClientError as e:
                logger.error("Ошибка при загрузке файла %s: %s", file.filename, e)
                raise HTTPException(status_code=500, detail="Error uploading file to S3") from e


    async def delete_object(self, key: str) -> None:
        logger.info("Удаление объекта из S3: %s", key)

        async with self.client as s3_client:
            try:
                await s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                logger.info("Объект успешно удален: %s", key)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code != 'NoSuchKey':
                    logger.error("Ошибка при удалении объекта %s: %s", key, e)
                    raise HTTPException(status_code=500, detail="Error deleting file from S3") from e
                else:
                    logger.warning("Объект не найден в S3 при попытке удаления: %s", key)
