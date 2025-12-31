"""
Query Service - RAG Orchestrator
Coordinates embedding, vector search, and LLM to answer questions

Session Management:
- Backend generates and manages session IDs (format: YYYYMMDD_NNNN)
- Frontend sends session_id=None for new session (F5/new tab)
- Document pinning state stored in PostgreSQL
"""
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Tuple
import logging
import httpx
from collections import defaultdict
import numpy as np
import time

from .config import settings
from .database import DatabaseClient
from .routers import forms as forms_router
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global clients
http_client = None
db_client = None

# Session counter (in-memory, synced with DB)
_session_counter = {"date": "", "counter": 0}

# GPU Swap state tracking
_current_gpu_model: Optional[str] = None  # "rerank" | "llm" | None


# ============= GPU SWAP HELPERS =============

async def prepare_rerank():
    """
    Prepare rerank service (load model if swap mode).
    Called before reranking documents.
    """
    global _current_gpu_model
    
    if not settings.GPU_SWAP_MODE:
        return
    
    try:
        logger.info("🔄 GPU Swap: Preparing rerank model...")
        response = await http_client.post(
            f"{settings.RERANK_SERVICE_URL}/prepare",
            timeout=120.0  # Model loading can take time
        )
        if response.status_code == 200:
            _current_gpu_model = "rerank"
            logger.info("✅ GPU Swap: Rerank model loaded")
        else:
            logger.warning(f"⚠️ Rerank prepare failed: {response.text}")
    except Exception as e:
        logger.error(f"❌ Rerank prepare error: {e}")


async def release_rerank():
    """
    Release rerank service (unload model if swap mode).
    Called after reranking to free VRAM for LLM.
    """
    global _current_gpu_model
    
    if not settings.GPU_SWAP_MODE:
        return
    
    try:
        logger.info("🔄 GPU Swap: Releasing rerank model...")
        await http_client.post(
            f"{settings.RERANK_SERVICE_URL}/release",
            timeout=30.0
        )
        if _current_gpu_model == "rerank":
            _current_gpu_model = None
        logger.info("✅ GPU Swap: Rerank model unloaded, VRAM freed")
    except Exception as e:
        logger.warning(f"⚠️ Rerank release error: {e}")


async def prepare_llm():
    """
    Prepare LLM service (load model if swap mode).
    Called before generating answers.
    """
    global _current_gpu_model
    
    if not settings.GPU_SWAP_MODE:
        return
    
    try:
        logger.info("🔄 GPU Swap: Preparing LLM model...")
        response = await http_client.post(
            f"{settings.LLM_SERVICE_URL}/prepare",
            timeout=180.0  # LLM loading takes longer
        )
        if response.status_code == 200:
            _current_gpu_model = "llm"
            logger.info("✅ GPU Swap: LLM model loaded")
        else:
            logger.warning(f"⚠️ LLM prepare failed: {response.text}")
    except Exception as e:
        logger.error(f"❌ LLM prepare error: {e}")


async def release_llm():
    """
    Release LLM service (unload model if swap mode).
    Called after generation to free VRAM for rerank (optional).
    
    Note: Usually we keep LLM loaded since it's the most common operation.
    Only release when explicitly needed for rerank.
    """
    global _current_gpu_model
    
    if not settings.GPU_SWAP_MODE:
        return
    
    try:
        logger.info("🔄 GPU Swap: Releasing LLM model...")
        await http_client.post(
            f"{settings.LLM_SERVICE_URL}/release",
            timeout=30.0
        )
        if _current_gpu_model == "llm":
            _current_gpu_model = None
        logger.info("✅ GPU Swap: LLM model unloaded, VRAM freed")
    except Exception as e:
        logger.warning(f"⚠️ LLM release error: {e}")


# ============= CONVERSATION STATE (Document Pinning) =============

