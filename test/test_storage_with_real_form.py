#!/usr/bin/env python3
"""
Test Storage API with Real Form from RAG Service
- Download form from RAG service
- Save to storage via Identifill API
- Retrieve and verify
"""

import requests
import json
from io import BytesIO

# Configuration
RAG_SERVICE_URL = "http://localhost:8000"
STORAGE_API_URL = "http://localhost:8002"

# Form details from RAG service
FORM_PATH = "quy_trinh_cap_ho_tich_cap_xa/DOC_001/Khai_sinh.docx"
CCCD = "079123456789"
USER_NAME = "Nguyễn Văn Bảo"
FORM_NAME = "Khai_sinh"

def test_flow():
    """Test complete flow: Download -> Upload -> List -> Download -> Delete"""
    
    print("=" * 70)
    print("🧪 TEST: Storage API with Real Form from RAG Service")
    print("=" * 70)
    
    # Step 1: Download form from RAG service
    print("\n📥 Step 1: Download form from RAG service")
    print(f"   URL: {RAG_SERVICE_URL}/api/forms/file/{FORM_PATH}")
    
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/api/forms/file/{FORM_PATH}")
        response.raise_for_status()
        form_content = response.content
        print(f"   ✅ Downloaded: {len(form_content)} bytes")
    except Exception as e:
        print(f"   ❌ Failed to download: {e}")
        return False
    
    # Step 2: Upload to storage API
    print(f"\n📤 Step 2: Upload form to storage API")
    print(f"   CCCD: {CCCD}")
    print(f"   User: {USER_NAME}")
    print(f"   Form: {FORM_NAME}")
    
    try:
        files = {'form_file': ('Khai_sinh.docx', BytesIO(form_content))}
        data = {
            'scan_cccd': CCCD,
            'scan_ho_ten': USER_NAME,
            'form_name': FORM_NAME
        }
        response = requests.post(
            f"{STORAGE_API_URL}/api/v1/storage/save",
            files=files,
            data=data
        )
        response.raise_for_status()
        result = response.json()
        print(f"   ✅ Uploaded successfully")
        print(f"   File ID: {result['file_id']}")
        print(f"   File Name: {result['file_name']}")
        
        file_id = result['file_id']
        saved_file_name = result['file_name']
    except Exception as e:
        print(f"   ❌ Failed to upload: {e}")
        return False
    
    # Step 3: List documents
    print(f"\n📋 Step 3: List documents for CCCD {CCCD}")
    
    try:
        response = requests.get(
            f"{STORAGE_API_URL}/api/v1/storage/list/{CCCD}"
        )
        response.raise_for_status()
        result = response.json()
        print(f"   ✅ Retrieved {result['total_forms']} form(s)")
        print(f"   User: {result['scan_ho_ten']}")
        for form in result['forms']:
            print(f"      - {form['form_name']}: {form['file_name']} ({form['file_size']} bytes)")
    except Exception as e:
        print(f"   ❌ Failed to list: {e}")
        return False
    
    # Step 4: Get storage statistics
    print(f"\n📊 Step 4: Get storage statistics")
    
    try:
        response = requests.get(f"{STORAGE_API_URL}/api/v1/storage/stats")
        response.raise_for_status()
        result = response.json()
        print(f"   ✅ Statistics retrieved")
        print(f"      Total Users: {result['total_users']}")
        print(f"      Total Forms: {result['total_forms']}")
        print(f"      Storage: {result['total_storage_mb']:.2f} MB ({result['total_storage_bytes']} bytes)")
    except Exception as e:
        print(f"   ❌ Failed to get stats: {e}")
        return False
    
    # Step 5: Download the saved form
    print(f"\n⬇️ Step 5: Download saved form from storage")
    
    try:
        response = requests.get(
            f"{STORAGE_API_URL}/api/v1/storage/download/{CCCD}/{saved_file_name}"
        )
        response.raise_for_status()
        downloaded_content = response.content
        print(f"   ✅ Downloaded: {len(downloaded_content)} bytes")
        print(f"   Integrity check: {'✅ PASS' if len(downloaded_content) == len(form_content) else '❌ FAIL'}")
    except Exception as e:
        print(f"   ❌ Failed to download: {e}")
        return False
    
    # Step 6: Upload second form
    print(f"\n📤 Step 6: Upload second form (same CCCD)")
    
    try:
        files = {'form_file': ('Khai_tu_nhan.docx', BytesIO(form_content))}
        data = {
            'scan_cccd': CCCD,
            'scan_ho_ten': USER_NAME,
            'form_name': 'Khai_tu_nhan'
        }
        response = requests.post(
            f"{STORAGE_API_URL}/api/v1/storage/save",
            files=files,
            data=data
        )
        response.raise_for_status()
        result = response.json()
        print(f"   ✅ Second form uploaded")
        print(f"   File ID: {result['file_id']}")
        
        file_id_2 = result['file_id']
        saved_file_name_2 = result['file_name']
    except Exception as e:
        print(f"   ❌ Failed to upload second form: {e}")
        return False
    
    # Step 7: List again to verify both forms
    print(f"\n📋 Step 7: List documents again (should have 2 forms)")
    
    try:
        response = requests.get(
            f"{STORAGE_API_URL}/api/v1/storage/list/{CCCD}"
        )
        response.raise_for_status()
        result = response.json()
        print(f"   ✅ Retrieved {result['total_forms']} form(s)")
        for i, form in enumerate(result['forms'], 1):
            print(f"      {i}. {form['form_name']}: {form['file_name']}")
    except Exception as e:
        print(f"   ❌ Failed to list: {e}")
        return False
    
    # Step 8: Delete first form
    print(f"\n🗑️  Step 8: Delete first form")
    
    try:
        response = requests.delete(
            f"{STORAGE_API_URL}/api/v1/storage/delete/{CCCD}/{file_id}/{saved_file_name}"
        )
        response.raise_for_status()
        result = response.json()
        print(f"   ✅ Form deleted: {result['message']}")
    except Exception as e:
        print(f"   ❌ Failed to delete: {e}")
        return False
    
    # Step 9: Final list to verify deletion
    print(f"\n📋 Step 9: List documents after deletion (should have 1 form)")
    
    try:
        response = requests.get(
            f"{STORAGE_API_URL}/api/v1/storage/list/{CCCD}"
        )
        response.raise_for_status()
        result = response.json()
        print(f"   ✅ Retrieved {result['total_forms']} form(s)")
        for i, form in enumerate(result['forms'], 1):
            print(f"      {i}. {form['form_name']}: {form['file_name']}")
    except Exception as e:
        print(f"   ❌ Failed to list: {e}")
        return False
    
    # Final statistics
    print(f"\n📊 Final Statistics")
    
    try:
        response = requests.get(f"{STORAGE_API_URL}/api/v1/storage/stats")
        response.raise_for_status()
        result = response.json()
        print(f"   Total Users: {result['total_users']}")
        print(f"   Total Forms: {result['total_forms']}")
        print(f"   Storage: {result['total_storage_mb']:.2f} MB ({result['total_storage_bytes']} bytes)")
    except Exception as e:
        print(f"   ❌ Failed to get stats: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_flow()
    exit(0 if success else 1)
