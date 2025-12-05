"""
Test admin-service hybrid form template workflow với document setup đầy đủ:
0. Create test document in DB
1. POST /admin/forms/process-template/detect → Get detected positions
2. Simulate admin selecting first 5 positions
3. POST /admin/forms/process-template/finalize → Create template with placeholders
4. Verify template was uploaded to MinIO and saved to DB
"""

import requests
import json
import time
import uuid
import psycopg2

ADMIN_URL = "http://localhost:8001"
FORM_FILE = "docs/thamkhao/form_thamkhao/hotich.docx"

# DB config
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'legalrag',
    'password': 'legalrag123',
    'database': 'legalrag'
}

# Generate test IDs
DOCUMENT_ID = str(uuid.uuid4())
FORM_NAME = "Mẫu Hộ Tịch Test"
DESCRIPTION = "Template tự động phát hiện và xác nhận"


def setup_test_document():
    """Create test document in DB"""
    print("\n" + "="*60)
    print("SETUP: CREATE TEST DOCUMENT")
    print("="*60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get first available collection or create a simple one
        cursor.execute("SELECT id FROM collections LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            collection_id = result[0]
            print(f"✅ Using existing collection: {collection_id}")
        else:
            # Create minimal collection
            cursor.execute("""
                INSERT INTO collections (id, name)
                VALUES (uuid_generate_v4(), 'Test Collection')
                RETURNING id
            """)
            collection_id = cursor.fetchone()[0]
            print(f"✅ Created new collection: {collection_id}")
        
        # Insert test document
        cursor.execute("""
            INSERT INTO documents (id, collection_id, title, filename, file_path)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            DOCUMENT_ID,
            collection_id,
            "Test Document for Form Template",
            "hotich.docx",
            f"test/{DOCUMENT_ID}/hotich.docx"
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Created test document: {DOCUMENT_ID}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test document: {e}")
        return False


def cleanup_test_data():
    """Delete test document and form from DB"""
    print("\n" + "="*60)
    print("CLEANUP: REMOVE TEST DATA")
    print("="*60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Delete forms first (foreign key)
        cursor.execute("DELETE FROM forms WHERE document_id = %s", (DOCUMENT_ID,))
        deleted_forms = cursor.rowcount
        
        # Delete document
        cursor.execute("DELETE FROM documents WHERE id = %s", (DOCUMENT_ID,))
        deleted_docs = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Deleted {deleted_forms} forms and {deleted_docs} documents")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False


def test_step1_detect():
    """Step 1: Detect positions"""
    print("\n" + "="*60)
    print("STEP 1: DETECT POSITIONS")
    print("="*60)
    
    with open(FORM_FILE, 'rb') as f:
        files = {'file': (FORM_FILE.split('/')[-1], f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        data = {
            'document_id': DOCUMENT_ID,
            'form_name': FORM_NAME
        }
        
        response = requests.post(
            f"{ADMIN_URL}/admin/forms/process-template/detect",
            files=files,
            data=data,
            timeout=30
        )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result['message']}")
        print(f"📊 Total Positions: {result['total_positions']}")
        print(f"\n📍 First 10 Detected Positions:")
        for pos in result['positions'][:10]:
            print(f"  [{pos['index']}] Paragraph {pos['paragraph_index']}: {pos['text'][:40]}...")
        
        return result
    else:
        print(f"❌ Error: {response.text}")
        return None


def test_step2_finalize(detect_result):
    """Step 2: Finalize template with selected positions"""
    print("\n" + "="*60)
    print("STEP 2: FINALIZE TEMPLATE")
    print("="*60)
    
    if not detect_result:
        print("❌ No detect result to finalize")
        return None
    
    # Simulate admin selecting first 5 positions
    total = detect_result['total_positions']
    selected = min(5, total)
    selected_indices = ','.join(str(i) for i in range(selected))
    
    print(f"🎯 Admin selected {selected} positions: {selected_indices}")
    
    with open(FORM_FILE, 'rb') as f:
        files = {'file': (FORM_FILE.split('/')[-1], f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        data = {
            'document_id': DOCUMENT_ID,
            'form_name': FORM_NAME,
            'description': DESCRIPTION,
            'selected_indices': selected_indices
        }
        
        response = requests.post(
            f"{ADMIN_URL}/admin/forms/process-template/finalize",
            files=files,
            data=data,
            timeout=30
        )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result['message']}")
        print(f"\n📝 Created Form:")
        print(f"  ID: {result['form']['id']}")
        print(f"  Name: {result['form']['form_name']}")
        print(f"  Template Path: {result['form']['template_path']}")
        print(f"  Placeholders: {result['form']['placeholders']}")
        print(f"  Created At: {result['form']['created_at']}")
        
        return result
    else:
        print(f"❌ Error: {response.text}")
        return None


def main():
    print("\n🚀 Testing Admin Form Template Hybrid Workflow (Full)")
    print(f"📄 File: {FORM_FILE}")
    print(f"🆔 Document ID: {DOCUMENT_ID}")
    
    # Setup
    if not setup_test_document():
        print("\n❌ Setup failed, aborting test")
        return
    
    # Wait for services
    print("\n⏳ Waiting for admin-service to be ready...")
    time.sleep(2)
    
    try:
        # Step 1: Detect
        detect_result = test_step1_detect()
        
        if detect_result:
            print("\n⏳ Waiting 2s before finalize...")
            time.sleep(2)
            
            # Step 2: Finalize
            finalize_result = test_step2_finalize(detect_result)
            
            if finalize_result:
                print("\n" + "="*60)
                print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
                print("="*60)
                print(f"✨ Template created with {len(finalize_result['form']['placeholders'])} placeholders")
                print(f"📦 Uploaded to MinIO: {finalize_result['form']['template_path']}")
                print(f"💾 Saved to PostgreSQL: {finalize_result['form']['id']}")
            else:
                print("\n❌ Finalize failed")
        else:
            print("\n❌ Detect failed")
    
    finally:
        # Cleanup
        print("\n⏳ Waiting 2s before cleanup...")
        time.sleep(2)
        cleanup_test_data()


if __name__ == "__main__":
    main()
