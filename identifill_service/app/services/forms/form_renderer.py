"""
Form Rendering Service - DOCX to HTML Conversion (Giai đoạn 1)
Đúng theo kế hoạch ban đầu: Mammoth → HTML string → Frontend render
"""

import io
import json
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import re
import mammoth
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class FormRenderingService:
    """
    Service render DOCX thành HTML tĩnh
    Theo đúng kế hoạch giai đoạn 1: Mammoth → HTML → dangerouslySetInnerHTML
    """
    
    def __init__(self, rag_service_url: Optional[str] = None):
        from app.core.config import settings
        if rag_service_url is None:
            rag_service_url = settings.RAG_SERVICE_URL
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
            # Get form file info từ RAG service (async)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.rag_service_url}/api/forms/file/{collection_id}/{doc_id}/{form_filename}",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=response.status, detail="Cannot get form file from RAG service")
                    
                    file_info = await response.json()
                    if not file_info.get("success"):
                        raise HTTPException(status_code=400, detail="RAG service error")
                    
                    file_path = file_info["data"]["file_path"]
            
            # Convert DOCX to HTML using Mammoth với cấu hình tối giản
            # để tránh lỗi alignment và checkbox
            with open(file_path, "rb") as docx_file:
                # Chỉ sử dụng default style map và không convert images
                options = {
                    "include_default_style_map": True,
                    "ignore_empty_paragraphs": False,
                    # KHÔNG set transform_document để tránh lỗi alignment
                    # KHÔNG set style_map để dùng default
                    # KHÔNG set convert_image để preserve checkboxes
                }
                
                result = mammoth.convert_to_html(docx_file, **options)
                html_content = result.value  # Clean HTML
                conversion_messages = result.messages
                
                # Post-process HTML to fix checkboxes and preserve alignment
                html_content = self._post_process_html(html_content)
            
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
            
        except aiohttp.ClientError as e:
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
    
    def _post_process_html(self, html_content: str) -> str:
        """
        Post-process HTML để fix các vấn đề:
        1. Thay thế broken images thành checkbox symbols
        2. Fix alignment được gán sai
        3. Wrap {{placeholder}} với class cho frontend styling
        """
        import re
        
        # Fix broken checkboxes - replace with proper checkbox symbols
        html_content = re.sub(
            r'<img src="data:image/png;base64," />',
            '☐',  # Unicode checkbox symbol
            html_content
        )
        
        # Fix any other broken base64 images
        html_content = re.sub(
            r'<img src="data:image/[^"]*;base64,[^"]+" />',
            '☐',
            html_content
        )
        
        # 🎯 NEW: Wrap {{placeholder}} với class để frontend dễ styling
        # Pattern: {{scan_ho_ten}} → <span class="placeholder_scan_ho_ten">{{scan_ho_ten}}</span>
        def wrap_placeholder(match):
            placeholder_full = match.group(0)  # {{scan_ho_ten}}
            placeholder_name = match.group(1)  # scan_ho_ten
            class_name = f"placeholder_{placeholder_name}"
            return f'<span class="{class_name}">{placeholder_full}</span>'
        
        # Wrap tất cả {{placeholder}} patterns
        html_content = re.sub(
            r'\{\{([^}]+)\}\}',
            wrap_placeholder,
            html_content
        )
        
        logger.info("🎨 Wrapped placeholders with CSS classes for frontend styling")
        
        # Fix lỗi tất cả đều căn giữa hoặc thiếu alignment
        # Kiểm tra nếu tất cả các <p> đều có style="text-align: center;"
        if html_content.count('style="text-align: center;"') > 10:
            # Remove all center alignment
            html_content = html_content.replace(' style="text-align: center;"', '')
        
        # Áp dụng căn giữa chỉ cho các header (luôn luôn chạy) - Fixed to handle existing style attributes
        html_content = re.sub(
            r'<p[^>]*><strong>(CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM)</strong></p>',
            r'<p style="text-align: center;"><strong>\1</strong></p>',
            html_content
        )
        html_content = re.sub(
            r'<p[^>]*><strong>(Độc lập - Tự do - Hạnh phúc)</strong></p>',
            r'<p style="text-align: center;"><strong>\1</strong></p>',
            html_content
        )
        html_content = re.sub(
            r'<p[^>]*><strong>(TỜ KHAI ĐĂNG KÝ KHAI SINH)</strong></p>',
            r'<p style="text-align: center;"><strong>\1</strong></p>',
            html_content
        )
        
        # Phần người yêu cầu căn giữa
        html_content = re.sub(
            r'<p><strong>(Người yêu cầu)</strong></p>',
            r'<p style="text-align: center;"><strong>\1</strong></p>',
            html_content
        )
        
        # Phần "Làm tại" căn phải - Fixed regex để handle các <p> có attributes
        html_content = re.sub(
            r'<p[^>]*>(\s*Làm tại[^<]*)</p>',
            r'<p style="text-align: right;">\1</p>',
            html_content
        )
        
        # Thêm pattern cho các dòng có format ngày tháng năm (chỉ những dòng thực sự chứa ngày tháng làm việc)
        # Chỉ match những dòng bắt đầu với khoảng trắng hoặc dấu chấm để tránh match title
        html_content = re.sub(
            r'<p[^>]*>(\s+.*ngày\s+\.\.\.\s+tháng\s+\.\.\.\s+năm[^<]*)</p>',
            r'<p style="text-align: right;">\1</p>',
            html_content
        )
        
        # Convert CSS classes to inline styles (fallback)
        html_content = html_content.replace('<p class="center">', '<p style="text-align: center;">')
        html_content = html_content.replace('<p class="right">', '<p style="text-align: right;">')
        html_content = html_content.replace('<p class="left">', '<p style="text-align: left;">')
        html_content = html_content.replace('<p class="justify">', '<p style="text-align: justify;">')
        
        return html_content
    
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
