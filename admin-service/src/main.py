"""
Admin Service - Document Processing Orchestrator (AICenter-RAG Pattern)
Workflow:
1. Call Storage: Upload file → storage_id
2. Admin: INSERT documents table (PostgreSQL direct)
3. Call Storage: Extract text
4. Admin: Extract metadata locally
5. Call Embedding: Chunk and embed
6. Call Vector-Service: INSERT chunks (document already exists)
7. Admin: UPDATE documents chunk_count
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import httpx
import re
import os
import uuid
import json
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ============= CONFIG =============

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8010")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8011")
VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8012")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8001))

# PostgreSQL config (AICenter pattern: Admin has direct DB access)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "legalrag")
POSTGRES_USER = os.getenv("POSTGRES_USER", "legalrag")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "legalrag_password")

logger.info(f"📡 Storage Service URL: {STORAGE_SERVICE_URL}")
logger.info(f"📡 Embedding Service URL: {EMBEDDING_SERVICE_URL}")
logger.info(f"📡 Vector Service URL: {VECTOR_SERVICE_URL}")
logger.info(f"🗄️  PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

# ============= MODELS =============

class ExtractedMetadata(BaseModel):
    """Extracted metadata from document"""
    document_code: Optional[str] = None
    dates: Optional[List[str]] = None
    organizations: Optional[List[str]] = None
    sections: Optional[List[str]] = None
    pages: Optional[int] = None
    word_count: Optional[int] = None
    extraction_confidence: float = 0.0


class ProcessDocumentResponse(BaseModel):
    """Response from document processing"""
    success: bool
    file_id: str
    file_path: str
    file_size: int
    text: str
    text_stats: Dict[str, Any]
    metadata: ExtractedMetadata
    message: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    storage_service: str


# ============= METADATA EXTRACTOR =============

class LegalMetadataExtractor:
    """Extract metadata from Vietnamese legal documents"""
    
    # Patterns for Vietnamese legal documents
    DOCUMENT_CODE_PATTERNS = [
        r'(\d+/\d{4}/NĐ-CP)',  # Nghị định: 68/2018/NĐ-CP
        r'(\d+/\d{4}/QĐ-)',     # Quyết định: 68/2018/QĐ-...
        r'(\d+/\d{4}/TT-)',     # Thông tư: 68/2018/TT-...
        r'(QT\s*0?\d+/)',       # Quy trình: QT 01/BTNN
    ]
    
    DATE_PATTERNS = [
        r'(\d{1,2}/\d{1,2}/\d{4})',  # DD/MM/YYYY
        r'(\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})',  # DD tháng MM năm YYYY
    ]
    
    ORGANIZATION_PATTERNS = [
        r'(Bộ\s+\w+)',  # Bộ Tư pháp, Bộ Lao động
        r'(Sở\s+\w+)',  # Sở Tư pháp, Sở Lao động
        r'(Cục\s+\w+)',  # Cục Thuế
        r'(Văn phòng\s+\w+)',  # Văn phòng Chính phủ
    ]
    
    SECTION_PATTERNS = [
        r'(Điều\s+\d+)',  # Điều 1, Điều 2
        r'(Mục\s+\d+\.\d+)',  # Mục 1.1, Mục 2.3
        r'(Chương\s+[IVX]+)',  # Chương I, Chương II
    ]
    
    @staticmethod
    def extract_document_code(text: str) -> Optional[str]:
        """Extract document code like '68/2018/NĐ-CP'"""
        for pattern in LegalMetadataExtractor.DOCUMENT_CODE_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]  # Return first match
        return None
    
    @staticmethod
    def extract_dates(text: str) -> Optional[List[str]]:
        """Extract all dates from text"""
        dates = []
        for pattern in LegalMetadataExtractor.DATE_PATTERNS:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        return list(set(dates)) if dates else None  # Remove duplicates
    
    @staticmethod
    def extract_organizations(text: str) -> Optional[List[str]]:
        """Extract Vietnamese government organizations"""
        orgs = []
        for pattern in LegalMetadataExtractor.ORGANIZATION_PATTERNS:
            matches = re.findall(pattern, text)
            orgs.extend(matches)
        return list(set(orgs)) if orgs else None
    
    @staticmethod
    def extract_sections(text: str) -> Optional[List[str]]:
        """Extract sections (Điều, Mục, Chương)"""
        sections = []
        for pattern in LegalMetadataExtractor.SECTION_PATTERNS:
            matches = re.findall(pattern, text)
            sections.extend(matches)
        return list(set(sections)) if sections else None
    
    @staticmethod
    def extract_all(text: str, pages: int = 0) -> Dict[str, Any]:
        """Extract all metadata from text"""
        
        document_code = LegalMetadataExtractor.extract_document_code(text)
        dates = LegalMetadataExtractor.extract_dates(text)
        organizations = LegalMetadataExtractor.extract_organizations(text)
        sections = LegalMetadataExtractor.extract_sections(text)
        
        # Calculate confidence based on what we extracted
        extracted_fields = sum([
            1 if document_code else 0,
            1 if dates else 0,
            1 if organizations else 0,
            1 if sections else 0,
        ])
        confidence = extracted_fields / 4.0  # 0.0 to 1.0
        
        return {
            "document_code": document_code,
            "dates": dates,
            "organizations": organizations,
            "sections": sections,
            "pages": pages,
            "word_count": len(text.split()),
            "extraction_confidence": confidence,
        }


# ============= DATABASE CONNECTION =============

def get_db_connection():
    """Get PostgreSQL connection (AICenter pattern)"""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


# ============= APP =============

app = FastAPI(
    title="Admin Service",
    description="Document processing orchestrator with direct PostgreSQL access",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= HEALTH CHECK =============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{STORAGE_SERVICE_URL}/health", timeout=5.0)
            if resp.status_code == 200:
                storage_healthy = resp.json().get("storage_connected", False)
                return HealthResponse(
                    status="healthy",
                    service="admin-service",
                    storage_service="healthy" if storage_healthy else "unhealthy"
                )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    
    return HealthResponse(
        status="unhealthy",
        service="admin-service",
        storage_service="unreachable"
    )


# ============= MAIN ORCHESTRATION ENDPOINT =============

@app.post("/admin/process-document", response_model=ProcessDocumentResponse)
async def process_document(
    file: UploadFile = File(...),
    collection_id: str = Form(...),  # UUID string từ dropdown
    title: str = Form(...),  # User nhập tay
    document_id: Optional[str] = Form(None),  # Optional, auto-generate nếu None
):
    """
    Process document: Full pipeline (AICenter-RAG Pattern)
    
    FRONTEND REQUIREMENTS:
    - collection_id: UUID của collection được chọn từ dropdown (bắt buộc)
    - title: Tên văn bản pháp luật user nhập (bắt buộc)
    - file: PDF file (bắt buộc)
    - document_id: Optional, nếu không có sẽ auto-generate UUID
    
    Workflow (AICenter Pattern):
    1. Storage: Upload file → storage_id, file_path
    2. **Admin: INSERT documents table (PostgreSQL direct)**
    3. Storage: Extract text → cleaned text
    4. Admin: Extract metadata locally
    5. Embedding: Chunk and embed → chunks with 768-D vectors
    6. **Vector-Service: INSERT chunks (document already exists)**
    7. **Admin: UPDATE documents.chunk_count (PostgreSQL direct)**
    
    Args:
        file: PDF file to process
        collection_id: UUID of the collection (from frontend dropdown)
        title: Document title (user input)
    
    Returns:
        {
            success: bool,
            file_id: str,
            file_path: str,
            file_size: int,
            text: str,
            text_stats: {pages, characters, words},
            metadata: {document_code, dates, organizations, sections, confidence},
            message: str
        }
    """
    
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename required")
        
        # Validate collection_id is UUID
        try:
            collection_uuid = str(uuid.UUID(collection_id))
        except:
            raise HTTPException(status_code=400, detail="Invalid collection_id (must be UUID)")
        
        # Generate document_id if not provided
        if not document_id:
            doc_uuid = str(uuid.uuid4())
        else:
            try:
                doc_uuid = str(uuid.UUID(document_id))
            except:
                # Generate UUID from string
                doc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, document_id))
        
        logger.info(f"📄 Processing: {title} (UUID: {doc_uuid}, Collection: {collection_uuid})")
        
        file_content = await file.read()
        file_size = len(file_content)
        
        # ===== STEP 1: Upload to Storage-Service =====
        logger.info(f"📤 STEP 1: Uploading to Storage-Service...")
        async with httpx.AsyncClient() as client:
            files = {'file': (file.filename, file_content, 'application/pdf')}
            params = {'document_id': doc_uuid}
            
            resp = await client.post(
                f"{STORAGE_SERVICE_URL}/upload",
                files=files,
                params=params,
                timeout=30.0
            )
            
            if resp.status_code != 201:
                error_msg = resp.text
                logger.error(f"❌ Storage upload failed: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Storage upload failed: {error_msg}"
                )
            
            upload_result = resp.json()
            file_path = upload_result['file_path']
            logger.info(f"✅ STEP 1 OK: {file_path}")
        
        # ===== STEP 2: INSERT documents table (AICenter Pattern - Admin does this) =====
        logger.info(f"💾 STEP 2: Inserting document metadata to PostgreSQL...")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO documents (
                    id, collection_id, title, filename,
                    file_path, file_size, status, metadata,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, 'processing', %s::jsonb,
                    NOW(), NOW()
                )
                RETURNING id;
            """, (
                doc_uuid, collection_uuid, title, file.filename,
                file_path, file_size, json.dumps({})  # Will update metadata later
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ STEP 2 OK: Document {doc_uuid} inserted")
            
        except Exception as e:
            logger.error(f"❌ STEP 2 FAILED: Database insert error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Database insert failed: {str(e)}"
            )
        
        # ===== STEP 3: Extract text from Storage-Service =====
        logger.info(f"📝 STEP 3: Extracting text from Storage-Service...")
        async with httpx.AsyncClient() as client:
            files = {'file': (file.filename, file_content, 'application/pdf')}
            
            resp = await client.post(
                f"{STORAGE_SERVICE_URL}/extract-text",
                files=files,
                timeout=30.0
            )
            
            if resp.status_code != 200:
                error_msg = resp.text
                logger.error(f"❌ Text extraction failed: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Text extraction failed: {error_msg}"
                )
            
            extraction_result = resp.json()
            text = extraction_result['text']
            pages = extraction_result['pages']
            char_count = extraction_result['character_count']
            word_count = extraction_result['word_count']
            
            logger.info(f"✅ STEP 3 OK: {pages} pages, {char_count} chars, {word_count} words")
        
        # ===== STEP 4: Extract metadata (Admin does this locally) =====
        logger.info(f"🔍 STEP 4: Extracting metadata locally...")
        metadata_dict = LegalMetadataExtractor.extract_all(text, pages=pages)
        metadata = ExtractedMetadata(**metadata_dict)
        
        logger.info(f"✅ STEP 4 OK: Metadata extracted")
        logger.info(f"   - Document Code: {metadata.document_code}")
        logger.info(f"   - Dates: {metadata.dates}")
        logger.info(f"   - Organizations: {metadata.organizations}")
        logger.info(f"   - Sections: {metadata.sections}")
        logger.info(f"   - Confidence: {metadata.extraction_confidence:.2f}")
        
        # ===== STEP 5: Call Embedding-Service for chunks =====
        logger.info(f"🧠 STEP 5: Calling Embedding-Service for chunks...")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{EMBEDDING_SERVICE_URL}/chunk-and-embed",
                headers={"X-API-Key": os.getenv("ADMIN_API_KEY", "admin-secret-key-change-in-production")},
                json={
                    "text": text,
                    "document_id": doc_uuid,
                    "metadata": {
                        "filename": file.filename,
                        "document_code": metadata.document_code,
                        "pages": pages
                    },
                    "add_overlap": True
                },
                timeout=60.0  # Embedding can take time
            )
            
            if resp.status_code != 200:
                error_msg = resp.text
                logger.error(f"❌ Embedding failed: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Embedding failed: {error_msg}"
                )
            
            embedding_result = resp.json()
            chunks = embedding_result['chunks']
            logger.info(f"✅ STEP 5 OK: Got {len(chunks)} chunks")
        
        # ===== STEP 6: Call Vector-Service to INSERT chunks (AICenter Pattern) =====
        logger.info(f"💾 STEP 6: Inserting chunks to PostgreSQL via Vector-Service...")
        
        # AICenter Pattern: Pass ONLY chunk data, document already exists
        vectors = []
        for chunk in chunks:
            chunk_info = chunk.get("chunk_info", {})
            vectors.append({
                "document_id": doc_uuid,  # Document already in DB
                "chunk_index": chunk_info.get("chunk_index", 0),
                "content": chunk_info.get("text", ""),
                "embedding": chunk.get("embedding", []),  # 768-D
                "metadata": {}  # Minimal metadata
            })
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{VECTOR_SERVICE_URL}/insert-batch",
                json={"vectors": vectors},  # AICenter Pattern: Only chunks
                timeout=60.0
            )
            
            if resp.status_code != 200:
                error_msg = resp.text
                logger.error(f"❌ Vector insertion failed: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Vector insertion failed: {error_msg}"
                )
            
            vector_result = resp.json()
            inserted_count = vector_result.get('inserted', 0)
            failed_count = vector_result.get('failed', 0)
            
            logger.info(f"✅ STEP 6 OK: Inserted {inserted_count} chunks")
            if failed_count > 0:
                logger.warning(f"⚠️  Failed to insert {failed_count} chunks")
        
        # ===== STEP 7: UPDATE documents.chunk_count (AICenter Pattern - Admin does this) =====
        logger.info(f"🔄 STEP 7: Updating chunk count in PostgreSQL...")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Update chunk_count and status
            cursor.execute("""
                UPDATE documents 
                SET chunk_count = %s, 
                    status = 'completed',
                    metadata = %s::jsonb,
                    processed_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
            """, (
                inserted_count,
                json.dumps({
                    "document_code": metadata.document_code,
                    "dates": metadata.dates,
                    "organizations": metadata.organizations,
                    "sections": metadata.sections,
                    "pages": pages,
                    "word_count": metadata.word_count,
                    "extraction_confidence": metadata.extraction_confidence
                }),
                doc_uuid
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ STEP 7 OK: Updated chunk_count = {inserted_count}")
            
        except Exception as e:
            logger.error(f"❌ STEP 7 FAILED: Update chunk count error: {e}")
            # Don't fail the whole process, chunks are already inserted
        
        # ===== RESULT =====
        logger.info(f"✅ Full document processing pipeline complete!")
        
        return ProcessDocumentResponse(
            success=True,
            file_id=doc_uuid,  # Always has value now
            file_path=file_path,
            file_size=file_size,
            text=text,
            text_stats={
                "pages": pages,
                "characters": char_count,
                "words": word_count,
            },
            metadata=metadata,
            message=f"Successfully processed {file.filename} - {inserted_count} chunks inserted"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============= ROOT ENDPOINT =============

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "admin-service",
        "version": "2.0.0",
        "status": "running",
        "description": "Simple synchronous document processing orchestrator",
        "endpoints": {
            "health": "GET /health",
            "process_document": "POST /admin/process-document",
            "docs": "GET /docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True
    )
