"""
Pydantic models for Rerank Service API.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class RerankRequest(BaseModel):
    """Request model for reranking documents."""
    
    query: str = Field(
        ...,
        description="Search query in Vietnamese",
        min_length=1,
        max_length=512,
        example="điều kiện thành lập công ty"
    )
    
    documents: List[str] = Field(
        ...,
        description="List of candidate documents to rerank",
        min_items=1,
        max_items=100,
        example=[
            "Văn bản về điều kiện thành lập doanh nghiệp theo luật mới",
            "Hướng dẫn đăng ký kinh doanh cho công ty TNHH",
            "Quy định về vốn điều lệ khi thành lập công ty"
        ]
    )
    
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="List of document IDs corresponding to each document (for same-document filtering)",
        example=["doc_123", "doc_123", "doc_456"]
    )
    
    top_k: Optional[int] = Field(
        default=None,
        description="Number of top results to return. IGNORED when same_document_only=True (returns all chunks from best doc)",
        ge=1,
        le=100,
        example=5
    )
    
    same_document_only: Optional[bool] = Field(
        default=True,
        description="If True, identify best document and return ALL its chunks (preserves full legal context)",
        example=True
    )


class RerankResult(BaseModel):
    """Single reranked document result."""
    
    index: int = Field(
        ...,
        description="Original index in input documents list",
        example=0
    )
    
    text: str = Field(
        ...,
        description="Document text",
        example="Văn bản về điều kiện thành lập doanh nghiệp..."
    )
    
    score: float = Field(
        ...,
        description="Relevance score (0-1, higher is better)",
        ge=0.0,
        le=1.0,
        example=0.8934
    )
    
    rank: int = Field(
        ...,
        description="New rank after reranking (1-based)",
        ge=1,
        example=1
    )


class RerankResponse(BaseModel):
    """Response model for reranking results."""
    
    results: List[RerankResult] = Field(
        ...,
        description="Reranked documents sorted by relevance score (descending)"
    )
    
    processing_time: float = Field(
        ...,
        description="Processing time in seconds",
        example=0.023
    )
    
    model_name: str = Field(
        ...,
        description="Model used for reranking",
        example="AITeamVN/Vietnamese_Reranker"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(
        default="healthy",
        example="healthy"
    )
    
    service: str = Field(
        default="rerank-service",
        example="rerank-service"
    )
    
    model_loaded: bool = Field(
        ...,
        description="Whether the reranker model is loaded",
        example=True
    )
    
    device: str = Field(
        ...,
        description="Device being used (cpu/cuda)",
        example="cpu"
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(
        ...,
        description="Error message",
        example="Invalid request"
    )
    
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information",
        example="Documents list cannot be empty"
    )
