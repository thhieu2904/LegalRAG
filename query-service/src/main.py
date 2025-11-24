"""
Query Service - RAG Orchestrator
Coordinates embedding, vector search, and LLM to answer questions
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import httpx

from .config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global HTTP client
http_client = None


# ============= MODELS =============

class QueryRequest(BaseModel):
    """Query request"""
    question: str
    top_k: int = settings.TOP_K
    threshold: float = settings.SIMILARITY_THRESHOLD


class SearchResult(BaseModel):
    """Search result"""
    content: str
    similarity: float


class QueryResponse(BaseModel):
    """Query response"""
    success: bool
    question: str
    answer: str
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
    global http_client
    http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("✅ Query Service started")


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


async def rerank_documents(query: str, documents: List[dict], top_k: int = 5) -> List[dict]:
    """
    Rerank documents using rerank service with document filtering.
    
    When same_document_only=True:
    - Rerank service identifies best document
    - Returns ALL chunks from that document (preserves full legal context)
    - top_k parameter is ignored by rerank service
    """
    try:
        # Prepare documents for reranking
        doc_texts = [doc.get('content', '') for doc in documents]
        doc_ids = [doc.get('document_id', 'unknown') for doc in documents]
        
        logger.info(f"Sending {len(documents)} chunks from {len(set(doc_ids))} unique documents to rerank")
        
        response = await http_client.post(
            f"{settings.RERANK_SERVICE_URL}/rerank",
            json={
                "query": query,
                "documents": doc_texts,
                "document_ids": doc_ids,
                # Note: top_k ignored when same_document_only=True (rerank returns all chunks from best doc)
                "top_k": top_k,
                "same_document_only": settings.RERANK_SAME_DOCUMENT_ONLY
            },
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            reranked = data.get("results", [])
            
            # Map reranked results back to original documents with scores
            reranked_docs = []
            for item in reranked:
                idx = item.get('index', 0)
                if idx < len(documents):
                    doc = documents[idx].copy()
                    doc['rerank_score'] = item.get('score', 0.0)
                    reranked_docs.append(doc)
            
            logger.info(f"✅ Reranked {len(reranked_docs)} documents")
            return reranked_docs
        else:
            logger.warning(f"⚠️ Rerank failed: {response.text}, using original order")
            return documents[:top_k]
    except Exception as e:
        logger.warning(f"⚠️ Rerank error: {e}, using original order")
        return documents[:top_k]


async def generate_answer(question: str, context: str) -> Optional[str]:
    """
    Generate answer using LLM Service's /generate-rag endpoint.
    
    This function sends question + context to LLM service,
    which automatically wraps with system_prompt.txt + citation_rules.txt.
    """
    try:
        response = await http_client.post(
            f"{settings.LLM_SERVICE_URL}/generate-rag",
            json={
                "question": question,
                "context": context,
                "max_tokens": 1024,
                "temperature": 0.3,  # Low temperature for factual legal answers
                "top_p": 0.85
            },
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
        reranked_results = await rerank_documents(request.question, search_results, top_k=5)
        
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
        # (LLM service will automatically wrap with system_prompt.txt + citation_rules.txt)
        logger.info("Step 5: Generating answer with RAG prompt...")
        answer = await generate_answer(request.question, context)
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


@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "query-service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "POST /query",
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
