from config import settings
from backend.src.conf.s3_client import S3StorageManager


class MediaStorage(S3StorageManager):
    bucket_name = settings.MINIO_MEDIA_BUCKET
    default_acl = 'public-read'

media_storage = MediaStorage()