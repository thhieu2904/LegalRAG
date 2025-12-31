# -*- coding: utf-8 -*-
"""
Template Processor Service - Unified hybrid approach for form template management.

Workflow:
1. Analyze: Detect fillable fields (dots patterns) in DOCX
2. Create: Insert {{placeholders}} at confirmed positions
3. Extract: Get placeholder names from template for frontend

This module consolidates form_field_detector.py and form_template_converter.py
into a single, clean implementation.
"""

import io
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class DetectedField:
    """A detected fillable field from analyzing DOCX"""
    id: str                          # Unique ID: field_1, field_2, ...
    label: str                       # Label text before fill area
    field_type: str                  # 'dots', 'tab', 'dots_label'
    paragraph_index: int             # Position in document
    suggested_name: str              # Suggested field_id based on label
    confidence: float = 0.8          # Detection confidence (0-1)
    original_text: str = ""          # Original dots/tab pattern
    full_paragraph: str = ""         # Complete paragraph text
    context_before: List[str] = field(default_factory=list)  # 2-3 paragraphs before
    context_after: List[str] = field(default_factory=list)   # 2-3 paragraphs after


@dataclass
class AnalyzeResult:
    """Result from analyzing a DOCX template"""
    success: bool
    fields: List[DetectedField] = field(default_factory=list)
    total_fields: int = 0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'fields': [asdict(f) for f in self.fields],
            'total_fields': self.total_fields,
            'errors': self.errors
        }


