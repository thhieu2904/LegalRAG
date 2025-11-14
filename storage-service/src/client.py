"""
Storage Service Client
For other services (Admin, Embedding, etc.) to call Storage-Service
"""
import httpx
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class StorageClient:
    """Client for Storage-Service API"""
    
    def __init__(self, base_url: str = "http://storage-service:8000"):
        """
        Initialize storage client
        
        Args:
            base_url: Storage-Service URL (default for Docker)
        """
        self.base_url = base_url
        self.client = httpx.Client(timeout=300.0)  # 5 min timeout for processing
        logger.info(f"✅ StorageClient initialized: {base_url}")
    
    def health_check(self) -> bool:
        """Check if storage service is healthy"""
        try:
            response = self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def upload_and_process(
        self,
        file_path: str,
        file_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload file to MinIO and process (extract + chunk)
        
        **RECOMMENDED METHOD FOR ADMIN-SERVICE**
        
        Args:
            file_path: Local path to PDF file
            file_name: Optional custom filename (default: basename of file_path)
        
        Returns:
            {
                'success': bool,
                'file_id': str,
                'file_path': str,
                'metadata': {...},
                'chunks': [...],
                'total_chunks': int,
                'processing_time_ms': int
            }
        """
        try:
            if not file_name:
                file_name = file_path.split('/')[-1]
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f, 'application/pdf')}
                response = self.client.post(
                    f"{self.base_url}/upload-and-process",
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Processed: {result['file_id']} ({result['total_chunks']} chunks)")
                return result
            else:
                raise Exception(f"Upload failed: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ Upload and process failed: {e}")
            raise
    
    def upload_file(
        self,
        file_path: str,
        file_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload file to MinIO only (no processing)
        
        Args:
            file_path: Local path to PDF file
            file_name: Optional custom filename
        
        Returns:
            {
                'success': bool,
                'file_path': str,
                'file_size': int,
                'bucket': str
            }
        """
        try:
            if not file_name:
                file_name = file_path.split('/')[-1]
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f, 'application/pdf')}
                response = self.client.post(
                    f"{self.base_url}/upload",
                    files=files,
                    params={'document_id': 'temp-upload'}
                )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"✅ Uploaded: {result['file_path']}")
                return result
            else:
                raise Exception(f"Upload failed: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            raise
    
    def download_file(self, file_path: str) -> bytes:
        """
        Download file from MinIO
        
        Args:
            file_path: Path in MinIO (e.g., "documents/uuid/file.pdf")
        
        Returns:
            File content as bytes
        """
        try:
            response = self.client.get(
                f"{self.base_url}/download",
                params={'file_path': file_path}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Downloaded: {file_path}")
                return response.content
            else:
                raise Exception(f"Download failed: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            raise
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from MinIO
        
        Args:
            file_path: Path in MinIO
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            response = self.client.delete(
                f"{self.base_url}/delete",
                params={'file_path': file_path}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Deleted: {file_path}")
                return True
            else:
                raise Exception(f"Delete failed: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ Delete failed: {e}")
            return False
    
    def list_files(self, prefix: str = "documents/") -> List[Dict[str, Any]]:
        """
        List files in MinIO bucket
        
        Args:
            prefix: Folder prefix
        
        Returns:
            List of file metadata
        """
        try:
            response = self.client.get(
                f"{self.base_url}/list",
                params={'prefix': prefix}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Listed: {result['total']} files")
                return result.get('files', [])
            else:
                raise Exception(f"List failed: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ List failed: {e}")
            return []


# Async version (for FastAPI apps)
class AsyncStorageClient:
    """Async client for Storage-Service API"""
    
    def __init__(self, base_url: str = "http://storage-service:8000"):
        self.base_url = base_url
        logger.info(f"✅ AsyncStorageClient initialized: {base_url}")
    
    async def upload_and_process(
        self,
        file_content: bytes,
        file_name: str,
    ) -> Dict[str, Any]:
        """
        Upload file and process (async)
        
        Args:
            file_content: File bytes
            file_name: Filename with extension
        
        Returns:
            Processing result with metadata and chunks
        """
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                files = {'file': (file_name, file_content, 'application/pdf')}
                response = await client.post(
                    f"{self.base_url}/upload-and-process",
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Processed: {result['file_id']} ({result['total_chunks']} chunks)")
                return result
            else:
                raise Exception(f"Processing failed: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ Async processing failed: {e}")
            raise
