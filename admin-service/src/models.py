"""
Updated Models for LegalRAG - Matching new schema design
Collections → Documents → Chunks/Vectors + Forms
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, date
from uuid import UUID

# ============================================
# COLLECTION MODELS
# ============================================

class CollectionBase(BaseModel):
    """Base collection model"""
    name: str = Field(..., description="Collection slug/identifier")
    display_name: str = Field(..., description="Display name")
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CollectionCreate(CollectionBase):
    """Create collection"""
    pass

class CollectionUpdate(BaseModel):
    """Update collection (all fields optional)"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class CollectionResponse(CollectionBase):
    """Collection response with stats"""
    id: UUID
    document_count: int = 0
    total_chunks: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# DOCUMENT MODELS
# ============================================

class DocumentBase(BaseModel):
    """Base document model"""
    collection_id: UUID
    document_code: Optional[str] = None
    title: str
    issuing_authority: Optional[str] = None
    executing_agency: Optional[str] = None
    document_type: Optional[str] = None
    issue_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentCreate(DocumentBase):
    """Create document"""
    filename: str
    file_path: Optional[str] = None

class DocumentUpdate(BaseModel):
    """Update document"""
    title: Optional[str] = None
    document_code: Optional[str] = None
    issuing_authority: Optional[str] = None
    executing_agency: Optional[str] = None
    document_type: Optional[str] = None
    issue_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(DocumentBase):
    """Document response with full details"""
    id: UUID
    filename: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    mime_type: Optional[str] = None
    status: str = "pending"
    chunk_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================
# CHUNK MODELS
# ============================================

class ChunkBase(BaseModel):
    """Base chunk model"""
    document_id: UUID
    chunk_index: int
    content: str
    section_title: Optional[str] = None
    source_reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChunkCreate(ChunkBase):
    """Create chunk with embedding"""
    embedding: List[float] = Field(..., description="384-dim vector")

class ChunkResponse(ChunkBase):
    """Chunk response (without embedding for efficiency)"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ChunkWithSimilarity(ChunkResponse):
    """Chunk with similarity score (for search results)"""
    similarity: float = Field(..., description="Cosine similarity score")
    document_title: Optional[str] = None
    document_code: Optional[str] = None
    collection_name: Optional[str] = None

# ============================================
# FORM MODELS
# ============================================

class FormBase(BaseModel):
    """Base form model"""
    document_id: UUID
    form_code: Optional[str] = None
    form_name: str
    form_type: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FormCreate(FormBase):
    """Create form"""
    template_path: Optional[str] = None
    preview_path: Optional[str] = None
    fields: List[Dict[str, Any]] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)

class FormUpdate(BaseModel):
    """Update form"""
    form_name: Optional[str] = None
    form_type: Optional[str] = None
    description: Optional[str] = None
    template_path: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None
    validation_rules: Optional[Dict[str, Any]] = None

class FormResponse(FormBase):
    """Form response"""
    id: UUID
    template_path: Optional[str] = None
    preview_path: Optional[str] = None
    fields: List[Dict[str, Any]] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# QUERY MODELS (existing, updated)
# ============================================

class QueryRequest(BaseModel):
    """Query request"""
    question: str = Field(..., description="User question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation")
    collection_filter: Optional[str] = Field(None, description="Filter by collection name")
    top_k: Optional[int] = Field(10, description="Number of chunks to retrieve")
    similarity_threshold: Optional[float] = Field(0.7, description="Minimum similarity")
    max_tokens: Optional[int] = Field(2048, description="Max tokens for response")
    temperature: Optional[float] = Field(0.1, description="Generation temperature")

class QueryResponse(BaseModel):
    """Query response"""
    answer: str = Field(..., description="Generated answer")
    sources: List[ChunkWithSimilarity] = Field(default_factory=list)
    session_id: Optional[str] = None
    processing_time: float = 0.0
    tokens_used: int = 0
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

# ============================================
# USER MODELS
# ============================================

class UserBase(BaseModel):
    """Base user model"""
    cccd_number: str = Field(..., description="CCCD number")
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class UserCreate(UserBase):
    """Create user"""
    cccd_front_image: Optional[str] = None
    cccd_back_image: Optional[str] = None
    qr_code_data: Optional[str] = None

class UserResponse(UserBase):
    """User response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# ADMIN MODELS
# ============================================

class AdminUserBase(BaseModel):
    """Base admin user model"""
    username: str
    email: str
    full_name: Optional[str] = None
    role: str = "admin"

class AdminUserCreate(AdminUserBase):
    """Create admin user"""
    password: str = Field(..., min_length=8)

class AdminUserLogin(BaseModel):
    """Admin login"""
    username: str
    password: str

class AdminUserResponse(AdminUserBase):
    """Admin user response"""
    id: UUID
    is_active: bool = True
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

# ============================================
# ANALYTICS MODELS
# ============================================

class CollectionStats(BaseModel):
    """Collection statistics"""
    collection_id: UUID
    collection_name: str
    document_count: int
    chunk_count: int
    total_file_size: int
    avg_chunks_per_document: float

class SystemMetric(BaseModel):
    """System metric"""
    metric_type: str
    metric_value: float
    collection_id: Optional[UUID] = None
    aggregation_period: Optional[str] = None
    recorded_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QueryLog(BaseModel):
    """Query log entry"""
    query_text: str
    answer_text: Optional[str] = None
    collection_routed: Optional[str] = None
    processing_time_ms: int
    confidence_score: Optional[float] = None
    created_at: datetime

# ============================================
# PAGINATION & LIST RESPONSES
# ============================================

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# ============================================
# UPLOAD & PROCESSING MODELS
# ============================================

class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    success: bool
    document_id: UUID
    filename: str
    message: str
    chunk_count: Optional[int] = None

class BatchUploadResponse(BaseModel):
    """Batch upload response"""
    success: bool
    total_uploaded: int
    successful: List[DocumentUploadResponse]
    failed: List[Dict[str, str]]

class ProcessingStatus(BaseModel):
    """Document processing status"""
    document_id: UUID
    status: str  # pending, processing, completed, failed
    progress: int = Field(0, ge=0, le=100)
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    estimated_completion: Optional[datetime] = None
