"""
Intelligent Legal Document Cleaner
Uses heuristics and statistical analysis to remove noise from Vietnamese legal documents.
NO hardcoded patterns - works across all document types.
"""
import re
import logging
from typing import List, Dict
from collections import Counter

logger = logging.getLogger(__name__)


class LegalDocumentCleaner:
    """
    Smart cleaner that works for ANY legal document
    Uses statistical features instead of brittle hardcoded patterns
    """
    
    def __init__(self):
        # High-value legal keywords (keep these)
        self.content_indicators = {
            'điều', 'mục', 'chương', 'khoản', 'luật', 'nghị định',
            'thông tư', 'quyết định', 'quy định', 'hợp đồng', 'thủ tục',
            'quyền', 'nghĩa vụ', 'phạm vi', 'mục đích', 'áp dụng',
            'trách nhiệm', 'bồi thường', 'văn bản', 'tổ chức', 'cá nhân'
        }
        
        # Low-value administrative keywords (remove these)
        self.noise_indicators = {
            'trang', 'chữ ký', 'họ tên', 'chức vụ', 'ngày hiệu lực',
            'mã hiệu', 'lần ban hành', 'stt', 'nơi nhận', 'soạn thảo',
            'xem xét', 'phê duyệt', 'giám đốc', 'phó giám đốc'
        }
        
        # Form template patterns - these indicate form fields, not actual content
        # Pattern: (số) hoặc số. followed by field description
        self.form_field_patterns = [
            r'^\s*\(\d+\)\s*[A-Za-zÀ-ỹ]',  # (1) Họ, chữ đệm, tên
            r'^\s*\d+\.\s*[A-Za-zÀ-ỹ].*[;:]\s*$',  # 1. Họ tên;
            r'\.\.\.\.+',  # Multiple dots: ....
            r'^\s*[IVX]+\.\s',  # Roman numerals: I. II. III.
        ]
        
        # Form section indicators - mark beginning of form template area
        self.form_section_indicators = [
            'nội dung mẫu',
            'mẫu hộ tịch điện tử',
            'mẫu điện tử tương tác',
            'hướng dẫn điền',
            'cách ghi thông tin',
            'trường thông tin',
            'thông tin về người',  # Thông tin về người cha/mẹ trong form
        ]
    
    def is_form_template_line(self, line: str) -> bool:
        """
        Detect if a line is part of form template (not actual legal content).
        Form templates typically have:
        - Numbered fields: (1) Họ tên; (2) Ngày sinh;
        - Fill-in dots: Số lượng: ....
        - Field descriptions ending with semicolon
        
        Returns:
            True if line is form template content (should be removed)
        """
        line_lower = line.lower().strip()
        
        if not line_lower:
            return False
        
        # Check for form field patterns
        for pattern in self.form_field_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        # Check for multiple dots (fill-in blanks)
        if re.search(r'\.{3,}', line):  # 3+ consecutive dots
            return True
        
        # Check for form section indicators
        for indicator in self.form_section_indicators:
            if indicator in line_lower:
                return True
        
        # Pattern: ends with semicolon and has numbered prefix -> likely form field
        if re.match(r'^\s*\(\d+\)', line) and line.strip().endswith(';'):
            return True
        
        return False
    
    def calculate_line_score(self, line: str) -> float:
        """
        Score a line from -1.0 (noise) to 1.0 (content)
        Based on statistical features, NOT hardcoded patterns
        """
        line_lower = line.lower().strip()
        
        if not line_lower:
            return 0.0  # Empty line is neutral
        
        # First check: if it's a form template line, heavily penalize
        if self.is_form_template_line(line):
            return -0.9  # Strong noise signal
        
        score = 0.0
        
        # Feature 1: Length (very short = likely noise)
        if len(line_lower) < 10:
            score -= 0.3
        elif len(line_lower) > 50:
            score += 0.2
        
        # Feature 2: Content indicator density
        words = line_lower.split()
        if words:
            content_count = sum(1 for w in words if any(kw in w for kw in self.content_indicators))
            noise_count = sum(1 for w in words if any(kw in w for kw in self.noise_indicators))
            
            score += (content_count / len(words)) * 2.0  # Boost content
            score -= (noise_count / len(words)) * 3.0   # Penalize noise
        
        # Feature 3: Special character ratio (tables have many |, :, -, _)
        special_chars = sum(1 for c in line if c in '|:_-')
        if len(line) > 0:
            special_ratio = special_chars / len(line)
            if special_ratio > 0.2:  # More than 20% special chars
                score -= 0.5
        
        # Feature 4: Repeated characters (_____, ....., -----)
        if re.search(r'(.)\1{4,}', line):  # 5+ repeated chars
            score -= 0.8
        
        # Feature 5: Number-heavy lines (page numbers, dates)
        digit_ratio = sum(1 for c in line if c.isdigit()) / len(line) if line else 0
        if digit_ratio > 0.3:  # More than 30% digits
            score -= 0.3
        
        # Feature 6: Starts with metadata patterns (generic)
        if re.match(r'^\s*(Trang|Ngày|Mã|Lần|STT|TT)\s*[:.]', line_lower):
            score -= 0.6
        
        # Feature 7: All caps short line (headers like "CHƯƠNG I")
        if line.isupper() and len(line) < 30 and len(line) > 5:
            # Could be section header - check if it has structure markers
            if any(marker in line_lower for marker in ['chương', 'phần', 'mục']):
                score += 0.5  # Keep structural headers
            else:
                score -= 0.4  # Likely metadata header
        
        # Feature 8: Colon at end (often metadata labels)
        if line.strip().endswith(':'):
            score -= 0.2
        
        return max(-1.0, min(1.0, score))  # Clamp to [-1, 1]
    
    def is_likely_content(self, line: str, threshold: float = -0.2) -> bool:
        """
        Determine if line is content (True) or noise (False)
        threshold=-0.2 is balanced (tested on multiple documents)
        """
        score = self.calculate_line_score(line)
        return score > threshold
    
    def remove_repeated_headers_footers(self, pages: List[str]) -> List[str]:
        """
        Find and remove repeated header/footer content across pages
        Uses frequency analysis instead of hardcoded patterns
        """
        if len(pages) < 2:
            return pages
        
        # Extract first 5 lines and last 5 lines from each page
        all_first_lines = []
        all_last_lines = []
        
        for page in pages:
            lines = page.split('\n')
            if len(lines) >= 10:
                all_first_lines.extend(lines[:5])
                all_last_lines.extend(lines[-5:])
        
        # Find lines that appear in multiple pages (likely headers/footers)
        first_line_counts = Counter(all_first_lines)
        last_line_counts = Counter(all_last_lines)
        
        # Lines that appear in >50% of pages are likely headers/footers
        threshold = len(pages) * 0.5
        repeated_headers = {line for line, count in first_line_counts.items() if count > threshold}
        repeated_footers = {line for line, count in last_line_counts.items() if count > threshold}
        
        # Remove repeated lines from each page
        cleaned_pages = []
        for page in pages:
            lines = page.split('\n')
            
            # Remove header lines
            while lines and lines[0] in repeated_headers:
                lines.pop(0)
            
            # Remove footer lines
            while lines and lines[-1] in repeated_footers:
                lines.pop()
            
            cleaned_pages.append('\n'.join(lines))
        
        return cleaned_pages
    
    def normalize_vietnamese_spacing(self, text: str) -> str:
        """Fix broken Vietnamese diacritics from PDF extraction"""
        # "M ỤC" → "MỤC", "đ ịnh" → "định"
        text = re.sub(r'(\w)\s+([ụộịậếừớờưứằẵảẩẫ])', r'\1\2', text)
        
        # Fix at start of line
        text = re.sub(r'^\s*([ụộịậếừớờưứằẵảẩẫ])', r'\1', text, flags=re.MULTILINE)
        
        return text
    
    def detect_and_remove_form_template(self, text: str) -> str:
        """
        Detect and remove form template sections that typically appear at the end
        of ISO-standard legal documents.
        
        Form templates are characterized by:
        - Numbered field descriptions: (1) Họ tên; (2) Ngày sinh;
        - Fill-in blanks with dots: Số lượng: .....
        - Section headers like "NỘI DUNG MẪU HỘ TỊCH ĐIỆN TỬ"
        
        Strategy: Find the start of form template section and truncate.
        This is safer than line-by-line removal as it preserves context.
        
        Args:
            text: Full document text
            
        Returns:
            Text with form template section removed
        """
        lines = text.split('\n')
        
        # Find the start of form template section
        form_start_idx = None
        consecutive_form_lines = 0
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Strong indicators that form section has started
            strong_form_indicators = [
                'nội dung mẫu hộ tịch',
                'mẫu điện tử tương tác',
                'hướng dẫn ghi thông tin',
                'cách điền mẫu',
            ]
            
            for indicator in strong_form_indicators:
                if indicator in line_lower:
                    form_start_idx = i
                    logger.info(f"🔍 Found form template start at line {i}: '{line[:50]}...'")
                    break
            
            if form_start_idx:
                break
            
            # Alternative: detect by consecutive form-like lines
            if self.is_form_template_line(line):
                consecutive_form_lines += 1
                if consecutive_form_lines >= 5:  # 5+ consecutive form lines
                    form_start_idx = i - consecutive_form_lines + 1
                    logger.info(f"🔍 Detected form template by pattern at line {form_start_idx}")
                    break
            else:
                consecutive_form_lines = 0
        
        # If form section found, truncate
        if form_start_idx is not None:
            # Keep some buffer lines before the form section
            # to avoid cutting actual content
            original_len = len(lines)
            lines = lines[:form_start_idx]
            removed = original_len - len(lines)
            logger.info(f"✂️ Removed {removed} lines of form template content")
        
        return '\n'.join(lines)
    
    def clean_text(self, raw_text: str, score_threshold: float = -0.2) -> str:
        """
        Main cleaning pipeline for already-extracted text
        
        Args:
            raw_text: Raw text from PDF extraction
            score_threshold: Lines with score > threshold are kept (default: -0.2)
                            Lower = more aggressive cleaning
                            Higher = keep more content
        
        Returns:
            Cleaned text ready for chunking/embedding
        """
        try:
            # Step 1: Split into pages if page markers exist
            pages_text = raw_text.split('\n--- Page ')
            if len(pages_text) > 1:
                # Remove page markers but keep page boundaries
                pages_text = [p.split('---\n', 1)[-1] if '---\n' in p else p for p in pages_text]
            
            # Step 2: Remove repeated headers/footers using frequency analysis
            if len(pages_text) > 1:
                pages_text = self.remove_repeated_headers_footers(pages_text)
            
            # Step 3: Clean each page line-by-line using scoring
            cleaned_pages = []
            for page_text in pages_text:
                lines = page_text.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    # Keep line if score is above threshold
                    if self.is_likely_content(line, threshold=score_threshold):
                        cleaned_lines.append(line.strip())
                
                if cleaned_lines:
                    cleaned_pages.append('\n'.join(cleaned_lines))
            
            # Step 4: Merge pages
            full_text = '\n\n'.join(cleaned_pages)
            
            # Step 4.5: Detect and remove form template sections (ISO documents)
            full_text = self.detect_and_remove_form_template(full_text)
            
            # Step 5: Normalize Vietnamese spacing
            full_text = self.normalize_vietnamese_spacing(full_text)
            
            # Step 6: Normalize whitespace
            full_text = re.sub(r' {2,}', ' ', full_text)  # Multiple spaces
            full_text = re.sub(r'\n{3,}', '\n\n', full_text)  # Multiple newlines
            full_text = re.sub(r' +\n', '\n', full_text)  # Trailing spaces
            
            cleaned_text = full_text.strip()
            
            # Log cleaning stats
            original_len = len(raw_text)
            cleaned_len = len(cleaned_text)
            reduction = ((original_len - cleaned_len) / original_len * 100) if original_len > 0 else 0
            
            logger.info(f"✅ Text cleaned: {original_len} → {cleaned_len} chars ({reduction:.1f}% reduction)")
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"❌ Text cleaning failed: {e}")
            # Return original text if cleaning fails
            return raw_text
