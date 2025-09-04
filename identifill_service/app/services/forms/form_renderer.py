"""
Form Rendering Service - DOCX to HTML Conversion (Giai đoạn 1)
Đúng theo kế hoạch ban đầu: Mammoth → HTML string → Frontend render
"""

import logging
import requests
import mammoth
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class FormRenderingService:
    """
    Service render DOCX thành HTML tĩnh
    Theo đúng kế hoạch giai đoạn 1: Mammoth → HTML → dangerouslySetInnerHTML
    """
    
    def __init__(self, rag_service_url: str = "http://localhost:8000"):
        self.rag_service_url = rag_service_url
        logger.info(f"FormRenderingService initialized with RAG URL: {rag_service_url}")
    
    async def convert_docx_to_html(self, collection_id: str, doc_id: str, form_filename: str) -> Dict[str, Any]:
        """
        Chuyển đổi DOCX thành HTML sạch bằng Mammoth
        Đúng theo kế hoạch giai đoạn 1
        
        Args:
            collection_id: ID collection
            doc_id: Document ID  
            form_filename: Tên file DOCX
            
        Returns:
            HTML string để frontend render với dangerouslySetInnerHTML
        """
        try:
            # Get form file info từ RAG service
            response = requests.get(
                f"{self.rag_service_url}/api/forms/file/{collection_id}/{doc_id}/{form_filename}",
                timeout=30
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Cannot get form file from RAG service")
            
            file_info = response.json()
            if not file_info.get("success"):
                raise HTTPException(status_code=400, detail="RAG service error")
            
            file_path = file_info["data"]["file_path"]
            
            # Convert DOCX to HTML using Mammoth
            with open(file_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value  # Clean HTML
                conversion_messages = result.messages
            
            # Apply basic styling wrapper
            styled_html = self._apply_basic_styling(html_content)
            
            logger.info(f"✅ Successfully converted DOCX to HTML: {form_filename}")
            logger.info(f"   - HTML length: {len(html_content)} chars")
            logger.info(f"   - Conversion messages: {len(conversion_messages)}")
            
            return {
                "html_content": styled_html,
                "raw_html": html_content,
                "conversion_messages": [str(msg) for msg in conversion_messages],
                "form_metadata": {
                    "collection_id": collection_id,
                    "doc_id": doc_id,
                    "form_filename": form_filename,
                    "conversion_success": True
                }
            }
            
        except requests.RequestException as e:
            logger.error(f"Network error calling RAG service: {e}")
            raise HTTPException(status_code=503, detail="Cannot connect to RAG service")
        except Exception as e:
            logger.error(f"Error converting DOCX to HTML: {e}")
            raise HTTPException(status_code=500, detail=f"DOCX conversion failed: {str(e)}")
    
    def _apply_basic_styling(self, html_content: str) -> str:
        """
        Apply basic wrapper - CSS sẽ ở frontend
        Chỉ wrap HTML trong container div
        """
        return f'<div class="legal-form-content">{html_content}</div>'
    
    def extract_text_placeholders(self, html_content: str) -> List[str]:
        """
        Extract basic placeholders cho giai đoạn 2 (tương lai)
        Hiện tại chỉ tìm pattern đơn giản
        """
        import re
        
        placeholders = []
        
        # Tìm dots pattern (..........)
        dots_pattern = r'\.{3,}'
        dots_matches = re.findall(dots_pattern, html_content)
        placeholders.extend([f"dots_{i}" for i, _ in enumerate(dots_matches)])
        
        # Tìm underscores pattern (__________)
        underscores_pattern = r'_{3,}'
        underscores_matches = re.findall(underscores_pattern, html_content)
        placeholders.extend([f"underscores_{i}" for i, _ in enumerate(underscores_matches)])
        
        logger.info(f"Found {len(placeholders)} potential placeholders for future phases")
        
        return placeholders
