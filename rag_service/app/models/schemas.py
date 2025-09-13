from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

class QueryRequest(BaseModel):
    """UNIFIED: Handles both initial queries and clarification responses"""
    query: str = Field(..., description="Câu hỏi của người dùng hoặc text từ clarification")
    session_id: Optional[str] = Field(None, description="Session ID cho conversation history")
    forced_collection: Optional[str] = Field(None, description="Collection bắt buộc nếu có")
    
    # Clarification fields - Optional, chỉ có khi đây là clarification response
    selected_option: Optional[Dict[str, Any]] = Field(None, description="Option được chọn từ clarification")
    original_query: Optional[str] = Field(None, description="Query gốc khi có clarification")
    
    # Query processing options
    max_tokens: Optional[int] = Field(2048, description="Số token tối đa cho response")
    temperature: Optional[float] = Field(0.1, description="Temperature cho generation")
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
    """UNIFIED: Supports both answer and clarification responses - ALL FIELDS OPTIONAL"""
    # Core response metadata
    type: str = Field(..., description="Type of response (clarification_needed, answer, error)")
    session_id: Optional[str] = Field(None, description="Session ID")
    processing_time: float = Field(default=0.0, description="Thời gian xử lý (giây)")
    message: Optional[str] = Field(None, description="User-facing message")
    
    # Answer fields - for type="answer"
    answer: Optional[str] = Field(None, description="Câu trả lời của AI với nguồn tham khảo")
    sources: Optional[List[DocumentChunk]] = Field(default=[], description="Các chunk tài liệu tham khảo")
    source_files: Optional[List[str]] = Field(default=[], description="Danh sách tên file tham khảo")
    form_attachments: Optional[List[FormAttachment]] = Field(default=[], description="Danh sách form đi kèm")
    collections_used: Optional[List[str]] = Field(default=[], description="Danh sách collection đã sử dụng")
    
    # Clarification fields - for type="clarification_needed" (DIRECT STRUCTURE)
    options: Optional[List["ClarificationOption"]] = Field(default=[], description="Clarification options - DIRECT ACCESS")
    confidence: Optional[float] = Field(None, description="Confidence score")
    show_manual_input: Optional[bool] = Field(default=False, description="Show manual input option")
    manual_input_placeholder: Optional[str] = Field(None, description="Placeholder for manual input")
    style: Optional[str] = Field(None, description="UI style hint")
    target_collection: Optional[str] = Field(None, description="Target collection if determined")
    document: Optional[str] = Field(None, description="Target document if determined")
    procedure: Optional[str] = Field(None, description="Target procedure if determined")
    
    # Error fields - for type="error"
    error: Optional[str] = Field(None, description="Error message if any")
    
    # Legacy fields for backward compatibility
    category: Optional[str] = Field(None, description="Response category")
    generated_questions: Optional[List[str]] = Field(default=[], description="Generated questions")
    context_info: Optional[dict] = Field(default={}, description="Context information")
    
    # Metadata
    routing_info: Optional[dict] = Field(default={}, description="Thông tin về query routing")
    session_cleared: Optional[bool] = Field(default=False, description="Session cleared status")
    context_preserved: Optional[bool] = Field(default=True, description="Context preserved status")
    preserved_collection: Optional[str] = Field(None, description="Preserved collection")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # DIRECT CLARIFICATION FIELDS - Support for direct structure
    options: Optional[List['ClarificationOption']] = Field(default=[], description="Direct clarification options")
    show_manual_input: Optional[bool] = Field(False, description="Show manual input option")
    manual_input_placeholder: Optional[str] = Field(None, description="Manual input placeholder")
    style: Optional[str] = Field(None, description="Style for display")
    target_collection: Optional[str] = Field(None, description="Target collection")
    document: Optional[str] = Field(None, description="Target document")
    procedure: Optional[str] = Field(None, description="Target procedure")
    
    # LEGACY NESTED STRUCTURE - For backward compatibility
    clarification: Optional[dict] = Field(default={}, description="Legacy nested clarification structure")

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


# =====================================================================
# CLARIFICATION SCHEMAS - STANDARDIZED FOR ALL LEVELS  
# =====================================================================

class ClarificationOption(BaseModel):
    """
    Option chuẩn hóa cho tất cả các tầng clarification
    Mỗi tầng có thể sử dụng tập con các trường này, nhưng format luôn nhất quán
    """
    id: str = Field(..., description="ID của option")
    title: str = Field(..., description="Tiêu đề hiển thị")
    description: Optional[str] = Field(None, description="Mô tả chi tiết")
    action: str = Field(..., description="Hành động khi chọn option")
    # Data fields - tùy theo tầng, một số trường có thể là None
    collection: Optional[str] = Field(None, description="Collection liên quan nếu có")
    document: Optional[str] = Field(None, description="Document liên quan nếu có")
    procedure: Optional[str] = Field(None, description="Thủ tục liên quan nếu có")
    question_text: Optional[str] = Field(None, description="Câu hỏi cụ thể nếu có")
    # Metadata fields
    confidence_percent: Optional[float] = Field(None, description="Điểm tin cậy nếu có")
    source_file: Optional[str] = Field(None, description="File nguồn nếu có")
    context_type: Optional[str] = Field(None, description="Loại context cần thu thập")
    # Phần mở rộng - để tương thích với frontend hiện tại
    examples: Optional[List[str]] = Field(default=[], description="Ví dụ cho option")
    category: Optional[str] = Field(None, description="Danh mục nếu có")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "1",
                "title": "Hộ tịch",
                "description": "Thủ tục về khai sinh, kết hôn, khai tử",
                "action": "proceed_with_collection",
                "collection": "quy_trinh_cap_ho_tich_cap_xa",
                "confidence_percent": 85.5
            }
        }

