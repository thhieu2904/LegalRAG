"""
MinIO Storage Client wrapper
Simple interface for file operations
"""
from minio import Minio
from minio.error import S3Error
import logging
from io import BytesIO
from typing import Optional

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO storage client wrapper"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        """Initialize MinIO client"""
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        logger.info(f"✅ MinIO client initialized: {endpoint}")
    
    def upload_file(self, bucket: str, file_path: str, file_data: bytes, content_type: str = "application/octet-stream"):
        """
        Upload file to MinIO
        
        Args:
            bucket: Bucket name
            file_path: File path in bucket (e.g., "documents/file.pdf")
            file_data: File content as bytes
            content_type: MIME type
        
        Returns:
            Upload result with ETag
        """
        try:
            result = self.client.put_object(
                bucket,
                file_path,
                BytesIO(file_data),
                len(file_data),
                content_type=content_type
            )
            logger.info(f"✅ Uploaded: {file_path} (ETag: {result.etag})")
            return {
                "success": True,
                "file_path": file_path,
                "etag": result.etag,
                "size": len(file_data)
            }
        except S3Error as e:
            logger.error(f"❌ Upload failed: {e}")
            raise
    
    def download_file(self, bucket: str, file_path: str) -> bytes:
        """
        Download file from MinIO
        
        Args:
            bucket: Bucket name
            file_path: File path in bucket
        
        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(bucket, file_path)
            data = response.read()
            logger.info(f"✅ Downloaded: {file_path}")
            return data
        except S3Error as e:
            logger.error(f"❌ Download failed: {e}")
            raise
    
    def list_files(self, bucket: str, prefix: str = "", recursive: bool = False) -> list:
        """
        List files in bucket
        
        Args:
            bucket: Bucket name
            prefix: Filter by prefix (e.g., "documents/")
            recursive: List recursively
        
        Returns:
            List of file objects
        """
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=recursive)
            files = []
            for obj in objects:
                files.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified
                })
            logger.info(f"✅ Listed {len(files)} files in {bucket}/{prefix}")
            return files
        except S3Error as e:
            logger.error(f"❌ List failed: {e}")
            raise
    
    def delete_file(self, bucket: str, file_path: str):
        """
        Delete file from MinIO
        
        Args:
            bucket: Bucket name
            file_path: File path in bucket
        """
        try:
            self.client.remove_object(bucket, file_path)
            logger.info(f"✅ Deleted: {file_path}")
            return {"success": True, "file_path": file_path}
        except S3Error as e:
            logger.error(f"❌ Delete failed: {e}")
            raise
    
    def file_exists(self, bucket: str, file_path: str) -> bool:
        """Check if file exists"""
        try:
            self.client.stat_object(bucket, file_path)
            return True
        except S3Error:
            return False


# Global client instance
_client: Optional[MinIOClient] = None


def init_minio_client(endpoint: str, access_key: str, secret_key: str, secure: bool = False):
    """Initialize global MinIO client and ensure bucket exists"""
    global _client
    _client = MinIOClient(endpoint, access_key, secret_key, secure)
    
    # Ensure bucket exists
    try:
        from .config import settings
        if not _client.client.bucket_exists(settings.MINIO_BUCKET):
            _client.client.make_bucket(settings.MINIO_BUCKET)
            logger.info(f"✅ Created bucket: {settings.MINIO_BUCKET}")
        else:
            logger.info(f"✅ Bucket exists: {settings.MINIO_BUCKET}")
    except Exception as e:
        logger.error(f"⚠️ Bucket creation/check failed: {e}")


def get_minio_client() -> MinIOClient:
    """Get global MinIO client"""
    if _client is None:
        raise RuntimeError("MinIO client not initialized. Call init_minio_client first.")
    return _client