@dataclass  
class CreateTemplateResult:
    """Result from creating a template with placeholders"""
    success: bool
    template_bytes: Optional[bytes] = None
    placeholders: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class TemplateProcessor:
    """
    Unified template processor for hybrid workflow.
    
    Usage:
        processor = TemplateProcessor()
        
        # Step 1: Analyze DOCX to detect fillable fields
        result = processor.analyze(docx_bytes)
        
        # Step 2: Admin reviews and confirms fields
        # (happens on frontend)
        
        # Step 3: Create template with placeholders
        template = processor.create_template(docx_bytes, confirmed_fields)
        
        # Later: Extract placeholders from template
        placeholders = processor.extract_placeholders(template_bytes)
    """
    
    # Vietnamese label mappings for better field naming
    LABEL_MAPPINGS = {
        'họ và tên': 'ho_ten',
        'họ, chữ đệm, tên': 'ho_ten', 
        'họ tên': 'ho_ten',
        'ngày sinh': 'ngay_sinh',
        'năm sinh': 'nam_sinh',
        'giới tính': 'gioi_tinh',
        'dân tộc': 'dan_toc',
        'quốc tịch': 'quoc_tich',
        'nơi sinh': 'noi_sinh',
        'nơi cư trú': 'noi_cu_tru',
        'quê quán': 'que_quan',
        'số định danh': 'so_dinh_danh',
        'giấy tờ tùy thân': 'giay_to',
        'kính gửi': 'kinh_gui',
        'số': 'so',
        'quyển số': 'quyen_so',
        'làm tại': 'lam_tai',
        'ngày': 'ngay',
        'tháng': 'thang',
        'năm': 'nam',
        'ghi chú': 'ghi_chu',
        'họ tên cha': 'cha_ho_ten',
        'họ và tên cha': 'cha_ho_ten',
        'họ tên mẹ': 'me_ho_ten',
        'họ và tên mẹ': 'me_ho_ten',
    }
    
    def __init__(self):
        self._field_counter = 0
        self._seen_names: Dict[str, int] = {}
        logger.info("TemplateProcessor initialized")
    
    def analyze(self, docx_content: bytes) -> AnalyzeResult:
        """
        Analyze DOCX to detect fillable fields.
        
        Detects patterns:
        - Label: ........ (dots after colon)
        - Label: TAB (tab after colon)
        - Standalone dots sequences
        
        Args:
            docx_content: DOCX file as bytes
            
        Returns:
            AnalyzeResult with detected fields
        """
        try:
            from docx import Document
            
            self._field_counter = 0
            self._seen_names = {}
            fields: List[DetectedField] = []
            
            doc = Document(io.BytesIO(docx_content))
            
            # First pass: collect all paragraphs with their text
            all_paragraphs = []
            para_idx = 0
            
            # Collect from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            all_paragraphs.append((para, para_idx))
                            para_idx += 1
            
            # Collect from main document
            for para in doc.paragraphs:
                all_paragraphs.append((para, para_idx))
                para_idx += 1
            
            # Second pass: detect fields with context
            for idx, (para, p_idx) in enumerate(all_paragraphs):
                detected = self._analyze_paragraph(para, p_idx)
                
                # Add context for each detected field
                for field in detected:
                    # Get 2-3 paragraphs before
                    context_before = []
                    for i in range(max(0, idx - 3), idx):
                        text = all_paragraphs[i][0].text.strip()
                        if text:
                            context_before.append(text)
                    
                    # Get 2-3 paragraphs after
                    context_after = []
                    for i in range(idx + 1, min(len(all_paragraphs), idx + 4)):
                        text = all_paragraphs[i][0].text.strip()
                        if text:
                            context_after.append(text)
                    
                    field.full_paragraph = para.text
                    field.context_before = context_before
                    field.context_after = context_after
                
                fields.extend(detected)
            
            logger.info(f"Analyzed DOCX: {len(fields)} fields detected")
            
            return AnalyzeResult(
                success=True,
                fields=fields,
                total_fields=len(fields)
            )
            
        except ImportError:
            return AnalyzeResult(
                success=False,
                errors=["python-docx not installed"]
            )
        except Exception as e:
            logger.error(f"Analyze error: {e}")
            return AnalyzeResult(
                success=False,
                errors=[str(e)]
            )
    
    def _analyze_paragraph(self, para, para_idx: int) -> List[DetectedField]:
        """Analyze a single paragraph for fillable patterns."""
        text = para.text
        if not text or not text.strip():
            return []
        
        # Skip continuation lines (only tabs/spaces)
        if text.replace('\t', '').replace(' ', '').strip() == '':
            return []
        
        fields = []
        
        # Pattern 1: "Label: ......." (dots after colon)
        # High confidence pattern
        for m in re.finditer(r'([A-Za-zÀ-ỹ][^:\t\n\.]{1,50}?)(?:\s*\(\d+\))?\s*[:：]\s*([\.…]{4,})', text):
            label = self._clean_label(m.group(1))
            if label and len(label) > 1:
                field = self._create_field(label, 'dots', para_idx, m.group(2), confidence=0.95)
                fields.append(field)
        
        # Pattern 2: "Label: TAB" (tab after colon)
        # Medium confidence - could be date fields
        for m in re.finditer(r'([A-Za-zÀ-ỹ][^:\t\n]{1,50}?)(?:\s*\(\d+\))?\s*[:：]\s*\t', text):
            label = self._clean_label(m.group(1))
            if label and len(label) > 1:
                # Skip if already detected as dots
                if not any(f.label == label and f.paragraph_index == para_idx for f in fields):
                    field = self._create_field(label, 'tab', para_idx, '\\t', confidence=0.7)
                    fields.append(field)
        
        # Pattern 3: Date pattern "ngày ... tháng ... năm ..."
        if re.search(r'ngày\s*[\.…\t]+\s*tháng\s*[\.…\t]+\s*năm', text, re.IGNORECASE):
            for part in ['ngày', 'tháng', 'năm']:
                field = self._create_field(part, 'date', para_idx, 'date_pattern', confidence=0.9)
                fields.append(field)
        
        return fields
    
    def _clean_label(self, label: str) -> str:
        """Clean label text."""
        label = re.sub(r'\s*\(\d+\)\s*', '', label)  # Remove (1), (2), etc
        label = label.strip().rstrip(':').rstrip('：').strip()
        return label
    
    def _normalize_label(self, label: str) -> str:
        """Convert Vietnamese label to field_id."""
        label_lower = label.lower().strip()
        
        # Check known mappings
        for vn_label, field_id in self.LABEL_MAPPINGS.items():
            if vn_label in label_lower or label_lower in vn_label:
                return field_id
        
        # Fallback: normalize to ASCII
        import unicodedata
        nfkd = unicodedata.normalize('NFKD', label_lower)
        ascii_label = ''.join(c for c in nfkd if not unicodedata.combining(c))
        snake = re.sub(r'[^a-z0-9]+', '_', ascii_label)
        return snake.strip('_')[:30] or 'field'
    
    def _create_field(
        self, 
        label: str, 
        field_type: str, 
        para_idx: int,
        original: str,
        confidence: float = 0.8
    ) -> DetectedField:
        """Create a DetectedField with unique ID."""
        self._field_counter += 1
        
        # Generate suggested name
        base_name = self._normalize_label(label)
        if base_name in self._seen_names:
            self._seen_names[base_name] += 1
            suggested_name = f"{base_name}_{self._seen_names[base_name]}"
        else:
            self._seen_names[base_name] = 1
            suggested_name = base_name
        
        return DetectedField(
            id=f"field_{self._field_counter}",
            label=label,
            field_type=field_type,
            paragraph_index=para_idx,
            suggested_name=suggested_name,
            confidence=confidence,
            original_text=original[:30] if original else ""
        )
    
    def create_template(
        self, 
        docx_content: bytes,
        confirmed_fields: List[Dict[str, Any]]
    ) -> CreateTemplateResult:
        """
        Create template by inserting {{placeholders}} at field positions.
        
        Args:
            docx_content: Original DOCX bytes
            confirmed_fields: List of confirmed fields from admin
                [{'paragraph_index': 0, 'field_name': 'ho_ten', ...}, ...]
                
        Returns:
            CreateTemplateResult with template bytes
        """
        try:
            from docx import Document
            
            doc = Document(io.BytesIO(docx_content))
            placeholders = []
            
            # Group fields by paragraph
            para_fields: Dict[int, List[Dict]] = {}
            for field in confirmed_fields:
                para_idx = field.get('paragraph_index', -1)
                if para_idx >= 0:
                    if para_idx not in para_fields:
                        para_fields[para_idx] = []
                    para_fields[para_idx].append(field)
            
            # Process paragraphs
            para_idx = 0
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            if para_idx in para_fields:
                                for field in para_fields[para_idx]:
                                    self._insert_placeholder(para, field)
                                    placeholders.append(field.get('field_name', f'field_{para_idx}'))
                            para_idx += 1
            
            for para in doc.paragraphs:
                if para_idx in para_fields:
                    for field in para_fields[para_idx]:
                        self._insert_placeholder(para, field)
                        placeholders.append(field.get('field_name', f'field_{para_idx}'))
                para_idx += 1
            
            # Save to bytes
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            
            logger.info(f"Created template with {len(placeholders)} placeholders")
            
            return CreateTemplateResult(
                success=True,
                template_bytes=output.getvalue(),
                placeholders=placeholders
            )
            
        except Exception as e:
            logger.error(f"Create template error: {e}")
            return CreateTemplateResult(
                success=False,
                errors=[str(e)]
            )
    
    def _insert_placeholder(self, para, field: Dict):
        """Insert {{placeholder}} into paragraph, replacing dots/tabs."""
        field_name = field.get('field_name', 'field')
        placeholder = f"{{{{{field_name}}}}}"
        
        for run in para.runs:
            # Replace dots pattern
            if re.search(r'[\.…]{4,}', run.text):
                run.text = re.sub(
                    r'([\.…]{4,})',
                    lambda m: placeholder + '.' * max(6, len(m.group(1)) - len(placeholder)),
                    run.text,
                    count=1
                )
                return
            
            # Replace tab
            if run.text == '\t':
                run.text = placeholder
                return
    
    def extract_placeholders(self, docx_content: bytes) -> List[str]:
        """
        Extract all {{placeholder}} names from a template DOCX.
        
        Used by frontend to know what fields to render.
        
        Args:
            docx_content: Template DOCX bytes
            
        Returns:
            List of placeholder names (without {{ }})
        """
        try:
            from docx import Document
            
            doc = Document(io.BytesIO(docx_content))
            all_text = ""
            
            # Collect all text
            for para in doc.paragraphs:
                all_text += para.text + "\n"
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        all_text += cell.text + "\n"
            
            # Find all {{placeholder}} patterns
            matches = re.findall(r'\{\{([^}]+)\}\}', all_text)
            unique = list(dict.fromkeys(matches))  # Preserve order, remove duplicates
            
            logger.info(f"Extracted {len(unique)} placeholders from template")
            return unique
            
        except Exception as e:
            logger.error(f"Extract placeholders error: {e}")
            return []


# Convenience functions
def analyze_template(docx_content: bytes) -> AnalyzeResult:
    """Analyze a DOCX template for fillable fields."""
    processor = TemplateProcessor()
    return processor.analyze(docx_content)


def create_template(docx_content: bytes, fields: List[Dict]) -> CreateTemplateResult:
    """Create a template with placeholders."""
    processor = TemplateProcessor()
    return processor.create_template(docx_content, fields)


def extract_placeholders(docx_content: bytes) -> List[str]:
    """Extract placeholder names from template."""
    processor = TemplateProcessor()
    return processor.extract_placeholders(docx_content)
