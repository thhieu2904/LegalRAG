"""
Metadata Extractor for Vietnamese Legal Documents
Extract structured information from PDF text using regex and pattern matching
"""
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from Vietnamese legal documents"""
    
    # REGEX PATTERNS for Vietnamese legal documents
    # Document code: "68/2018/NĐ-CP", "Decision No. 123/2023/QĐ-UBND"
    DOCUMENT_CODE_PATTERNS = [
        r'\b(\d+/\d+/[NĐQTC]{1,3}-[\w\-]+)\b',  # "68/2018/NĐ-CP"
        r'(?:Số|Decision No\.?|Quyết định số)\s*[\:\=]?\s*(\d+/\d+/[A-Za-z\-]+)',  # "Số: 68/2018/NĐ-CP"
    ]
    
    # Date patterns: "15/5/2018", "15-05-2018", "15 tháng 5 năm 2018"
    DATE_PATTERNS = [
        r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',  # 15/5/2018
        r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b',  # 15-05-2018
        r'\b(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})\b',  # 15 tháng 5 năm 2018
    ]
    
    # Organization patterns: "Bộ Tư pháp", "UBND TP HCM", "Sở Nội vụ"
    ORGANIZATION_PATTERNS = [
        r'\b(Bộ\s+[\w\s]+)\b',  # Bộ Tư pháp
        r'\b(UBND\s+[\w\s]+)\b',  # UBND TP HCM
        r'\b(Sở\s+[\w\s]+)\b',  # Sở Nội vụ
        r'\b(Cục\s+[\w\s]+)\b',  # Cục Đất đai
        r'\b(Vụ\s+[\w\s]+)\b',  # Vụ Pháp chế
        r'\b(Hội\s+[\w\s]+)\b',  # Hội Đông Quản lý
    ]
    
    # Section patterns: "Điều 1", "Mục 2.3", "Chương III"
    SECTION_PATTERNS = [
        r'\b(Điều\s+[\dIVXivx\-]+)\b',  # Điều 1, Điều I
        r'\b(Mục\s+[\d\.]+)\b',  # Mục 2.3
        r'\b(Chương\s+[\dIVXivx]+)\b',  # Chương III
        r'\b(Phần\s+[\dIVXivx]+)\b',  # Phần II
        r'\b(Khoản\s+[\d]+)\b',  # Khoản 1
        r'\b(Điểm\s+[a-z])\b',  # Điểm a
    ]
    
    def __init__(self):
        """Initialize extractor"""
        logger.info("✅ MetadataExtractor initialized")
    
    def extract_all(self, text: str, num_pages: int = 0) -> Dict[str, Any]:
        """
        Extract all metadata from document text
        
        Args:
            text: Full document text
            num_pages: Number of pages in PDF (from metadata)
        
        Returns:
            Dictionary with extracted metadata
        """
        try:
            extraction_notes = []
            metadata = {}
            
            # Extract document code
            document_codes = self._extract_document_codes(text)
            if document_codes:
                metadata['document_code'] = document_codes[0]  # Take first match
            else:
                extraction_notes.append("Không tìm thấy mã văn bản")
            
            # Extract dates
            dates = self._extract_dates(text)
            if dates:
                metadata['dates'] = list(set(dates))  # Remove duplicates
            else:
                extraction_notes.append("Không tìm thấy ngày tháng")
            
            # Extract organizations
            organizations = self._extract_organizations(text)
            if organizations:
                metadata['organizations'] = list(set(organizations))
            else:
                extraction_notes.append("Không tìm thấy tên cơ quan")
            
            # Extract sections
            sections = self._extract_sections(text)
            if sections:
                metadata['sections'] = list(set(sections))
            else:
                extraction_notes.append("Không tìm thấy các điều/mục")
            
            # Add basic stats
            metadata['pages'] = num_pages if num_pages > 0 else self._estimate_pages(text)
            metadata['language'] = 'vi'  # Vietnamese legal documents
            metadata['word_count'] = len(text.split())
            
            # Detect special structures
            metadata['has_tables'] = 'Bảng' in text or '|' in text
            metadata['has_signatures'] = any(
                word in text for word in ['Ký', 'Chữ ký', 'Chứng thực', 'Xác nhận']
            )
            
            # Calculate confidence score
            # Full extraction (all main fields) = 1.0
            # Partial extraction = 0.5-0.8
            # Minimal extraction = 0.2-0.5
            confidence = self._calculate_confidence(
                has_code=bool(metadata.get('document_code')),
                has_dates=bool(metadata.get('dates')),
                has_organizations=bool(metadata.get('organizations')),
                has_sections=bool(metadata.get('sections')),
            )
            metadata['extraction_confidence'] = confidence
            
            # Add notes if extraction was incomplete
            if extraction_notes:
                metadata['extraction_notes'] = '; '.join(extraction_notes)
            
            logger.info(f"✅ Metadata extracted (confidence: {confidence:.2f}): {metadata.keys()}")
            return metadata
        
        except Exception as e:
            logger.error(f"❌ Metadata extraction failed: {e}")
            return {
                'extraction_confidence': 0.0,
                'extraction_notes': f"Lỗi extraction: {str(e)}"
            }
    
    def _extract_document_codes(self, text: str) -> List[str]:
        """Extract document codes (e.g., "68/2018/NĐ-CP")"""
        codes = []
        for pattern in self.DOCUMENT_CODE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if isinstance(matches[0], tuple):
                codes.extend([m[0] if isinstance(m, tuple) else m for m in matches])
            else:
                codes.extend(matches)
        return codes[:5]  # Return top 5 matches
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates (e.g., "15/5/2018")"""
        dates = []
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    # Normalize format to DD/MM/YYYY
                    day, month, year = match[0], match[1], match[2]
                    dates.append(f"{day.zfill(2)}/{month.zfill(2)}/{year}")
                else:
                    dates.append(match)
        return dates[:10]  # Return top 10 matches
    
    def _extract_organizations(self, text: str) -> List[str]:
        """Extract organization names"""
        organizations = []
        for pattern in self.ORGANIZATION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            organizations.extend(matches)
        # Clean up and limit
        return [org.strip() for org in organizations][:10]
    
    def _extract_sections(self, text: str) -> List[str]:
        """Extract section references (Điều, Mục, Chương, etc.)"""
        sections = []
        for pattern in self.SECTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            sections.extend(matches)
        return sections[:20]  # Return top 20 matches
    
    def _estimate_pages(self, text: str) -> int:
        """Estimate page count from text"""
        # Average 3000 characters per page
        return max(1, len(text) // 3000)
    
    def _calculate_confidence(
        self,
        has_code: bool = False,
        has_dates: bool = False,
        has_organizations: bool = False,
        has_sections: bool = False,
    ) -> float:
        """
        Calculate extraction confidence score
        
        Full extraction (all fields): 1.0
        3 of 4 fields: 0.85
        2 of 4 fields: 0.65
        1 of 4 fields: 0.40
        0 of 4 fields: 0.10
        """
        found_count = sum([has_code, has_dates, has_organizations, has_sections])
        
        confidence_map = {
            0: 0.10,
            1: 0.40,
            2: 0.65,
            3: 0.85,
            4: 1.00,
        }
        return confidence_map.get(found_count, 0.0)
    
    def extract_source_references(self, text: str) -> Dict[int, str]:
        """
        Extract source references for chunks
        Maps line/paragraph to section reference (Điều X, khoản Y, điểm Z)
        
        Returns:
            Dict mapping line number to full reference path
        """
        references = {}
        current_section = None
        
        for i, line in enumerate(text.split('\n')):
            # Check if line contains section header
            section_match = re.search(
                r'(Điều\s+[\d\-]+|Mục\s+[\d\.]+|Chương\s+[\dIVXivx]+)',
                line,
                re.IGNORECASE
            )
            if section_match:
                current_section = section_match.group(1)
            
            # Add reference if line is not empty
            if line.strip() and current_section:
                references[i] = current_section
        
        return references
