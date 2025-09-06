"""
Template Filling Service for CCCD data
Unified service combining template download and smart CCCD auto-filling
Integrates FieldExtractor and AutoFillService logic
"""

import io
import logging
import aiohttp
import tempfile
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from docx import Document

logger = logging.getLogger(__name__)

class TemplateFillingService:
    def __init__(self, rag_service_url: str = "http://localhost:8000"):
        self.rag_service_url = rag_service_url
        self.placeholder_pattern = re.compile(r'\{\{([^}]+)\}\}')
        # Default CCCD field mapping
        self.cccd_field_mapping = {
            "scan_ho_ten": ["ho_ten", "ho_va_ten", "full_name"],
            "scan_cccd": ["so_cccd", "cccd", "citizen_id"],
            "scan_ngay_sinh": ["ngay_sinh", "date_of_birth"],
            "scan_gioi_tinh": ["gioi_tinh", "gender"],
            "scan_dia_chi": ["dia_chi", "address"],
            "scan_ngay_cap": ["ngay_cap"],
            "scan_noi_cap": ["noi_cap"]
        }
        logger.info("TemplateFillingService initialized with unified logic")
        
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
            # Use forms endpoint instead of templates for better structure alignment
            if template_name:
                # Use forms download endpoint that matches physical directory structure
                url = f"{self.rag_service_url}/api/forms/file/{collection_id}/{doc_id}/{template_name}/download"
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
    
    def extract_placeholders_from_docx(self, docx_content: bytes) -> Dict[str, Any]:
        """
        Extract all {{placeholder}} from DOCX content using integrated FieldExtractor logic
        
        Returns:
        {
            "scan_fields": [...],  # {{scan_*}} fields from CCCD
            "form_fields": [...],  # {{form_*}} fields need user input  
            "all_fields": [...]    # All unique placeholders
        }
        """
        try:
            # Create temporary document from bytes
            temp_file = io.BytesIO(docx_content)
            doc = Document(temp_file)
            
            # Extract all text content
            all_text = ""
            for paragraph in doc.paragraphs:
                all_text += paragraph.text + "\n"
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        all_text += cell.text + "\n"
            
            # Find all placeholders
            matches = self.placeholder_pattern.findall(all_text)
            unique_fields = list(set(matches))
            
            # Categorize by prefix
            scan_fields = [field for field in unique_fields if field.startswith('scan_')]
            form_fields = [field for field in unique_fields if field.startswith('form_')]
            
            logger.info(f"📋 Extracted placeholders: {len(scan_fields)} scan, {len(form_fields)} form")
            
            return {
                "scan_fields": scan_fields,
                "form_fields": form_fields, 
                "all_fields": unique_fields
            }
            
        except Exception as e:
            logger.error(f"Error extracting placeholders: {e}")
            return {"scan_fields": [], "form_fields": [], "all_fields": []}

    def prepare_smart_cccd_context(self, cccd_data: Dict[str, Any], template_placeholders: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Smart context preparation using scan_xxx and form_xxx logic
        Auto-maps CCCD data to template placeholders intelligently
        
        Args:
            cccd_data: Raw CCCD data from scan
            template_placeholders: Optional list of placeholders from template
            
        Returns:
            Smart-mapped context for template filling
        """
        context = {}
        
        # 1. Direct mapping for scan_* fields (CCCD auto-fill)
        for scan_field, possible_keys in self.cccd_field_mapping.items():
            # Try direct scan_* key first
            if scan_field in cccd_data:
                context[scan_field] = cccd_data[scan_field]
            else:
                # Try alternative keys
                for key in possible_keys:
                    if key in cccd_data:
                        context[scan_field] = cccd_data[key]
                        break
                else:
                    context[scan_field] = ""  # Empty if not found
        
        # 2. Add any additional data as-is (for form_* fields if provided)
        for key, value in cccd_data.items():
            if key not in context:
                context[key] = value
        
        # 3. Template-specific mapping if placeholders provided
        if template_placeholders:
            for placeholder in template_placeholders:
                if placeholder not in context:
                    # Try to find matching value from cccd_data
                    context[placeholder] = self._find_best_match(placeholder, cccd_data)
        
        logger.info(f"🎯 Smart context prepared: {len(context)} fields mapped")
        logger.debug(f"Context details: {context}")
        return context
    
    def _find_best_match(self, placeholder: str, cccd_data: Dict[str, Any]) -> str:
        """Find best matching value for a placeholder from CCCD data"""
        # Direct match first
        if placeholder in cccd_data:
            return str(cccd_data[placeholder])
        
        # Pattern matching for common variations
        placeholder_lower = placeholder.lower()
        for key, value in cccd_data.items():
            key_lower = key.lower()
            if (placeholder_lower in key_lower or 
                key_lower in placeholder_lower or
                any(part in key_lower for part in placeholder_lower.split('_'))):
                return str(value)
        
        return ""  # Default empty

    def prepare_cccd_context(self, cccd_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy method - redirects to smart context preparation
        """
        return self.prepare_smart_cccd_context(cccd_data)
    
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
            
            # Step 2: Extract placeholders from template for smart mapping
            placeholder_info = self.extract_placeholders_from_docx(template_content)
            logger.info(f"📋 Template analysis: {len(placeholder_info['scan_fields'])} scan fields, {len(placeholder_info['form_fields'])} form fields")
            
            # Step 3: Prepare smart CCCD context using extracted placeholders
            context = self.prepare_smart_cccd_context(cccd_data, placeholder_info['all_fields'])
            
            # Step 4: Fill template with smart-mapped data
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
