"""
Reprocess all documents: Download from MinIO → Extract text → Chunk with new chunker → Insert vectors
"""
import asyncio
import httpx
import os
import sys
from io import BytesIO

# Service URLs
STORAGE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8010")
EMBEDDING_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8011")
VECTOR_URL = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8012")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "admin-secret-key-change-in-production")

# MinIO config
from minio import Minio
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "legal-documents")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

# PostgreSQL
import psycopg2
from psycopg2.extras import RealDictCursor

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "legalrag")
POSTGRES_USER = os.getenv("POSTGRES_USER", "legalrag")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "legalrag123")


def get_db_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def get_all_documents():
    """Get all documents with their file paths"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, title, file_path 
                FROM documents 
                WHERE file_path IS NOT NULL
                ORDER BY created_at
            """)
            return cur.fetchall()
    finally:
        conn.close()


def update_chunk_count(doc_id: str, count: int):
    """Update document chunk count"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET chunk_count = %s WHERE id = %s",
                (count, doc_id)
            )
            conn.commit()
    finally:
        conn.close()


async def process_document(client: httpx.AsyncClient, doc: dict) -> dict:
    """Process single document: download → extract → chunk → insert"""
    doc_id = doc['id']
    title = doc['title']
    file_path = doc['file_path']
    
    print(f"\n📄 Processing: {title[:50]}...")
    
    try:
        # Step 1: Download file from MinIO
        print(f"   1️⃣ Downloading from MinIO: {file_path}...")
        try:
            response = minio_client.get_object(MINIO_BUCKET, file_path)
            file_content = response.read()
            response.close()
            response.release_conn()
        except Exception as e:
            print(f"   ❌ MinIO download failed: {e}")
            return {"id": doc_id, "success": False, "error": f"minio_failed: {e}"}
        
        print(f"   ✅ Downloaded {len(file_content)} bytes")
        
        # Step 2: Extract text via storage-service
        print(f"   2️⃣ Extracting text...")
        files = {'file': (file_path.split('/')[-1], file_content, 'application/pdf')}
        resp = await client.post(
            f"{STORAGE_URL}/extract-text",
            files=files,
            params={"clean": True},
            timeout=60.0
        )
        
        if resp.status_code != 200:
            print(f"   ❌ Extract failed: {resp.text}")
            return {"id": doc_id, "success": False, "error": "extract_failed"}
        
        extract_result = resp.json()
        text = extract_result.get("text", "")
        pages = extract_result.get("pages", 0)
        
        if not text.strip():
            print(f"   ⚠️ Empty text, skipping")
            return {"id": doc_id, "success": False, "error": "empty_text"}
        
        print(f"   ✅ Extracted: {pages} pages, {len(text)} chars")
        
        # Step 3: Chunk and embed
        print(f"   3️⃣ Chunking and embedding...")
        resp = await client.post(
            f"{EMBEDDING_URL}/chunk-and-embed",
            headers={"X-API-Key": ADMIN_API_KEY},
            json={
                "text": text,
                "document_id": doc_id,
                "metadata": {"title": title, "pages": pages},
                "add_overlap": True
            },
            timeout=120.0
        )
        
        if resp.status_code != 200:
            print(f"   ❌ Embedding failed: {resp.text}")
            return {"id": doc_id, "success": False, "error": "embedding_failed"}
        
        embedding_result = resp.json()
        chunks = embedding_result.get("chunks", [])
        print(f"   ✅ Created {len(chunks)} chunks")
        
        # Step 4: Insert vectors
        print(f"   4️⃣ Inserting to vector DB...")
        vectors = []
        for chunk in chunks:
            chunk_info = chunk.get("chunk_info", {})
            vectors.append({
                "document_id": doc_id,
                "chunk_index": chunk_info.get("chunk_index", 0),
                "content": chunk_info.get("text", ""),
                "embedding": chunk.get("embedding", []),
                "section_title": None,
                "source_reference": None,
                "token_count": chunk_info.get("tokens", 0),
                "metadata": {}
            })
        
        resp = await client.post(
            f"{VECTOR_URL}/insert-batch",
            json={"vectors": vectors},
            timeout=60.0
        )
        
        if resp.status_code != 200:
            print(f"   ❌ Insert failed: {resp.text}")
            return {"id": doc_id, "success": False, "error": "insert_failed"}
        
        insert_result = resp.json()
        inserted = insert_result.get("inserted", 0)
        
        # Step 5: Update chunk count
        update_chunk_count(doc_id, inserted)
        
        print(f"   ✅ Done! Inserted {inserted} chunks")
        return {"id": doc_id, "success": True, "chunks": inserted}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"id": doc_id, "success": False, "error": str(e)}


async def main():
    print("=" * 60)
    print("🔄 REPROCESS ALL DOCUMENTS")
    print("=" * 60)
    
    # Get all documents
    documents = get_all_documents()
    print(f"\n📊 Found {len(documents)} documents to process\n")
    
    if not documents:
        print("No documents found!")
        return
    
    # Process each document
    results = []
    async with httpx.AsyncClient() as client:
        for i, doc in enumerate(documents, 1):
            print(f"\n[{i}/{len(documents)}]", end="")
            result = await process_document(client, doc)
            results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    success = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    total_chunks = sum(r.get("chunks", 0) for r in success)
    
    print(f"✅ Success: {len(success)}/{len(results)} documents")
    print(f"📦 Total chunks: {total_chunks}")
    
    if failed:
        print(f"\n❌ Failed ({len(failed)}):")
        for r in failed:
            print(f"   - {r['id'][:8]}...: {r.get('error', 'unknown')}")


if __name__ == "__main__":
    asyncio.run(main())
