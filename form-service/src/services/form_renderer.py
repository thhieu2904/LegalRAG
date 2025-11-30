"""
Form Renderer Service
Converts DOCX templates to HTML for frontend display.
Downloads template from storage-service, converts using mammoth.
"""

import io
import re
import logging
import httpx
import mammoth

from config import settings
from src.models import FormRenderResponse

logger = logging.getLogger(__name__)


class FormRenderer:
    """
    Renders DOCX form templates to HTML.
    Wraps placeholders with CSS classes for styling.
    """
    
    def __init__(self):
        self.storage_url = settings.STORAGE_SERVICE_URL
        self.timeout = settings.STORAGE_TIMEOUT
        logger.info(f"FormRenderer initialized with storage: {self.storage_url}")
    
    async def render(self, template_path: str) -> FormRenderResponse:
        """
        Render DOCX template to HTML.
        
        Args:
            template_path: Path in MinIO (e.g., forms/{doc_id}/{form_file})
            
        Returns:
            FormRenderResponse with HTML content and placeholders
        """
        try:
            # Download template from storage-service
            docx_content = await self._download_template(template_path)
            if not docx_content:
                return FormRenderResponse(
                    success=False,
                    message=f"Failed to download template: {template_path}"
                )
            
            # Convert DOCX to HTML
            html_content = self._convert_to_html(docx_content)
            if not html_content:
                return FormRenderResponse(
                    success=False,
                    message="Failed to convert DOCX to HTML"
                )
            
            # Post-process HTML
            processed_html = self._post_process_html(html_content)
            
            # Extract placeholders
            placeholders = self._extract_placeholders(processed_html)
            
            # Wrap with styling container
            styled_html = f'<div class="legal-form-content">{processed_html}</div>'
            
            logger.info(f"✅ Rendered template: {template_path}, {len(placeholders)} placeholders")
            
            return FormRenderResponse(
                success=True,
                html_content=styled_html,
                raw_html=processed_html,
                placeholders=placeholders,
                message="Template rendered successfully"
            )
            
        except Exception as e:
            logger.error(f"Render error: {e}")
            return FormRenderResponse(
                success=False,
                message=f"Render error: {str(e)}"
            )
    
    async def _download_template(self, template_path: str) -> bytes | None:
        """Download template file from storage-service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.storage_url}/download",
                    params={"file_path": template_path}
                )
                
                if response.status_code == 200:
                    logger.debug(f"Downloaded template: {len(response.content)} bytes")
                    return response.content
                else:
                    logger.error(f"Download failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    def _convert_to_html(self, docx_content: bytes) -> str | None:
        """Convert DOCX bytes to HTML using mammoth"""
        try:
            docx_stream = io.BytesIO(docx_content)
            
            result = mammoth.convert_to_html(
                docx_stream,
                include_default_style_map=True,
                ignore_empty_paragraphs=False
            )
            
            html_content = result.value
            
            if result.messages:
                for msg in result.messages:
                    logger.debug(f"Mammoth message: {msg}")
            
            return html_content
            
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return None
    
    def _post_process_html(self, html_content: str) -> str:
        """
        Post-process HTML:
        1. Fix broken checkbox images
        2. Wrap {{placeholder}} with CSS classes
        3. Fix alignment for legal document headers
        """
        # Fix broken checkboxes
        html_content = re.sub(
            r'<img src="data:image/png;base64," />',
            '☐',
            html_content
        )
        html_content = re.sub(
            r'<img src="data:image/[^"]*;base64,[^"]+" />',
            '☐',
            html_content
        )
        
        # Wrap {{placeholder}} with CSS classes
        def wrap_placeholder(match):
            placeholder_full = match.group(0)  # {{scan_ho_ten}}
            placeholder_name = match.group(1)  # scan_ho_ten
            return f'<span class="placeholder_{placeholder_name}">{placeholder_full}</span>'
        
        html_content = re.sub(r'\{\{([^}]+)\}\}', wrap_placeholder, html_content)
        
        # Fix over-centered alignment
        if html_content.count('style="text-align: center;"') > 10:
            html_content = html_content.replace(' style="text-align: center;"', '')
        
        # Center legal document headers
        header_patterns = [
            (r'<p[^>]*><strong>(CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM)</strong></p>',
             r'<p style="text-align: center;"><strong>\1</strong></p>'),
            (r'<p[^>]*><strong>(Độc lập - Tự do - Hạnh phúc)</strong></p>',
             r'<p style="text-align: center;"><strong>\1</strong></p>'),
            (r'<p[^>]*><strong>(TỜ KHAI[^<]*)</strong></p>',
             r'<p style="text-align: center;"><strong>\1</strong></p>'),
        ]
        
        for pattern, replacement in header_patterns:
            html_content = re.sub(pattern, replacement, html_content)
        
        # Right-align date lines
        html_content = re.sub(
            r'<p[^>]*>(\s*Làm tại[^<]*)</p>',
            r'<p style="text-align: right;">\1</p>',
            html_content
        )
        html_content = re.sub(
            r'<p[^>]*>(\s+.*ngày\s+\.\.\.\s+tháng\s+\.\.\.\s+năm[^<]*)</p>',
            r'<p style="text-align: right;">\1</p>',
            html_content
        )
        
        return html_content
    
    def _extract_placeholders(self, html_content: str) -> list[str]:
        """Extract all {{placeholder}} names from HTML"""
        matches = re.findall(r'\{\{([^}]+)\}\}', html_content)
        unique_placeholders = list(set(matches))
        
        # Sort: scan_* first, then form_*
        scan_fields = [p for p in unique_placeholders if p.startswith('scan_')]
        form_fields = [p for p in unique_placeholders if p.startswith('form_')]
        other_fields = [p for p in unique_placeholders if not p.startswith(('scan_', 'form_'))]
        
        return sorted(scan_fields) + sorted(form_fields) + sorted(other_fields)
