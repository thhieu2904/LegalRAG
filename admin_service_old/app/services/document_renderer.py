"""
Document Rendering Service
===========================

Handles document rendering for Admin Service preview functionality.
Calls RAG Service to get raw files, then renders locally.

Architecture:
- RAG Service (Data Layer): Serves raw files
- Admin Service (Presentation Layer): Renders HTML from DOCX/DOC

Pattern learned from: questions.py and internal_files.py structure

Note: Vietnamese legal documents from government agencies are typically
in .doc format (Office 97-2003). We use LibreOffice for .doc conversion
and mammoth for .docx files.
"""

import mammoth
import logging
import httpx
import subprocess
import tempfile
import os
from io import BytesIO
from typing import Dict, Any, Optional
from pathlib import Path

from .rag_client import RAGServiceClient

logger = logging.getLogger(__name__)


class DocumentRenderer:
    """
    Service for rendering documents fetched from RAG Service
    
    Responsibilities:
    1. Fetch raw DOCX files from RAG Service
    2. Render DOCX to HTML using mammoth (locally)
    3. Fetch and return JSON data from RAG Service
    4. Handle errors gracefully
    """
    
    def __init__(self, rag_client: Optional[RAGServiceClient] = None):
        """
        Initialize Document Renderer
        
        Args:
            rag_client: RAG Service HTTP client (optional, will create if not provided)
        """
        self.rag_client = rag_client or RAGServiceClient()
        logger.info("📄 Document Renderer initialized")
    
    async def render_docx_to_html(
        self,
        collection: str,
        doc_id: str
    ) -> str:
        """
        Render DOCX document to HTML
        
        Architecture Flow:
        1. Call RAG Service to get raw DOCX bytes
        2. Use mammoth to convert DOCX → HTML locally
        3. Return HTML string
        
        Args:
            collection: Collection name (e.g., 'hop_dong')
            doc_id: Document ID (e.g., 'DOC_001')
            
        Returns:
            HTML content string
            
        Raises:
            httpx.HTTPError: If RAG Service request fails
            Exception: If rendering fails
        """
        try:
            logger.info(f"📡 Fetching raw DOCX from RAG Service: {collection}/{doc_id}")
            
            # Step 1: Get raw DOCX bytes from RAG Service
            docx_bytes = await self.rag_client.get_document_file(
                collection=collection,
                doc_id=doc_id,
                file_type="docx"
            )
            
            logger.info(f"📥 Received {len(docx_bytes)} bytes from RAG Service")
            
            # Step 2: Render DOCX to HTML locally
            logger.info(f"🎨 Rendering document to HTML (Admin Service - Presentation Layer)")
            
            # Detect file format
            signature = docx_bytes[:2]
            is_old_doc_format = signature == b'\xD0\xCF'
            
            if is_old_doc_format:
                logger.info(f"📄 Old .doc format detected (Office 97-2003) - Using LibreOffice")
                return await self._convert_doc_with_libreoffice(docx_bytes, doc_id)
            else:
                logger.info(f"📄 .docx format detected - Using mammoth")
                return await self._convert_docx_with_mammoth(docx_bytes, doc_id)
            
        except httpx.HTTPError as e:
            logger.error(f"❌ RAG Service error fetching DOCX: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error rendering DOCX to HTML: {e}")
            raise
    
    async def _convert_doc_with_libreoffice(self, doc_bytes: bytes, doc_id: str) -> str:
        """
        Convert .doc file to HTML using LibreOffice headless
        
        Args:
            doc_bytes: Raw .doc file bytes
            doc_id: Document ID for logging
            
        Returns:
            HTML content string
        """
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Save input .doc file
                input_path = os.path.join(tmpdir, 'input.doc')
                with open(input_path, 'wb') as f:
                    f.write(doc_bytes)
                
                logger.info(f"💾 Saved temp .doc file: {input_path}")
                
                # Convert using LibreOffice headless
                logger.info(f"🔄 Converting .doc → HTML with LibreOffice...")
                
                result = subprocess.run([
                    'soffice',
                    '--headless',
                    '--convert-to', 'html',
                    '--outdir', tmpdir,
                    input_path
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    logger.error(f"❌ LibreOffice conversion failed: {result.stderr}")
                    raise Exception(f"LibreOffice conversion failed: {result.stderr}")
                
                # Read HTML output
                output_path = os.path.join(tmpdir, 'input.html')
                
                if not os.path.exists(output_path):
                    logger.error(f"❌ HTML output file not found: {output_path}")
                    raise Exception("LibreOffice conversion succeeded but output file not found")
                
                with open(output_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                logger.info(f"✅ LibreOffice conversion successful ({len(html_content)} chars)")
                
                # Add notice about conversion method
                html_with_notice = f"""
                <div style='background: #e3f2fd; border-left: 4px solid #2196f3; padding: 12px; margin-bottom: 20px; font-family: Arial, sans-serif;'>
                    <strong>ℹ️ Thông tin:</strong> File .doc (Office 97-2003) - Đã chuyển đổi bằng LibreOffice
                </div>
                {html_content}
                """
                
                return html_with_notice
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ LibreOffice conversion timeout after 30s")
            raise Exception("Document conversion timeout (> 30s)")
        except Exception as e:
            logger.error(f"❌ Error in LibreOffice conversion: {e}")
            raise
    
    async def _convert_docx_with_mammoth(self, docx_bytes: bytes, doc_id: str) -> str:
        """
        Convert .docx file to HTML using mammoth
        
        Args:
            docx_bytes: Raw .docx file bytes
            doc_id: Document ID for logging
            
        Returns:
            HTML content string
        """
        try:
            docx_file = BytesIO(docx_bytes)
            
            result = mammoth.convert_to_html(docx_file)
            html_content = result.value
            messages = result.messages
            
            # Check if conversion produced any content
            if not html_content or len(html_content.strip()) == 0:
                logger.error(f"❌ Mammoth produced empty HTML output")
                raise Exception("Document conversion produced empty output")
            
            # Log any warnings from mammoth
            if messages:
                logger.warning(f"⚠️ Mammoth conversion warnings ({len(messages)} messages):")
                for msg in messages[:5]:
                    logger.warning(f"   - {msg}")
                if len(messages) > 5:
                    logger.warning(f"   ... and {len(messages) - 5} more warnings")
            
            logger.info(f"✅ Mammoth conversion successful ({len(html_content)} chars)")
            
            return html_content
            
        except Exception as e:
            logger.error(f"❌ Mammoth conversion failed: {e}")
            raise
    
    async def get_json_content(
        self,
        collection: str,
        doc_id: str
    ) -> Dict[str, Any]:
        """
        Get JSON document content
        
        Architecture Flow:
        1. Call RAG Service to get parsed JSON data
        2. Extract 'content' field from response wrapper
        3. Return JSON data directly
        
        Args:
            collection: Collection name (e.g., 'hop_dong')
            doc_id: Document ID (e.g., 'DOC_001')
            
        Returns:
            Parsed JSON data as dictionary (the actual document data)
            
        Raises:
            httpx.HTTPError: If RAG Service request fails
        """
        try:
            logger.info(f"📡 Fetching JSON from RAG Service: {collection}/{doc_id}")
            
            # Get JSON data from RAG Service
            json_response = await self.rag_client.get_document_json(
                collection=collection,
                doc_id=doc_id
            )
            
            logger.debug(f"📋 RAG Service response structure: {json_response.keys()}")
            
            # Extract content from response wrapper
            # RAG Service returns: {success, content_type, content: {...actual_data}, doc_id, collection, filename, timestamp}
            # We only need the 'content' field which contains the actual JSON data
            if "content" in json_response:
                json_content = json_response["content"]
                logger.info(f"✅ Successfully extracted JSON content: {len(json_content)} fields")
            else:
                # Fallback: if no 'content' field, return the entire response
                # This handles different response formats
                logger.warning(f"⚠️ No 'content' field in response, returning full response")
                json_content = json_response
            
            return json_content
            
        except httpx.HTTPError as e:
            logger.error(f"❌ RAG Service error fetching JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error getting JSON content: {e}")
            raise
    
    async def get_document_metadata(
        self,
        collection: str,
        doc_id: str,
        file_type: str
    ) -> Dict[str, Any]:
        """
        Get document metadata without rendering
        
        Args:
            collection: Collection name
            doc_id: Document ID
            file_type: File type ('docx' or 'json')
            
        Returns:
            Document metadata
        """
        try:
            logger.info(f"📋 Getting metadata for {collection}/{doc_id} ({file_type})")
            
            # Could be extended to call RAG Service for metadata
            # For now, return basic info
            metadata = {
                "collection": collection,
                "doc_id": doc_id,
                "file_type": file_type,
                "renderer": "Admin Service (Presentation Layer)"
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Error getting document metadata: {e}")
            raise


# ============================================================================
# Helper Functions
# ============================================================================

def get_document_renderer() -> DocumentRenderer:
    """
    Factory function to get DocumentRenderer instance
    
    Returns:
        DocumentRenderer instance with RAG client
    """
    return DocumentRenderer()
