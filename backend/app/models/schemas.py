from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

class QueryRequest(BaseModel):
    question: str = Field(..., description="Câu hỏi của người dùng")
    max_tokens: Optional[int] = Field(2048, description="Số token tối đa cho response")
    temperature: Optional[float] = Field(0.1, description="Temperature cho generation (thấp để bám sát văn bản)")
    top_k: Optional[int] = Field(5, description="Số lượng document liên quan")

# =====================================================================
# ENHANCED QUERY SCHEMAS
# =====================================================================

class EnhancedQueryRequest(BaseModel):
    """Enhanced query request với preprocessing features"""
    question: str = Field(..., description="Câu hỏi của người dùng")
    session_id: Optional[str] = Field(None, description="Session ID cho conversation history")
    max_tokens: Optional[int] = Field(2048, description="Số token tối đa cho response")
    temperature: Optional[float] = Field(0.1, description="Temperature cho generation")
    enable_clarification: bool = Field(True, description="Bật/tắt tính năng yêu cầu làm rõ")
    enable_context_synthesis: bool = Field(True, description="Bật/tắt tổng hợp ngữ cảnh từ lịch sử")
    clarification_threshold: Literal['low', 'medium', 'high'] = Field('medium', description="Ngưỡng yêu cầu làm rõ")
    target_context_length: Optional[int] = Field(2500, description="Độ dài context mục tiêu")

class ClarificationRequest(BaseModel):
    """Request để trả lời các câu hỏi làm rõ"""
    session_id: str = Field(..., description="Session ID")
    original_question: str = Field(..., description="Câu hỏi gốc")
    responses: Dict[str, str] = Field(..., description="Các câu trả lời làm rõ")

class ClarificationResponse(BaseModel):
    """Response sau khi xử lý clarification"""
    type: Literal['clarified_answer'] = Field(..., description="Loại response")
    answer: str = Field(..., description="Câu trả lời sau khi làm rõ")
    original_query: str = Field(..., description="Câu hỏi gốc")
    clarified_query: str = Field(..., description="Câu hỏi đã được làm rõ")
    clarification_responses: Dict[str, str] = Field(..., description="Các câu trả lời làm rõ")
    sources: List['DocumentChunk'] = Field(default=[], description="Các chunk tài liệu tham khảo")
    source_files: List[str] = Field(default=[], description="Danh sách tên file")
    context_strategy: Dict[str, Any] = Field(default={}, description="Thông tin về chiến lược context")
    processing_time: float = Field(default=0.0, description="Thời gian xử lý")
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.now)

class EnhancedQueryResponse(BaseModel):
    """Enhanced response với thông tin preprocessing"""
    type: Literal['answer', 'clarification_request', 'clarified_answer'] = Field(..., description="Loại response")
    answer: str = Field(default="", description="Câu trả lời (nếu có)")
    original_query: str = Field(..., description="Câu hỏi gốc")
    processed_query: Optional[str] = Field(None, description="Câu hỏi đã xử lý")
    clarification_questions: List[str] = Field(default=[], description="Các câu hỏi làm rõ")
    clarification_responses: Optional[Dict[str, str]] = Field(None, description="Các câu trả lời làm rõ")
    sources: List['DocumentChunk'] = Field(default=[], description="Các chunk tài liệu tham khảo")
    source_files: List[str] = Field(default=[], description="Danh sách tên file")
    context_strategy: Dict[str, Any] = Field(default={}, description="Thông tin về chiến lược context")
    preprocessing_steps: List[str] = Field(default=[], description="Các bước preprocessing đã thực hiện")
    processing_time: float = Field(default=0.0, description="Thời gian xử lý tổng")
    session_id: Optional[str] = Field(None, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.now)

# =====================================================================
# SESSION MANAGEMENT SCHEMAS  
# =====================================================================

class SessionInfoResponse(BaseModel):
    """Thông tin session"""
    session_id: str = Field(..., description="Session ID")
    created_at: datetime = Field(..., description="Thời gian tạo")
    last_accessed: datetime = Field(..., description="Lần truy cập cuối")
    conversation_turns: int = Field(default=0, description="Số lượt hội thoại")
    topics: List[str] = Field(default=[], description="Chủ đề đã thảo luận")
    recent_queries: List[str] = Field(default=[], description="Câu hỏi gần đây")
    metadata: Dict[str, Any] = Field(default={}, description="Metadata session")