class StandardClarificationResponse(BaseModel):
    """
    Schema chuẩn hóa cho mọi response clarification ở tất cả tầng
    Đảm bảo tất cả tầng đều có cùng format, frontend dễ xử lý
    """
    # Core fields - luôn có
    type: str = Field(..., description="Loại response (clarification_needed, auto_route, v.v.)")
    confidence_level: Optional[str] = Field(None, description="Mức độ tin cậy (high_confidence, medium_high_confidence, v.v.)")
    confidence: Optional[float] = Field(None, description="Điểm tin cậy (0-1)")
    message: str = Field(..., description="Thông báo cho người dùng")
    answer: Optional[str] = Field(None, description="Câu trả lời tạm thời hoặc thông báo")
    
    # DIRECT DATA FIELDS - Simplified structure  
    options: List[ClarificationOption] = Field(default=[], description="Các lựa chọn cho người dùng - DIRECT ACCESS")
    
    # Context fields
    target_collection: Optional[str] = Field(None, description="Collection đích nếu đã xác định")
    document: Optional[str] = Field(None, description="Document đích nếu đã xác định")
    procedure: Optional[str] = Field(None, description="Thủ tục liên quan nếu đã xác định")
    # Metadata và extension fields
    requires_user_input: bool = Field(default=False, description="Có yêu cầu người dùng nhập thêm không")
    show_manual_input: Optional[bool] = Field(default=False, description="Hiển thị ô nhập thủ công")
    manual_input_placeholder: Optional[str] = Field(None, description="Placeholder cho ô nhập thủ công")
    style: Optional[str] = Field(None, description="Style hiển thị (confirmation, multiple_choice, v.v.)")
    routing_context: Optional[Dict[str, Any]] = Field(default={}, description="Context từ router")
    routing_info: Optional[Dict[str, Any]] = Field(default={}, description="Thông tin routing")
    strategy: Optional[str] = Field(None, description="Chiến lược clarification")
    session_id: Optional[str] = Field(None, description="Session ID nếu có")
    additional_help: Optional[str] = Field(None, description="Hướng dẫn bổ sung hiển thị cho người dùng")
    processing_time: Optional[float] = Field(None, description="Thời gian xử lý")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "clarification_needed",
                "confidence_level": "medium_confidence",
                "confidence": 0.58,
                "message": "Câu hỏi của bạn có thể liên quan đến các thủ tục sau. Bạn muốn hỏi về:",
                "options": [  # ← DIRECT ACCESS - No nesting!
                    {
                        "id": "1",
                        "title": "Hộ Tịch",
                        "description": "Thủ tục về khai sinh, kết hôn, khai tử",
                        "action": "proceed_with_collection",
                        "collection": "quy_trinh_cap_ho_tich_cap_xa",
                        "confidence_percent": 58.5
                    }
                ],
                "target_collection": "quy_trinh_cap_ho_tich_cap_xa",
                "style": "multiple_choice",
                "session_id": "abc-123"
            }
        }

# Action responses - chuẩn hóa cho các action handler

class ClarificationActionResponse(BaseModel):
    """Base class cho tất cả các action response"""
    response_type: str = Field(..., description="Loại action response")
    message: str = Field(..., description="Thông báo cho action")
    session_id: Optional[str] = Field(None, description="Session ID")

class ProceedWithQuestionResponse(BaseModel):
    """Response khi người dùng chọn một câu hỏi cụ thể"""
    response_type: Literal["proceed_with_question"] = "proceed_with_question"
    message: str = Field(..., description="Thông báo cho action")
    session_id: Optional[str] = Field(None, description="Session ID")
    final_query: str = Field(..., description="Câu hỏi cuối cùng để xử lý")
    collection: Optional[str] = Field(None, description="Collection để tìm câu trả lời")
    document: Optional[str] = Field(None, description="Document cụ thể nếu có")
    procedure: Optional[str] = Field(None, description="Thủ tục liên quan")

class CollectionOverviewResponse(BaseModel):
    """Response khi người dùng muốn xem tổng quan về một collection"""
    response_type: Literal["collection_overview"] = "collection_overview"
    message: str = Field(..., description="Thông báo cho action")
    session_id: Optional[str] = Field(None, description="Session ID")
    collection: str = Field(..., description="Collection được chọn")
    questions: List[Dict[str, Any]] = Field(default=[], description="Danh sách câu hỏi mẫu")

class ManualInputResponse(BaseModel):
    """Response khi yêu cầu người dùng nhập thủ công"""
    response_type: Literal["manual_input_request"] = "manual_input_request"
    message: str = Field(..., description="Thông báo cho action")
    session_id: Optional[str] = Field(None, description="Session ID")
    collection: Optional[str] = Field(None, description="Collection gợi ý nếu có")
    document: Optional[str] = Field(None, description="Document gợi ý nếu có")
    procedure: Optional[str] = Field(None, description="Thủ tục gợi ý nếu có")

class ClarificationErrorResponse(BaseModel):
    """Response khi có lỗi xảy ra"""
    response_type: Literal["error"] = "error"
    message: str = Field(..., description="Thông báo cho action")
    session_id: Optional[str] = Field(None, description="Session ID")
    error: str = Field(..., description="Thông báo lỗi chi tiết")
