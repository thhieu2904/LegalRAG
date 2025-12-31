"""
Storage models - FastAPI response schemas (SIMPLE - CRUD ONLY)
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    storage_connected: bool


class FileMetadata(BaseModel):
    """File metadata"""
    name: str
    size: int
    content_type: str
    etag: Optional[str] = None
    last_modified: Optional[datetime] = None


class FileUploadResponse(BaseModel):
    """File upload response"""
    success: bool
    message: str
    file_path: str
    file_size: int
    bucket: str
    content_type: str = "application/pdf"


class FileListResponse(BaseModel):
    """List files response"""
    success: bool
    files: List[FileMetadata]
    total: int


class DeleteResponse(BaseModel):
    """Delete file response"""
    success: bool
    message: str
    file_path: str


class TextExtractionResponse(BaseModel):
    """Text extraction response (LOW-LEVEL, raw text only)"""
    success: bool
    text: str
    pages: int
    character_count: int
    word_count: int
    raw_length: Optional[int] = None  # Original text length before cleaning