@dataclass
class ConversationState:
    """
    Tracks the active topic/document in a conversation.
    
    This enables "Document Pinning" - when a user asks a follow-up question,
    we search within the pinned document instead of the entire corpus.
    
    Inspired by Microsoft/OpenAI Conversational RAG pattern.
    """
    session_id: str
    active_document_id: Optional[str] = None
    active_document_title: Optional[str] = None
    last_question: Optional[str] = None
    last_question_embedding: Optional[List[float]] = field(default=None, repr=False)  # For semantic topic detection
    last_confidence: float = 0.0
    conversation_turns: int = 0
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
    
    def is_valid(self) -> bool:
        """Check if state is still valid (not expired, has document)"""
        if not self.active_document_id:
            return False
        # Expire after 30 minutes of inactivity
        if datetime.now() - self.updated_at > timedelta(minutes=30):
            return False
        return True
    
    def update(self, document_id: str, document_title: str, question: str, confidence: float, embedding: Optional[List[float]] = None):
        """Update state with new active document"""
        self.active_document_id = document_id
        self.active_document_title = document_title
        self.last_question = question
        self.last_question_embedding = embedding
        self.last_confidence = confidence
        self.conversation_turns += 1
        self.updated_at = datetime.now()
    
    def clear(self):
        """Clear state when topic changes"""
        self.active_document_id = None
        self.active_document_title = None
        self.last_question = None
        self.last_question_embedding = None
        self.last_confidence = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dict for database storage"""
        return {
            "active_document_id": self.active_document_id,
            "active_document_title": self.active_document_title,
            "last_question": self.last_question,
            "last_question_embedding": self.last_question_embedding,  # Store embedding for topic detection
            "last_confidence": self.last_confidence,
            "conversation_turns": self.conversation_turns
        }
    
    @classmethod
    def from_dict(cls, session_id: str, data: dict) -> 'ConversationState':
        """Create from database dict"""
        state = cls(session_id=session_id)
        state.active_document_id = data.get("active_document_id")
        state.active_document_title = data.get("active_document_title")
        state.last_question = data.get("last_question")
        state.last_question_embedding = data.get("last_question_embedding")
        state.last_confidence = data.get("last_confidence", 0.0)
        state.conversation_turns = data.get("conversation_turns", 0)
        return state


# ============= SESSION ID GENERATION (Backend-driven) =============

def generate_session_id() -> str:
    """
    Generate a unique session ID (format: YYYYMMDD_NNNN).
    
    This is now handled by the backend to ensure consistency and proper logging.
    Counter is maintained in-memory and synced with database.
    
    Returns:
        str: Session ID like "20251128_0001"
    """
    global _session_counter
    
    # Get current date
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    
    # Check if date changed (reset counter daily)
    if _session_counter["date"] != date_str:
        _session_counter["date"] = date_str
        _session_counter["counter"] = 0
        logger.info(f"📅 New day detected: {date_str}, counter reset")
    
    # Increment counter
    _session_counter["counter"] += 1
    
    # Prevent overflow (max 9999 sessions/day)
    if _session_counter["counter"] > 9999:
        _session_counter["counter"] = 1
        logger.warning("⚠️ Session counter exceeded 9999, resetting to 1")
    
    # Format: YYYYMMDD_NNNN
    session_id = f"{date_str}_{_session_counter['counter']:04d}"
    
    logger.info(f"📌 Generated new session ID: {session_id}")
    return session_id


def get_or_create_session_id(provided_session_id: Optional[str]) -> Tuple[str, bool]:
    """
    Get existing session ID or create new one.
    
    Args:
        provided_session_id: Session ID from frontend (None = new session)
        
    Returns:
        Tuple of (session_id, is_new_session)
        
    Note:
        Backend is the source of truth. If session not found/expired,
        create a NEW session. Frontend must sync from response.
    """
    # If no session ID provided, create new one
    if not provided_session_id:
        return generate_session_id(), True
    
    # Check if session exists and is valid
    if db_client:
        session_data = db_client.get_session(provided_session_id)
        if session_data:
            logger.debug(f"📂 Found existing session: {provided_session_id}")
            return provided_session_id, False
    
    # Session not found or expired - create NEW session
    # Frontend will sync to new session_id from response
    logger.info(f"📌 Session {provided_session_id} not found/expired, creating new")
    return generate_session_id(), True


def get_conversation_state(session_id: str) -> ConversationState:
    """
    Get conversation state from database, or create new one.
    Uses PostgreSQL for persistence across server restarts.
    """
    if not db_client:
        # Fallback to empty state if no DB
        return ConversationState(session_id=session_id)
    
    # Try to load from database
    session_data = db_client.get_session(session_id)
    
    if session_data and session_data.get('context'):
        context = session_data['context']
        if isinstance(context, str):
            import json
            context = json.loads(context)
        state = ConversationState.from_dict(session_id, context)
        state.conversation_turns = session_data.get('conversation_turns', 0)
        logger.debug(f"📂 Loaded session from DB: {session_id}")
        return state
    
    # Create new state
    return ConversationState(session_id=session_id)


def save_conversation_state(state: ConversationState) -> bool:
    """Save conversation state to database"""
    if not db_client:
        return False
    
    return db_client.save_session(
        session_id=state.session_id,
        context=state.to_dict(),
        conversation_turns=state.conversation_turns
    )


# ============= EMBEDDING CACHE & SIMILARITY =============

_embedding_cache: Dict[str, Tuple[float, List[float]]] = {}
_cache_ttl = 300  # 5 minutes


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two embedding vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    dot_product = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


async def embed_text_cached(text: str) -> Optional[List[float]]:
    """Embed text with caching to reduce API calls."""
    cache_key = hash(text)
    current_time = time.time()
    
    # Check cache
    if cache_key in _embedding_cache:
        cached_time, embedding = _embedding_cache[cache_key]
        if current_time - cached_time < _cache_ttl:
            return embedding
    
    # Call embedding service
    embedding = await embed_text(text)
    
    if embedding:
        _embedding_cache[cache_key] = (current_time, embedding)
        # Clean old cache entries (keep max 100)
        if len(_embedding_cache) > 100:
            oldest_keys = sorted(_embedding_cache.keys(), 
                                key=lambda k: _embedding_cache[k][0])[:50]
            for k in oldest_keys:
                del _embedding_cache[k]
    
    return embedding


def is_followup_question(question: str) -> bool:
    """
    Detect if a question is likely a follow-up that needs context.
    
    Uses lightweight linguistic patterns. Semantic topic detection is handled
    separately via embeddings to keep this function focused on phrasing hints.
    
    Args:
        question: The user's question
    """
    q_lower = question.lower().strip()
    
    # Pattern 1: Very short questions (< 30 chars) are usually follow-ups
    # But only if topic matches (checked above)
    if len(q_lower) < 30:
        logger.info(f"🔍 Short question ({len(q_lower)} chars): likely follow-up")
        return True
    
    # Pattern 2: Starts with question words about attributes (not new topic)
    followup_starters = [
        r"^(lệ phí|phí|chi phí|giá|bao nhiêu)",      # Cost
        r"^(thời gian|bao lâu|mấy ngày|khi nào)",    # Time
        r"^(ở đâu|tại đâu|địa chỉ|địa điểm)",        # Location
        r"^(cần gì|cần những gì|hồ sơ gồm|giấy tờ)", # Documents needed
        r"^(ai|cơ quan nào|nơi nào)",                # Who/Where
        r"^(còn gì|thêm gì|gì nữa|gì khác)",         # More info
        r"^(thế thì|vậy thì|như vậy)",               # Continuation
    ]
    
    for pattern in followup_starters:
        if re.search(pattern, q_lower):
            logger.info(f"🔍 Follow-up pattern matched: {pattern}")
            return True
    
    # Pattern 3: Contains referential words (referring to previous topic)
    referential_patterns = [
        r"(của nó|về nó|cho nó)",
        r"(thủ tục này|việc này|vấn đề này)",
        r"(như trên|ở trên|vừa nói)",
    ]
    
    for pattern in referential_patterns:
        if re.search(pattern, q_lower):
            logger.info(f"🔍 Referential pattern matched: {pattern}")
            return True
    
    return False


def should_use_pinned_document(question: str, state: ConversationState) -> bool:
    """
    Decide whether to search within pinned document or full corpus.
    
    Strategy (Priority order):
    1. If no valid pinned document → Full corpus search
    2. If explicit topic change phrases detected → Clear and full search
    3. If short follow-up question detected → Use pinned
    4. If referential patterns detected → Use pinned
    5. Long questions (>50 chars) → Full corpus (might be new topic)
    6. Default medium questions → Use pinned for continuity
    
    Note: Semantic similarity checks run before this function; this helper only
    looks at linguistic hints now that topic changes are governed by embeddings.
    """
    if not state.is_valid():
        logger.info("📌 No valid pinned document → Full corpus search")
        return False
    
    q_lower = question.lower()
    
    # Check if question explicitly mentions a NEW topic (User wants to change subject)
    new_topic_indicators = [
        r"(muốn hỏi về|hỏi về|cho tôi biết về)",  # "I want to ask about..."
        r"(chuyển sang|đổi qua|hỏi cái khác)",   # "Switch to..."
        r"(thủ tục khác|văn bản khác)",          # "Different procedure"
        r"(không phải|không liên quan)",         # "Not related"
    ]
    
    for pattern in new_topic_indicators:
        if re.search(pattern, q_lower):
            logger.info(f"📌 New topic detected: {pattern} → Full corpus search")
            state.clear()  # Clear pinned document
            return False
    
    # If it's a follow-up question, use pinned document
    # Pass pinned title to check for topic mismatch
    if is_followup_question(question):
        logger.info(f"📌 Follow-up detected → Using pinned document: {state.active_document_title}")
        return True
    
    # For longer questions, check if they might be about a new topic
    if len(q_lower) > 50:
        # Long question - could be new topic, do full search to be safe
        logger.info("📌 Long question → Full corpus search (might be new topic)")
        return False
    
    # Default for medium-length questions: use pinned for continuity
    logger.info(f"📌 Default → Using pinned document: {state.active_document_title}")
    return True




# REMOVED: check_semantic_topic_change() function
# Semantic similarity doesn't work well for legal documents
# User must explicitly clear session (F5/Clear button) to start new topic


# ============= MODELS =============

class HistoryMessage(BaseModel):
    """A single message in chat history"""
    role: str  # 'user' or 'assistant'
    content: str


class SessionInfo(BaseModel):
    """Session information returned in responses"""
    session_id: str
    is_new_session: bool = False
    pinned_document_id: Optional[str] = None
    pinned_document_title: Optional[str] = None
    conversation_turns: int = 0


class QueryRequest(BaseModel):
    """Query request with optional chat history and session tracking"""
    question: str
    session_id: Optional[str] = None  # None = request new session (F5/new tab)
    top_k: int = settings.TOP_K
    threshold: float = settings.SIMILARITY_THRESHOLD
    history: Optional[List[HistoryMessage]] = None  # Last 3 turns for context


class SearchResult(BaseModel):
    """Search result with document info"""
    content: str
    similarity: float
    chunk_id: Optional[str] = None  # Chunk UUID for evaluation metrics
    document_id: Optional[str] = None  # Document UUID for download
    document_title: Optional[str] = None  # Tên văn bản pháp luật
    file_path: Optional[str] = None  # Path in MinIO for download


class FormInfo(BaseModel):
    """Form information for download"""
    id: str
    form_name: str
    template_path: Optional[str] = None
    description: Optional[str] = None


class DocumentOption(BaseModel):
    """Document option for clarification"""
    document_id: str
    title: str
    chunk_count: int
    confidence: float
    preview: str


class ConfirmRequest(BaseModel):
    """User confirms document selection"""
    question: str
    document_id: str
    session_id: Optional[str] = None  # For conversation state tracking
    history: Optional[List[HistoryMessage]] = None  # Chat history for follow-up context


class ClearSessionRequest(BaseModel):
    """Request to clear/reset session (unpin document)"""
    session_id: str


class SessionStartResponse(BaseModel):
    """Response for new session creation"""
    success: bool
    session_info: SessionInfo
    message: str


class SessionClearResponse(BaseModel):
    """Response for session clear"""
    success: bool
    session_id: str
    message: str


class SessionInfoResponse(BaseModel):
    """Response for session info query"""
    success: bool
    session_info: Optional[SessionInfo] = None
    message: str


class QueryResponse(BaseModel):
    """Query response with optional clarification"""
    success: bool
    question: str
    answer: Optional[str] = None
    
    # Session info (always included)
    session_id: str
    session_info: Optional[SessionInfo] = None
    
    # Clarification fields
    needs_clarification: bool = False
    clarification_message: Optional[str] = None
    document_options: Optional[List[DocumentOption]] = None
    
    # Conversation state info (for debugging/transparency)
    used_pinned_document: bool = False
    pinned_document_title: Optional[str] = None
    
    # Sources and forms (for UI display)
    sources: List[SearchResult]
    forms: Optional[List[FormInfo]] = None  # Forms attached to source documents
    tokens_used: int
    
    # Performance metrics
    took_ms: Optional[int] = None  # Total processing time in milliseconds
    timing: Optional[dict] = None  # Step-by-step timing: embed_ms, search_ms, rerank_ms, llm_ms


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    embedding_service: str
    vector_service: str
    llm_service: str


# ============= APP =============

app = FastAPI(
    title="Query Service",
    description="RAG orchestrator for legal document Q&A",
    version="1.0.0"
)

# Include routers
app.include_router(forms_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    global http_client, db_client, _session_counter
    http_client = httpx.AsyncClient(timeout=30.0)
    
    # Initialize PostgreSQL client
    db_client = DatabaseClient(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB
    )
    
    # Sync session counter with database (find highest session number for today)
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    _session_counter["date"] = date_str
    
    # Query database for highest session number today
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            dbname=settings.POSTGRES_DB
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT session_id FROM query_logs WHERE session_id LIKE %s ORDER BY session_id DESC LIMIT 1",
            (f"{date_str}_%",)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            last_session_id = result[0]
            # Extract counter from session_id like "20251128_0003"
            try:
                counter = int(last_session_id.split("_")[1])
                _session_counter["counter"] = counter
                logger.info(f"📊 Synced session counter from DB: {date_str}_{counter:04d}")
            except (IndexError, ValueError):
                _session_counter["counter"] = 0
                logger.warning(f"⚠️ Could not parse session ID from DB: {last_session_id}")
        else:
            _session_counter["counter"] = 0
            logger.info(f"📊 No sessions found for today, starting from {date_str}_0001")
    except Exception as e:
        logger.warning(f"⚠️ Could not sync session counter from DB: {e}")
        _session_counter["counter"] = 0
    
    logger.info("✅ Query Service started (with DB client)")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global http_client
    if http_client:
        await http_client.aclose()
    logger.info("✅ Query Service stopped")


# ============= SESSION API ENDPOINTS =============

@app.post("/session/start", response_model=SessionStartResponse)
async def start_session():
    """
    Start a new session (called on F5/refresh/new tab).
    
    This is the primary way frontend should get a session ID.
    Creates a fresh session with no pinned document.
    """
    try:
        # Generate new session ID
        session_id = generate_session_id()
        
        # Create empty state
        state = ConversationState(session_id=session_id)
        
        # Save to database
        save_conversation_state(state)
        
        # Build response
        session_info = SessionInfo(
            session_id=session_id,
            is_new_session=True,
            pinned_document_id=None,
            pinned_document_title=None,
            conversation_turns=0
        )
        
        return SessionStartResponse(
            success=True,
            session_info=session_info,
            message=f"New session created: {session_id}"
        )
        
    except Exception as e:
        logger.error(f"❌ Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session/clear", response_model=SessionClearResponse)
async def clear_session(request: ClearSessionRequest):
    """
    Clear session state (unpin document).
    
    Keeps the session ID but clears:
    - Pinned document
    - Last question embedding
    - Conversation context
    
    Use this when user explicitly wants to "start fresh" or unpin document.
    """
    try:
        session_id = request.session_id
        
        # Load existing state
        state = get_conversation_state(session_id)
        
        if state:
            # Clear the state but keep session
            old_title = state.active_document_title
            state.clear()
            save_conversation_state(state)
            
            logger.info(f"📌 Session {session_id} cleared (was pinned to: {old_title})")
            message = f"Session cleared. Previously pinned: {old_title}" if old_title else "Session cleared"
        else:
            # Create new empty state
            state = ConversationState(session_id=session_id)
            save_conversation_state(state)
            message = "Session created (was not found)"
        
        return SessionClearResponse(
            success=True,
            session_id=session_id,
            message=message
        )
        
    except Exception as e:
        logger.error(f"❌ Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/info/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(session_id: str):
    """
    Get current session information.
    
    Returns:
    - Session ID
    - Pinned document (if any)
    - Conversation turns count
    """
    try:
        state = get_conversation_state(session_id)
        
        if state:
            session_info = SessionInfo(
                session_id=session_id,
                is_new_session=False,
                pinned_document_id=state.active_document_id,
                pinned_document_title=state.active_document_title,
                conversation_turns=state.conversation_turns
            )
            return SessionInfoResponse(
                success=True,
                session_info=session_info,
                message="Session found"
            )
        else:
            return SessionInfoResponse(
                success=False,
                session_info=None,
                message="Session not found"
            )
            
    except Exception as e:
        logger.error(f"❌ Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= HELPER FUNCTIONS =============

async def embed_text(text: str) -> Optional[List[float]]:
    """Embed text using embedding service"""
    try:
        response = await http_client.post(
            f"{settings.EMBEDDING_SERVICE_URL}/embed",
            json={"text": text}
        )
        if response.status_code == 200:
            data = response.json()
            return data["embedding"]
        else:
            logger.error(f"❌ Embedding failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Embedding error: {e}")
        return None


async def search_vectors(embedding: List[float]) -> List[dict]:
    """Search similar vectors"""
    try:
        response = await http_client.post(
            f"{settings.VECTOR_SERVICE_URL}/search",
            json={
                "embedding": embedding,
                "top_k": settings.TOP_K,
                "threshold": settings.SIMILARITY_THRESHOLD
            }
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
        else:
            logger.error(f"❌ Vector search failed: {response.text}")
            return []
    except Exception as e:
        logger.error(f"❌ Vector search error: {e}")
        return []


async def rerank_documents(query: str, documents: List[dict], top_k: int = 10) -> Tuple[List[dict], Optional[List[dict]]]:
    """
    Rerank documents using rerank service with title-aware scoring.
    
    GPU Swap Mode: Prepares rerank model before use, releases after.
    
    Returns:
    - Tuple of (reranked_docs, document_scores)
    - document_scores: List of {document_id, avg_score, max_score, chunk_count}
      Used to decide if clarification is needed (when scores are close)
    """
    try:
        # GPU Swap: Prepare rerank model
        await prepare_rerank()
        
        # Prepare documents for reranking
        doc_texts = [doc.get('content', '') for doc in documents]
        doc_ids = [doc.get('document_id', 'unknown') for doc in documents]
        unique_doc_ids = list(set(doc_ids))
        
        # Fetch document titles for title-aware reranking
        titles_map = {}
        if db_client:
            titles_map = db_client.fetch_document_titles(unique_doc_ids)
        
        # Map titles to each chunk (in same order as doc_ids)
        doc_titles = [titles_map.get(doc_id, '') for doc_id in doc_ids]
        
        logger.info(f"Sending {len(documents)} chunks from {len(unique_doc_ids)} unique documents to rerank (title-aware)")
        
        response = await http_client.post(
            f"{settings.RERANK_SERVICE_URL}/rerank",
            json={
                "query": query,
                "documents": doc_texts,
                "document_ids": doc_ids,
                "document_titles": doc_titles,
                "top_k": top_k,
                "include_document_scores": True  # NEW: Get aggregated doc scores
            },
            timeout=90.0  # Increased: rerank on CPU can take 30-40s
        )
        
        # GPU Swap: Release rerank model to free VRAM for LLM
        await release_rerank()
        
        if response.status_code == 200:
            data = response.json()
            reranked = data.get("results", [])
            document_scores = data.get("document_scores", None)  # NEW: Get doc scores
            
            # Map reranked results back to original documents with scores
            reranked_docs = []
            for item in reranked:
                idx = item.get('index', 0)
                if idx < len(documents):
                    doc = documents[idx].copy()
                    doc['rerank_score'] = item.get('score', 0.0)
                    doc['document_title'] = titles_map.get(doc.get('document_id', ''), 'Văn bản')
                    reranked_docs.append(doc)
            
            logger.info(f"✅ Reranked {len(reranked_docs)} chunks, {len(document_scores) if document_scores else 0} document scores")
            return reranked_docs, document_scores
        else:
            logger.warning(f"⚠️ Rerank failed: {response.text}, using original order")
            return documents[:top_k], None
    except Exception as e:
        logger.warning(f"⚠️ Rerank error: {e}, using original order")
        return documents[:top_k], None


async def generate_answer(
    question: str, 
    context: str, 
    history: Optional[List[dict]] = None
) -> Tuple[Optional[str], int]:
    """
    Generate answer using LLM Service's /generate-rag endpoint.
    
    GPU Swap Mode: Prepares LLM model before use.
    
    This function sends question + context + history to LLM service,
    which automatically wraps with system_prompt.txt + citation_rules.txt.
    
    Args:
        question: Current user question
        context: RAG context from vector search
        history: Optional chat history (last 3 turns) for follow-up questions
    """
    try:
        # GPU Swap: Prepare LLM model
        await prepare_llm()
        
        payload = {
            "question": question,
            "context": context,
            # Don't specify max_tokens, temperature, top_p - let LLM service use its env config
            # LLM service will use: MAX_TOKENS=2048, TEMPERATURE=0.7, TOP_P=0.9
        }
        
        # Add history if provided (for follow-up context)
        if history:
            payload["history"] = history
            logger.info(f"📜 Sending {len(history)} history messages to LLM")
        
        response = await http_client.post(
            f"{settings.LLM_SERVICE_URL}/generate-rag",
            json=payload,
            timeout=120.0  # LLM can be slow
        )
        
        # Note: We keep LLM loaded after generation (most common operation)
        # Only release if we need VRAM for something else
        
        if response.status_code == 200:
            data = response.json()
            tokens_used = data.get('total_tokens', 0)
            logger.info(f"✅ LLM generated {data.get('completion_tokens', 0)} tokens (total: {tokens_used})")
            return data.get("text", ""), tokens_used
        else:
            logger.error(f"❌ LLM generation failed: {response.status_code} - {response.text}")
            return None, 0
    except Exception as e:
        logger.error(f"❌ LLM generation error: {type(e).__name__}: {str(e)}")
        return None, 0


def group_chunks_by_document(chunks: List[dict]) -> Dict[str, List[dict]]:
    """
    Group chunks by document_id
    
    Args:
        chunks: List of chunks with document_id field
        
    Returns:
        Dict mapping document_id → list of chunks
    """
    groups = defaultdict(list)
    for chunk in chunks:
        doc_id = chunk.get('document_id')
        if doc_id:
            groups[doc_id].append(chunk)
    
    return dict(groups)


def apply_ranking_heuristics(query: str, document_scores: List[dict], titles_map: Dict[str, str]) -> List[dict]:
    """
    Re-sort document scores based on heuristics when scores are close.
    
    Heuristics:
    1. Specificity Penalty: Titles with specific words (nước ngoài, lưu động) 
       that are NOT in the query get penalized.
    2. Title Length: Shorter titles are usually more general (tie-breaker).
    
    Args:
        query: User query
        document_scores: List of {document_id, avg_score, ...}
        titles_map: Map of document_id -> title
        
    Returns:
        Re-sorted document_scores
    """
    if not document_scores:
        return []
        
    query_lower = query.lower()
    
    # Calculate heuristic score for each document
    scored_docs = []
    for doc in document_scores:
        doc_id = doc.get('document_id')
        title = titles_map.get(doc_id, "").lower()
        original_score = doc.get('avg_score', 0)
        
        penalty = 0.0
        
        # Heuristic 1: Specificity Penalty (STRICT for legal domain)
        # If title has specific keywords NOT in query -> Heavy penalty
        # Legal documents require precision - wrong document = wrong legal advice
        for keyword in settings.SPECIFIC_KEYWORDS:
            if keyword in title and keyword not in query_lower:
                penalty += settings.SPECIFIC_KEYWORD_PENALTY
                logger.info(f"📉 Penalty applied to '{title[:40]}...': contains '{keyword}' not in query (-{settings.SPECIFIC_KEYWORD_PENALTY})")
        
        # Heuristic 2: Title Length Bias (minor tie-breaker)
        # Prefer shorter titles (usually more general)
        # Normalize length factor: 0.001 per 10 chars
        length_penalty = len(title) * 0.0001
        
        final_score = original_score - penalty - length_penalty
        
        # Store modified score
        doc_copy = doc.copy()
        doc_copy['heuristic_score'] = final_score
        doc_copy['original_score'] = original_score
        scored_docs.append(doc_copy)
    
    # Sort by heuristic_score descending
    scored_docs.sort(key=lambda x: x['heuristic_score'], reverse=True)
    
    # Log reordering
    if scored_docs[0]['document_id'] != document_scores[0]['document_id']:
        old_top = titles_map.get(document_scores[0]['document_id'], "")
        new_top = titles_map.get(scored_docs[0]['document_id'], "")
        logger.info(f"🔄 Reordered top document: '{old_top}' -> '{new_top}'")
        
    return scored_docs


# ============= ENDPOINTS =============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check all service health"""
    
    async def check_service(url: str) -> str:
        try:
            response = await http_client.get(f"{url}/health", timeout=5.0)
            return "ok" if response.status_code == 200 else "down"
        except:
            return "down"
    
    return HealthResponse(
        status="healthy",
        embedding_service=await check_service(settings.EMBEDDING_SERVICE_URL),
        vector_service=await check_service(settings.VECTOR_SERVICE_URL),
        llm_service=await check_service(settings.LLM_SERVICE_URL)
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process query with Conversation State + Document Pinning.
    
    Flow:
    1. Get or create session (backend-driven)
    2. Check if session has pinned document
    3. If follow-up question + pinned doc → Search within pinned doc only
    4. If new topic or no pinned doc → Full corpus search
    5. After confident answer → Pin the top document for future follow-ups
    6. Return session_id and session_info in response
    """
    start_time = time.time()  # Track processing time
    timing = {"embed_ms": 0, "search_ms": 0, "rerank_ms": 0, "llm_ms": 0}  # Step-by-step timing
    try:
        logger.info(f"🔍 Query: {request.question}")
        
        # Get or create session (backend-driven)
        session_id, is_new_session = get_or_create_session_id(request.session_id)
        state = get_conversation_state(session_id)
        
        # IMPORTANT: If new session, save immediately so subsequent requests can find it
        if is_new_session:
            save_conversation_state(state)
            logger.info(f"📌 New session saved to DB: {session_id}")
        
        # Helper to build session_info for responses
        def build_session_info() -> SessionInfo:
            return SessionInfo(
                session_id=session_id,
                is_new_session=is_new_session,
                pinned_document_id=state.active_document_id,
                pinned_document_title=state.active_document_title,
                conversation_turns=state.conversation_turns
            )
        
        # Track if we're using pinned document
        use_pinned = False
        pinned_doc_id = None
        pinned_doc_title = None
        
        # Detect small talk / greetings
        question_lower = request.question.lower().strip()
        small_talk_patterns = [
            "xin chào", "chào bạn", "chào anh", "chào chị",
            "hello", "hi ", "hey ",
            "bạn là ai", "bạn tên gì", "ai tạo ra bạn",
            "cảm ơn", "thank", "bye", "tạm biệt"
        ]
        
        # Only match if pattern is at start/end or standalone
        is_small_talk = False
        for pattern in small_talk_patterns:
            if question_lower == pattern or \
               question_lower.startswith(pattern + " ") or \
               question_lower.endswith(" " + pattern) or \
               question_lower.startswith(pattern + "!") or \
               question_lower.endswith("!" + pattern):
                is_small_talk = True
                break
        
        if is_small_talk:
            return QueryResponse(
                success=True,
                question=request.question,
                answer="Xin chào! Tôi là trợ lý AI tra cứu văn bản pháp luật của Trung tâm. Tôi có thể giúp bạn tìm hiểu về các thủ tục hành chính như đăng ký khai sinh, kết hôn, cấp CCCD và các vấn đề pháp lý khác. Bạn có thể hỏi tôi bất kỳ câu hỏi nào về thủ tục hành chính nhé!",
                session_id=session_id,
                session_info=build_session_info(),
                sources=[],
                tokens_used=0,
                used_pinned_document=False,
                took_ms=int((time.time() - start_time) * 1000)
            )
        
        # REMOVED: Semantic topic change detection
        # In legal domain, questions about fees/procedures are still SAME TOPIC
        # User must explicitly clear session (F5 reload or Clear button) to start new topic
        # Example: "khai sinh" → "phí bao nhiêu?" should KEEP using pinned doc
        
        # Step 0: Check if we should use pinned document (Document Pinning)
        use_pinned = should_use_pinned_document(request.question, state)
        
        if use_pinned and state.active_document_id:
            pinned_doc_id = state.active_document_id
            pinned_doc_title = state.active_document_title
            logger.info(f"📌 Using pinned document: {pinned_doc_title} ({pinned_doc_id[:8]}...)")
        
        # Step 1: Embed question (with context expansion for follow-ups)
        logger.info("Step 1: Embedding question...")
        embed_start = time.time()
        
        # QUERY EXPANSION: For short follow-up questions, add context from pinned document
        # This helps semantic search find relevant chunks
        # Example: "phí bao nhiêu?" → "đăng ký khai sinh phí lệ phí bao nhiêu?"
        query_for_embedding = request.question
        
        if use_pinned and pinned_doc_title and len(request.question) < 50:
            # Extract key topic from document title (remove numbering like "01. ")
            topic = pinned_doc_title
            if ". " in topic:
                topic = topic.split(". ", 1)[1]
            
            # Expand query with topic context
            query_for_embedding = f"{topic} {request.question}"
            logger.info(f"📌 Expanded query for embedding: '{query_for_embedding}'")
        
        embedding = await embed_text(query_for_embedding)
        timing["embed_ms"] = int((time.time() - embed_start) * 1000)
        if embedding is None:
            raise HTTPException(status_code=503, detail="Embedding service unavailable")
        
        # Step 2: Search - either pinned document or full corpus
        logger.info("Step 2: Searching similar documents...")
        search_start = time.time()
        if use_pinned and pinned_doc_id:
            # PINNED DOCUMENT SEARCH - search within specific document only
            # For pinned doc, get ALL chunks (no top_k limit) since user chose this doc
            logger.info(f"📌 Searching within pinned document: {pinned_doc_id[:8]}...")
            response = await http_client.post(
                f"{settings.VECTOR_SERVICE_URL}/search",
                json={
                    "embedding": embedding,
                    "top_k": 100,  # High limit to get all chunks from single doc
                    "threshold": 0.1,  # Very low threshold - we want all chunks from pinned doc
                    "document_ids": [pinned_doc_id]
                }
            )
            if response.status_code == 200:
                search_results = response.json().get("results", [])
                
                # Check if semantic search found useful results
                best_semantic_score = max((r.get('similarity', 0) for r in search_results), default=0)
                
                if best_semantic_score < 0.3:
                    # KEYWORD FALLBACK: Semantic search weak, try keyword search
                    logger.info(f"📌 Semantic search low ({best_semantic_score:.3f}), trying keyword fallback...")
                    
                    if db_client:
                        keyword_results = db_client.keyword_search_in_document(
                            document_id=pinned_doc_id,
                            question=request.question,
                            limit=5
                        )
                        
                        if keyword_results:
                            logger.info(f"✅ Keyword fallback found {len(keyword_results)} chunks")
                            # Merge: keyword results first (more likely relevant), then semantic
                            # Remove duplicates by chunk id
                            seen_ids = {r.get('id') for r in keyword_results}
                            unique_semantic = [r for r in search_results if r.get('id') not in seen_ids]
                            search_results = keyword_results + unique_semantic[:5]
                        else:
                            logger.info("📌 Keyword fallback found nothing, using semantic results")
                    # Keep using pinned doc, don't fall back to corpus
                else:
                    logger.info(f"📌 Semantic search good ({best_semantic_score:.3f})")
                    
                if not search_results:
                    # Still no results after keyword fallback
                    logger.info("📌 No results in pinned document after keyword fallback")
                    return QueryResponse(
                        success=True,
                        question=request.question,
                        answer=f"Xin lỗi, tôi không tìm thấy thông tin về \"{request.question}\" trong văn bản \"{pinned_doc_title}\". Bạn có thể hỏi câu hỏi khác về văn bản này.",
                        session_id=session_id,
                        session_info=build_session_info(),
                        sources=[],
                        tokens_used=0,
                        used_pinned_document=True,
                        pinned_document_title=pinned_doc_title,
                        took_ms=int((time.time() - start_time) * 1000)
                    )
            else:
                logger.warning(f"⚠️ Pinned search failed, falling back to full corpus")
                search_results = await search_vectors(embedding)
                use_pinned = False
        else:
            # FULL CORPUS SEARCH
            search_results = await search_vectors(embedding)
        if not search_results:
            return QueryResponse(
                success=True,
                question=request.question,
                answer="Xin lỗi, tôi không tìm thấy thông tin liên quan trong cơ sở dữ liệu văn bản pháp luật. Vui lòng thử lại với câu hỏi khác hoặc liên hệ bộ phận hỗ trợ để được tư vấn chi tiết.",
                session_id=session_id,
                session_info=build_session_info(),
                sources=[],
                tokens_used=0,
                took_ms=int((time.time() - start_time) * 1000)
            )
        timing["search_ms"] = int((time.time() - search_start) * 1000)
        
        # Step 3: Rerank documents for better relevance
        # For pinned doc: rerank ALL chunks to find best matches
        # For corpus search: use standard top_k to limit processing
        rerank_top_k = len(search_results) if use_pinned else settings.RERANK_TOP_K
        logger.info(f"Step 3: Reranking {len(search_results)} documents (top_k={rerank_top_k})...")
        rerank_start = time.time()
        reranked_results, document_scores = await rerank_documents(
            request.question, search_results, top_k=rerank_top_k
        )
        timing["rerank_ms"] = int((time.time() - rerank_start) * 1000)
        
        # Step 3.5: Smart clarification check using document scores
        max_score = max(r.get('rerank_score', 0) for r in reranked_results) if reranked_results else 0
        logger.info(f"📊 Max chunk confidence: {max_score:.3f}")
        
        # Check if we have keyword matches (from hybrid search)
        has_keyword_match = any(r.get('match_type') == 'keyword' for r in reranked_results)
        
        # KEYWORD FALLBACK after rerank: If rerank score very low but using pinned doc
        # This catches cases where semantic search was OK but reranker failed (e.g., text without accents)
        if use_pinned and max_score < 0.15 and not has_keyword_match and db_client:
            logger.info(f"📌 Rerank score very low ({max_score:.3f}), trying keyword fallback...")
            keyword_results = db_client.keyword_search_in_document(
                document_id=pinned_doc_id,
                question=request.question,
                limit=5
            )
            
            if keyword_results:
                logger.info(f"✅ Keyword fallback found {len(keyword_results)} chunks after rerank")
                # Re-rerank with keyword results included
                merged = keyword_results + search_results[:5]
                reranked_results, document_scores = await rerank_documents(
                    request.question, merged, top_k=settings.RERANK_TOP_K
                )
                max_score = max(r.get('rerank_score', 0) for r in reranked_results) if reranked_results else 0
                has_keyword_match = any(r.get('match_type') == 'keyword' for r in reranked_results)
                logger.info(f"📊 After keyword merge - Max score: {max_score:.3f}, Has keyword: {has_keyword_match}")
        
        if has_keyword_match:
            logger.info("✅ Has keyword matches - boosting confidence")
        
        # NEW: Apply heuristics if we have document scores
        if document_scores:
            # Fetch titles early for heuristics
            doc_ids = [ds.get('document_id') for ds in document_scores]
            titles_map = db_client.fetch_document_titles(doc_ids)
            
            # Apply heuristics to reorder
            document_scores = apply_ranking_heuristics(request.question, document_scores, titles_map)
        else:
            titles_map = {}

        needs_clarification = False
        clarification_reason = ""
        
        # Check 1: Low confidence (using original max score from chunks)
        # SKIP if using pinned doc with keyword matches (hybrid search worked)
        effective_threshold = settings.CLARIFICATION_THRESHOLD
        if use_pinned:
            effective_threshold = 0.15  # Very low for pinned doc with keyword fallback
            logger.info(f"📌 Using lower threshold for pinned document: {effective_threshold}")
        
        # If we have keyword matches, trust them even with low rerank score
        if max_score < effective_threshold and not has_keyword_match:
            if use_pinned and pinned_doc_title:
                # User is asking follow-up but info not in pinned document
                logger.info(f"📌 Very low confidence in pinned doc → Returning 'not found' message")
                return QueryResponse(
                    success=True,
                    question=request.question,
                    answer=f"Xin lỗi, tôi không tìm thấy thông tin về \"{request.question}\" trong văn bản \"{pinned_doc_title}\". Bạn có thể hỏi câu hỏi khác hoặc thử tìm kiếm mới.",
                    session_id=session_id,
                    session_info=build_session_info(),
                    sources=[],
                    tokens_used=0,
                    used_pinned_document=True,
                    pinned_document_title=pinned_doc_title,
                    took_ms=int((time.time() - start_time) * 1000)
                )
            else:
                needs_clarification = True
                clarification_reason = "low_confidence"
                logger.info(f"❓ Low confidence ({max_score:.3f} < {effective_threshold}) → Clarification needed")
        
        # Check 2: Score gap between top documents (ambiguous query)
        # SKIP gap check for pinned document (user already chose the doc)
        elif document_scores and len(document_scores) >= 2 and not use_pinned:
            top1_score = document_scores[0].get('heuristic_score', document_scores[0].get('avg_score'))
            top2_score = document_scores[1].get('heuristic_score', document_scores[1].get('avg_score'))
            score_gap = top1_score - top2_score
            
            logger.info(f"📊 Document scores (heuristic): Top1={top1_score:.3f}, Top2={top2_score:.3f}, Gap={score_gap:.3f}")
            
            if score_gap < settings.SCORE_GAP_THRESHOLD:
                needs_clarification = True
                clarification_reason = "ambiguous_query"
                logger.info(f"❓ Ambiguous query (gap={score_gap:.3f} < {settings.SCORE_GAP_THRESHOLD}) → Clarification needed")
        
        if needs_clarification:
            # Build clarification options from document_scores
            if document_scores:
                # Titles are already fetched in titles_map
                
                options = []
                for ds in document_scores[:3]:  # Top 3 documents
                    doc_id = ds.get('document_id')
                    
                    # Find preview from reranked_results
                    preview = ""
                    for r in reranked_results:
                        if r.get('document_id') == doc_id:
                            preview = r.get('content', '')[:150] + "..."
                            break
                    
                    options.append(DocumentOption(
                        document_id=doc_id,
                        title=titles_map.get(doc_id, "Văn bản"),
                        chunk_count=ds.get('chunk_count', 1),
                        confidence=ds.get('avg_score', 0),
                        preview=preview
                    ))
                
                # Log clarification query
                if db_client:
                    db_client.log_query(
                        session_id=session_id,
                        query_text=request.question,
                        query_type="clarification",
                        answer_text=None,
                        sources_used=[{"document_id": o.document_id, "title": o.title} for o in options],
                        confidence_score=max_score,
                        metadata={"clarification_reason": "ambiguous_top_n", "num_options": len(options)}
                    )
                
                return QueryResponse(
                    success=True,
                    question=request.question,
                    answer=None,
                    session_id=session_id,
                    session_info=build_session_info(),
                    needs_clarification=True,
                    clarification_message="Tôi tìm thấy nhiều văn bản có thể liên quan. Bạn muốn xem văn bản nào?",
                    document_options=options,
                    used_pinned_document=use_pinned,
                    pinned_document_title=pinned_doc_title if use_pinned else None,
                    sources=[],
                    tokens_used=0,
                    took_ms=int((time.time() - start_time) * 1000)
                )
            else:
                # Fallback: group by document from reranked_results
                doc_groups = group_chunks_by_document(reranked_results)
                doc_ids = list(doc_groups.keys())
                titles = db_client.fetch_document_titles(doc_ids)
                
                options = []
                for doc_id, chunks in doc_groups.items():
                    max_chunk_score = max(c.get('rerank_score', 0) for c in chunks)
                    options.append(DocumentOption(
                        document_id=doc_id,
                        title=titles.get(doc_id, "Văn bản"),
                        chunk_count=len(chunks),
                        confidence=max_chunk_score,
                        preview=chunks[0].get('content', '')[:150] + "..."
                    ))
                
                options.sort(key=lambda x: x.confidence, reverse=True)
                
                # Log clarification query  
                if db_client:
                    db_client.log_query(
                        session_id=session_id,
                        query_text=request.question,
                        query_type="clarification",
                        answer_text=None,
                        sources_used=[{"document_id": o.document_id, "title": o.title} for o in options[:3]],
                        confidence_score=max_score,
                        metadata={"clarification_reason": "fallback_grouping", "num_options": len(options[:3])}
                    )
                
                return QueryResponse(
                    success=True,
                    question=request.question,
                    answer=None,
                    session_id=session_id,
                    session_info=build_session_info(),
                    needs_clarification=True,
                    clarification_message="Tôi tìm thấy các văn bản có thể liên quan. Bạn muốn xem văn bản nào?",
                    document_options=options[:3],
                    used_pinned_document=use_pinned,
                    pinned_document_title=pinned_doc_title if use_pinned else None,
                    sources=[],
                    tokens_used=0,
                    took_ms=int((time.time() - start_time) * 1000)
                )
        
        # HIGH CONFIDENCE & CLEAR WINNER → Answer directly
        logger.info("✅ High confidence with clear winner → Answering directly")
        
        # Filter to only chunks from top document for coherent answer
        final_doc_id = None
        final_doc_title = None
        
        if use_pinned and pinned_doc_id:
            # Already searching within pinned document
            final_doc_id = pinned_doc_id
            final_doc_title = pinned_doc_title or "Văn bản"
            # Add title to results
            for r in reranked_results:
                r['document_title'] = final_doc_title
        elif document_scores and len(document_scores) > 0:
            top_doc_id = document_scores[0].get('document_id')
            final_doc_id = top_doc_id
            reranked_results = [r for r in reranked_results if r.get('document_id') == top_doc_id]
            final_doc_title = titles_map.get(top_doc_id, 'Văn bản') if top_doc_id else 'Văn bản'
            logger.info(f"📄 Filtered to {len(reranked_results)} chunks from top document: {top_doc_id[:8] if top_doc_id else 'unknown'}...")
            
            # Add title to results for context building
            for r in reranked_results:
                r['document_title'] = final_doc_title
        
        # Step 4: Build context from TOP reranked results
        # Limit to top 5 chunks for LLM context to avoid token overflow
        # Reranked results are already sorted by relevance score
        context_chunks = reranked_results[:5]  # Top 5 most relevant chunks
        logger.info(f"📝 Building context from top {len(context_chunks)} chunks (of {len(reranked_results)} total)")
        
        context_parts = []
        for idx, result in enumerate(context_chunks, 1):
            content = result['content']
            doc_title = result.get('document_title', 'Văn bản')
            metadata = result.get('metadata', {})
            doc_code = metadata.get('document_code', '') if metadata else ''
            
            # Format với trích dẫn
            if doc_code:
                citation = f"[{doc_title} - {doc_code}]"
            else:
                citation = f"[{doc_title}]"
            
            context_parts.append(f"{citation}\n{content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 5: Generate answer using LLM with RAG endpoint
        logger.info("Step 5: Generating answer with RAG prompt...")
        llm_start = time.time()
        
        # Prepare history for LLM (convert to dict format)
        history_for_llm = None
        if request.history:
            history_for_llm = [{"role": h.role, "content": h.content} for h in request.history]
        
        answer, tokens_used = await generate_answer(request.question, context, history=history_for_llm)
        timing["llm_ms"] = int((time.time() - llm_start) * 1000)
        if answer is None:
            raise HTTPException(status_code=503, detail="LLM service unavailable")
        
        # Step 6: Update conversation state - PIN the document for future follow-ups
        # Track if we newly pinned a document in this request
        newly_pinned = False
        if final_doc_id and max_score >= settings.CLARIFICATION_THRESHOLD:
            # Pin document with current embedding for future follow-ups
            state.update(
                document_id=final_doc_id,
                document_title=final_doc_title or "Văn bản",
                question=request.question,
                confidence=max_score,
                embedding=embedding  # Use query embedding (no semantic check needed)
            )
            # Save to database for persistence
            save_conversation_state(state)
            newly_pinned = True
            logger.info(f"📌 Pinned document for session {session_id}: {final_doc_title}")
        
        # Step 7: Log query to database for analytics
        if db_client:
            sources_for_log = [
                {"document_id": final_doc_id, "title": final_doc_title}
            ] if final_doc_id else []
            
            db_client.log_query(
                session_id=session_id,
                query_text=request.question,
                query_type="follow_up" if use_pinned else "initial",
                answer_text=answer[:500] if answer else None,  # Truncate for storage
                sources_used=sources_for_log,
                confidence_score=max_score,
                metadata={
                    "used_pinned_document": use_pinned,
                    "pinned_document_title": pinned_doc_title
                }
            )
        
        # Step 8: Fetch document file paths and forms for frontend download
        doc_info_map = {}
        forms_list = []
        if db_client and final_doc_id:
            doc_info_map = db_client.fetch_document_info([final_doc_id])
            forms_map = db_client.fetch_forms_by_document_ids([final_doc_id])
            # Flatten forms from all documents
            for doc_forms in forms_map.values():
                for form in doc_forms:
                    forms_list.append(FormInfo(
                        id=form['id'],
                        form_name=form['form_name'],
                        template_path=form['template_path'],
                        description=form['description']
                    ))
        
        took_ms = int((time.time() - start_time) * 1000)
        logger.info(f"⏱️ Query completed in {took_ms}ms | Embed: {timing['embed_ms']}ms, Search: {timing['search_ms']}ms, Rerank: {timing['rerank_ms']}ms, LLM: {timing['llm_ms']}ms")
        
        return QueryResponse(
            success=True,
            question=request.question,
            answer=answer,
            session_id=session_id,
            session_info=build_session_info(),
            used_pinned_document=use_pinned or newly_pinned,
            pinned_document_title=final_doc_title if (use_pinned or newly_pinned) else None,
            sources=[
                SearchResult(
                    content=result['content'],
                    similarity=result.get('rerank_score', result.get('similarity', 0.0)),
                    chunk_id=result.get('chunk_id') or result.get('vector_id') or result.get('id'),  # For evaluation metrics
                    document_id=result.get('document_id'),
                    document_title=result.get('document_title', 'Văn bản'),
                    file_path=doc_info_map.get(result.get('document_id'), {}).get('file_path')
                )
                for result in reranked_results
            ],
            forms=forms_list if forms_list else None,
            tokens_used=tokens_used,
            took_ms=took_ms,
            timing=timing
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/confirm", response_model=QueryResponse)
async def query_confirm(request: ConfirmRequest):
    """
    Handle user's document selection and PIN it for future follow-ups.
    
    Flow:
    1. Get or create session (backend-driven)
    2. Embed original question
    3. Search with document_id filter
    4. Rerank filtered results
    5. Generate answer
    6. PIN the confirmed document for conversation state
    7. Return session_id and session_info in response
    """
    start_time = time.time()  # Track processing time
    try:
        logger.info(f"✅ User confirmed document: {request.document_id}")
        
        # Get or create session (backend-driven)
        session_id, is_new_session = get_or_create_session_id(request.session_id)
        state = get_conversation_state(session_id)
        
        # IMPORTANT: If new session, save immediately so subsequent requests can find it
        if is_new_session:
            save_conversation_state(state)
            logger.info(f"📌 New session saved to DB: {session_id}")
        
        # Helper to build session_info for responses
        def build_session_info() -> SessionInfo:
            return SessionInfo(
                session_id=session_id,
                is_new_session=is_new_session,
                pinned_document_id=state.active_document_id,
                pinned_document_title=state.active_document_title,
                conversation_turns=state.conversation_turns
            )
        
        # Fetch document title for state
        doc_title = "Văn bản"
        if db_client:
            titles = db_client.fetch_document_titles([request.document_id])
            doc_title = titles.get(request.document_id, "Văn bản")
        
        # Step 1: Embed
        embedding = await embed_text(request.question)
        if not embedding:
            raise HTTPException(503, "Embedding service unavailable")
        
        # Step 2: Search with document filter
        response = await http_client.post(
            f"{settings.VECTOR_SERVICE_URL}/search",
            json={
                "embedding": embedding,
                "top_k": 20,
                "threshold": 0.3,
                "document_ids": [request.document_id]
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Vector search failed: {response.text}")
            raise HTTPException(503, "Vector search failed")
        
        search_results = response.json().get("results", [])
        
        if not search_results:
            return QueryResponse(
                success=True,
                question=request.question,
                answer="Xin lỗi, không tìm thấy thông tin trong văn bản đã chọn.",
                session_id=session_id,
                session_info=build_session_info(),
                needs_clarification=False,
                sources=[],
                tokens_used=0,
                used_pinned_document=False,
                took_ms=int((time.time() - start_time) * 1000)
            )
        
        # Step 3: Rerank
        reranked_results, _ = await rerank_documents(
            request.question, 
            search_results, 
            top_k=5
        )
        
        # Get max score for confidence
        max_score = max(r.get('rerank_score', 0) for r in reranked_results) if reranked_results else 0
        
        # Step 4: Build context
        context_parts = []
        for result in reranked_results:
            content = result['content']
            section = result.get('section_title', '')
            
            if section:
                context_parts.append(f"[{doc_title} - {section}]\n{content}")
            else:
                context_parts.append(f"[{doc_title}]\n{content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 5: Generate answer with history for follow-up context
        history_for_llm = None
        if request.history:
            history_for_llm = [{"role": h.role, "content": h.content} for h in request.history]
        
        answer, tokens_used = await generate_answer(request.question, context, history=history_for_llm)
        
        if not answer:
            raise HTTPException(503, "LLM service unavailable")
        
        # Step 6: PIN the confirmed document for future follow-ups
        state.update(
            document_id=request.document_id,
            document_title=doc_title,
            question=request.question,
            confidence=max_score,
            embedding=embedding  # Store for semantic topic detection
        )
        # Persist state to database
        save_conversation_state(state)
        logger.info(f"📌 Pinned confirmed document for session {session_id}: {doc_title}")
        
        # Step 7: Log query to database
        if db_client:
            db_client.log_query(
                session_id=session_id,
                query_text=request.question,
                query_type="confirm",
                answer_text=answer[:500] if answer else None,
                sources_used=[{"document_id": request.document_id, "title": doc_title}],
                confidence_score=max_score,
                metadata={
                    "confirmed_document_id": request.document_id,
                    "confirmed_document_title": doc_title
                }
            )
        
        # Step 8: Fetch document file path and forms for frontend download
        doc_info_map = {}
        forms_list = []
        if db_client:
            doc_info_map = db_client.fetch_document_info([request.document_id])
            forms_map = db_client.fetch_forms_by_document_ids([request.document_id])
            for doc_forms in forms_map.values():
                for form in doc_forms:
                    forms_list.append(FormInfo(
                        id=form['id'],
                        form_name=form['form_name'],
                        template_path=form['template_path'],
                        description=form['description']
                    ))
        
        file_path = doc_info_map.get(request.document_id, {}).get('file_path')
        
        took_ms = int((time.time() - start_time) * 1000)
        logger.info(f"⏱️ Query confirm completed in {took_ms}ms")
        
        return QueryResponse(
            success=True,
            question=request.question,
            answer=answer,
            session_id=session_id,
            session_info=build_session_info(),
            needs_clarification=False,
            used_pinned_document=True,  # User confirmed = document is now pinned
            pinned_document_title=doc_title,
            sources=[
                SearchResult(
                    content=r['content'],
                    similarity=r.get('rerank_score', 0),
                    chunk_id=r.get('chunk_id') or r.get('vector_id') or r.get('id'),  # For evaluation metrics
                    document_id=request.document_id,
                    document_title=doc_title,
                    file_path=file_path
                )
                for r in reranked_results
            ],
            forms=forms_list if forms_list else None,
            tokens_used=tokens_used,
            took_ms=took_ms
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Query confirm failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "query-service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "POST /query",
            "query_confirm": "POST /query/confirm",
            "session_start": "POST /session/start",
            "session_clear": "POST /session/clear",
            "session_info": "GET /session/info/{session_id}",
            "forms": {
                "cccd_scan": "POST /forms/cccd/scan",
                "cccd_upload": "POST /forms/cccd/scan/upload",
                "render": "POST /forms/render",
                "fill": "POST /forms/fill",
                "save": "POST /forms/save"
            },
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True
    )
