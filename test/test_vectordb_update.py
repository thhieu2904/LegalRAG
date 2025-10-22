"""
Test VectorDB Update After JSON Edit
=====================================

Verifies that JSON content changes actually update VectorDB.

Test flow:
1. Get VectorDB timestamp BEFORE edit
2. Edit JSON content (add unique marker)
3. Save with rebuild
4. Wait for rebuild to complete
5. Get VectorDB timestamp AFTER edit
6. Query RAG with marker text
7. Verify response includes marker
"""

import requests
import time
from datetime import datetime
import subprocess

# Config
ADMIN_API = "http://localhost:8001"
RAG_API = "http://localhost:8000"
COLLECTION = "quy_trinh_cap_ho_tich_cap_xa"
DOC_ID = "DOC_001"

def get_vectordb_timestamp():
    """Get VectorDB file modification timestamp"""
    result = subprocess.run(
        ["docker", "exec", "legalrag-rag-service-dev", 
         "stat", "-c", "%y", "/app/data/vectordb/chroma.sqlite3"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def wait_for_rebuild(max_wait=30):
    """Wait for rebuild to complete"""
    print("\n⏳ Waiting for rebuild to complete...")
    start = time.time()
    
    while time.time() - start < max_wait:
        try:
            response = requests.get(
                f"{ADMIN_API}/api/collections/{COLLECTION}/documents/{DOC_ID}/json/rebuild/status"
            )
            
            if response.status_code == 200:
                data = response.json()
                status_data = data.get("data", {})
                status = status_data.get("status")
                progress = status_data.get("progress", 0)
                message = status_data.get("message", "")
                
                print(f"  Status: {status} | Progress: {progress}% | {message}")
                
                if status == "success":
                    print("✅ Rebuild completed!")
                    return True
                elif status == "error":
                    print(f"❌ Rebuild failed: {status_data.get('error')}")
                    return False
        except Exception as e:
            print(f"⚠️ Error checking status: {e}")
        
        time.sleep(1)
    
    print("⏰ Timeout waiting for rebuild")
    return False

def main():
    print("=" * 80)
    print("🧪 Testing VectorDB Update After JSON Edit")
    print("=" * 80)
    
    # Step 1: Get VectorDB timestamp BEFORE
    print("\n📸 Step 1: VectorDB timestamp BEFORE edit")
    timestamp_before = get_vectordb_timestamp()
    print(f"  Timestamp: {timestamp_before}")
    
    # Step 2: Get current JSON
    print("\n📥 Step 2: Getting current JSON...")
    response = requests.get(
        f"{ADMIN_API}/api/collections/{COLLECTION}/documents/{DOC_ID}/json"
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get JSON: {response.status_code}")
        return
    
    current_data = response.json()["data"]
    original_title = current_data.get("title", "")
    print(f"  Current title: {original_title}")
    
    # Step 3: Add unique test marker
    print("\n✏️ Step 3: Adding unique test marker...")
    test_marker = f"TEST_MARKER_{int(time.time())}"
    modified_data = current_data.copy()
    modified_data["title"] = f"{original_title} [{test_marker}]"
    
    print(f"  Marker: {test_marker}")
    print(f"  New title: {modified_data['title']}")
    
    # Step 4: Save with rebuild
    print("\n💾 Step 4: Saving with rebuild trigger...")
    response = requests.put(
        f"{ADMIN_API}/api/collections/{COLLECTION}/documents/{DOC_ID}/json",
        json={
            "data": modified_data,
            "trigger_rebuild": True
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to save: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    print(f"✅ Saved successfully")
    print(f"  Rebuild triggered: {result.get('rebuild_triggered')}")
    
    # Step 5: Wait for rebuild
    if not wait_for_rebuild():
        print("❌ Rebuild did not complete successfully")
        return
    
    # Step 6: Get VectorDB timestamp AFTER
    print("\n📸 Step 6: VectorDB timestamp AFTER edit")
    time.sleep(2)  # Extra delay to ensure file system sync
    timestamp_after = get_vectordb_timestamp()
    print(f"  Timestamp: {timestamp_after}")
    
    # Step 7: Compare timestamps
    print("\n🔍 Step 7: Comparing timestamps...")
    print(f"  BEFORE: {timestamp_before}")
    print(f"  AFTER:  {timestamp_after}")
    
    if timestamp_before == timestamp_after:
        print("❌ VectorDB NOT UPDATED - Timestamps are identical!")
        print("   This means rebuild did NOT update VectorDB chunks")
    else:
        print("✅ VectorDB UPDATED - Timestamps are different!")
        print("   Rebuild successfully updated VectorDB chunks")
    
    # Step 8: Query RAG with marker
    print(f"\n💬 Step 8: Querying RAG for marker '{test_marker}'...")
    response = requests.post(
        f"{RAG_API}/api/chat",
        json={
            "message": f"Tìm thông tin về {test_marker}",
            "session_id": "test_session"
        }
    )
    
    if response.status_code == 200:
        rag_response = response.json()
        answer = rag_response.get("answer", "")
        
        if test_marker in answer:
            print(f"✅ RAG found marker in response!")
            print(f"   Response includes: {test_marker}")
        else:
            print(f"⚠️ RAG did NOT find marker in response")
            print(f"   This might mean VectorDB chunks not used for this query")
    else:
        print(f"❌ RAG query failed: {response.status_code}")
    
    print("\n" + "=" * 80)
    print("🏁 Test completed!")
    print("=" * 80)

if __name__ == "__main__":
    main()
