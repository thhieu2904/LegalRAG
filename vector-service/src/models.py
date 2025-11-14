"""
Vector Service Response Models
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    db: str
    pgvector: str


class VectorInsertRequest(BaseModel):
    """Insert single vector"""
    document_id: str
    chunk_index: int
    content: str
    embedding: List[float]
    metadata: Optional[dict] = None


class VectorInsertResponse(BaseModel):
    """Insert response"""
    success: bool
    vector_id: str
    message: str


class VectorBatchInsertRequest(BaseModel):
    """Insert multiple vectors"""
    vectors: List[VectorInsertRequest]


class VectorBatchInsertResponse(BaseModel):
    """Batch insert response"""
    success: bool
    inserted: int
    failed: int
    total: int


class SearchRequest(BaseModel):
    """Search request"""
    embedding: List[float]
    top_k: int = 10
    threshold: float = 0.7
    document_ids: Optional[List[str]] = None


class SearchResult(BaseModel):
    """Single search result"""
    vector_id: str
    document_id: str
    chunk_index: int
    content: str
    similarity: float


class SearchResponse(BaseModel):
    """Search response"""
    success: bool
    results: List[SearchResult]
    total: int


class VectorDeleteRequest(BaseModel):
    """Delete vector(s)"""
    vector_ids: Optional[List[str]] = None
    document_id: Optional[str] = None


class DeleteResponse(BaseModel):
    """Delete response"""
    success: bool
    deleted: int
    message: str


class VectorCountResponse(BaseModel):
    """Vector count response"""
    success: bool
    total_vectors: int
    total_documents: int
