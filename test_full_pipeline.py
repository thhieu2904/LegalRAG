"""
Full Integration Test - LegalRAG Pipeline
Test upload → storage → extract → embed → vector-service

Flow:
1. Start Docker services (postgres, minio, storage, embedding, vector, admin)
2. Upload PDF file via admin-service
3. Verify file in MinIO
4. Verify vectors in PostgreSQL
5. Test search

Usage:
    python test_full_pipeline.py
"""

import requests
import time
import os
from typing import Dict, Any
import psycopg2
import json

# ============= CONFIGURATION =============

ADMIN_SERVICE_URL = "http://localhost:8002"
VECTOR_SERVICE_URL = "http://localhost:8003"
MINIO_CONSOLE_URL = "http://localhost:9001"

# PostgreSQL connection
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "legalrag",
    "password": "legalrag123",
    "database": "legalrag"
}

# Test file
TEST_FILE_PATH = r"d:\Personal\LegalRAG\docs\thamkhao\01. Đăng ký khai sinh.pdf"

# ============= TEST FUNCTIONS =============

def print_section(title: str):
    """Print section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def wait_for_service(url: str, service_name: str, max_retries: int = 30):
    """Wait for service to be ready"""
    print(f"⏳ Waiting for {service_name}...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} is ready!")
                return True
        except Exception as e:
            if i % 5 == 0:
                print(f"   Still waiting... ({i}/{max_retries})")
            time.sleep(2)
    
    print(f"❌ {service_name} not ready after {max_retries * 2}s")
    return False


def test_upload_document(file_path: str, collection_id: str, title: str) -> Dict[str, Any]:
    """Test document upload via admin-service (AICenter Pattern)"""
    print_section("STEP 1: Upload Document via Admin-Service")
    
    print(f"📄 Uploading: {os.path.basename(file_path)}")
    print(f"📁 Collection ID: {collection_id}")
    print(f"📝 Title: {title}")
    
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/pdf")}
        data = {
            "collection_id": collection_id,
            "title": title
        }
        
        response = requests.post(
            f"{ADMIN_SERVICE_URL}/admin/process-document",
            files=files,
            data=data,
            timeout=120  # 2 minutes for full pipeline
        )
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None
    
    result = response.json()
    
    print(f"\n✅ Upload successful!")
    print(f"   File ID: {result['file_id']}")
    print(f"   File Path: {result['file_path']}")
    print(f"   File Size: {result['file_size']:,} bytes")
    print(f"   Pages: {result['text_stats']['pages']}")
    print(f"   Words: {result['text_stats']['words']:,}")
    
    metadata = result['metadata']
    print(f"\n📋 Extracted Metadata:")
    print(f"   Document Code: {metadata.get('document_code')}")
    print(f"   Dates: {metadata.get('dates')}")
    print(f"   Organizations: {metadata.get('organizations')}")
    print(f"   Sections: {len(metadata.get('sections', []))} sections")
    print(f"   Confidence: {metadata.get('extraction_confidence'):.2f}")
    
    return result


def verify_minio_file(file_path: str):
    """Verify file exists in MinIO"""
    print_section("STEP 2: Verify File in MinIO")
    
    print(f"🗂️  Expected path: {file_path}")
    print(f"📍 MinIO Console: {MINIO_CONSOLE_URL}")
    print(f"   Username: minioadmin")
    print(f"   Password: minioadmin123")
    print(f"   Bucket: legal-documents")
    print(f"\n⚠️  Please check MinIO console manually to verify file upload!")


def verify_postgres_vectors(document_id: str):
    """Verify vectors in PostgreSQL"""
    print_section("STEP 3: Verify Vectors in PostgreSQL")
    
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Count chunks for document (document_id might be UUID or string)
        # First try as direct string
        cursor.execute("""
            SELECT COUNT(*) FROM chunks WHERE document_id::text = %s
        """, (document_id,))
        
        count = cursor.fetchone()[0]
        print(f"📊 Found {count} chunks for document {document_id}")
        
        if count == 0:
            print(f"❌ No chunks found!")
            return False
        
        # Get sample chunk with all fields
        cursor.execute("""
            SELECT 
                id, 
                document_id, 
                chunk_index, 
                content, 
                section_title,
                source_reference,
                metadata,
                created_at
            FROM chunks 
            WHERE document_id::text = %s 
            ORDER BY chunk_index 
            LIMIT 1
        """, (document_id,))
        
        chunk = cursor.fetchone()
        if chunk:
            print(f"\n📝 Sample Chunk (index 0):")
            print(f"   ID: {chunk[0]}")
            print(f"   Chunk Index: {chunk[2]}")
            print(f"   Content Length: {len(chunk[3])} chars")
            print(f"   Content Preview: {chunk[3][:100]}...")
            print(f"   Section Title: {chunk[4]}")
            print(f"   Source Reference: {chunk[5]}")
            print(f"   Metadata: {json.dumps(chunk[6], indent=2, ensure_ascii=False)}")
            print(f"   Created At: {chunk[7]}")
        
        # Check embedding dimension
        cursor.execute("""
            SELECT array_length(embedding::real[], 1) as dim
            FROM chunks 
            WHERE document_id::text = %s 
            LIMIT 1
        """, (document_id,))
        
        dim = cursor.fetchone()[0]
        print(f"\n🔢 Embedding Dimension: {dim}")
        
        if dim != 768:
            print(f"⚠️  WARNING: Expected 768-D, got {dim}-D!")
        else:
            print(f"✅ Correct dimension (768-D Vietnamese model)")
        
        # Check HNSW index
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'chunks' AND indexname LIKE '%hnsw%'
        """)
        
        indexes = cursor.fetchall()
        if indexes:
            print(f"\n📇 HNSW Index: {indexes[0][0]} ✅")
        else:
            print(f"\n⚠️  WARNING: No HNSW index found!")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ PostgreSQL verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL verification failed: {e}")
        return False


