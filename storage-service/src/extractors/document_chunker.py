"""
Document Chunker for Vietnamese Legal Documents
Split documents into semantic chunks while preserving section information
"""
import re
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class Chunk:
    """Represents a document chunk"""
    
    def __init__(
        self,
        index: int,
        content: str,
        section_title: Optional[str] = None,
        source_reference: Optional[str] = None,
        page_range: Optional[Tuple[int, int]] = None,
    ):
        self.index = index
        self.content = content
        self.section_title = section_title
        self.source_reference = source_reference
        self.page_range = page_range
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database"""
        return {
            'chunk_index': self.index,
            'content': self.content,
            'section_title': self.section_title,
            'source_reference': self.source_reference,
            'metadata': {
                'page_range': self.page_range,
            } if self.page_range else {}
        }


class DocumentChunker:
    """Chunk Vietnamese legal documents by sections"""
    
    # Section header patterns (cấp 1: Chương, cấp 2: Mục, cấp 3: Điều, cấp 4: Khoản)
    SECTION_PATTERNS = [
        r'^\s*(Chương\s+[\dIVXivx\-]+)\s*$',  # Chapter level 1
        r'^\s*(Mục\s+[\d\.]+)\s*$',  # Section level 2
        r'^\s*(Điều\s+[\d\-]+)\s*$',  # Article level 3
        r'^\s*(Khoản\s+\d+)\s*$',  # Paragraph level 4
    ]
    
    def __init__(self, min_chunk_size: int = 200, max_chunk_size: int = 1000):
        """
        Initialize chunker
        
        Args:
            min_chunk_size: Minimum characters per chunk (skip if smaller)
            max_chunk_size: Maximum characters per chunk (split if larger)
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        logger.info(f"✅ DocumentChunker initialized (min={min_chunk_size}, max={max_chunk_size})")
    
    def chunk_by_sections(
        self,
        text: str,
        page_numbers: Optional[Dict[int, int]] = None,
    ) -> List[Chunk]:
        """
        Chunk document by sections (Chương, Mục, Điều)
        Preserves section hierarchy and references
        
        Args:
            text: Full document text
            page_numbers: Optional dict mapping line number to page number
        
        Returns:
            List of Chunk objects
        """
        try:
            chunks = []
            lines = text.split('\n')
            
            current_section_stack = []  # Stack of current sections: [Chương X, Mục Y, Điều Z]
            buffer = []  # Buffer for current chunk
            chunk_index = 0
            
            for line_num, line in enumerate(lines):
                # Check if this line is a section header
                section_match = None
                section_level = None
                
                for level, pattern in enumerate(self.SECTION_PATTERNS):
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        section_match = match.group(1)
                        section_level = level
                        break
                
                if section_match:
                    # If buffer has content, save it as chunk
                    if buffer:
                        chunk = self._create_chunk(
                            chunk_index,
                            buffer,
                            current_section_stack.copy(),
                            page_numbers,
                        )
                        if chunk:
                            chunks.append(chunk)
                            chunk_index += 1
                        buffer = []
                    
                    # Update section stack
                    if section_level is not None:
                        current_section_stack = current_section_stack[:section_level]
                        current_section_stack.append(section_match)
                    
                    # Add section header to buffer (start new chunk)
                    buffer.append(line)
                else:
                    # Regular content line
                    if line.strip():  # Skip empty lines in beginning
                        buffer.append(line)
                    
                    # Check if buffer exceeds max size
                    buffer_text = '\n'.join(buffer)
                    if len(buffer_text) > self.max_chunk_size:
                        # Split buffer into smaller chunks
                        sub_chunks = self._split_large_chunk(
                            buffer_text,
                            chunk_index,
                            current_section_stack.copy(),
                            page_numbers,
                        )
                        chunks.extend(sub_chunks)
                        chunk_index += len(sub_chunks)
                        buffer = []
            
            # Handle remaining buffer
            if buffer:
                buffer_text = '\n'.join(buffer)
                if buffer_text.strip() and len(buffer_text) >= self.min_chunk_size:
                    chunk = self._create_chunk(
                        chunk_index,
                        buffer,
                        current_section_stack.copy(),
                        page_numbers,
                    )
                    if chunk:
                        chunks.append(chunk)
            
            logger.info(f"✅ Created {len(chunks)} chunks from document")
            return chunks
        
        except Exception as e:
            logger.error(f"❌ Chunking failed: {e}")
            raise
    
    def _create_chunk(
        self,
        index: int,
        lines: List[str],
        section_stack: List[str],
        page_numbers: Optional[Dict[int, int]] = None,
    ) -> Optional[Chunk]:
        """Create a chunk from lines"""
        content = '\n'.join(lines).strip()
        
        if len(content) < self.min_chunk_size:
            return None  # Skip too small chunks
        
        # Build section title and source reference
        section_title = section_stack[-1] if section_stack else None
        source_reference = ' > '.join(section_stack) if section_stack else None
        
        page_range = None
        if page_numbers and section_stack:
            # Try to find page range for this section
            first_page = min([p for p in page_numbers.values() if p is not None], default=None)
            last_page = max([p for p in page_numbers.values() if p is not None], default=None)
            if first_page is not None and last_page is not None:
                page_range = (first_page, last_page)
        
        return Chunk(
            index=index,
            content=content,
            section_title=section_title,
            source_reference=source_reference,
            page_range=page_range,
        )
    
    def _split_large_chunk(
        self,
        text: str,
        start_index: int,
        section_stack: List[str],
        page_numbers: Optional[Dict[int, int]] = None,
    ) -> List[Chunk]:
        """Split a large chunk into smaller pieces by sentences or paragraphs"""
        chunks = []
        
        # Split by paragraphs first (double newline)
        paragraphs = text.split('\n\n')
        buffer = []
        chunk_index = start_index
        
        for para in paragraphs:
            buffer.append(para)
            buffer_text = '\n\n'.join(buffer)
            
            if len(buffer_text) > self.max_chunk_size:
                # Save current buffer and start new one
                if buffer:
                    chunk_lines = buffer[:-1]  # Don't include current paragraph
                    if chunk_lines:
                        chunk = Chunk(
                            index=chunk_index,
                            content='\n\n'.join(chunk_lines),
                            section_title=section_stack[-1] if section_stack else None,
                            source_reference=' > '.join(section_stack) if section_stack else None,
                        )
                        chunks.append(chunk)
                        chunk_index += 1
                buffer = [para]  # Start new buffer with current paragraph
        
        # Handle remaining buffer
        if buffer:
            remaining = '\n\n'.join(buffer).strip()
            if remaining and len(remaining) >= self.min_chunk_size:
                chunk = Chunk(
                    index=chunk_index,
                    content=remaining,
                    section_title=section_stack[-1] if section_stack else None,
                    source_reference=' > '.join(section_stack) if section_stack else None,
                )
                chunks.append(chunk)
        
        return chunks
    
    def chunk_by_size(self, text: str, chunk_size: int = 1000) -> List[Chunk]:
        """
        Simple chunking by fixed size (backup method)
        
        Args:
            text: Document text
            chunk_size: Bytes per chunk
        
        Returns:
            List of Chunk objects
        """
        chunks = []
        words = text.split()
        
        current_chunk = []
        chunk_index = 0
        
        for word in words:
            current_chunk.append(word)
            current_text = ' '.join(current_chunk)
            
            if len(current_text) > chunk_size:
                if len(current_text) >= self.min_chunk_size:
                    chunks.append(Chunk(
                        index=chunk_index,
                        content=current_text,
                    ))
                    chunk_index += 1
                current_chunk = []
        
        # Handle remaining
        if current_chunk:
            remaining = ' '.join(current_chunk)
            if len(remaining) >= self.min_chunk_size:
                chunks.append(Chunk(
                    index=chunk_index,
                    content=remaining,
                ))
        
        logger.info(f"✅ Created {len(chunks)} chunks by size")
        return chunks
