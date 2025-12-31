# -*- coding: utf-8 -*-
"""
Form Templates Router - Hybrid template management for admin.

Endpoints:
- POST /admin/templates/analyze: Upload DOCX, detect fillable fields
- POST /admin/templates/create: Create template with confirmed placeholders
- GET /admin/templates/{form_id}/fields: Extract placeholders from saved template
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import logging
import os
import io
import re
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/templates", tags=["Form Templates"])

# Service URLs
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8010")


# ============= MODELS =============

class DetectedFieldResponse(BaseModel):
    """A detected fillable field"""
    id: str
    label: str
    field_type: str
    paragraph_index: int
    suggested_name: str
    confidence: float
    original_text: str = ""


class AnalyzeResponse(BaseModel):
    """Response from analyzing a DOCX template"""
    success: bool
    fields: List[DetectedFieldResponse]
    total_fields: int
    errors: List[str] = []


class ConfirmedField(BaseModel):
    """A field confirmed by admin"""
    paragraph_index: int
    field_name: str
    label: str = ""


class CreateTemplateRequest(BaseModel):
    """Request to create template with placeholders"""
    form_id: str  # UUID of form record
    confirmed_fields: List[ConfirmedField]


class CreateTemplateResponse(BaseModel):
    """Response from creating template"""
    success: bool
    template_path: Optional[str] = None
    placeholders: List[str] = []
    message: str = ""


class ExtractFieldsResponse(BaseModel):
    """Response with extracted placeholder names"""
    success: bool
    placeholders: List[str]
    message: str = ""


# ============= TEMPLATE PROCESSOR (embedded) =============
# Note: This is a simplified version. In production, import from form-service.

class TemplateProcessor:
    """Simplified template processor for admin-service."""
    
    LABEL_MAPPINGS = {
        'họ và tên': 'ho_ten',
        'họ, chữ đệm, tên': 'ho_ten',
        'ngày sinh': 'ngay_sinh',
        'năm sinh': 'nam_sinh',
        'giới tính': 'gioi_tinh',
        'dân tộc': 'dan_toc',
        'quốc tịch': 'quoc_tich',
        'nơi sinh': 'noi_sinh',
        'nơi cư trú': 'noi_cu_tru',
        'giấy tờ tùy thân': 'giay_to',
        'kính gửi': 'kinh_gui',
        'làm tại': 'lam_tai',
    }
    
    def __init__(self):
        self._field_counter = 0
        self._seen_names: Dict[str, int] = {}
    
    def analyze(self, docx_content: bytes) -> Dict:
        """Analyze DOCX to detect fillable fields."""
        try:
            from docx import Document
            
            self._field_counter = 0
            self._seen_names = {}
            fields = []
            
            doc = Document(io.BytesIO(docx_content))
            para_idx = 0
            
            # Process tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            detected = self._analyze_paragraph(para.text, para_idx)
                            fields.extend(detected)
                            para_idx += 1
            
            # Process paragraphs
            for para in doc.paragraphs:
                detected = self._analyze_paragraph(para.text, para_idx)
                fields.extend(detected)
                para_idx += 1
            
            return {
                'success': True,
                'fields': fields,
                'total_fields': len(fields),
                'errors': []
            }
            
        except Exception as e:
            logger.error(f"Analyze error: {e}")
            return {
                'success': False,
                'fields': [],
                'total_fields': 0,
                'errors': [str(e)]
            }
    
    def _analyze_paragraph(self, text: str, para_idx: int) -> List[Dict]:
        """Analyze single paragraph."""
        if not text or not text.strip():
            return []
        
        # Skip continuation lines
        if text.replace('\t', '').replace(' ', '').strip() == '':
            return []
        
        fields = []
        
        # Pattern 1: "Label: ......." (dots after colon)
        for m in re.finditer(r'([A-Za-zÀ-ỹ][^:\t\n\.]{1,50}?)(?:\s*\(\d+\))?\s*[:：]\s*([\.…]{4,})', text):
            label = self._clean_label(m.group(1))
            if label and len(label) > 1:
                fields.append(self._create_field(label, 'dots', para_idx, m.group(2), 0.95))
        
        # Pattern 2: "Label: TAB"
        for m in re.finditer(r'([A-Za-zÀ-ỹ][^:\t\n]{1,50}?)(?:\s*\(\d+\))?\s*[:：]\s*\t', text):
            label = self._clean_label(m.group(1))
            if label and len(label) > 1:
                if not any(f['label'] == label and f['paragraph_index'] == para_idx for f in fields):
                    fields.append(self._create_field(label, 'tab', para_idx, '\\t', 0.7))
        
        # Pattern 3: Date
        if re.search(r'ngày\s*[\.…\t]+\s*tháng\s*[\.…\t]+\s*năm', text, re.IGNORECASE):
            for part in ['ngày', 'tháng', 'năm']:
                fields.append(self._create_field(part, 'date', para_idx, 'date', 0.9))
        
        return fields
    
    def _clean_label(self, label: str) -> str:
        label = re.sub(r'\s*\(\d+\)\s*', '', label)
        return label.strip().rstrip(':').rstrip('：').strip()
    
    def _normalize_label(self, label: str) -> str:
        label_lower = label.lower().strip()
        for vn, en in self.LABEL_MAPPINGS.items():
            if vn in label_lower:
                return en
        
        import unicodedata
        nfkd = unicodedata.normalize('NFKD', label_lower)
        ascii_label = ''.join(c for c in nfkd if not unicodedata.combining(c))
        snake = re.sub(r'[^a-z0-9]+', '_', ascii_label)
        return snake.strip('_')[:30] or 'field'
    
    def _create_field(self, label: str, ftype: str, para_idx: int, original: str, conf: float) -> Dict:
        self._field_counter += 1
        base_name = self._normalize_label(label)
        
        if base_name in self._seen_names:
            self._seen_names[base_name] += 1
            suggested = f"{base_name}_{self._seen_names[base_name]}"
        else:
            self._seen_names[base_name] = 1
            suggested = base_name
        
        return {
            'id': f"field_{self._field_counter}",
            'label': label,
            'field_type': ftype,
            'paragraph_index': para_idx,
            'suggested_name': suggested,
            'confidence': conf,
            'original_text': original[:30] if original else ""
        }
    
    def create_template(self, docx_content: bytes, confirmed_fields: List[Dict]) -> Dict:
        """Create template with placeholders."""
        try:
            from docx import Document
            
            doc = Document(io.BytesIO(docx_content))
            placeholders = []
            
            # Group by paragraph
            para_fields: Dict[int, List[Dict]] = {}
            for f in confirmed_fields:
                pi = f.get('paragraph_index', -1)
                if pi >= 0:
                    para_fields.setdefault(pi, []).append(f)
            
            para_idx = 0
            
            # Process tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            if para_idx in para_fields:
                                for f in para_fields[para_idx]:
                                    self._insert_placeholder(para, f)
                                    placeholders.append(f.get('field_name', f'field_{para_idx}'))
                            para_idx += 1
            
            # Process paragraphs
            for para in doc.paragraphs:
                if para_idx in para_fields:
                    for f in para_fields[para_idx]:
                        self._insert_placeholder(para, f)
                        placeholders.append(f.get('field_name', f'field_{para_idx}'))
                para_idx += 1
            
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            
            return {
                'success': True,
                'template_bytes': output.getvalue(),
                'placeholders': placeholders
            }
            
        except Exception as e:
            logger.error(f"Create template error: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    def _insert_placeholder(self, para, field: Dict):
        """Insert {{placeholder}} into paragraph.
        
        Strategy: Track which runs have been replaced to avoid replacing
        the same position multiple times when a paragraph has multiple fields.
        """
        field_name = field.get('field_name', 'field')
        placeholder = f"{{{{{field_name}}}}}"
        
        # Mark which run was replaced to avoid duplicate replacements
        replaced = False
        
        for run_idx, run in enumerate(para.runs):
            # Skip if this run was already replaced (has placeholder)
            if '{{field_' in run.text:
                continue
                
            # Replace dots
            if re.search(r'[\.…]{4,}', run.text):
                run.text = re.sub(
                    r'([\.…]{4,})',
                    lambda m: placeholder + '.' * max(6, len(m.group(1)) - len(placeholder)),
                    run.text,
                    count=1
                )
                replaced = True
                return
            # Replace tab
            if run.text == '\t':
                run.text = placeholder
                replaced = True
                return
        
        # If no dots/tabs found, try to append at end of paragraph
        if not replaced and para.runs:
            # Add placeholder at the end
            last_run = para.runs[-1]
            last_run.text += f" {placeholder}"
    
    def extract_placeholders(self, docx_content: bytes) -> List[str]:
        """Extract placeholder names from template."""
        try:
            from docx import Document
            
            doc = Document(io.BytesIO(docx_content))
            all_text = ""
            
            for para in doc.paragraphs:
                all_text += para.text + "\n"
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        all_text += cell.text + "\n"
            
            matches = re.findall(r'\{\{([^}]+)\}\}', all_text)
            return list(dict.fromkeys(matches))
            
        except Exception as e:
            logger.error(f"Extract error: {e}")
            return []


# Global processor instance
_processor = TemplateProcessor()


# ============= ENDPOINTS =============

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_template(file: UploadFile = File(...)):
    """
    Analyze uploaded DOCX to detect fillable fields.
    
    This is Step 1 of the hybrid workflow:
    1. Admin uploads DOCX with dots (........)
    2. Backend detects and suggests fields
    3. Returns list for admin to review/edit
    
    Args:
        file: DOCX file to analyze
        
    Returns:
        List of detected fields with suggested names
    """
    if not file.filename or not file.filename.endswith(('.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")
    
    try:
        content = await file.read()
        
        processor = TemplateProcessor()
        result = processor.analyze(content)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('errors', ['Analysis failed']))
        
        return AnalyzeResponse(
            success=True,
            fields=[DetectedFieldResponse(**f) for f in result['fields']],
            total_fields=result['total_fields']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=CreateTemplateResponse)
async def create_template(
    file: UploadFile = File(...),
    form_id: str = Form(...),
    confirmed_fields: str = Form(...)  # JSON string
):
    """
    Create template with placeholders at confirmed field positions.
    
    This is Step 2 of the hybrid workflow:
    1. Admin reviews detected fields
    2. Admin confirms/edits field names
    3. Backend creates template with {{placeholders}}
    4. Template is saved to MinIO
    
    Args:
        file: Original DOCX file
        form_id: UUID of form record in database
        confirmed_fields: JSON array of confirmed fields
            [{"paragraph_index": 0, "field_name": "ho_ten", "label": "Họ tên"}, ...]
    
    Returns:
        Template path in MinIO and list of placeholders
    """
    import json
    
    if not file.filename or not file.filename.endswith(('.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")
    
    try:
        # Parse confirmed fields
        fields_list = json.loads(confirmed_fields)
        
        if not fields_list:
            raise HTTPException(status_code=400, detail="No fields confirmed")
        
        content = await file.read()
        
        processor = TemplateProcessor()
        result = processor.create_template(content, fields_list)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('errors', ['Template creation failed']))
        
        template_bytes = result['template_bytes']
        placeholders = result['placeholders']
        
        # Upload to storage-service
        # Path: forms/templates/{form_id}_template.docx
        storage_path = f"forms/templates/{form_id}_template.docx"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": (f"{form_id}_template.docx", template_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            params = {"folder": "forms/templates"}
            
            response = await client.post(
                f"{STORAGE_SERVICE_URL}/upload",
                files=files,
                params=params
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Storage upload failed: {response.text}")
                raise HTTPException(status_code=500, detail=f"Storage upload failed: {response.text}")
            
            upload_result = response.json()
            template_path = upload_result.get('file_path', storage_path)
        
        logger.info(f"Template created: {template_path} with {len(placeholders)} placeholders")
        
        return CreateTemplateResponse(
            success=True,
            template_path=template_path,
            placeholders=placeholders,
            message=f"Template created with {len(placeholders)} fields"
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid confirmed_fields JSON")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create template error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def preview_template(
    file: UploadFile = File(...),
    selected_indices: str = Form(...)  # "0,1,2,5,7" - comma-separated indices
):
    """
    Create temporary preview template with {{field_N}} placeholders.
    
    Used by Visual Mode in frontend to render document with placeholders
    for user to click and select/deselect.
    
    Args:
        file: Original DOCX file
        selected_indices: Comma-separated indices of detected positions to show
            E.g., "0,1,2,5,7,10" - will replace positions 0,1,2,5,7,10 with {{field_0}}, {{field_1}}, ...
    
    Returns:
        Binary DOCX file with placeholders inserted
    """
    import json
    from fastapi.responses import StreamingResponse
    
    if not file.filename or not file.filename.endswith(('.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")
    
    try:
        # Parse indices
        indices = [int(x.strip()) for x in selected_indices.split(',') if x.strip()]
        
        if not indices:
            raise HTTPException(status_code=400, detail="No indices provided")
        
        content = await file.read()
        
        # First, detect all positions
        processor = TemplateProcessor()
        analyze_result = processor.analyze(content)
        
        if not analyze_result.get('success'):
            raise HTTPException(status_code=500, detail="Failed to analyze document")
        
        detected_fields = analyze_result['fields']
        
        # Filter by selected indices
        confirmed_fields = []
        for idx in indices:
            if idx < len(detected_fields):
                field = detected_fields[idx]
                confirmed_fields.append({
                    'paragraph_index': field['paragraph_index'],
                    'field_name': f'field_{idx}',  # Use index as field name for preview
                    'label': field.get('label', '')
                })
        
        if not confirmed_fields:
            raise HTTPException(status_code=400, detail="No valid positions found for selected indices")
        
        # Create preview template
        result = processor.create_template(content, confirmed_fields)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('errors', ['Preview creation failed']))
        
        template_bytes = result['template_bytes']
        
        logger.info(f"Preview created with {len(confirmed_fields)} placeholders for indices: {indices}")
        
        # Return as binary stream
        return StreamingResponse(
            io.BytesIO(template_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename=preview_template.docx"
            }
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid selected_indices format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview template error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{form_id}/fields", response_model=ExtractFieldsResponse)
async def get_template_fields(form_id: str):
    """
    Extract placeholder names from a saved template.
    
    Used by frontend to know what fields to render in the fill form.
    
    Args:
        form_id: UUID of form record
        
    Returns:
        List of placeholder names (e.g., ["ho_ten", "ngay_sinh", ...])
    """
    try:
        # Download template from storage
        template_path = f"forms/templates/{form_id}_template.docx"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{STORAGE_SERVICE_URL}/download",
                params={"file_path": template_path}
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Template not found")
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Storage error: {response.text}")
            
            template_content = response.content
        
        processor = TemplateProcessor()
        placeholders = processor.extract_placeholders(template_content)
        
        return ExtractFieldsResponse(
            success=True,
            placeholders=placeholders,
            message=f"Found {len(placeholders)} fields"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get fields error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
