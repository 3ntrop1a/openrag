"""
MinIO Object Storage Service
"""

from typing import Optional
from minio import Minio
from minio.error import S3Error
from loguru import logger
import os
import io


class MinIOStorage:
    """Handles object storage operations with MinIO"""
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        self.access_key = os.getenv("MINIO_ROOT_USER", "admin")
        self.secret_key = os.getenv("MINIO_ROOT_PASSWORD", "admin123456")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        # Ensure default bucket exists
        self._ensure_bucket(os.getenv("MINIO_BUCKET_NAME", "documents"))
    
    def _ensure_bucket(self, bucket_name: str):
        """Create the bucket if it does not already exist"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Bucket created: {bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket: {e}")
            raise
    
    async def upload_file(
        self,
        bucket_name: str,
        object_key: str,
        file_data: bytes,
        content_type: Optional[str] = None
    ):
        """Upload a file to MinIO"""
        try:
            self._ensure_bucket(bucket_name)
            
            file_stream = io.BytesIO(file_data)
            file_size = len(file_data)
            
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_key,
                data=file_stream,
                length=file_size,
                content_type=content_type or "application/octet-stream"
            )
            
            logger.info(f"File uploaded: {object_key} to {bucket_name}")
            
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    async def download_file(self, bucket_name: str, object_key: str) -> bytes:
        """Download a file from MinIO"""
        try:
            response = self.client.get_object(bucket_name, object_key)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.debug(f"File downloaded: {object_key} from {bucket_name}")
            return data
            
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    async def delete_file(self, bucket_name: str, object_key: str):
        """Delete a file from MinIO"""
        try:
            self.client.remove_object(bucket_name, object_key)
            logger.info(f"File deleted: {object_key} from {bucket_name}")
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    def file_exists(self, bucket_name: str, object_key: str) -> bool:
        """Check whether a file exists in the bucket"""
        try:
            self.client.stat_object(bucket_name, object_key)
            return True
        except S3Error:
            return False
    
    def health_check(self):
        """Check MinIO connectivity"""
        try:
            self.client.list_buckets()
            return True
        except S3Error as e:
            logger.error(f"MinIO health check failed: {e}")
            raise
