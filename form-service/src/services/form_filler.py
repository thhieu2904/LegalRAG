"""
Form Filler Service
Fills DOCX templates with provided data and returns filled document.

Features:
- Dot-padding: Keeps trailing dots to preserve formatting
- Run-level replacement: Preserves text styles
"""

import io
import re
import logging
import httpx
from typing import Dict, Any, Optional, Tuple

from config import settings

logger = logging.getLogger(__name__)


class FormFiller:
    """
    Fills DOCX form templates with data.
    Replaces {{placeholder}} with actual values + dot padding to preserve format.
    
    Example:
        Template: "Họ tên: {{ho_ten}}............"
        Data: {"ho_ten": "Nguyễn Văn A"}
        Result: "Họ tên: Nguyễn Văn A..........."
    """
    
    # Minimum dots to keep after value
    MIN_PADDING_DOTS = 1
    
    def __init__(self):
        self.storage_url = settings.STORAGE_SERVICE_URL
        self.timeout = settings.STORAGE_TIMEOUT
        logger.info(f"FormFiller initialized with storage: {self.storage_url}")
    
    async def fill(self, template_path: str, data: Dict[str, Any]) -> tuple[bytes | None, str | None, Dict[str, Any] | None]:
        """
        Fill template with provided data.
        
        Args:
            template_path: Path in MinIO (e.g., forms/{doc_id}/{form_file})
            data: Dictionary with placeholder values {scan_ho_ten: "...", form_nghe_nghiep: "..."}
            
        Returns:
            Tuple of (filled_docx_bytes, error_message, validation_info)
        """
        try:
            # Download template
            template_content = await self._download_template(template_path)
            if not template_content:
                return None, f"Failed to download template: {template_path}", None
            
            # Extract placeholders from template
            placeholders = self._extract_placeholders_from_docx(template_content)
            logger.info(f"Template has {len(placeholders)} placeholders")
            
            # Prepare context (map data to placeholders)
            context = self._prepare_context(data, placeholders)
            
            # Calculate validation info
            filled_count = len([v for v in context.values() if v])
            missing_fields = [k for k, v in context.items() if not v]
            
            validation_info = {
                "total_fields": len(placeholders),
                "filled_fields": filled_count,
                "missing_fields": missing_fields
            }
            
            # Fill template
            filled_content = self._fill_docx(template_content, context)
            if not filled_content:
                return None, "Failed to fill template", validation_info
            
            logger.info(f"✅ Filled template: {template_path}, {filled_count}/{len(placeholders)} fields")
            return filled_content, None, validation_info
            
        except Exception as e:
            logger.error(f"Fill error: {e}")
            return None, f"Fill error: {str(e)}", None
    
    async def _download_template(self, template_path: str) -> bytes | None:
        """Download template from storage-service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.storage_url}/download",
                    params={"file_path": template_path}
                )
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Download failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    def _extract_placeholders_from_docx(self, docx_content: bytes) -> list[str]:
        """Extract {{placeholder}} names from DOCX content"""
        try:
            from docx import Document
            
            doc = Document(io.BytesIO(docx_content))
            
            all_text = ""
            for paragraph in doc.paragraphs:
                all_text += paragraph.text + "\n"
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        all_text += cell.text + "\n"
            
            # Find all {{placeholder}} patterns
            matches = re.findall(r'\{\{([^}]+)\}\}', all_text)
            unique_placeholders = list(set(matches))
            
            return unique_placeholders
            
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return []
    
    def _prepare_context(self, data: Dict[str, Any], placeholders: list[str]) -> Dict[str, str]:
        """
        Prepare context by mapping input data to template placeholders.
        Direct mapping: placeholder name = data key (field_1 = field_1)
        """
        context = {}
        
        for placeholder in placeholders:
            if placeholder in data:
                value = data[placeholder]
                context[placeholder] = str(value) if value is not None else ""
            else:
                context[placeholder] = ""  # Empty string for missing values
        
        filled_count = len([v for v in context.values() if v])
        logger.debug(f"Context prepared: {filled_count}/{len(placeholders)} filled")
        
        return context
    
    def _fill_docx(self, template_content: bytes, context: Dict[str, str]) -> bytes | None:
        """
        Fill DOCX template with dot-padding to preserve formatting.
        
        Uses run-level replacement instead of docxtpl to keep trailing dots.
        Pattern: {{field_id}}.... → value........
        """
        try:
            from docx import Document
            
            doc = Document(io.BytesIO(template_content))
            filled_count = 0
            
            def process_runs(runs):
                """Process runs in a paragraph, replacing placeholders with values + dots."""
                nonlocal filled_count
                
                for run in runs:
                    text = run.text
                    
                    # Find all placeholders in this run
                    for field_id, value in context.items():
                        placeholder = f"{{{{{field_id}}}}}"
                        
                        if placeholder not in text:
                            continue
                        
                        # Pattern: {{field}}[dots] - capture dots after placeholder
                        pattern = re.escape(placeholder) + r'([\.…]*)'
                        match = re.search(pattern, text)
                        
                        if not match:
                            continue
                        
                        original_dots = match.group(1)
                        total_space = len(placeholder) + len(original_dots)
                        
                        if value:  # Has value - replace with value + padding dots
                            # Calculate padding: value + dots to fill original space
                            value_len = len(value)
                            padding_dots = max(self.MIN_PADDING_DOTS, total_space - value_len)
                            
                            # Replace with value + padding dots
                            replacement = value + ('.' * padding_dots)
                            text = re.sub(pattern, replacement, text, count=1)
                            filled_count += 1
                            logger.debug(f"Filled '{field_id}' = '{value}' ({padding_dots} dots)")
                        
                        else:  # Empty value - restore original dots (remove placeholder)
                            # Replace {{field_N}} with dots to match original length
                            # Example: {{field_5}}...... → ................. (restore to dots only)
                            restored_dots = '.' * total_space
                            text = re.sub(pattern, restored_dots, text, count=1)
                            logger.debug(f"Restored '{field_id}' to {total_space} dots (empty value)")
                    
                    run.text = text
            
            # Process all paragraphs in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            process_runs(para.runs)
            
            # Process main document paragraphs
            for para in doc.paragraphs:
                process_runs(para.runs)
            
            logger.info(f"Filled {filled_count} placeholders with dot-padding")
            
            # Save to bytes
            output_buffer = io.BytesIO()
            doc.save(output_buffer)
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except ImportError:
            logger.error("python-docx not installed")
            return None
        except Exception as e:
            logger.error(f"Fill DOCX error: {e}")
            return None
    
    def generate_filename(
        self, 
        form_name: str, 
        session_id: str, 
        cccd_number: str | None = None
    ) -> str:
        """
        Generate filename for filled form.
        Format: {cccd}_{form-name}.docx or {form-name}.docx
        """
        # Vietnamese to ASCII mapping for common chars
        vn_map = {
            'đ': 'd', 'Đ': 'D',
            'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        }
        
        # Convert Vietnamese chars
        safe_name = form_name.lower()
        for vn_char, ascii_char in vn_map.items():
            safe_name = safe_name.replace(vn_char.lower(), ascii_char)
        
        # Remove remaining special chars, keep alphanumeric, spaces and hyphens
        safe_name = re.sub(r'[^a-z0-9\s-]', '', safe_name)
        safe_name = re.sub(r'\s+', '-', safe_name.strip())
        safe_name = safe_name[:50]  # Limit length
        
        if cccd_number and len(cccd_number) == 12:
            return f"{cccd_number}_{safe_name}.docx"
        else:
            return f"{safe_name}.docx"
    
    def generate_storage_path(
        self,
        session_id: str,
        filename: str
    ) -> str:
        """
        Generate storage path for filled form.
        Format: user_forms/{session_id}/{filename}
        """
        return f"user_forms/{session_id}/{filename}"
