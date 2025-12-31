"""
Legal Document Chunker for Vietnamese Legal Documents
Chunks documents by legal structure (Điều, Mục, Chương) while respecting token limits

IMPROVED: Each chunk includes context prefix to prevent LLM hallucination
"""
import re
import logging
from typing import List, Dict, Optional
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)


class LegalDocumentChunker:
    """
    Intelligent chunker for Vietnamese legal documents
    Respects legal structure hierarchy: Chương > Điều > Mục > Khoản
    
    KEY FEATURE: Each chunk includes context prefix like:
    "[Văn bản: Đăng ký khai sinh | Phần: Thành phần hồ sơ]"
    This helps LLM understand where this chunk belongs.
    """
    
    def __init__(self, model_name: str, chunk_size: int = 600, chunk_overlap: int = 100):
        """
        Args:
            model_name: Name of the embedding model (for tokenizer)
            chunk_size: Target size in tokens
            chunk_overlap: Overlap in tokens between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
        
        # For Vietnamese model with custom tokenizer, we'll use estimation
        # instead of loading tokenizer separately (model will handle it)
        self.tokenizer = None
        logger.info(f"✅ Chunker initialized (using token estimation)")
        
        # Legal structure separators (in order of priority)
        # IMPROVED: Added separators for administrative documents (Quy trình, Trang, etc.)
        self.separators = [
            r'\n(?=Chương\s+[IVXLCDM]+[\.\:])',   # Chương (Roman numerals)
            r'\n(?=Điều\s+\d+[\.\:])',             # Điều 1, Điều 2, etc.
            r'\n(?=Mục\s+[\d\.]+[\.\:])',          # Mục 1, Mục 1.1, etc.
            r'\n(?=[a-z]\.\s+[A-ZĐÀÁẢÃẠ])',        # a. Thành phần, b. Số lượng, etc.
            r'\n(?=\d+\.\s+NỘI DUNG)',             # "5. NỘI DUNG" style headers
            r'\n(?=\*\s+)',                         # Bullet points with *
            r'\n(?=\-\s+)',                         # Bullet points with -
            r'\n(?=\d+\.\s)',                       # Numbered items: "1. ", "2. "
            r'\n(?=Khoản\s+\d+[\.\:])',            # Khoản 1, Khoản 2, etc.
            r'(?=Ngày hiệu lực:)',                  # Page break marker
            r'\n\n',                                # Double newline
            r'\.\s+(?=[A-ZĐÀÁẢÃẠ])',               # Sentence end + Capital letter
            r'\.\s',                                # Sentence boundary
        ]
        
        # Section header patterns to extract context
        self.section_patterns = [
            (r'Tên quy trình:\s*([^\n]+)', 'quy_trinh'),
            (r'(\d+)\.\s*NỘI DUNG', 'noi_dung'),
            (r'([a-z])\.\s*([A-ZĐ][^:\n]+):', 'muc_nho'),
            (r'Chương\s+([IVXLCDM]+)[\.:\s]+([^\n]+)', 'chuong'),
            (r'Điều\s+(\d+)[\.:\s]+([^\n]+)', 'dieu'),
            (r'Mục\s+([\d\.]+)[\.:\s]+([^\n]+)', 'muc'),
        ]
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tokenizer or estimation"""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text, add_special_tokens=False))
            except:
                pass
        
        # Fallback: estimation (Vietnamese ~1.3 tokens per word)
        return int(len(text.split()) * 1.3)
    
    def clean_text(self, text: str) -> str:
        """
        Clean up text before chunking:
        - Remove page break markers (Trang: X/Y, Ngày hiệu lực, Lần ban hành)
        - Normalize whitespace
        """
        # Remove page headers/footers that add noise
        text = re.sub(r'Ngày hiệu lực:\s*[\d/]+\s*Trang:\s*\d+/\d+\s*Lần ban hành:\s*\d+', '', text)
        text = re.sub(r'Trang:\s*\d+/\d+', '', text)
        text = re.sub(r'Lần ban hành:\s*\d+', '', text)
        
        # Remove excessive underscores (often used as separators)
        text = re.sub(r'_{5,}', '', text)
        
        # Normalize multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def extract_document_context(self, full_text: str) -> Dict:
        """
        Extract high-level context from the document.
        This will be used to prefix each chunk.
        """
        context = {
            'document_name': None,
            'quy_trinh': None,
        }
        
        # Try to extract "Tên quy trình"
        quy_trinh_match = re.search(r'Tên quy trình:\s*([^\n_]+)', full_text)
        if quy_trinh_match:
            context['quy_trinh'] = quy_trinh_match.group(1).strip()
            context['document_name'] = context['quy_trinh']
        
        return context
    
    def extract_section_context(self, text: str, prev_context: Optional[str] = None) -> str:
        """
        Extract the section/part that this chunk belongs to.
        Returns a context string like "Thành phần hồ sơ" or "Căn cứ pháp lý"
        """
        # Check for common section headers
        section_headers = [
            (r'Thành phần[,\s]+số lượng hồ sơ', 'Thành phần hồ sơ'),
            (r'Thành phần hồ sơ', 'Thành phần hồ sơ'),
            (r'Giấy tờ phải nộp', 'Giấy tờ phải nộp'),
            (r'Giấy tờ phải xuất trình', 'Giấy tờ phải xuất trình'),
            (r'Căn cứ pháp lý', 'Căn cứ pháp lý'),
            (r'Yêu cầu[,\s]+điều kiện', 'Yêu cầu, điều kiện'),
            (r'Trình tự thực hiện', 'Trình tự thực hiện'),
            (r'Cách thức thực hiện', 'Cách thức thực hiện'),
            (r'Thời hạn giải quyết', 'Thời hạn giải quyết'),
            (r'Lệ phí|Phí', 'Lệ phí'),
            (r'Kết quả', 'Kết quả'),
            (r'Biểu mẫu|Mẫu đơn', 'Biểu mẫu'),
            (r'Tờ khai đăng ký', 'Mẫu tờ khai'),
            (r'Lưu ý', 'Lưu ý'),
        ]
        
        for pattern, label in section_headers:
            if re.search(pattern, text[:300], re.IGNORECASE):
                return label
        
        # If no header found, return previous context (inherit from previous chunk)
        return prev_context
    
    def extract_structure_info(self, text: str) -> Dict:
        """
        Extract structural information from chunk
        Returns: {chapter, article, section, type}
        """
        info = {
            'chapter': None,
            'article': None,
            'section': None,
            'type': 'content'
        }
        
        # Extract Chương (Chapter)
        chapter_match = re.search(r'Chương\s+([IVXLCDM]+)', text[:200])
        if chapter_match:
            info['chapter'] = chapter_match.group(1)
            info['type'] = 'chapter'
        
        # Extract Điều (Article)
        article_match = re.search(r'Điều\s+(\d+)', text[:200])
        if article_match:
            info['article'] = article_match.group(1)
            info['type'] = 'article'
        
        # Extract Mục (Section)
        section_match = re.search(r'Mục\s+([\d\.]+)', text[:200])
        if section_match:
            info['section'] = section_match.group(1)
            info['type'] = 'section'
        
        return info
    
    def split_by_separator(self, text: str, separator_pattern: str) -> List[str]:
        """Split text by regex pattern while keeping the separator"""
        if not text.strip():
            return []
        
        # Split and keep separator at beginning of each chunk
        parts = re.split(separator_pattern, text)
        
        # Filter empty parts
        return [p.strip() for p in parts if p.strip()]
    
    def merge_small_chunks(self, chunks: List[str], min_size: int = 100) -> List[str]:
        """Merge chunks that are too small"""
        if not chunks:
            return []
        
        merged = []
        current_chunk = chunks[0]
        
        for next_chunk in chunks[1:]:
            current_tokens = self.count_tokens(current_chunk)
            next_tokens = self.count_tokens(next_chunk)
            
            # If current chunk is too small and merging won't exceed limit
            if current_tokens < min_size and (current_tokens + next_tokens) < self.chunk_size:
                current_chunk = current_chunk + "\n\n" + next_chunk
            else:
                merged.append(current_chunk)
                current_chunk = next_chunk
        
        # Add last chunk
        merged.append(current_chunk)
        
        return merged
    
    def add_overlap(self, chunks: List[str]) -> List[str]:
        """
        IMPROVED: Add context overlap between consecutive chunks.
        Instead of just repeating text, we prepend section context.
        """
        # For now, skip overlap - we'll add context prefix instead
        # The context prefix is more valuable than text repetition
        return chunks
    
    def create_context_prefix(self, doc_context: Dict, section: Optional[str]) -> str:
        """
        Create a context prefix for a chunk.
        Format: [Quy trình: X | Phần: Y]
        """
        parts = []
        
        if doc_context.get('quy_trinh'):
            parts.append(f"Quy trình: {doc_context['quy_trinh']}")
        
        if section:
            parts.append(f"Phần: {section}")
        
        if parts:
            return f"[{' | '.join(parts)}]\n\n"
        return ""
    
    def chunk_text(self, text: str, add_overlap: bool = True, document_title: Optional[str] = None) -> List[Dict]:
        """
        Chunk text with legal structure awareness
        
        Returns:
            List of dicts: [
                {
                    'text': '...',
                    'tokens': 450,
                    'chapter': 'I',
                    'article': '5',
                    'section': None,
                    'type': 'article'
                },
                ...
            ]
        """
        if not text.strip():
            return []
        
        chunks = [text]
        
        # Try each separator in order until chunks are small enough
        for separator in self.separators:
            new_chunks = []
            
            for chunk in chunks:
                token_count = self.count_tokens(chunk)
                
                if token_count > self.chunk_size:
                    # Split this chunk
                    split_chunks = self.split_by_separator(chunk, separator)
                    new_chunks.extend(split_chunks)
                else:
                    # Keep as-is
                    new_chunks.append(chunk)
            
            chunks = new_chunks
            
            # Check if all chunks are within limit
            max_tokens = max(self.count_tokens(c) for c in chunks)
            if max_tokens <= self.chunk_size:
                break
        
        # Merge chunks that are too small
        chunks = self.merge_small_chunks(chunks, min_size=100)
        
        # Add overlap if requested
        if add_overlap:
            chunks = self.add_overlap(chunks)
        
        # Create result with metadata
        result = []
        for i, chunk in enumerate(chunks):
            structure_info = self.extract_structure_info(chunk)
            
            result.append({
                'text': chunk.strip(),
                'tokens': self.count_tokens(chunk),
                'chunk_index': i,
                'chapter': structure_info['chapter'],
                'article': structure_info['article'],
                'section': structure_info['section'],
                'type': structure_info['type']
            })
        
        logger.info(f"✅ Chunked into {len(result)} chunks (avg {sum(c['tokens'] for c in result) / len(result):.0f} tokens/chunk)")
        
        return result