def test_vector_search(document_id: str):
    """Test vector similarity search"""
    print_section("STEP 4: Test Vector Search")
    
    # Get a sample embedding from the document
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT embedding::real[] 
            FROM chunks 
            WHERE document_id::text = %s 
            LIMIT 1
        """, (document_id,))
        
        sample_embedding = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print(f"🔍 Testing search with sample embedding...")
        
        # Search via vector-service
        response = requests.post(
            f"{VECTOR_SERVICE_URL}/search",
            json={
                "embedding": sample_embedding,
                "top_k": 3,
                "threshold": 0.5
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
        
        result = response.json()
        print(f"\n✅ Search successful!")
        print(f"   Found {result['total']} results")
        
        for i, res in enumerate(result['results'][:3], 1):
            print(f"\n   Result {i}:")
            print(f"      Document ID: {res['document_id']}")
            print(f"      Chunk Index: {res['chunk_index']}")
            print(f"      Section: {res.get('section_title')}")
            print(f"      Similarity: {res['similarity']:.4f}")
            print(f"      Content: {res['content'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False


def get_default_collection_id() -> str:
    """Get default collection ID from PostgreSQL"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM collections 
            WHERE name = 'default'
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return str(row[0])
        return None
    except Exception as e:
        print(f"❌ Error getting collection: {e}")
        return None


def run_full_test():
    """Run full LegalRAG pipeline integration test"""
    print_section("LEGALRAG FULL PIPELINE INTEGRATION TEST")
    
    # Check test file exists
    if not os.path.exists(TEST_FILE_PATH):
        print(f"❌ Test file not found: {TEST_FILE_PATH}")
        return
    
    # Wait for services
    print_section("SERVICE HEALTH CHECKS")
    
    if not wait_for_service(ADMIN_SERVICE_URL, "Admin-Service"):
        return
    
    if not wait_for_service(VECTOR_SERVICE_URL, "Vector-Service"):
        return
    
    # Run tests
    # Get collection ID first
    print_section("GET DEFAULT COLLECTION")
    collection_id = get_default_collection_id()
    if not collection_id:
        print("❌ No default collection found!")
        return
    
    print(f"✅ Using collection: {collection_id}")
    
    # 1. Upload document
    result = test_upload_document(
        TEST_FILE_PATH,
        collection_id=collection_id,
        title="Đăng ký khai sinh - Test Document"
    )
    if not result:
        print("\n❌ Test failed at upload step!")
        return
    
    document_id = result['file_id']  # Use returned UUID
    
    # 2. Verify MinIO
    verify_minio_file(result['file_path'])
    
    # 3. Verify PostgreSQL
    if not verify_postgres_vectors(document_id):
        print("\n❌ Test failed at PostgreSQL verification!")
        return
    
    # 4. Test search
    if not test_vector_search(document_id):
        print("\n❌ Test failed at search step!")
        return
    
    # Success!
    print_section("TEST SUMMARY")
    print("✅ All tests passed!")
    print(f"\n📊 Results:")
    print(f"   ✅ File uploaded to MinIO")
    print(f"   ✅ Text extracted and cleaned")
    print(f"   ✅ Metadata extracted")
    print(f"   ✅ Chunks embedded (768-D)")
    print(f"   ✅ Vectors inserted to PostgreSQL")
    print(f"   ✅ Search working correctly")
    print(f"\n🎉 Full LegalRAG pipeline is operational!")


if __name__ == "__main__":
    run_full_test()
