"""
Pydantic models for Embedding Service
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# ============= REQUEST MODELS =============

class EmbedRequest(BaseModel):
    """Single text embedding request"""
    text: str = Field(..., description="Text to embed")


class EmbedBatchRequest(BaseModel):
    """Batch embedding request"""
    texts: List[str] = Field(..., description="List of texts to embed")


class ChunkAndEmbedRequest(BaseModel):
    """Document chunking + embedding request (admin-only)"""
    text: str = Field(..., description="Document text to chunk and embed")
    document_id: str = Field(..., description="Document identifier")
    metadata: Optional[Dict] = Field(default=None, description="Optional metadata from admin-service")
    add_overlap: bool = Field(default=True, description="Add overlap between chunks")


# ============= RESPONSE MODELS =============

class EmbedResponse(BaseModel):
    """Single embedding response"""
    success: bool
    embedding: List[float]
    dimension: int
    tokens: int


class EmbedBatchResponse(BaseModel):
    """Batch embedding response"""
    success: bool
    embeddings: List[List[float]]
    total: int
    dimension: int


class ChunkInfo(BaseModel):
    """Information about a single chunk"""
    text: str
    tokens: int
    chunk_index: int
    chapter: Optional[str] = None
    article: Optional[str] = None
    section: Optional[str] = None
    type: str  # 'chapter', 'article', 'section', 'content'


class ChunkWithEmbedding(BaseModel):
    """Chunk with its embedding"""
    chunk_info: ChunkInfo
    embedding: List[float]


class ChunkAndEmbedResponse(BaseModel):
    """Document chunking + embedding response"""
    success: bool
    document_id: str
    total_chunks: int
    chunks: List[ChunkWithEmbedding]
    dimension: int
    metadata: Optional[Dict] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    model_loaded: bool
    model_name: str
    device: str
    embedding_dimension: int
    max_seq_length: int
