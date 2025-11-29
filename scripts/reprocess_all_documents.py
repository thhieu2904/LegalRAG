"""
Reprocess ALL documents with IMPROVED cleaning logic:
1. Delete old chunks and vectors
2. Re-extract text from MinIO files
3. Clean with new form template removal
4. Chunk and create new embeddings
5. Insert new vectors

Usage:
    python scripts/reprocess_all_documents.py
    python scripts/reprocess_all_documents.py --dry-run  # Preview only
    python scripts/reprocess_all_documents.py --collection "quy_trinh_ho_tich"  # Specific collection
"""
import asyncio
import argparse
import httpx
import os
import sys
from datetime import datetime

# Add storage-service to path for direct cleaner usage
sys.path.insert(0, 'd:/Personal/LegalRAG/storage-service/src')

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


def get_all_collections():
    """Get all collections with document counts"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT c.id, c.name, c.display_name, COUNT(d.id) as doc_count
                FROM collections c
                LEFT JOIN documents d ON d.collection_id = c.id
                GROUP BY c.id, c.name, c.display_name
                ORDER BY c.display_name
            """)
            return cur.fetchall()
    finally:
        conn.close()


def get_documents_by_collection(collection_name: str = None):
    """Get all documents, optionally filtered by collection"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if collection_name:
                cur.execute("""
                    SELECT d.id, d.title, d.file_path, c.name as collection_name, c.display_name as collection_display
                    FROM documents d
                    JOIN collections c ON d.collection_id = c.id
                    WHERE d.file_path IS NOT NULL AND c.name = %s
                    ORDER BY c.display_name, d.title
                """, (collection_name,))
            else:
                cur.execute("""
                    SELECT d.id, d.title, d.file_path, c.name as collection_name, c.display_name as collection_display
                    FROM documents d
                    JOIN collections c ON d.collection_id = c.id
                    WHERE d.file_path IS NOT NULL
                    ORDER BY c.display_name, d.title
                """)
            return cur.fetchall()
    finally:
        conn.close()


def delete_document_chunks(doc_id: str) -> int:
    """Delete all chunks for a document from PostgreSQL, returns count deleted"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Table is named 'chunks' not 'document_chunks'
            cur.execute("DELETE FROM chunks WHERE document_id = %s", (doc_id,))
            deleted = cur.rowcount
            conn.commit()
            return deleted
    finally:
        conn.close()


def delete_document_vectors(doc_id: str) -> int:
    """Delete all vectors for a document - same as chunks table (vectors stored in chunks.embedding)"""
    # In this schema, vectors are stored in chunks table, not separate
    # This function is kept for compatibility but returns 0
    return 0


def update_document_chunk_count(doc_id: str, count: int):
    """Update document chunk_count in documents table"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET chunk_count = %s, updated_at = NOW() WHERE id = %s",
                (count, doc_id)
            )
            conn.commit()
    finally:
        conn.close()


def get_total_vectors_count():
    """Get total vectors in DB (same as chunks since vectors are in chunks.embedding)"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL")
            result = cur.fetchone()
            return result[0] if result else 0
    finally:
        conn.close()


