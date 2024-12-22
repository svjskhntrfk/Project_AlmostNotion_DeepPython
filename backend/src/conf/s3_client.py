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
from config import settings
import logging

logger = logging.getLogger(__name__)

class S3AsyncClient:
    _cached_session = None

    def __init__(self):
        logger.info(f"Initializing S3AsyncClient with domain: {settings.MINIO_DOMAIN}")
        self.endpoint_domain = settings.MINIO_DOMAIN
        self.use_ssl = settings.MINIO_USE_SSL
        if S3AsyncClient._cached_session is None:
            logger.debug("Creating new S3 session")
            S3AsyncClient._cached_session = aioboto3.Session(
                aws_access_key_id=settings.MINIO_ACCESS_KEY,
                aws_secret_access_key=settings.MINIO_SECRET_KEY,
                region_name=settings.MINIO_REGION_NAME
            )
        self.endpoint_url = self._get_endpoint_url()
        logger.debug(f"S3AsyncClient initialized with endpoint URL: {self.endpoint_url}")

    @property
    def client(self):
        return S3AsyncClient._cached_session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            use_ssl=self.use_ssl
        )

    def _get_endpoint_url(self) -> str:
        logger.debug(f"Generating endpoint URL for domain: {self.endpoint_domain}")
        if self.endpoint_domain.startswith("http"):
            logger.error("Invalid domain format: domain should not start with http/https")
            raise ValueError(
                "settings.MINIO_DOMAIN should not start with 'http' or 'https'. Please use just the domain name.")

        protocol = "https" if self.use_ssl else "http"
        url = f"{protocol}://{self.endpoint_domain}"
        logger.debug(f"Generated endpoint URL: {url}")
        return url

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
        logger.debug("Validating S3StorageManager class attributes")
        required_attributes = ("bucket_name", "default_acl")

        for attr in required_attributes:
            value = getattr(cls, attr)
            if value is None:
                logger.error(f"Missing required attribute: {attr}")
                raise ValueError(f"The '{attr}' class attribute is required and cannot be None.")

    def _prepare_path(self, path: str) -> str:
        if path and not path.endswith('/'):
            path += '/'
        return path

    async def _read_file(self, file: UploadFile) -> tuple[bytes, str]:
        logger.debug(f"Reading file: {file.filename}")
        try:
            file_content = await file.read()
            file_name = file.filename
            logger.debug(f"Successfully read file: {file_name}, size: {len(file_content)} bytes")
            return file_content, file_name
        except Exception as e:
            logger.error(f"Error reading file {file.filename}: {str(e)}")
            raise

    async def _generate_unique_key(self, s3_client, file_name: str) -> str:
        base_name, extension = os.path.splitext(file_name)
        key = file_name
        counter = 1
        while True:
            try:
                await s3_client.head_object(Bucket=self.bucket_name, Key=key)
                key = f"{base_name}_{counter}{extension}"
                counter += 1
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    break
                else:
                    raise
        return key

    def _convert_to_webp(self, file_content: bytes) -> tuple[bytes, str]:
        logger.debug("Converting image to WebP format")
        try:
            image = Image.open(io.BytesIO(file_content))
            image.load()
            output = io.BytesIO()
            image.save(output, format="WEBP")
            logger.debug("Successfully converted image to WebP")
            return output.getvalue(), "image/webp"
        except UnidentifiedImageError:
            logger.error("Invalid image file during WebP conversion")
            raise HTTPException(status_code=400, detail="Invalid image file")
        except Exception as e:
            logger.error(f"Error converting image to WebP: {str(e)}")
            raise HTTPException(status_code=500, detail="An error occurred while processing the image") from e

    async def generate_url(self, key: str, expiration: int = 3600) -> str:
        logger.debug(f"Generating URL for key: {key}, expiration: {expiration}s")
        async with self.client as s3_client:
            protocol = "https" if self.use_ssl else "http"
            if self.custom_domain:
                url = f"{protocol}://{self.custom_domain}/{key}"
                logger.debug(f"Generated custom domain URL: {url}")
                return url
            if self.default_acl == 'public-read':
                url = f"{protocol}://{self.endpoint_domain}/{self.bucket_name}/{key}"
                logger.debug(f"Generated public URL: {url}")
                return url
            try:
                url = await s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expiration
                )
                logger.debug(f"Generated presigned URL: {url}")
                return url
            except ClientError as e:
                logger.error(f"Error generating presigned URL for key {key}: {str(e)}")
                raise HTTPException(status_code=500, detail="Error generating presigned URL") from e

    async def put_object(self, file: UploadFile, path: str = "", file_type: str = "image") -> str:
        logger.info(f"Starting file upload: {file.filename}, type: {file_type}")
        async with self.client as s3_client:
            try:
                file_content, file_name = await self._read_file(file)
                path = self._prepare_path(path)
                logger.debug(f"Prepared path: {path}")

                kind = filetype.guess(file_content)
                is_image = kind is not None and kind.mime.startswith("image")

                if file_type == "image":
                    if not is_image:
                        logger.error(f"Invalid image file: {file.filename}")
                        raise HTTPException(status_code=400, detail="Invalid image file")
                    file_content, content_type = self._convert_to_webp(file_content)
                    file_name = os.path.splitext(file_name)[0] + ".webp"
                else:
                    content_type = kind.mime if kind else 'application/octet-stream'
                
                logger.debug(f"Processing file: {file_name}, content_type: {content_type}")
                key = await self._generate_unique_key(s3_client, path + file_name)
                
                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_content,
                    ContentType=content_type,
                    ACL=self.default_acl
                )

                logger.info(f"Successfully uploaded file to S3: {key}")
                return key

            except ClientError as e:
                logger.error(f"S3 client error uploading file {file.filename}: {str(e)}")
                raise HTTPException(status_code=500, detail="Error uploading file to S3") from e
            except Exception as e:
                logger.error(f"Unexpected error uploading file {file.filename}: {str(e)}")
                raise HTTPException(status_code=500, detail="Unexpected error during file upload") from e

    async def delete_object(self, key: str) -> None:
        logger.info(f"Attempting to delete object with key: {key}")
        async with self.client as s3_client:
            try:
                await s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                logger.info(f"Successfully deleted object: {key}")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code != 'NoSuchKey':
                    logger.error(f"Error deleting object {key}: {str(e)}")
                    raise HTTPException(status_code=500, detail="Error deleting file from S3") from e
                logger.warning(f"Object not found for deletion: {key}")
