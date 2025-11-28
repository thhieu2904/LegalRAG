"""
Legal Document Chunker V2 - For Vietnamese Administrative Procedure Documents (Quy trình ISO)

These documents have a FIXED structure:
1. MỤC ĐÍCH
2. PHẠM VI
3. TÀI LIỆU VIỆN DẪN
4. ĐỊNH NGHĨA/VIẾT TẮT
5. NỘI DUNG (most important section with subsections a, b, c, d, e, f, g, h, i)
6. BIỂU MẪU
7. HỒ SƠ LƯU TRỮ

Strategy:
1. Clean noise (page markers, headers, table of contents)
2. Split by MAJOR sections (1. MỤC ĐÍCH, 2. PHẠM VI, etc.)
3. For section 5 (NỘI DUNG), split further by subsections (a, b, c, d...)
4. Add context prefix to each chunk: [Quy trình: X | Phần: Y]
5. Merge small chunks, split large chunks while respecting sentence boundaries
"""
import re
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class LegalDocumentChunkerV2:
    """
    Smart chunker for Vietnamese Administrative Procedure Documents.
    
    Key improvements over V1:
    - Section-aware splitting (respects document structure)
    - Noise removal (page markers, TOC, revision history)
    - Context prefix for each chunk
    - Better handling of subsections in "5. NỘI DUNG"
    """
    
    def __init__(self, model_name: str, chunk_size: int = 800, chunk_overlap: int = 50):
        """
        Args:
            model_name: Name of the embedding model (for tokenizer)
            chunk_size: Target size in tokens (increased from 600)
            chunk_overlap: Overlap in tokens between chunks (reduced - we use context prefix instead)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
        
        logger.info(f"✅ LegalDocumentChunkerV2 initialized (chunk_size={chunk_size})")
        
        # Main section patterns (numbered sections)
        self.main_sections = [
            (r'^1\.\s*MỤC ĐÍCH', 'Mục đích'),
            (r'^2\.\s*PHẠM VI', 'Phạm vi'),
            (r'^3\.\s*TÀI LIỆU VIỆN DẪN', 'Tài liệu viện dẫn'),
            (r'^4\.\s*ĐỊNH NGHĨA', 'Định nghĩa/Viết tắt'),
            (r'^5\.\s*NỘI DUNG', 'Nội dung'),
            (r'^6\.\s*BIỂU MẪU', 'Biểu mẫu'),
            (r'^7\.\s*HỒ SƠ', 'Hồ sơ lưu trữ'),
        ]
        
        # Subsection patterns for section 5 (NỘI DUNG)
        self.content_subsections = [
            (r'^a\.\s*Thành phần', 'Thành phần hồ sơ'),
            (r'^b\.\s*Thời hạn', 'Thời hạn giải quyết'),
            (r'^c\.\s*Cơ quan', 'Cơ quan thực hiện'),
            (r'^d\.\s*Đối tượng', 'Đối tượng thực hiện'),
            (r'^e\.\s*Cách thức', 'Cách thức thực hiện'),
            (r'^f\.\s*Lệ phí', 'Lệ phí'),
            (r'^g\.\s*Tên mẫu', 'Mẫu đơn/tờ khai'),
            (r'^h\.\s*Yêu cầu', 'Yêu cầu, điều kiện'),
            (r'^i\.\s*Căn cứ', 'Căn cứ pháp lý'),
        ]
        
        # Noise patterns to remove
        self.noise_patterns = [
            # Page markers
            r'Ngày hiệu lực:\s*[\d/]+\s*Trang:\s*\d+/\d+\s*Lần ban hành:\s*\d+',
            r'Trang:\s*\d+/\d+',
            r'Lần ban hành:\s*\d+',
            # Underline separators
            r'_{5,}',
            # Header/footer patterns
            r'Tên quy trình:\s*[^\n]+\n_{5,}',
        ]
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count (Vietnamese ~1.5 tokens per word due to subword tokenization)"""
        return int(len(text.split()) * 1.5)
    
    def clean_text(self, text: str) -> str:
        """
        Remove noise from text:
        - Page markers (Ngày hiệu lực, Trang X/Y, Lần ban hành)
        - Separator lines (________)
        - Redundant headers
        """
        cleaned = text
        
        for pattern in self.noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE)
        
        # Normalize multiple newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in cleaned.split('\n')]
        cleaned = '\n'.join(line for line in lines if line)  # Remove empty lines
        
        return cleaned.strip()
    
    def extract_document_title(self, text: str) -> Optional[str]:
        """
        Extract the document/procedure title from the text.
        Usually appears after "QUY TRÌNH" or in "Tên quy trình:"
        """
        # Try "Tên quy trình:"
        match = re.search(r'Tên quy trình:\s*([^\n_]+)', text)
        if match:
            return match.group(1).strip()
        
        # Try line after "QUY TRÌNH"
        match = re.search(r'QUY TRÌNH\s*\n\s*Mã hiệu:[^\n]+\n\s*([^\n]+)', text)
        if match:
            return match.group(1).strip()
        
        return None
    
    def remove_header_section(self, text: str) -> str:
        """
        Remove the header section (before "1. MỤC ĐÍCH").
        This includes: Title page, TOC, Revision history, Approval signatures.
        """
        # Find where main content starts
        match = re.search(r'\n1\.\s*MỤC ĐÍCH', text, re.IGNORECASE)
        if match:
            return text[match.start():]
        return text
    
    def split_into_sections(self, text: str) -> List[Tuple[str, str]]:
        """
        Split text into major sections.
        Returns: List of (section_name, section_content) tuples
        """
        sections = []
        
        # Build regex to find all section starts
        section_starts = []
        for pattern, name in self.main_sections:
            for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
                section_starts.append((match.start(), match.end(), name))
        
        # Sort by position
        section_starts.sort(key=lambda x: x[0])
        
        # Extract content between sections
        for i, (start, header_end, name) in enumerate(section_starts):
            # Find end of this section (start of next section or end of text)
            if i + 1 < len(section_starts):
                end = section_starts[i + 1][0]
            else:
                end = len(text)
            
            content = text[start:end].strip()
            if content:
                sections.append((name, content))
        
        return sections
    
    def split_content_section(self, content: str) -> List[Tuple[str, str]]:
        """
        Split the "5. NỘI DUNG" section into subsections (a, b, c, d, e, f, g, h, i).
        Returns: List of (subsection_name, subsection_content) tuples
        """
        subsections = []
        
        # Find all subsection starts
        subsection_starts = []
        for pattern, name in self.content_subsections:
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                subsection_starts.append((match.start(), name))
        
        # Sort by position
        subsection_starts.sort(key=lambda x: x[0])
        
        if not subsection_starts:
            # No subsections found, return as single chunk
            return [('Nội dung', content)]
        
        # Extract content between subsections
        for i, (start, name) in enumerate(subsection_starts):
            if i + 1 < len(subsection_starts):
                end = subsection_starts[i + 1][0]
            else:
                end = len(content)
            
            sub_content = content[start:end].strip()
            if sub_content:
                subsections.append((name, sub_content))
        
        return subsections
    
    def split_large_chunk(self, text: str, section_name: str) -> List[str]:
        """
        Split a large chunk into smaller pieces while respecting sentence boundaries.
        Each piece will include the section context.
        """
        if self.count_tokens(text) <= self.chunk_size:
            return [text]
        
        # Split by sentences (. followed by space and capital letter, or newline)
        sentences = re.split(r'(?<=\.)\s+(?=[A-ZĐÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ])', text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def create_context_prefix(self, doc_title: str, section: str, subsection: Optional[str] = None) -> str:
        """
        Create a context prefix for each chunk.
        Format: [Quy trình: X | Phần: Y | Mục: Z]
        """
        parts = []
        
        if doc_title:
            parts.append(f"Quy trình: {doc_title}")
        
        if section:
            parts.append(f"Phần: {section}")
        
        if subsection and subsection != section:
            parts.append(f"Mục: {subsection}")
        
        if parts:
            return f"[{' | '.join(parts)}]\n\n"
        return ""
    
    def chunk_text(self, text: str, document_title: Optional[str] = None) -> List[Dict]:
        """
        Main chunking method.
        
        Args:
            text: Full document text
            document_title: Optional title (will try to extract if not provided)
        
        Returns:
            List of chunk dicts with:
            - text: Chunk content with context prefix
            - tokens: Token count
            - section: Section name
            - subsection: Subsection name (if applicable)
            - chunk_index: Index in the document
        """
        if not text.strip():
            return []
        
        # Step 1: Extract document title
        if not document_title:
            document_title = self.extract_document_title(text)
        
        # Step 2: Clean noise
        cleaned_text = self.clean_text(text)
        
        # Step 3: Remove header (TOC, revision history, etc.)
        main_content = self.remove_header_section(cleaned_text)
        
        # If we removed too much, use cleaned text
        if len(main_content) < len(cleaned_text) * 0.3:
            main_content = cleaned_text
        
        # Step 4: Split into major sections
        sections = self.split_into_sections(main_content)
        
        # If no sections found, treat as single section
        if not sections:
            sections = [('Nội dung', main_content)]
        
        # Step 5: Process each section
        result = []
        chunk_index = 0
        
        for section_name, section_content in sections:
            # Special handling for "Nội dung" section - split into subsections
            if section_name == 'Nội dung':
                subsections = self.split_content_section(section_content)
                
                for subsection_name, subsection_content in subsections:
                    # Split large chunks
                    text_chunks = self.split_large_chunk(subsection_content, subsection_name)
                    
                    for chunk_text in text_chunks:
                        prefix = self.create_context_prefix(document_title, section_name, subsection_name)
                        full_text = prefix + chunk_text
                        
                        result.append({
                            'text': full_text,
                            'tokens': self.count_tokens(full_text),
                            'section': section_name,
                            'subsection': subsection_name,
                            'chunk_index': chunk_index,
                        })
                        chunk_index += 1
            else:
                # Other sections - just split if too large
                text_chunks = self.split_large_chunk(section_content, section_name)
                
                for chunk_text in text_chunks:
                    prefix = self.create_context_prefix(document_title, section_name)
                    full_text = prefix + chunk_text
                    
                    result.append({
                        'text': full_text,
                        'tokens': self.count_tokens(full_text),
                        'section': section_name,
                        'subsection': None,
                        'chunk_index': chunk_index,
                    })
                    chunk_index += 1
        
        # Log summary
        total_tokens = sum(c['tokens'] for c in result)
        avg_tokens = total_tokens / len(result) if result else 0
        logger.info(f"✅ Chunked '{document_title}' into {len(result)} chunks (avg {avg_tokens:.0f} tokens/chunk)")
        
        return result


# Backward compatibility
LegalDocumentChunker = LegalDocumentChunkerV2
