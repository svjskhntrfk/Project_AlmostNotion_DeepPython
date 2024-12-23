from src.db.cfg.config import settings
from src.backend.conf.s3_client import S3StorageManager


class MediaStorage(S3StorageManager):
    bucket_name = settings.MINIO_MEDIA_BUCKET
    default_acl = 'public-read'

media_storage = MediaStorage()