# =====================================================================
# DOCUMENT AND RESPONSE SCHEMAS
# =====================================================================

class DocumentChunk(BaseModel):
    content: str = Field(..., description="Nội dung của chunk")
    document_title: str = Field(..., description="Tiêu đề tài liệu")
    document_code: Optional[str] = Field(None, description="Mã số tài liệu")
    section_title: Optional[str] = Field(None, description="Tiêu đề phần/mục")
    source_reference: Optional[str] = Field(None, description="Tham chiếu nguồn (Mục x.y)")
    file_path: Optional[str] = Field(None, description="Đường dẫn file")
    issuing_authority: Optional[str] = Field(None, description="Cơ quan ban hành")
    executing_agency: Optional[str] = Field(None, description="Cơ quan thực hiện")
    effective_date: Optional[str] = Field(None, description="Ngày hiệu lực")
    collection: str = Field(..., description="Tên collection chứa chunk")
    similarity: float = Field(..., description="Điểm similarity (0-1)")
    keywords: List[str] = Field(default=[], description="Từ khóa liên quan")
    processing_time: Optional[str] = Field(None, description="Thời gian xử lý thủ tục")
    fee_info: Optional[str] = Field(None, description="Thông tin lệ phí")
    legal_basis: List[str] = Field(default=[], description="Căn cứ pháp lý")
    # Form-related fields
    has_form: bool = Field(default=False, description="Có form đi kèm không")
    form_url: Optional[str] = Field(None, description="URL download form (nếu có)")

class FormAttachment(BaseModel):
    """Form file đi kèm với response"""
    document_id: str = Field(..., description="ID của document")
    document_title: str = Field(..., description="Tiêu đề document")
    form_filename: str = Field(..., description="Tên file form")
    form_url: str = Field(..., description="URL download form")
    collection_id: str = Field(..., description="Collection chứa form")

class QueryResponse(BaseModel):
    answer: str = Field(..., description="Câu trả lời của AI với nguồn tham khảo")
    sources: List[DocumentChunk] = Field(..., description="Các chunk tài liệu tham khảo")
    source_files: List[str] = Field(default=[], description="Danh sách tên file tham khảo")
    # Form attachments
    form_attachments: List[FormAttachment] = Field(default=[], description="Danh sách form đi kèm")
    collections_used: Optional[List[str]] = Field(default=[], description="Danh sách collection đã sử dụng")
    routing_info: Optional[dict] = Field(default={}, description="Thông tin về query routing")
    processing_time: float = Field(..., description="Thời gian xử lý (giây)")
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthResponse(BaseModel):
    status: str = Field(..., description="Trạng thái service")
    version: str = Field(default="1.0.0", description="Phiên bản API")
    model_loaded: bool = Field(..., description="Trạng thái model")
    vectordb_status: bool = Field(..., description="Trạng thái vector database")
    total_collections: Optional[int] = Field(default=0, description="Tổng số collections")
    total_documents: Optional[int] = Field(default=0, description="Tổng số documents")
    collections: Optional[List[dict]] = Field(default=[], description="Thông tin chi tiết collections")
    query_router_available: Optional[bool] = Field(default=False, description="Trạng thái query router")
    # Enhanced fields
    embedding_model: Optional[str] = Field(default="", description="Tên embedding model")
    reranker_loaded: Optional[bool] = Field(default=False, description="Trạng thái reranker")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    additional_info: Optional[Dict[str, Any]] = Field(default={}, description="Thông tin bổ sung")

class IndexingRequest(BaseModel):
    force_rebuild: Optional[bool] = Field(False, description="Có rebuild index hay không")
    chunk_size: Optional[int] = Field(800, description="Kích thước chunk")
    overlap: Optional[int] = Field(200, description="Overlap giữa chunks")

class IndexingResponse(BaseModel):
    status: str = Field(..., description="Trạng thái indexing")
    collections_processed: Optional[int] = Field(default=0, description="Số collections đã xử lý")
    total_documents: Optional[int] = Field(default=0, description="Tổng số tài liệu đã xử lý")
    total_chunks: Optional[int] = Field(default=0, description="Tổng số chunks đã tạo")
    processing_time: float = Field(..., description="Thời gian xử lý")
    collections_detail: Optional[dict] = Field(default={}, description="Chi tiết từng collection")
    message: str = Field(..., description="Thông báo chi tiết")
    # Enhanced fields
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
