"""
Template Filling Service for CCCD data
Handles downloading templates from rag_service and filling them with CCCD data
"""

import io
import logging
import aiohttp
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class TemplateFillingService:
    def __init__(self, rag_service_url: str = "http://localhost:8000"):
        self.rag_service_url = rag_service_url
        
    async def download_template(self, collection_id: str, doc_id: str, template_name: Optional[str] = None) -> bytes:
        """
        Download template file from rag_service
        
        Args:
            collection_id: Collection ID
            doc_id: Document ID
            template_name: Optional specific template name
            
        Returns:
            Template file content as bytes
        """
        try:
            # Construct URL cho template endpoint mới
            if template_name:
                url = f"{self.rag_service_url}/api/templates/{template_name}"
            else:
                # Fallback to default template
                url = f"{self.rag_service_url}/api/templates/application_template.docx"
            
            logger.info(f"Downloading template from: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        logger.info(f"Downloaded template: {len(content)} bytes")
                        return content
                    else:
                        error_text = await response.text()
                        raise HTTPException(
                            status_code=response.status, 
                            detail=f"Failed to download template: {error_text}"
                        )
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error downloading template: {e}")
            raise HTTPException(
                status_code=503, 
                detail=f"Cannot connect to rag_service: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error downloading template: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Template download failed: {str(e)}"
            )
    
    def prepare_cccd_context(self, cccd_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare CCCD data for template filling
        
        Args:
            cccd_data: Raw CCCD data from scan
            
        Returns:
            Formatted context for template
        """
        # Chuẩn hóa tên placeholder theo yêu cầu
        # Ưu tiên lấy từ scan_* fields trước, sau đó fallback
        context = {
            "scan_ho_ten": cccd_data.get("scan_ho_ten") or cccd_data.get("name") or cccd_data.get("ho_ten", ""),
            "scan_ngay_sinh": cccd_data.get("scan_ngay_sinh") or cccd_data.get("birth_date") or cccd_data.get("ngay_sinh", ""),
            "scan_dia_chi": cccd_data.get("scan_dia_chi") or cccd_data.get("address") or cccd_data.get("dia_chi", ""),
            "scan_cccd": cccd_data.get("scan_cccd") or cccd_data.get("citizen_id") or cccd_data.get("so_cccd", ""),
            "scan_gioi_tinh": cccd_data.get("scan_gioi_tinh") or cccd_data.get("gender") or cccd_data.get("gioi_tinh", "")
        }
        
        # Log để debug
        logger.info(f"Prepared CCCD context: {context}")
        return context
    
    async def fill_template_with_cccd_data(
        self, 
        collection_id: str, 
        doc_id: str, 
        cccd_data: Dict[str, Any],
        template_name: Optional[str] = None
    ) -> bytes:
        """
        Main method: Download template and fill with CCCD data
        
        Args:
            collection_id: Collection ID
            doc_id: Document ID  
            cccd_data: CCCD data from scan
            template_name: Optional specific template name
            
        Returns:
            Filled .docx file as bytes
        """
        try:
            # Step 1: Download template from rag_service
            template_content = await self.download_template(collection_id, doc_id, template_name)
            
            # Step 2: Prepare CCCD data context
            context = self.prepare_cccd_context(cccd_data)
            
            # Step 3: Fill template with data
            filled_content = await self._fill_docx_template(template_content, context)
            
            return filled_content
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in fill_template_with_cccd_data: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Template filling failed: {str(e)}"
            )
    
    async def _fill_docx_template(self, template_content: bytes, context: Dict[str, Any]) -> bytes:
        """
        Fill DOCX template with context data using python-docx-template
        
        Args:
            template_content: Template file content as bytes
            context: Data to fill in template
            
        Returns:
            Filled document as bytes
        """
        try:
            # Import here to avoid issues if library not installed
            try:
                from docxtpl import DocxTemplate
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="python-docx-template not installed. Please install it first."
                )
            
            # Create template from bytes
            template_file = io.BytesIO(template_content)
            doc = DocxTemplate(template_file)
            
            # Fill template with context
            doc.render(context)
            
            # Save to bytes
            output_buffer = io.BytesIO()
            doc.save(output_buffer)
            output_buffer.seek(0)
            
            filled_content = output_buffer.getvalue()
            logger.info(f"Template filled successfully: {len(filled_content)} bytes")
            
            return filled_content
            
        except Exception as e:
            logger.error(f"Error filling DOCX template: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"DOCX template filling failed: {str(e)}"
            )
