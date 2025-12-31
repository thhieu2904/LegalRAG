"""
Universal Document Chunker for Vietnamese Administrative Documents

Works with ANY document structure - no hardcoded section patterns.
Uses smart paragraph-based splitting with sentence boundary respect.

Key features:
1. Paragraph-based splitting (respects natural document breaks)
2. Sentence boundary awareness (never cuts mid-sentence)
3. Context metadata (each chunk carries its document info without inline text)
4. Noise removal (page markers, repeated headers)
5. Smart merging (combines small paragraphs)
"""
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class UniversalDocumentChunker:
    """
    Universal chunker that works with ANY Vietnamese document structure.
    
    Strategy:
    1. Clean noise (page markers, headers, footers)
    2. Split by paragraphs (natural content boundaries)
    3. Merge small paragraphs / split large ones
    4. Preserve document context as metadata (no inline prefix)
    5. Respect sentence boundaries
    """
    
    def __init__(
        self, 
        model_name: str,
        chunk_size: int = 800,  # Target tokens per chunk
        chunk_overlap: int = 0,  # Overlap disabled in favor of metadata context
        min_chunk_size: int = 100,  # Minimum tokens (merge smaller chunks)
    ):
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        logger.info(f"✅ UniversalDocumentChunker initialized (target: {chunk_size} tokens)")
        
        # Noise patterns to remove
        self.noise_patterns = [
            # Page markers with various formats
            r'Ngày hiệu lực:\s*[\d/]+\s*Trang:\s*\d+/\d+\s*Lần ban hành:\s*\d+',
            r'Trang:\s*\d+/\d+',
            r'Lần ban hành:\s*\d+',
            r'Ngày hiệu lực:\s*[\d/]+',
            # Separators
            r'_{10,}',  # Long underscores
            r'-{10,}',  # Long dashes
            # PDF page markers
            r'--- Page \d+ ---',
        ]
        
        # Patterns to detect document title
        self.title_patterns = [
            r'Tên quy trình:\s*([^\n_]+)',
            r'QUY TRÌNH\s*\n[^\n]*\n\s*([A-ZĐÀ-Ỹ][^\n]{5,50})',
        ]
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for Vietnamese text.
        Vietnamese with subword tokenization: ~1.5 tokens per word
        """
        if not text:
            return 0
        words = text.split()
        return int(len(words) * 1.5)
    
    def clean_text(self, text: str) -> str:
        """
        Remove noise from document text.
        """
        cleaned = text
        
        # Remove noise patterns
        for pattern in self.noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)
        
        # Normalize multiple newlines (keep max 2)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Remove lines that are just whitespace or form noise
        lines = cleaned.split('\n')
        valid_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # Check for form noise (excessive dots/underscores)
            # Example: "Họ và tên: ..................................................."
            dots = stripped.count('.')
            underscores = stripped.count('_')
            length = len(stripped)
            
            # If line is long (>10 chars) and has > 40% dots/underscores, skip it
            # This removes form placeholders while keeping content
            if length > 10 and (dots + underscores) / length > 0.4:
                continue
                
            valid_lines.append(line)
            
        cleaned = '\n'.join(valid_lines)
        
        return cleaned.strip()
    
    def extract_document_title(self, text: str) -> Optional[str]:
        """
        Try to extract the document/procedure title.
        """
        for pattern in self.title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up title
                title = re.sub(r'[_\-]+$', '', title).strip()
                if len(title) > 5 and len(title) < 100:
                    return title
        return None
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs (by double newlines or semantic breaks).
        """
        # First split by double newlines
        paragraphs = re.split(r'\n\n+', text)
        
        # Clean and filter empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def split_by_sentences(self, text: str) -> List[str]:
        """
        Split text by sentences while keeping Vietnamese punctuation.
        """
        # Vietnamese sentence endings: . ! ? followed by space and capital letter
        sentences = re.split(
            r'(?<=[.!?])\s+(?=[A-ZĐÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ\d\-])',
            text
        )
        return [s.strip() for s in sentences if s.strip()]
    
    def merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """
        Merge chunks that are too small.
        """
        if not chunks:
            return []
        
        merged = []
        current_chunk = chunks[0]
        
        for next_chunk in chunks[1:]:
            current_tokens = self.count_tokens(current_chunk)
            next_tokens = self.count_tokens(next_chunk)
            combined_tokens = current_tokens + next_tokens
            
            # Merge if current is too small and combined is within limit
            if current_tokens < self.min_chunk_size and combined_tokens <= self.chunk_size:
                current_chunk = current_chunk + "\n\n" + next_chunk
            else:
                # Save current and start new
                if self.count_tokens(current_chunk) >= self.min_chunk_size // 2:
                    merged.append(current_chunk)
                current_chunk = next_chunk
        
        # Don't forget the last chunk
        if current_chunk and self.count_tokens(current_chunk) >= self.min_chunk_size // 2:
            merged.append(current_chunk)
        
        return merged
    
    def split_large_chunk(self, text: str) -> List[str]:
        """
        Split a chunk that exceeds max size by sentence boundaries.
        """
        if self.count_tokens(text) <= self.chunk_size:
            return [text]
        
        sentences = self.split_by_sentences(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                # Start new chunk with this sentence
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def chunk_text(
        self, 
        text: str, 
        add_overlap: bool = False,  # Ignored - metadata context removed overlap need
        document_title: Optional[str] = None
    ) -> List[Dict]:
        """
        Main chunking method.
        
        Args:
            text: Full document text
            add_overlap: Ignored (kept for backward compatibility)
            document_title: Optional document title for metadata context
        
        Returns:
            List of chunk dicts with: text, tokens, chunk_index, type, etc.
        """
        if not text or not text.strip():
            return []
        
        # Step 1: Clean noise
        cleaned_text = self.clean_text(text)
        
        if not cleaned_text:
            return []
        
        # Step 2: Extract document title if not provided
        if not document_title:
            document_title = self.extract_document_title(text)
        
        # Step 3: Split into paragraphs
        paragraphs = self.split_into_paragraphs(cleaned_text)
        
        if not paragraphs:
            return []
        
        # Step 4: Process paragraphs - merge small, split large
        chunks = []
        for para in paragraphs:
            tokens = self.count_tokens(para)
            
            if tokens > self.chunk_size:
                # Split large paragraph
                sub_chunks = self.split_large_chunk(para)
                chunks.extend(sub_chunks)
            else:
                chunks.append(para)
        
        # Step 5: Merge small chunks
        chunks = self.merge_small_chunks(chunks)
        
        if not chunks:
            return []
        
        # Step 6: Create result with metadata (document context no longer prepended)
        result = []
        
        for i, chunk_text in enumerate(chunks):
            chunk_record = {
                'text': chunk_text,
                'tokens': self.count_tokens(chunk_text),
                'chunk_index': i,
                'chapter': None,  # Not used in universal chunker
                'article': None,  # Not used in universal chunker
                'section': None,  # Not used in universal chunker
                'type': 'content',
            }
            
            if document_title:
                chunk_record['document_title'] = document_title
            
            result.append(chunk_record)
        
        # Log summary
        total_tokens = sum(c['tokens'] for c in result)
        avg_tokens = total_tokens / len(result) if result else 0
        logger.info(
            f"✅ Chunked document into {len(result)} chunks "
            f"(avg {avg_tokens:.0f} tokens/chunk, title: '{document_title or 'unknown'}')"
        )
        
        return result


# Backward compatibility alias
LegalDocumentChunker = UniversalDocumentChunker
