"""
Legal Document Chunker for Vietnamese Legal Documents
Chunks documents by legal structure (Điều, Mục, Chương) while respecting token limits
"""
import re
import logging
from typing import List, Dict
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)


class LegalDocumentChunker:
    """
    Intelligent chunker for Vietnamese legal documents
    Respects legal structure hierarchy: Chương > Điều > Mục > Khoản
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
        self.separators = [
            r'\n(?=Chương\s+[IVXLCDM]+[\.\:])',  # Chương (Roman numerals)
            r'\n(?=Điều\s+\d+[\.\:])',            # Điều 1, Điều 2, etc.
            r'\n(?=Mục\s+[\d\.]+[\.\:])',         # Mục 1, Mục 1.1, etc.
            r'\n(?=\d+\.\s)',                      # Numbered items: "1. ", "2. "
            r'\n(?=Khoản\s+\d+[\.\:])',           # Khoản 1, Khoản 2, etc.
            r'\n\n',                               # Double newline
            r'\.\s',                               # Sentence boundary
            r',\s',                                # Comma
            r'\s',                                 # Whitespace
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
        """Add overlap between consecutive chunks"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped = [chunks[0]]  # First chunk as-is
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # Take last N tokens from previous chunk
            prev_words = prev_chunk.split()
            overlap_words = prev_words[-self.chunk_overlap:] if len(prev_words) > self.chunk_overlap else prev_words
            overlap_text = ' '.join(overlap_words)
            
            # Prepend overlap to current chunk
            if overlap_text:
                overlapped_chunk = overlap_text + "\n\n" + current_chunk
            else:
                overlapped_chunk = current_chunk
            
            overlapped.append(overlapped_chunk)
        
        return overlapped
    
    def chunk_text(self, text: str, add_overlap: bool = True) -> List[Dict]:
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
