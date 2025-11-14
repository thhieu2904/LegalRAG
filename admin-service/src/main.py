"""
Admin Service - Document Management & Ingestion
Upload documents, process them into chunks, embed, and index
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import psycopg2
import httpx
import uuid
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global instances
db_conn = None
http_client = None


# ============= MODELS =============

class DocumentUploadResponse(BaseModel):
    """Upload response"""
    success: bool
    document_id: str
    filename: str
    message: str


class DocumentListResponse(BaseModel):
    """List response"""
    success: bool
    documents: List[dict]
    total: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    db: str
    services: str


# ============= APP =============

app = FastAPI(
    title="Admin Service",
    description="Document management and ingestion",
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
    global db_conn, http_client
    
    logger.info("🚀 Starting Admin Service...")
    
    # Connect to database
    try:
        db_conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            dbname=settings.POSTGRES_DB
        )
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise
    
    # Initialize HTTP client
    http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("✅ Admin Service started")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup"""
    global db_conn, http_client
    if db_conn:
        db_conn.close()
    if http_client:
        await http_client.aclose()
    logger.info("✅ Admin Service stopped")


# ============= HELPER FUNCTIONS =============

def chunk_text(text: str, chunk_size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


async def embed_texts(texts: List[str]) -> Optional[List[List[float]]]:
    """Embed multiple texts"""
    try:
        response = await http_client.post(
            f"{settings.EMBEDDING_SERVICE_URL}/embed-batch",
            json={"texts": texts}
        )
        if response.status_code == 200:
            data = response.json()
            return data["embeddings"]
        return None
    except Exception as e:
        logger.error(f"❌ Embedding failed: {e}")
        return None


async def store_vectors(document_id: str, chunks: List[str], embeddings: List[List[float]]) -> bool:
    """Store vectors in vector service"""
    try:
        vectors = [
            {
                "document_id": document_id,
                "chunk_index": i,
                "content": chunk,
                "embedding": emb
            }
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        
        response = await http_client.post(
            f"{settings.VECTOR_SERVICE_URL}/insert-batch",
            json={"vectors": vectors}
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Vector storage failed: {e}")
        return False


def save_document_to_db(document_id: str, filename: str) -> bool:
    """Save document metadata to database"""
    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO documents (id, filename, status, created_at)
            VALUES (%s, %s, %s, %s)
        """, (document_id, filename, "completed", datetime.now()))
        db_conn.commit()
        cursor.close()
        return True
    except Exception as e:
        logger.error(f"❌ DB save failed: {e}")
        db_conn.rollback()
        return False


# ============= ENDPOINTS =============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    status = "healthy"
    db_status = "ok" if db_conn else "down"
    
    async def check_service(url: str) -> str:
        try:
            response = await http_client.get(f"{url}/health", timeout=5.0)
            return "ok" if response.status_code == 200 else "down"
        except:
            return "down"
    
    services_status = await check_service(settings.STORAGE_SERVICE_URL)
    
    return HealthResponse(
        status=status,
        db=db_status,
        services=services_status
    )


@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document"""
    try:
        document_id = str(uuid.uuid4())
        filename = file.filename
        
        logger.info(f"📄 Uploading: {filename}")
        
        # Read file
        content = await file.read()
        
        # Upload to storage
        logger.info(f"💾 Saving to storage...")
        upload_response = await http_client.post(
            f"{settings.STORAGE_SERVICE_URL}/upload",
            data={"file": (filename, content, file.content_type)},
            params={"document_id": document_id}
        )
        
        if upload_response.status_code != 201:
            raise HTTPException(status_code=500, detail="Storage failed")
        
        # Extract text (for PDF)
        logger.info(f"📖 Extracting text...")
        text = content.decode("utf-8", errors="ignore")[:10000]  # Simplified
        
        # Chunk text
        logger.info(f"✂️  Chunking text...")
        chunks = chunk_text(text)
        
        # Embed chunks
        logger.info(f"🧠 Embedding {len(chunks)} chunks...")
        embeddings = await embed_texts(chunks)
        
        if not embeddings:
            raise HTTPException(status_code=503, detail="Embedding service unavailable")
        
        # Store vectors
        logger.info(f"📍 Storing vectors...")
        if not await store_vectors(document_id, chunks, embeddings):
            raise HTTPException(status_code=503, detail="Vector service unavailable")
        
        # Save metadata to database
        logger.info(f"🗃️  Saving metadata...")
        if not save_document_to_db(document_id, filename):
            raise HTTPException(status_code=500, detail="Database save failed")
        
        logger.info(f"✅ Document processed: {document_id}")
        
        return DocumentUploadResponse(
            success=True,
            document_id=document_id,
            filename=filename,
            message=f"Processed {len(chunks)} chunks"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List all documents"""
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT id, filename, created_at FROM documents WHERE is_deleted = false ORDER BY created_at DESC")
        docs = cursor.fetchall()
        cursor.close()
        
        return DocumentListResponse(
            success=True,
            documents=[
                {"id": doc[0], "filename": doc[1], "created_at": str(doc[2])}
                for doc in docs
            ],
            total=len(docs)
        )
    except Exception as e:
        logger.error(f"❌ List failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete document (soft delete)"""
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            "UPDATE documents SET is_deleted = true WHERE id = %s",
            (document_id,)
        )
        db_conn.commit()
        cursor.close()
        
        return {"success": True, "message": "Document deleted"}
    except Exception as e:
        logger.error(f"❌ Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "admin-service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "upload": "POST /upload",
            "documents": "GET /documents",
            "delete": "DELETE /documents/{id}",
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
