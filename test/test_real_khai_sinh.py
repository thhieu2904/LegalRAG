#!/usr/bin/env python3
"""
Clean Test: Only with Real Khai_sinh.docx from RAG Service
- Clean old test data
- Download real Khai_sinh.docx
- Run complete test flow
"""

import requests
import json
import sqlite3
import os
import shutil
from io import BytesIO
from pathlib import Path

# Configuration
RAG_SERVICE_URL = "http://localhost:8000"
STORAGE_API_URL = "http://localhost:8002"
DB_PATH = "d:\\Personal\\LegalRAG_OCR\\identifill_service\\data\\legalrag.db"
STORAGE_DIR = "d:\\Personal\\LegalRAG_OCR\\identifill_service\\data\\scanned_documents"

# Test data
FORM_PATH = "quy_trinh_cap_ho_tich_cap_xa/DOC_001/Khai_sinh.docx"
CCCD = "079987654321"  # Different from previous tests
USER_NAME = "Trần Thị Hà"
FORM_NAME = "Khai_sinh"

def cleanup_test_data():
    """Remove previous test data from database and filesystem"""
    print("🧹 Cleaning up previous test data...")
    
    try:
        # Clean database - remove entries for our test CCCD
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("DELETE FROM stored_forms WHERE file_id IN (SELECT file_id FROM stored_forms WHERE created_at > datetime('now', '-1 hour'))")
        db.commit()
        
        # Clean storage directory
        if os.path.exists(STORAGE_DIR):
            for cccd_dir in os.listdir(STORAGE_DIR):
                cccd_path = os.path.join(STORAGE_DIR, cccd_dir)
                if os.path.isdir(cccd_path):
                    shutil.rmtree(cccd_path)
        
        print("   ✅ Cleanup complete")
        db.close()
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")

def test_real_flow():
    """Test with real Khai_sinh.docx"""
    
    print("\n" + "=" * 80)
    print("🧪 CLEAN TEST: Real Khai_sinh.docx from RAG Service")
    print("=" * 80)
    
    # Step 1: Download form from RAG service
    print(f"\n📥 Step 1: Download Khai_sinh.docx from RAG Service")
    print(f"   URL: {RAG_SERVICE_URL}/api/forms/file/{FORM_PATH}")
    
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/api/forms/file/{FORM_PATH}")
        response.raise_for_status()
        form_content = response.content
        original_size = len(form_content)
        print(f"   ✅ Downloaded: {original_size} bytes")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Step 2: Save to storage
    print(f"\n💾 Step 2: Save form to storage API")
    print(f"   CCCD: {CCCD}")
    print(f"   User: {USER_NAME}")
    print(f"   Form Name: {FORM_NAME}")
    
    try:
        files = {'form_file': (f'{FORM_NAME}.docx', BytesIO(form_content))}
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
        
        file_id = result['file_id']
        saved_file_name = result['file_name']
        
        print(f"   ✅ Saved successfully")
        print(f"      File ID: {file_id}")
        print(f"      Stored as: {saved_file_name}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Step 3: Retrieve list
    print(f"\n📋 Step 3: Retrieve stored forms for CCCD {CCCD}")
    
    try:
        response = requests.get(f"{STORAGE_API_URL}/api/v1/storage/list/{CCCD}")
        response.raise_for_status()
        result = response.json()
        
        print(f"   ✅ Retrieved {result['total_forms']} form(s)")
        print(f"      User: {result['scan_ho_ten']}")
        
        for form in result['forms']:
            print(f"      📄 {form['form_name']}")
            print(f"         File: {form['file_name']}")
            print(f"         Size: {form['file_size']} bytes")
            print(f"         Created: {form['created_at']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Step 4: Download from storage
    print(f"\n⬇️  Step 4: Download form from storage")
    
    try:
        response = requests.get(
            f"{STORAGE_API_URL}/api/v1/storage/download/{CCCD}/{saved_file_name}"
        )
        response.raise_for_status()
        downloaded_content = response.content
        
        print(f"   ✅ Downloaded: {len(downloaded_content)} bytes")
        
        # Verify integrity
        if len(downloaded_content) == original_size:
            print(f"   ✅ Integrity check: PASS (size matches)")
        else:
            print(f"   ❌ Integrity check: FAIL (size mismatch: {original_size} vs {len(downloaded_content)})")
            return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Step 5: Get statistics
    print(f"\n📊 Step 5: Get storage statistics")
    
    try:
        response = requests.get(f"{STORAGE_API_URL}/api/v1/storage/stats")
        response.raise_for_status()
        result = response.json()
        
        print(f"   ✅ Statistics:")
        print(f"      Total Users: {result['total_users']}")
        print(f"      Total Forms: {result['total_forms']}")
        print(f"      Total Storage: {result['total_storage_mb']:.2f} MB ({result['total_storage_bytes']} bytes)")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Step 6: Verify file in filesystem
    print(f"\n🔍 Step 6: Verify file stored in filesystem")
    
    expected_path = os.path.join(STORAGE_DIR, CCCD, "forms", saved_file_name)
    
    try:
        if os.path.exists(expected_path):
            file_size = os.path.getsize(expected_path)
            print(f"   ✅ File exists at: {expected_path}")
            print(f"      Size: {file_size} bytes")
            
            if file_size == original_size:
                print(f"   ✅ File integrity verified")
            else:
                print(f"   ❌ File size mismatch")
                return False
        else:
            print(f"   ❌ File not found at: {expected_path}")
            return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Step 7: Verify in database
    print(f"\n🗄️  Step 7: Verify entry in database")
    
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        
        cursor.execute("SELECT * FROM stored_forms WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        
        if row:
            print(f"   ✅ Database entry found:")
            print(f"      File ID: {row['file_id']}")
            print(f"      Form Name: {row['form_name']}")
            print(f"      File Name: {row['file_name']}")
            print(f"      File Size: {row['file_size']} bytes")
            print(f"      Created: {row['created_at']}")
        else:
            print(f"   ❌ Database entry not found")
            return False
        
        db.close()
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Real Khai_sinh.docx Successfully Stored & Retrieved")
    print("=" * 80)
    return True

if __name__ == "__main__":
    cleanup_test_data()
    success = test_real_flow()
    exit(0 if success else 1)
