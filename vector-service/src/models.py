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
    """Insert single vector chunk for LegalRAG"""
    document_id: str
    chunk_index: int
    content: str
    section_title: Optional[str] = None  # Legal section: "Điều 1", "Mục 2.3"
    source_reference: Optional[str] = None  # Legal reference: "Điều 1, khoản 1"
    embedding: List[float]  # 768-D Vietnamese model
    token_count: Optional[int] = None
    metadata: Optional[dict] = None  # Full metadata from admin-service


class VectorInsertResponse(BaseModel):
    """Insert response"""
    success: bool
    vector_id: str
    message: str


class DocumentInfo(BaseModel):
    """Document information for creating document record"""
    id: str  # UUID
    collection_id: str  # UUID
    title: str
    filename: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    metadata: Optional[dict] = None


class VectorBatchInsertRequest(BaseModel):
    """
    Insert multiple vectors (AICenter Pattern)
    Document must already exist - Admin Service creates it first
    """
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
    """Single search result for LegalRAG"""
    vector_id: str
    document_id: str
    chunk_index: int
    content: str
    section_title: Optional[str] = None
    source_reference: Optional[str] = None
    similarity: float
    metadata: Optional[dict] = None


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
