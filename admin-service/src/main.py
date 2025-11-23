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
import time
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ============= CONFIG =============

ADMIN_SERVICE_URL = os.getenv("ADMIN_SERVICE_URL", "http://localhost:8001")
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8010")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8002")
VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8004")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8001))

# PostgreSQL config (AICenter pattern: Admin has direct DB access)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "legalrag")
POSTGRES_USER = os.getenv("POSTGRES_USER", "legalrag")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "legalrag_password")

logger.info(f"📡 Admin Service URL: {ADMIN_SERVICE_URL}")
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
            "language": "vi",
            "extraction_confidence": confidence,
            "extraction_notes": "Auto-extracted using regex patterns"
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


# ============= AUDIT LOG HELPER =============

def log_admin_action(cursor, action: str, resource_type: str, resource_id: str, details: dict):
    """
    Simple audit log for admin actions
    Logs: action, resource, timestamp, basic details
    """
    try:
        cursor.execute("""
            INSERT INTO admin_logs (
                action, 
                resource_type, 
                resource_id, 
                old_values,
                created_at
            ) VALUES (%s, %s, %s, %s, NOW())
        """, (action, resource_type, resource_id, json.dumps(details)))
        logger.info(f"📝 Audit log: {action} {resource_type} {resource_id}")
    except Exception as e:
        # Don't fail the operation if audit log fails
        logger.warning(f"⚠️  Failed to write audit log: {e}")


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


@app.get("/admin/system-stats")
async def get_system_stats():
    """Get system statistics for dashboard"""
    try:
        # Use synchronous psycopg2 connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get collections count
            cursor.execute("SELECT COUNT(*) as count FROM collections WHERE is_active = true")
            collections_count = cursor.fetchone()[0]
            
            # Get documents count
            cursor.execute("SELECT COUNT(*) as count FROM documents")
            documents_count = cursor.fetchone()[0]
            
            # Get forms count
            cursor.execute("SELECT COUNT(*) as count FROM forms")
            forms_count = cursor.fetchone()[0]
            
            # Get total chunks count (sum from all documents)
            cursor.execute("SELECT COALESCE(SUM(chunk_count), 0) as total_chunks FROM documents")
            chunks_count = cursor.fetchone()[0]
            
        finally:
            cursor.close()
            conn.close()
        
        # Check storage service health
        storage_status = "unknown"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{STORAGE_SERVICE_URL}/health", timeout=3.0)
                if resp.status_code == 200 and resp.json().get("storage_connected"):
                    storage_status = "healthy"
                else:
                    storage_status = "unhealthy"
        except Exception:
            storage_status = "unreachable"
        
        return {
            "collections_count": collections_count,
            "documents_count": documents_count,
            "forms_count": forms_count,
            "chunks_count": chunks_count,
            "storage_status": storage_status
        }
        
    except Exception as e:
        logger.error(f"Error fetching system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/usage-analytics")
