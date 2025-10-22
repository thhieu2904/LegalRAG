"""
Test JSON Document Rebuild - Verify VectorDB Update
====================================================

Test workflow:
1. Get current JSON document
2. Modify a field (add timestamp to title)
3. Save with trigger_rebuild=True
4. Wait for rebuild to complete
5. Verify VectorDB timestamp updated
"""

import requests
import json
import time
from datetime import datetime

# Config
ADMIN_API = "http://localhost:8001"
COLLECTION = "quy_trinh_cap_ho_tich_cap_xa"
DOC_ID = "DOC_001"

def test_json_rebuild():
    print("=" * 80)
    print("🧪 Testing JSON Document Rebuild with VectorDB Update")
    print("=" * 80)
    
    # Step 1: Get current JSON
    print("\n📥 Step 1: Getting current JSON document...")
    response = requests.get(
        f"{ADMIN_API}/api/collections/{COLLECTION}/documents/{DOC_ID}/json"
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get JSON: {response.status_code}")
        print(response.text)
        return
    
    current_data = response.json()["data"]
    print(f"✅ Current title: {current_data.get('title', 'N/A')}")
    
    # Step 2: Modify data (add timestamp to title)
    print("\n✏️ Step 2: Modifying JSON data...")
    timestamp = datetime.now().strftime("%H:%M:%S")
    modified_data = current_data.copy()
    original_title = modified_data.get("title", "")
    modified_data["title"] = f"{original_title} [TEST {timestamp}]"
    
    print(f"📝 New title: {modified_data['title']}")
    
    # Step 3: Save with rebuild
    print("\n💾 Step 3: Saving with trigger_rebuild=True...")
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
    print(f"✅ Save result: {result.get('message')}")
    print(f"📦 Backup created: {result.get('backup_created')}")
    print(f"🔄 Rebuild triggered: {result.get('rebuild_triggered')}")
    
    # Step 4: Monitor rebuild status
    print("\n⏳ Step 4: Waiting for rebuild to complete...")
    max_wait = 60  # 60 seconds max
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        # Check rebuild status
        try:
            status_response = requests.get(
                f"{ADMIN_API}/api/rebuild/status"
            )
            
            if status_response.status_code == 200:
                status = status_response.json()
                current_status = status.get("status", "unknown")
                progress = status.get("progress", 0)
                message = status.get("message", "")
                
                print(f"📊 Status: {current_status} | Progress: {progress}% | {message}")
                
                if current_status == "success":
                    print("✅ Rebuild completed successfully!")
                    break
                elif current_status == "error":
                    print(f"❌ Rebuild failed: {message}")
                    return
        except Exception as e:
            print(f"⚠️ Could not check status: {e}")
        
        time.sleep(2)  # Check every 2 seconds
    
    # Step 5: Verify VectorDB updated
    print("\n🔍 Step 5: Verifying VectorDB timestamp...")
    print("Please manually check:")
    print("Run: docker exec legalrag-rag-service-dev sh -c \"ls -lh /app/data/vectordb/chroma.sqlite3\"")
    print(f"Expected: Timestamp should be AFTER {datetime.now().strftime('%H:%M:%S')}")
    
    print("\n" + "=" * 80)
    print("✅ Test completed! Please verify VectorDB timestamp manually.")
    print("=" * 80)

if __name__ == "__main__":
    test_json_rebuild()