def get_total_chunks_count():
    """Get total chunks in DB"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM chunks")
            result = cur.fetchone()
            return result[0] if result else 0
    finally:
        conn.close()


async def process_document(client: httpx.AsyncClient, doc: dict, dry_run: bool = False) -> dict:
    """Process single document: delete old → download → clean → chunk → embed → insert"""
    doc_id = doc['id']
    title = doc['title']
    file_path = doc['file_path']
    collection = doc.get('collection_display', doc.get('collection_name', 'unknown'))
    
    result = {
        "id": doc_id,
        "title": title,
        "collection": collection,
        "success": False,
        "old_chunks_deleted": 0,
        "old_vectors_deleted": 0,
        "new_chunks": 0,
        "text_reduction_pct": 0,
        "error": None
    }
    
    try:
        # Step 1: Delete old chunks and vectors
        if not dry_run:
            result["old_chunks_deleted"] = delete_document_chunks(doc_id)
            result["old_vectors_deleted"] = delete_document_vectors(doc_id)
            print(f"   🗑️  Deleted: {result['old_chunks_deleted']} chunks, {result['old_vectors_deleted']} vectors")
        else:
            print(f"   🗑️  [DRY-RUN] Would delete chunks and vectors")
        
        # Step 2: Download file from MinIO
        print(f"   📥 Downloading from MinIO...")
        try:
            response = minio_client.get_object(MINIO_BUCKET, file_path)
            file_content = response.read()
            response.close()
            response.release_conn()
        except Exception as e:
            result["error"] = f"minio_download: {e}"
            return result
        
        # Step 3: Extract and clean text via storage-service
        print(f"   📝 Extracting and cleaning text...")
        if not dry_run:
            files = {'file': (file_path.split('/')[-1], file_content, 'application/pdf')}
            resp = await client.post(
                f"{STORAGE_URL}/extract-text",
                files=files,
                params={"clean": True},  # Uses new cleaning with form removal!
                timeout=120.0
            )
            
            if resp.status_code != 200:
                result["error"] = f"extract_failed: {resp.status_code}"
                return result
            
            extract_data = resp.json()
            cleaned_text = extract_data.get("text", "")
            raw_length = extract_data.get("raw_length", len(cleaned_text))
            clean_length = len(cleaned_text)
            
            if raw_length > 0:
                result["text_reduction_pct"] = round((1 - clean_length/raw_length) * 100, 1)
            
            print(f"   ✅ Cleaned: {raw_length} → {clean_length} chars ({result['text_reduction_pct']}% reduction)")
            
            if not cleaned_text.strip():
                result["error"] = "empty_text_after_cleaning"
                return result
        else:
            print(f"   📝 [DRY-RUN] Would extract and clean text")
            cleaned_text = ""
        
        # Step 4: Chunk and embed via embedding-service
        print(f"   🔢 Creating chunks and embeddings...")
        if not dry_run:
            resp = await client.post(
                f"{EMBEDDING_URL}/chunk-and-embed",
                headers={"X-API-Key": ADMIN_API_KEY},
                json={
                    "text": cleaned_text,
                    "document_id": doc_id,
                    "metadata": {"title": title, "collection": collection},
                    "add_overlap": True
                },
                timeout=180.0
            )
            
            if resp.status_code != 200:
                result["error"] = f"embedding_failed: {resp.status_code}"
                return result
            
            embed_data = resp.json()
            chunks = embed_data.get("chunks", [])
            print(f"   ✅ Created {len(chunks)} chunks with embeddings")
        else:
            print(f"   🔢 [DRY-RUN] Would create chunks and embeddings")
            chunks = []
        
        # Step 5: Insert vectors via vector-service
        if not dry_run and chunks:
            print(f"   💾 Inserting vectors...")
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
                timeout=120.0
            )
            
            if resp.status_code != 200:
                result["error"] = f"insert_failed: {resp.status_code}"
                return result
            
            insert_data = resp.json()
            inserted = insert_data.get("inserted", 0)
            
            # Update document chunk count
            update_document_chunk_count(doc_id, inserted)
            
            result["new_chunks"] = inserted
            print(f"   ✅ Inserted {inserted} vectors")
        else:
            print(f"   💾 [DRY-RUN] Would insert vectors")
        
        result["success"] = True
        return result
        
    except Exception as e:
        result["error"] = str(e)
        return result


async def main():
    parser = argparse.ArgumentParser(description="Reprocess all documents with improved cleaning")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't make changes")
    parser.add_argument("--collection", type=str, help="Process only specific collection slug")
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔄 REPROCESS ALL DOCUMENTS - With Improved Form Template Removal")
    print("=" * 70)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.dry_run:
        print("⚠️  DRY-RUN MODE: No changes will be made")
    
    # Show collections overview
    print("\n📚 COLLECTIONS OVERVIEW:")
    print("-" * 50)
    collections = get_all_collections()
    for c in collections:
        marker = "→" if args.collection and c['name'] == args.collection else " "
        display = c.get('display_name', c['name'])
        print(f" {marker} {display}: {c['doc_count']} documents")
    
    # Get documents to process
    documents = get_documents_by_collection(args.collection)
    
    if not documents:
        print("\n❌ No documents found!")
        return
    
    print(f"\n📊 DOCUMENTS TO PROCESS: {len(documents)}")
    
    # Get current totals
    current_vectors = get_total_vectors_count()
    current_chunks = get_total_chunks_count()
    print(f"📦 Current vectors in DB: {current_vectors}")
    print(f"📦 Current chunks in DB: {current_chunks}")
    
    # Confirm before proceeding
    if not args.dry_run:
        print("\n" + "=" * 70)
        print("⚠️  WARNING: This will DELETE and RECREATE all chunks/vectors!")
        print("=" * 70)
        confirm = input("Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled by user")
            return
    
    # Process documents
    print("\n" + "=" * 70)
    print("🚀 PROCESSING DOCUMENTS")
    print("=" * 70)
    
    results = []
    async with httpx.AsyncClient() as client:
        for i, doc in enumerate(documents, 1):
            print(f"\n[{i}/{len(documents)}] 📄 {doc['title'][:50]}...")
            print(f"   📂 Collection: {doc['collection_name']}")
            result = await process_document(client, doc, args.dry_run)
            results.append(result)
            
            if result["success"]:
                print(f"   ✅ SUCCESS")
            else:
                print(f"   ❌ FAILED: {result['error']}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    success = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    total_old_chunks = sum(r.get("old_chunks_deleted", 0) for r in results)
    total_old_vectors = sum(r.get("old_vectors_deleted", 0) for r in results)
    total_new_chunks = sum(r.get("new_chunks", 0) for r in results)
    avg_reduction = sum(r.get("text_reduction_pct", 0) for r in success) / len(success) if success else 0
    
    print(f"\n✅ Successful: {len(success)}/{len(results)} documents")
    print(f"❌ Failed: {len(failed)}/{len(results)} documents")
    
    print(f"\n🗑️  Deleted: {total_old_chunks} chunks, {total_old_vectors} vectors")
    print(f"📦 Created: {total_new_chunks} new chunks/vectors")
    print(f"📉 Avg text reduction: {avg_reduction:.1f}%")
    
    if not args.dry_run:
        new_vectors = get_total_vectors_count()
        new_chunks = get_total_chunks_count()
        print(f"\n📊 New totals in DB:")
        print(f"   Vectors: {current_vectors} → {new_vectors}")
        print(f"   Chunks: {current_chunks} → {new_chunks}")
    
    if failed:
        print(f"\n❌ FAILED DOCUMENTS:")
        for r in failed:
            print(f"   - [{r['collection']}] {r['title'][:40]}...")
            print(f"     Error: {r['error']}")
    
    print(f"\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
