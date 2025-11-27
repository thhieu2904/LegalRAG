"""
Query Service - RAG Orchestrator
Coordinates embedding, vector search, and LLM to answer questions
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Tuple
import logging
import httpx
from collections import defaultdict

from .config import settings
from .database import DatabaseClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global clients
http_client = None
db_client = None


# ============= MODELS =============

class HistoryMessage(BaseModel):
    """A single message in chat history"""
    role: str  # 'user' or 'assistant'
    content: str


class QueryRequest(BaseModel):
    """Query request with optional chat history"""
    question: str
    top_k: int = settings.TOP_K
    threshold: float = settings.SIMILARITY_THRESHOLD
    history: Optional[List[HistoryMessage]] = None  # Last 3 turns for context


class SearchResult(BaseModel):
    """Search result"""
    content: str
    similarity: float


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
    history: Optional[List[HistoryMessage]] = None  # Chat history for follow-up context


class QueryResponse(BaseModel):
    """Query response with optional clarification"""
    success: bool
    question: str
    answer: Optional[str] = None
    
    # Clarification fields
    needs_clarification: bool = False
    clarification_message: Optional[str] = None
    document_options: Optional[List[DocumentOption]] = None
    
    sources: List[SearchResult]
    tokens_used: int


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
    global http_client, db_client
    http_client = httpx.AsyncClient(timeout=30.0)
    
    # Initialize PostgreSQL client
    db_client = DatabaseClient(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB
    )
    
    logger.info("✅ Query Service started (with DB client)")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global http_client
    if http_client:
        await http_client.aclose()
    logger.info("✅ Query Service stopped")


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
    
    Returns:
    - Tuple of (reranked_docs, document_scores)
    - document_scores: List of {document_id, avg_score, max_score, chunk_count}
      Used to decide if clarification is needed (when scores are close)
    """
    try:
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
            timeout=30.0
        )
        
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
) -> Optional[str]:
    """
    Generate answer using LLM Service's /generate-rag endpoint.
    
    This function sends question + context + history to LLM service,
    which automatically wraps with system_prompt.txt + citation_rules.txt.
    
    Args:
        question: Current user question
        context: RAG context from vector search
        history: Optional chat history (last 3 turns) for follow-up questions
    """
    try:
        payload = {
            "question": question,
            "context": context,
            "max_tokens": 1280,  # Optimized for Vietnamese responses
            "temperature": 0.3,  # Low temperature for factual legal answers
            "top_p": 0.85
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
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ LLM generated {data.get('completion_tokens', 0)} tokens")
            return data.get("text", "")
        else:
            logger.error(f"❌ LLM generation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ LLM generation error: {type(e).__name__}: {str(e)}")
        return None


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
                penalty += 0.15  # 15% penalty per unmatched specific keyword (strict for legal)
                logger.info(f"📉 Penalty applied to '{title[:30]}...': contains '{keyword}' not in query (-0.15)")
        
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
    """Process query (RAG pipeline)"""
    try:
        logger.info(f"🔍 Query: {request.question}")
        
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
                sources=[],
                tokens_used=0
            )
        
        # Step 1: Embed question
        logger.info("Step 1: Embedding question...")
        embedding = await embed_text(request.question)
        if embedding is None:
            raise HTTPException(status_code=503, detail="Embedding service unavailable")
        
        # Step 2: Search similar documents
        logger.info("Step 2: Searching similar documents...")
        search_results = await search_vectors(embedding)
        if not search_results:
            return QueryResponse(
                success=True,
                question=request.question,
                answer="Xin lỗi, tôi không tìm thấy thông tin liên quan trong cơ sở dữ liệu văn bản pháp luật. Vui lòng thử lại với câu hỏi khác hoặc liên hệ bộ phận hỗ trợ để được tư vấn chi tiết.",
                sources=[],
                tokens_used=0
            )
        
        # Step 3: Rerank documents for better relevance
        logger.info("Step 3: Reranking documents...")
        reranked_results, document_scores = await rerank_documents(
            request.question, search_results, top_k=settings.RERANK_TOP_K
        )
        
        # Step 3.5: Smart clarification check using document scores
        max_score = max(r.get('rerank_score', 0) for r in reranked_results) if reranked_results else 0
        logger.info(f"📊 Max chunk confidence: {max_score:.3f}")
        
        # NEW: Apply heuristics if we have document scores
        if document_scores:
            # Fetch titles early for heuristics
            doc_ids = [ds.get('document_id') for ds in document_scores]
            titles_map = db_client.fetch_document_titles(doc_ids)
            
            # Apply heuristics to reorder
            document_scores = apply_ranking_heuristics(request.question, document_scores, titles_map)
            
            # Update max_score based on new top document (optional, but good for consistency)
            # Note: We keep original max_score for low_confidence check, 
            # but use reordered list for gap check
        else:
            titles_map = {}

        needs_clarification = False
        clarification_reason = ""
        
        # Check 1: Low confidence (using original max score from chunks)
        if max_score < settings.CLARIFICATION_THRESHOLD:
            needs_clarification = True
            clarification_reason = "low_confidence"
            logger.info(f"❓ Low confidence ({max_score:.3f} < {settings.CLARIFICATION_THRESHOLD}) → Clarification needed")
        
        # Check 2: Score gap between top documents (ambiguous query)
        # Now using HEURISTIC scores for gap check
        elif document_scores and len(document_scores) >= 2:
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
                
                return QueryResponse(
                    success=True,
                    question=request.question,
                    answer=None,
                    needs_clarification=True,
                    clarification_message="Tôi tìm thấy nhiều văn bản có thể liên quan. Bạn muốn xem văn bản nào?",
                    document_options=options,
                    sources=[],
                    tokens_used=0
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
                
                return QueryResponse(
                    success=True,
                    question=request.question,
                    answer=None,
                    needs_clarification=True,
                    clarification_message="Tôi tìm thấy các văn bản có thể liên quan. Bạn muốn xem văn bản nào?",
                    document_options=options[:3],
                    sources=[],
                    tokens_used=0
                )
        
        # HIGH CONFIDENCE & CLEAR WINNER → Answer directly
        logger.info("✅ High confidence with clear winner → Answering directly")
        
        # Filter to only chunks from top document for coherent answer
        if document_scores and len(document_scores) > 0:
            top_doc_id = document_scores[0].get('document_id')
            reranked_results = [r for r in reranked_results if r.get('document_id') == top_doc_id]
            logger.info(f"📄 Filtered to {len(reranked_results)} chunks from top document: {top_doc_id[:8]}...")
            
            # Add title to results for context building
            for r in reranked_results:
                r['document_title'] = titles_map.get(top_doc_id, 'Văn bản')
        
        # Step 4: Build context from reranked results
        context_parts = []
        for idx, result in enumerate(reranked_results, 1):
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
        
        # Prepare history for LLM (convert to dict format)
        history_for_llm = None
        if request.history:
            history_for_llm = [{"role": h.role, "content": h.content} for h in request.history]
        
        answer = await generate_answer(request.question, context, history=history_for_llm)
        if answer is None:
            raise HTTPException(status_code=503, detail="LLM service unavailable")
        
        return QueryResponse(
            success=True,
            question=request.question,
            answer=answer,
            sources=[
                SearchResult(
                    content=result['content'],
                    similarity=result.get('rerank_score', result.get('similarity', 0.0))
                )
                for result in reranked_results
            ],
            tokens_used=0  # LLM service will track tokens
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/confirm", response_model=QueryResponse)
async def query_confirm(request: ConfirmRequest):
    """
    Handle user's document selection
    
    Flow:
    1. Embed original question
    2. Search with document_id filter
    3. Rerank filtered results
    4. Generate answer
    """
    try:
        logger.info(f"✅ User confirmed document: {request.document_id}")
        
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
                needs_clarification=False,
                sources=[],
                tokens_used=0
            )
        
        # Step 3: Rerank
        reranked_results, _ = await rerank_documents(
            request.question, 
            search_results, 
            top_k=5
        )
        
        # Step 4: Build context
        context_parts = []
        for result in reranked_results:
            content = result['content']
            section = result.get('section_title', '')
            
            if section:
                context_parts.append(f"[{section}]\n{content}")
            else:
                context_parts.append(content)
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 5: Generate answer with history for follow-up context
        history_for_llm = None
        if request.history:
            history_for_llm = [{"role": h.role, "content": h.content} for h in request.history]
        
        answer = await generate_answer(request.question, context, history=history_for_llm)
        
        if not answer:
            raise HTTPException(503, "LLM service unavailable")
        
        return QueryResponse(
            success=True,
            question=request.question,
            answer=answer,
            needs_clarification=False,
            sources=[
                SearchResult(
                    content=r['content'],
                    similarity=r.get('rerank_score', 0)
                )
                for r in reranked_results
            ],
            tokens_used=0
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
