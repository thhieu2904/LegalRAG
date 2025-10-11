"""
RAG Service HTTP Client
=======================

HTTP client for communicating with RAG Service Internal APIs.
Handles CRUD operations for questions and rebuild triggers.
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.config import AdminConfig

logger = logging.getLogger(__name__)


class RAGServiceClient:
    """HTTP client for RAG Service Internal APIs"""
    
    def __init__(self):
        self.base_url = AdminConfig.RAG_SERVICE_URL
        self.api_key = AdminConfig.INTERNAL_API_KEY
        self.timeout = AdminConfig.RAG_REQUEST_TIMEOUT
        self.max_retries = AdminConfig.RAG_MAX_RETRIES
        
        # Default headers for all requests
        self.headers = {
            "X-Internal-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        logger.info(f"🔧 RAG Service Client initialized: {self.base_url}")
    
    def _get_internal_url(self, endpoint: str) -> str:
        """Construct full URL for internal API endpoint"""
        return f"{self.base_url}/api/internal{endpoint}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint path
            **kwargs: Additional httpx request parameters
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPError: On HTTP errors
            httpx.TimeoutException: On timeout
            httpx.ConnectError: On connection errors
        """
        url = self._get_internal_url(endpoint)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"📡 {method} {url}")
            
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    **kwargs
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"✅ {method} {url} - Status: {response.status_code}")
                return data
                
            except httpx.HTTPStatusError as e:
                logger.error(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
                raise
            except httpx.TimeoutException:
                logger.error(f"⏱️ Timeout after {self.timeout}s: {url}")
                raise
            except httpx.ConnectError as e:
                logger.error(f"🔌 Connection failed: {url} - {str(e)}")
                raise
            except Exception as e:
                logger.error(f"❌ Unexpected error: {str(e)}")
                raise
    
    # ========== Questions CRUD Operations ==========
    
    async def get_questions(
        self,
        collection: str,
        doc_id: str
    ) -> Dict[str, Any]:
        """
        Get questions for a document
        
        Args:
            collection: Collection name
            doc_id: Document ID
            
        Returns:
            Questions data with main_question and question_variants
        """
        endpoint = f"/files/questions/collections/{collection}/documents/{doc_id}"
        return await self._make_request("GET", endpoint)
    
    async def create_questions(
        self,
        collection: str,
        doc_id: str,
        main_question: str,
        question_variants: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create new questions for a document
        
        Args:
            collection: Collection name
            doc_id: Document ID
            main_question: Main question text
            question_variants: List of question variants (optional)
            
        Returns:
            Success response with created data
        """
        endpoint = f"/files/questions/collections/{collection}/documents/{doc_id}"
        payload = {
            "main_question": main_question,
            "question_variants": question_variants or []
        }
        return await self._make_request("POST", endpoint, json=payload)
    
    async def update_questions(
        self,
        collection: str,
        doc_id: str,
        main_question: str,
        question_variants: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update questions for a document
        
        Args:
            collection: Collection name
            doc_id: Document ID
            main_question: Updated main question text
            question_variants: Updated list of question variants (optional)
            
        Returns:
            Success response with backup path
        """
        endpoint = f"/files/questions/collections/{collection}/documents/{doc_id}"
        payload = {
            "main_question": main_question,
            "question_variants": question_variants or []
        }
        return await self._make_request("PUT", endpoint, json=payload)
    
    async def delete_questions(
        self,
        collection: str,
        doc_id: str
    ) -> Dict[str, Any]:
        """
        Delete questions file for a document
        
        Args:
            collection: Collection name
            doc_id: Document ID
            
        Returns:
            Success response with backup path
        """
        endpoint = f"/files/questions/collections/{collection}/documents/{doc_id}"
        return await self._make_request("DELETE", endpoint)
    
    async def update_variants(
        self,
        collection: str,
        doc_id: str,
        question_variants: List[str]
    ) -> Dict[str, Any]:
        """
        Update only question variants (keep main_question unchanged)
        
        Args:
            collection: Collection name
            doc_id: Document ID
            question_variants: New list of question variants
            
        Returns:
            Success response with backup path
        """
        endpoint = f"/files/questions/collections/{collection}/documents/{doc_id}/variants"
        # RAG Service expects List[str] directly, not wrapped in object
        return await self._make_request("PATCH", endpoint, json=question_variants)
    
    async def restore_questions(
        self,
        collection: str,
        doc_id: str,
        backup_filename: str
    ) -> Dict[str, Any]:
        """
        Restore questions from backup file
        
        Args:
            collection: Collection name
            doc_id: Document ID
            backup_filename: Name of backup file to restore
            
        Returns:
            Success response
        """
        endpoint = f"/files/questions/collections/{collection}/documents/{doc_id}/restore"
        payload = {
            "backup_filename": backup_filename
        }
        return await self._make_request("POST", endpoint, json=payload)
    
    # ========== Rebuild Operations ==========
    
    async def trigger_rebuild(
        self,
        scope: str = "document",
        collection: Optional[str] = None,
        doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger VectorDB rebuild
        
        Args:
            scope: Rebuild scope (document, collection, all)
            collection: Collection name (required for document/collection scope)
            doc_id: Document ID (required for document scope)
            
        Returns:
            Success response with process PID
        """
        endpoint = "/rebuild/trigger"
        payload = {
            "scope": scope
        }
        
        if collection:
            payload["collection"] = collection
        if doc_id:
            payload["doc_id"] = doc_id
        
        return await self._make_request("POST", endpoint, json=payload)
    
    async def get_rebuild_status(self) -> Dict[str, Any]:
        """
        Get rebuild process status
        
        Returns:
            Status data with progress percentage
        """
        endpoint = "/rebuild/status"
        return await self._make_request("GET", endpoint)
    
    async def cancel_rebuild(self) -> Dict[str, Any]:
        """
        Cancel running rebuild process
        
        Returns:
            Success response
        """
        endpoint = "/rebuild/cancel"
        return await self._make_request("POST", endpoint)
    
    async def clear_rebuild_status(self) -> Dict[str, Any]:
        """
        Clear rebuild status file
        
        Returns:
            Success response
        """
        endpoint = "/rebuild/status"
        return await self._make_request("DELETE", endpoint)


# Singleton instance
_rag_client: Optional[RAGServiceClient] = None


def get_rag_client() -> RAGServiceClient:
    """
    Get RAG Service Client singleton instance
    
    Returns:
        RAGServiceClient instance
    """
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGServiceClient()
    return _rag_client
