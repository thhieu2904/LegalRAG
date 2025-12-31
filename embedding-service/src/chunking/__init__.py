"""Chunking package"""
# Universal chunker works with ANY Vietnamese document structure
# Uses paragraph-based splitting with sentence boundary awareness
from .universal_chunker import UniversalDocumentChunker

# Backward compatibility alias
LegalDocumentChunker = UniversalDocumentChunker

__all__ = ["LegalDocumentChunker", "UniversalDocumentChunker"]