async def get_usage_analytics(period: str = "7days"):
    """
    Get usage analytics for different time periods
    Supported periods: today, 7days, 30days, 3months
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Determine date range based on period
        if period == "today":
            date_filter = "created_at >= CURRENT_DATE"
            interval = "1 day"
        elif period == "7days":
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '7 days'"
            interval = "7 days"
        elif period == "30days":
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
            interval = "30 days"
        elif period == "3months":
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '3 months'"
            interval = "3 months"
        else:
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '7 days'"
            interval = "7 days"
        
        try:
            # Total queries in period
            cursor.execute(f"""
                SELECT COUNT(*) as total_queries
                FROM query_logs
                WHERE {date_filter}
            """)
            total_queries = cursor.fetchone()[0] or 0
            
            # Previous period comparison
            cursor.execute(f"""
                SELECT COUNT(*) as prev_queries
                FROM query_logs
                WHERE created_at >= CURRENT_DATE - INTERVAL '{interval}' * 2
                AND created_at < CURRENT_DATE - INTERVAL '{interval}'
            """)
            prev_queries = cursor.fetchone()[0] or 0
            
            # Calculate percentage change
            if prev_queries > 0:
                change_percent = ((total_queries - prev_queries) / prev_queries) * 100
            else:
                change_percent = 100.0 if total_queries > 0 else 0.0
            
            # Daily breakdown for chart
            cursor.execute(f"""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM query_logs
                WHERE {date_filter}
                GROUP BY DATE(created_at)
                ORDER BY date ASC
            """)
            daily_data = [{"date": str(row[0]), "count": row[1]} for row in cursor.fetchall()]
            
            # Top collections
            cursor.execute(f"""
                SELECT 
                    collection_routed,
                    COUNT(*) as count
                FROM query_logs
                WHERE {date_filter} AND collection_routed IS NOT NULL
                GROUP BY collection_routed
                ORDER BY count DESC
                LIMIT 5
            """)
            top_collections = [{"collection": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            # Average confidence
            cursor.execute(f"""
                SELECT AVG(confidence_score) as avg_confidence
                FROM query_logs
                WHERE {date_filter} AND confidence_score IS NOT NULL
            """)
            avg_confidence = cursor.fetchone()[0] or 0.0
            
        finally:
            cursor.close()
            conn.close()
        
        return {
            "period": period,
            "total_queries": total_queries,
            "prev_period_queries": prev_queries,
            "change_percent": round(change_percent, 1),
            "daily_data": daily_data,
            "top_collections": top_collections,
            "avg_confidence": round(avg_confidence, 2) if avg_confidence else 0.0
        }
        
    except Exception as e:
        logger.error(f"Error fetching usage analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/recent-queries")
async def get_recent_queries(limit: int = 10):
    """Get recent queries with session info"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    ql.id,
                    ql.query_text,
                    ql.collection_routed,
                    ql.confidence_score,
                    ql.processing_time_ms,
                    ql.created_at,
                    ql.session_id,
                    qs.conversation_turns
                FROM query_logs ql
                LEFT JOIN query_sessions qs ON ql.session_id = qs.session_id
                ORDER BY ql.created_at DESC
                LIMIT %s
            """, (limit,))
            
            results = cursor.fetchall()
            queries = []
            for row in results:
                queries.append({
                    "id": str(row[0]),
                    "query_text": row[1],
                    "collection": row[2],
                    "confidence": round(row[3], 2) if row[3] else 0.0,
                    "processing_time": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "session_id": row[6],
                    "conversation_turns": row[7] or 0
                })
            
        finally:
            cursor.close()
            conn.close()
        
        return {"queries": queries}
        
    except Exception as e:
        logger.error(f"Error fetching recent queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/services-health")
async def get_services_health():
    """Check health of all microservices"""
    services = [
        {"name": "Admin Service", "url": f"{ADMIN_SERVICE_URL}/health", "port": 8001},
        {"name": "Storage Service", "url": f"{STORAGE_SERVICE_URL}/health", "port": 8010},
        {"name": "Embedding Service", "url": f"{EMBEDDING_SERVICE_URL}/health", "port": 8002},
        {"name": "Vector Service", "url": f"{VECTOR_SERVICE_URL}/health", "port": 8004},
    ]
    
    results = []
    async with httpx.AsyncClient() as client:
        for service in services:
            try:
                start = time.time()
                resp = await client.get(service["url"], timeout=3.0)
                response_time = int((time.time() - start) * 1000)
                
                if resp.status_code == 200:
                    status = "healthy"
                    details = resp.json() if resp.text else {}
                else:
                    status = "unhealthy"
                    details = {"error": f"HTTP {resp.status_code}"}
                    
            except Exception as e:
                status = "down"
                response_time = 0
                details = {"error": str(e)}
            
            results.append({
                "name": service["name"],
                "status": status,
                "response_time": response_time,
                "port": service["port"],
                "details": details
            })
    
    return {"services": results}


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
        
        # ===== STEP 2: INSERT documents table (SIMPLIFIED - no status/metadata) =====
        logger.info(f"💾 STEP 2: Inserting document metadata to PostgreSQL...")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO documents (
                    id, collection_id, title, filename,
                    file_path, file_size,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s,
                    NOW(), NOW()
                )
                RETURNING id;
            """, (
                doc_uuid, collection_uuid, title, file.filename,
                file_path, file_size
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
                    "language": "vi",
                    "extraction_confidence": metadata.extraction_confidence,
                    "extraction_notes": "Auto-extracted using regex patterns"
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


# ============= COLLECTION & DOCUMENT MANAGEMENT ENDPOINTS =============

# ===== COLLECTION CRUD =====

class CreateCollectionRequest(BaseModel):
    """Request to create a new collection"""
    name: str  # Slug identifier (unique)
    display_name: str
    description: Optional[str] = None
    icon: Optional[str] = "file-text"
    color: Optional[str] = "#3b82f6"


class UpdateCollectionRequest(BaseModel):
    """Request to update collection metadata"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


@app.post("/admin/collections")
async def create_collection(request: CreateCollectionRequest):
    """
    Create a new collection
    
    Args:
        name: Slug identifier (unique, lowercase with underscores)
        display_name: Human-readable name
        description: Optional description
        icon: Optional icon name
        color: Optional hex color
    
    Returns:
        Created collection with UUID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Insert new collection
        cursor.execute("""
            INSERT INTO collections (
                name, display_name, description, icon, color,
                document_count, total_chunks, is_active,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                0, 0, TRUE,
                NOW(), NOW()
            )
            RETURNING id, name, display_name, description, icon, color, created_at;
        """, (
            request.name,
            request.display_name,
            request.description,
            request.icon,
            request.color
        ))
        
        collection = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Created collection: {request.name} (UUID: {collection['id']})")
        
        return {
            "success": True,
            "collection": {
                "id": str(collection['id']),
                "name": collection['name'],
                "display_name": collection['display_name'],
                "description": collection['description'],
                "icon": collection['icon'],
                "color": collection['color'],
                "created_at": collection['created_at'].isoformat()
            }
        }
    
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(
            status_code=409,
            detail=f"Collection with name '{request.name}' already exists"
        )
    except Exception as e:
        logger.error(f"❌ Failed to create collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/collections")
async def list_collections():
    """
    List all active collections with statistics
    Returns collections from collections table (not derived from documents)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query collections table directly (AICenter pattern)
        cursor.execute("""
            SELECT 
                id,
                name,
                display_name,
                description,
                icon,
                color,
                document_count,
                total_chunks,
                is_active,
                created_at,
                updated_at
            FROM collections
            ORDER BY updated_at DESC
        """)
        
        collections = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "collections": [
                {
                    "id": str(col['id']),
                    "name": col['name'],
                    "display_name": col['display_name'],
                    "description": col['description'],
                    "icon": col.get('icon', 'file-text'),
                    "color": col.get('color', '#3b82f6'),
                    "document_count": col['document_count'],
                    "total_chunks": col.get('total_chunks', 0),
                    "is_active": col['is_active'],
                    "created_at": col['created_at'].isoformat() if col['created_at'] else None,
                    "updated_at": col['updated_at'].isoformat() if col['updated_at'] else None
                }
                for col in collections
            ]
        }
    except Exception as e:
        logger.error(f"❌ Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/admin/collections/{collection_id}")
async def update_collection(collection_id: str, request: UpdateCollectionRequest):
    """
    Update collection metadata (display_name, description, icon, color)
    NOTE: Cannot change 'name' (slug) to avoid breaking references
    """
    try:
        # Validate UUID
        try:
            uuid.UUID(collection_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid collection_id UUID")
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build dynamic UPDATE query
        updates = []
        params = []
        
        if request.display_name is not None:
            updates.append("display_name = %s")
            params.append(request.display_name)
        
        if request.description is not None:
            updates.append("description = %s")
            params.append(request.description)
        
        if request.icon is not None:
            updates.append("icon = %s")
            params.append(request.icon)
        
        if request.color is not None:
            updates.append("color = %s")
            params.append(request.color)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = NOW()")
        params.append(collection_id)
        
        query = f"""
            UPDATE collections
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, name, display_name, description, icon, color, updated_at;
        """
        
        cursor.execute(query, params)
        collection = cursor.fetchone()
        
        if not collection:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Collection not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Updated collection: {collection_id}")
        
        return {
            "success": True,
            "collection": {
                "id": str(collection['id']),
                "name": collection['name'],
                "display_name": collection['display_name'],
                "description": collection['description'],
                "icon": collection['icon'],
                "color": collection['color'],
                "updated_at": collection['updated_at'].isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/admin/collections/{collection_id}")
async def delete_collection(collection_id: str):
    """
    Hard delete a collection and all associated documents/chunks
    WARNING: This will permanently delete collection and CASCADE delete all documents/chunks
    """
    try:
        # Validate UUID
        try:
            uuid.UUID(collection_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid collection_id UUID")
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get collection info and document count
        cursor.execute("""
            SELECT 
                c.name,
                c.display_name,
                c.document_count,
                COUNT(d.id) as actual_documents
            FROM collections c
            LEFT JOIN documents d ON c.id = d.collection_id
            WHERE c.id = %s
            GROUP BY c.id, c.name, c.display_name, c.document_count
        """, (collection_id,))
        
        collection = cursor.fetchone()
        
        if not collection:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Count chunks that will be deleted (via CASCADE)
        cursor.execute("""
            SELECT COUNT(*) as chunk_count
            FROM chunks ch
            JOIN documents d ON ch.document_id = d.id
            WHERE d.collection_id = %s
        """, (collection_id,))
        
        chunk_result = cursor.fetchone()
        chunk_count = chunk_result['chunk_count'] if chunk_result else 0
        
        # Log audit before deletion
        log_admin_action(
            cursor, 
            action="delete",
            resource_type="collection",
            resource_id=collection_id,
            details={
                "name": collection['name'],
                "display_name": collection['display_name'],
                "document_count": collection['actual_documents'],
                "chunk_count": chunk_count
            }
        )
        
        # Hard delete collection (CASCADE will delete documents → chunks automatically)
        cursor.execute("""
            DELETE FROM collections WHERE id = %s
        """, (collection_id,))
        
        deleted_docs = collection['actual_documents']
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Permanently deleted collection: {collection['name']} ({deleted_docs} documents, ~{chunk_count} chunks)")
        
        return {
            "success": True,
            "message": f"Collection '{collection['display_name']}' permanently deleted",
            "collection_id": collection_id,
            "deleted_documents": deleted_docs,
            "deleted_chunks_estimate": chunk_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== DOCUMENT CRUD =====

class UpdateDocumentRequest(BaseModel):
    """Request to update document metadata"""
    title: Optional[str] = None


@app.get("/admin/documents")
async def list_documents(
    collection_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List documents with optional filtering
    
    Args:
        collection_id: Filter by collection UUID
        limit: Max results to return
        offset: Pagination offset
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query with filters
        query = "SELECT * FROM documents WHERE 1=1"
        params = []
        
        if collection_id:
            query += " AND collection_id = %s"
            params.append(collection_id)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        documents = cursor.fetchall()
        
        # Get forms count for each document
        document_ids = [doc['id'] for doc in documents]  # Keep as UUID, not string
        forms_counts = {}
        
        if document_ids:
            cursor.execute("""
                SELECT document_id, COUNT(*) as forms_count
                FROM forms
                WHERE document_id = ANY(%s::uuid[])
                GROUP BY document_id
            """, (document_ids,))
            
            for row in cursor.fetchall():
                forms_counts[str(row['document_id'])] = row['forms_count']
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM documents WHERE 1=1"
        count_params = []
        if collection_id:
            count_query += " AND collection_id = %s"
            count_params.append(collection_id)
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "documents": [
                {
                    "id": str(doc['id']),
                    "collection_id": str(doc['collection_id']),
                    "title": doc['title'],
                    "filename": doc['filename'],
                    "file_path": doc['file_path'],
                    "file_size": doc['file_size'],
                    "chunk_count": doc.get('chunk_count', 0),
                    "forms_count": forms_counts.get(str(doc['id']), 0),
                    "created_at": doc['created_at'].isoformat() if doc['created_at'] else None,
                    "updated_at": doc['updated_at'].isoformat() if doc.get('updated_at') else None
                }
                for doc in documents
            ]
        }
    except Exception as e:
        logger.error(f"❌ Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/documents/{document_id}")
async def get_document_detail(document_id: str):
    """
    Get detailed information about a specific document
    Includes chunks and forms
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get document info
        cursor.execute("""
            SELECT d.*, c.display_name as collection_name
            FROM documents d
            JOIN collections c ON d.collection_id = c.id
            WHERE d.id = %s
        """, (document_id,))
        
        document = cursor.fetchone()
        
        if not document:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get chunks
        cursor.execute("""
            SELECT id, chunk_index, content, section_title
            FROM chunks
            WHERE document_id = %s
            ORDER BY chunk_index
        """, (document_id,))
        
        chunks = cursor.fetchall()
        
        # Get forms (simplified - only 5 fields)
        cursor.execute("""
            SELECT id, form_name, description, template_path, created_at
            FROM forms
            WHERE document_id = %s
            ORDER BY created_at DESC
        """, (document_id,))
        
        forms = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "document": {
                "id": str(document['id']),
                "collection_id": str(document['collection_id']),
                "title": document['title'],
                "filename": document['filename'],
                "file_path": document.get('file_path'),
                "file_size": document['file_size'],
                "chunk_count": document.get('chunk_count', 0),
                "created_at": document['created_at'].isoformat() if document['created_at'] else None,
                "updated_at": document['updated_at'].isoformat() if document['updated_at'] else None
            },
            "collection_name": document['collection_name'],
            "chunks": [
                {
                    "id": str(chunk['id']),
                    "chunk_index": chunk['chunk_index'],
                    "content": chunk['content'],
                    "section_title": chunk.get('section_title')
                }
                for chunk in chunks
            ],
            "forms": [
                {
                    "id": str(form['id']),
                    "form_name": form['form_name'],
                    "description": form.get('description'),
                    "template_path": form.get('template_path'),
                    "created_at": form['created_at'].isoformat() if form.get('created_at') else None
                }
                for form in forms
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get document detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/admin/documents/{document_id}")
async def update_document(document_id: str, request: UpdateDocumentRequest):
    """
    Update document metadata (title only, does NOT touch chunks)
    
    Args:
        document_id: UUID of document
        title: New document title
    
    Returns:
        Updated document info
    """
    try:
        # Validate UUID
        try:
            uuid.UUID(document_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid document_id UUID")
        
        if not request.title:
            raise HTTPException(status_code=400, detail="Title is required")
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Update only title, NOT chunks
        cursor.execute("""
            UPDATE documents
            SET title = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id, title, updated_at;
        """, (request.title, document_id))
        
        document = cursor.fetchone()
        
        if not document:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Document not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Updated document title: {document_id}")
        
        return {
            "success": True,
            "document": {
                "id": str(document['id']),
                "title": document['title'],
                "updated_at": document['updated_at'].isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/admin/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Hard delete a document and all associated chunks
    - Permanently delete document from database
    - CASCADE delete all chunks
    - Delete file from MinIO storage
    
    Args:
        document_id: UUID of document to delete
    
    Returns:
        Deletion confirmation with stats
    """
    try:
        # Validate UUID
        try:
            uuid.UUID(document_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid document_id UUID")
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get document info before deletion
        cursor.execute("""
            SELECT 
                id,
                collection_id,
                title,
                filename,
                file_path,
                chunk_count
            FROM documents
            WHERE id = %s
        """, (document_id,))
        
        document = cursor.fetchone()
        
        if not document:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Count actual chunks
        cursor.execute("""
            SELECT COUNT(*) as chunk_count
            FROM chunks
            WHERE document_id = %s
        """, (document_id,))
        
        chunk_result = cursor.fetchone()
        actual_chunks = chunk_result['chunk_count'] if chunk_result else 0
        
        # Log audit before deletion
        log_admin_action(
            cursor,
            action="delete",
            resource_type="document",
            resource_id=document_id,
            details={
                "title": document['title'],
                "filename": document['filename'],
                "collection_id": str(document['collection_id']),
                "chunk_count": actual_chunks,
                "file_path": document['file_path']
            }
        )
        
        # Hard delete document (CASCADE will delete chunks automatically)
        cursor.execute("""
            DELETE FROM documents WHERE id = %s
        """, (document_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Delete file from MinIO (Storage-Service)
        file_deleted = False
        if document['file_path']:
            try:
                async with httpx.AsyncClient() as client:
                    # NOTE: Storage-Service needs to implement DELETE endpoint
                    resp = await client.delete(
                        f"{STORAGE_SERVICE_URL}/files",
                        params={"file_path": document['file_path']},
                        timeout=10.0
                    )
                    
                    if resp.status_code == 200:
                        file_deleted = True
                        logger.info(f"✅ Deleted file from MinIO: {document['file_path']}")
                    else:
                        logger.warning(f"⚠️  Failed to delete file from MinIO: {resp.text}")
            except Exception as e:
                logger.warning(f"⚠️  Could not delete file from MinIO: {e}")
        
        logger.info(f"✅ Deleted document: {document['title']} ({actual_chunks} chunks)")
        
        return {
            "success": True,
            "message": f"Document '{document['title']}' deleted",
            "document_id": document_id,
            "deleted_chunks": actual_chunks,
            "file_deleted": file_deleted,
            "file_path": document['file_path']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/documents/{document_id}/replace")
async def replace_document(
    document_id: str,
    file: UploadFile = File(...),
    keep_title: bool = Form(True)
):
    """
    Replace an existing document with a new PDF file
    - Keeps same document_id and collection_id
    - Optionally keeps same title
    - Deletes old chunks and file
    - Uploads new file and creates new chunks
    
    Args:
        document_id: UUID of document to replace
        file: New PDF file
        keep_title: Keep existing title (default: True)
    
    Returns:
        Updated document info with new chunk statistics
    """
    try:
        # Validate UUID
        try:
            uuid.UUID(document_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid document_id UUID")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename required")
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get existing document info
        cursor.execute("""
            SELECT 
                id,
                collection_id,
                title,
                file_path,
                chunk_count
            FROM documents
            WHERE id = %s
        """, (document_id,))
        
        old_document = cursor.fetchone()
        
        if not old_document:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Document not found")
        
        collection_id = str(old_document['collection_id'])
        old_title = old_document['title']
        old_file_path = old_document['file_path']
        old_chunks = old_document['chunk_count']
        
        # Count actual old chunks
        cursor.execute("""
            SELECT COUNT(*) as chunk_count FROM chunks WHERE document_id = %s
        """, (document_id,))
        old_chunk_count = cursor.fetchone()['chunk_count']
        
        logger.info(f"🔄 Replacing document: {document_id} ({old_chunk_count} old chunks)")
        
        # STEP 1: Delete old chunks (explicit, before file operations)
        cursor.execute("""
            DELETE FROM chunks WHERE document_id = %s
        """, (document_id,))
        deleted_chunks = cursor.rowcount
        conn.commit()
        
        logger.info(f"✅ Deleted {deleted_chunks} old chunks")
        
        # STEP 2: Update document status to processing
        cursor.execute("""
            UPDATE documents
            SET status = 'processing', chunk_count = 0, updated_at = NOW()
            WHERE id = %s
        """, (document_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # STEP 3: Delete old file from MinIO
        if old_file_path:
            try:
                async with httpx.AsyncClient() as client:
                    await client.delete(
                        f"{STORAGE_SERVICE_URL}/files",
                        params={"file_path": old_file_path},
                        timeout=10.0
                    )
                logger.info(f"✅ Deleted old file from MinIO")
            except Exception as e:
                logger.warning(f"⚠️  Could not delete old file: {e}")
        
        # STEP 4: Upload new file (same workflow as process_document)
        file_content = await file.read()
        file_size = len(file_content)
        
        logger.info(f"📤 Uploading new file to Storage-Service...")
        async with httpx.AsyncClient() as client:
            files = {'file': (file.filename, file_content, 'application/pdf')}
            params = {'document_id': document_id}
            
            resp = await client.post(
                f"{STORAGE_SERVICE_URL}/upload",
                files=files,
                params=params,
                timeout=30.0
            )
            
            if resp.status_code != 201:
                raise HTTPException(status_code=500, detail=f"Upload failed: {resp.text}")
            
            upload_result = resp.json()
            new_file_path = upload_result['file_path']
            logger.info(f"✅ Uploaded: {new_file_path}")
        
        # STEP 5: Extract text
        logger.info(f"📝 Extracting text...")
        async with httpx.AsyncClient() as client:
            files = {'file': (file.filename, file_content, 'application/pdf')}
            
            resp = await client.post(
                f"{STORAGE_SERVICE_URL}/extract-text",
                files=files,
                timeout=30.0
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Extraction failed: {resp.text}")
            
            extraction_result = resp.json()
            text = extraction_result['text']
            pages = extraction_result['pages']
            logger.info(f"✅ Extracted: {pages} pages")
        
        # STEP 6: Extract metadata
        logger.info(f"🔍 Extracting metadata...")
        metadata_dict = LegalMetadataExtractor.extract_all(text, pages=pages)
        
        # STEP 7: Chunk and embed
        logger.info(f"🧠 Creating chunks and embeddings...")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{EMBEDDING_SERVICE_URL}/chunk-and-embed",
                headers={"X-API-Key": os.getenv("ADMIN_API_KEY", "admin-secret-key-change-in-production")},
                json={
                    "text": text,
                    "document_id": document_id,
                    "metadata": {
                        "filename": file.filename,
                        "document_code": metadata_dict.get('document_code'),
                        "pages": pages
                    },
                    "add_overlap": True
                },
                timeout=60.0
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Embedding failed: {resp.text}")
            
            embedding_result = resp.json()
            chunks = embedding_result['chunks']
            logger.info(f"✅ Created {len(chunks)} chunks")
        
        # STEP 8: Insert new chunks
        logger.info(f"💾 Inserting chunks to database...")
        vectors = []
        for chunk in chunks:
            chunk_info = chunk.get("chunk_info", {})
            vectors.append({
                "document_id": document_id,
                "chunk_index": chunk_info.get("chunk_index", 0),
                "content": chunk_info.get("text", ""),
                "embedding": chunk.get("embedding", []),
                "metadata": {}
            })
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{VECTOR_SERVICE_URL}/insert-batch",
                json={"vectors": vectors},
                timeout=60.0
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Vector insertion failed: {resp.text}")
            
            vector_result = resp.json()
            new_chunk_count = vector_result.get('inserted', 0)
            logger.info(f"✅ Inserted {new_chunk_count} chunks")
        
        # STEP 9: Update document with new info
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        new_title = old_title if keep_title else file.filename
        
        cursor.execute("""
            UPDATE documents
            SET 
                title = %s,
                filename = %s,
                file_path = %s,
                file_size = %s,
                status = 'completed',
                chunk_count = %s,
                metadata = %s::jsonb,
                processed_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, title, chunk_count, updated_at;
        """, (
            new_title,
            file.filename,
            new_file_path,
            file_size,
            new_chunk_count,
            json.dumps(metadata_dict),
            document_id
        ))
        
        updated_doc = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Document replaced successfully: {old_chunks} → {new_chunk_count} chunks")
        
        return {
            "success": True,
            "message": f"Document replaced successfully",
            "document_id": document_id,
            "old_chunks_deleted": old_chunk_count,
            "new_chunks_created": new_chunk_count,
            "document": {
                "id": str(updated_doc['id']),
                "title": updated_doc['title'],
                "chunk_count": updated_doc['chunk_count'],
                "updated_at": updated_doc['updated_at'].isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to replace document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============= FORMS API =============

@app.get("/admin/documents/{document_id}/forms")
async def list_document_forms(document_id: str):
    """
    List all forms for a specific document
    
    Args:
        document_id: UUID of document
    
    Returns:
        List of forms with details
    """
    try:
        uuid.UUID(document_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid document_id UUID")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if document exists
        cursor.execute("SELECT id FROM documents WHERE id = %s", (document_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get forms (simplified - only 5 fields)
        cursor.execute("""
            SELECT 
                id,
                form_name,
                description,
                template_path,
                created_at,
                updated_at
            FROM forms
            WHERE document_id = %s
            ORDER BY created_at DESC
        """, (document_id,))
        
        forms = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "total": len(forms),
            "forms": [
                {
                    "id": str(form['id']),
                    "form_name": form['form_name'],
                    "description": form.get('description'),
                    "template_path": form.get('template_path'),
                    "created_at": form['created_at'].isoformat() if form.get('created_at') else None,
                    "updated_at": form['updated_at'].isoformat() if form.get('updated_at') else None
                }
                for form in forms
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list forms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/forms")
async def upload_form(
    document_id: str = Form(...),
    form_name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """
    Upload a form template file (PDF, DOCX, etc.)
    
    Args:
        document_id: UUID of parent document
        form_name: Display name
        description: Form description (optional)
        file: Template file (PDF, DOC, DOCX only)
    
    Returns:
        Created form info
    
    Path structure in MinIO:
        forms/{document_id}/{form_id}_{filename}
    """
    # Helper function: Sanitize filename
    def sanitize_filename(filename: str) -> str:
        """Remove special characters and limit length"""
        import re
        import os
        
        # Split name and extension
        name, ext = os.path.splitext(filename)
        
        # Remove special chars, keep alphanumeric and hyphens
        # Support Vietnamese characters (keep unicode letters)
        name = re.sub(r'[^\w\s-]', '', name, flags=re.UNICODE)
        
        # Replace spaces with underscores
        name = re.sub(r'\s+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        # Limit length (keep first 150 chars)
        name = name[:150] if len(name) > 150 else name
        
        # Fallback if name is empty
        if not name:
            name = "form"
        
        return f"{name}{ext.lower()}"
    
    # Validate UUID
    try:
        uuid.UUID(document_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid document_id UUID")
    
    # Validate file extension (PDF, DOC, DOCX only)
    allowed_extensions = {'.pdf', '.doc', '.docx'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Only PDF, DOC, DOCX allowed. Got: {file_ext}"
        )
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if document exists and get collection info
        cursor.execute("""
            SELECT d.id, d.title, c.name as collection_name
            FROM documents d
            JOIN collections c ON d.collection_id = c.id
            WHERE d.id = %s
        """, (document_id,))
        document = cursor.fetchone()
        
        if not document:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Upload file to storage-service
        # Path structure: forms/{document_id}/{form_id}_{sanitized_filename}
        form_id = str(uuid.uuid4())
        safe_filename = sanitize_filename(file.filename)
        storage_filename = f"{form_id}_{safe_filename}"
        storage_folder = f"forms/{document_id}"
        
        logger.info(f"📤 Uploading form: {file.filename} → {storage_filename}")
        
        file_content = await file.read()
        
        async with httpx.AsyncClient() as client:
            files_data = {"file": (storage_filename, file_content, file.content_type)}
            
            # Send folder as query param (storage-service expects it)
            resp = await client.post(
                f"{STORAGE_SERVICE_URL}/upload",
                params={"folder": storage_folder},  # Query param
                files=files_data,
                timeout=30.0
            )
            
            if resp.status_code not in [200, 201]:
                error_detail = resp.text
                logger.error(f"❌ Storage service error (status {resp.status_code}): {error_detail}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to upload form file to storage: {error_detail}"
                )
            
            storage_result = resp.json()
            file_path = storage_result.get('file_path')
            
            if not file_path:
                raise HTTPException(status_code=500, detail="Storage service did not return file path")
        
        # Insert form record (only 6 fields now)
        cursor.execute("""
            INSERT INTO forms (
                id, document_id, form_name, description, template_path
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, form_name, template_path, created_at
        """, (
            form_id, document_id, form_name, description, file_path
        ))
        
        form = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Form uploaded: {form_name} for document {document_id}")
        
        return {
            "success": True,
            "message": "Form uploaded successfully",
            "form": {
                "id": str(form['id']),
                "form_name": form['form_name'],
                "template_path": file_path,
                "created_at": form['created_at'].isoformat() if form.get('created_at') else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to upload form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/admin/forms/{form_id}")
async def delete_form(form_id: str):
    """
    Delete a form and its template file
    
    Args:
        form_id: UUID of form to delete
    
    Returns:
        Deletion confirmation
    """
    try:
        uuid.UUID(form_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid form_id UUID")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get form info before deletion
        cursor.execute("""
            SELECT id, form_name, template_path, document_id
            FROM forms
            WHERE id = %s
        """, (form_id,))
        
        form = cursor.fetchone()
        
        if not form:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Form not found")
        
        # Delete from database
        cursor.execute("DELETE FROM forms WHERE id = %s", (form_id,))
        
        # Log audit
        log_admin_action(
            cursor,
            action="delete",
            resource_type="form",
            resource_id=form_id,
            details={
                "form_name": form['form_name'],
                "document_id": str(form['document_id']),
                "template_path": form.get('template_path')
            }
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Delete file from storage
        file_deleted = False
        if form.get('template_path'):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.delete(
                        f"{STORAGE_SERVICE_URL}/files",
                        params={"file_path": form['template_path']},
                        timeout=10.0
                    )
                    
                    if resp.status_code == 200:
                        file_deleted = True
                        logger.info(f"✅ Deleted form file: {form['template_path']}")
            except Exception as e:
                logger.warning(f"⚠️  Could not delete form file: {e}")
        
        logger.info(f"✅ Deleted form: {form['form_name']}")
        
        return {
            "success": True,
            "message": f"Form '{form['form_name']}' deleted",
            "form_id": form_id,
            "file_deleted": file_deleted
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= ROOT ENDPOINT =============

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "admin-service",
        "version": "3.0.0",
        "status": "running",
        "description": "Complete document and collection management with CRUD operations",
        "endpoints": {
            "health": "GET /health",
            "collections_list": "GET /admin/collections",
            "collections_create": "POST /admin/collections",
            "collections_update": "PATCH /admin/collections/{id}",
            "collections_delete": "DELETE /admin/collections/{id}",
            "documents_list": "GET /admin/documents",
            "documents_detail": "GET /admin/documents/{id}",
            "documents_create": "POST /admin/process-document",
            "documents_update": "PATCH /admin/documents/{id}",
            "documents_delete": "DELETE /admin/documents/{id}",
            "documents_replace": "POST /admin/documents/{id}/replace",
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
