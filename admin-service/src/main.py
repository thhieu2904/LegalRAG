"""
Admin Service - Simple Document Processing Orchestrator
Synchronous, straightforward workflow:
1. Call Storage: Upload file
2. Call Storage: Extract text
3. Admin: Extract metadata locally
4. Return results

No async jobs, no complexity. Just orchestration.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import httpx
import re
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ============= CONFIG =============

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8001")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8002))

logger.info(f"📡 Storage Service URL: {STORAGE_SERVICE_URL}")

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


# ============= APP =============

app = FastAPI(
    title="Admin Service",
    description="Simple synchronous document processing orchestrator",
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
    document_id: str = "doc-001",
):
    """
    Process document: Upload → Extract text → Extract metadata
    
    Workflow (Synchronous, Simple):
    1. Upload file to Storage-Service → get file_path
    2. Extract text from Storage-Service → get raw text
    3. Extract metadata from text locally (Admin does this)
    4. Return everything
    
    Args:
        file: PDF file to process
        document_id: Optional document ID (default: doc-001)
    
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
        
        logger.info(f"📄 Processing: {file.filename}")
        
        file_content = await file.read()
        file_size = len(file_content)
        
        # ===== STEP 1: Upload to Storage-Service =====
        logger.info(f"📤 Step 1: Uploading to Storage-Service...")
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
                error_msg = resp.text
                logger.error(f"❌ Storage upload failed: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Storage upload failed: {error_msg}"
                )
            
            upload_result = resp.json()
            file_path = upload_result['file_path']
            logger.info(f"✅ Uploaded: {file_path}")
        
        # ===== STEP 2: Extract text from Storage-Service =====
        logger.info(f"📝 Step 2: Extracting text from Storage-Service...")
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
            
            logger.info(f"✅ Extracted: {pages} pages, {char_count} chars, {word_count} words")
        
        # ===== STEP 3: Extract metadata (Admin does this locally) =====
        logger.info(f"🔍 Step 3: Extracting metadata locally...")
        metadata_dict = LegalMetadataExtractor.extract_all(text, pages=pages)
        metadata = ExtractedMetadata(**metadata_dict)
        
        logger.info(f"✅ Metadata extracted:")
        logger.info(f"   - Document Code: {metadata.document_code}")
        logger.info(f"   - Dates: {metadata.dates}")
        logger.info(f"   - Organizations: {metadata.organizations}")
        logger.info(f"   - Sections: {metadata.sections}")
        logger.info(f"   - Confidence: {metadata.extraction_confidence:.2f}")
        
        # ===== RESULT =====
        logger.info(f"✅ Document processing complete!")
        
        return ProcessDocumentResponse(
            success=True,
            file_id=document_id,
            file_path=file_path,
            file_size=file_size,
            text=text,
            text_stats={
                "pages": pages,
                "characters": char_count,
                "words": word_count,
            },
            metadata=metadata,
            message=f"Successfully processed {file.filename}"
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
