#!/usr/bin/env python3
"""
Test script for refactored Storage-Service (CRUD only)
Tests:
  1. Health check
  2. Upload file
  3. List files
  4. Download file
  5. Delete file
  6. Extract text
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8001"
TEST_FILE = "docs/thamkhao/1. Thủ tục xác định cơ quan giải quyết bồi thường.pdf"

def test_health():
    """Test 1: Health check"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    try:
        resp = requests.get(f"{BASE_URL}/health")
        data = resp.json()
        print(f"✅ Service status: {data['status']}")
        print(f"✅ Storage connected: {data['storage_connected']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_upload():
    """Test 2: Upload file"""
    print("\n" + "="*60)
    print("TEST 2: Upload File")
    print("="*60)
    try:
        if not Path(TEST_FILE).exists():
            print(f"❌ Test file not found: {TEST_FILE}")
            return None
        
        with open(TEST_FILE, 'rb') as f:
            file_size = Path(TEST_FILE).stat().st_size
            print(f"📄 File: {Path(TEST_FILE).name}")
            print(f"📊 Size: {file_size / 1024:.1f} KB")
            
            files = {'file': f}
            params = {'document_id': 'test-doc-001'}
            
            resp = requests.post(f"{BASE_URL}/upload", files=files, params=params)
            
            if resp.status_code == 201:
                data = resp.json()
                print(f"✅ Upload successful!")
                print(f"✅ File path: {data['file_path']}")
                return data['file_path']
            else:
                print(f"❌ Upload failed: {resp.status_code}")
                print(f"❌ Response: {resp.text}")
                return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def test_list(prefix="documents/"):
    """Test 3: List files"""
    print("\n" + "="*60)
    print("TEST 3: List Files")
    print("="*60)
    try:
        resp = requests.get(f"{BASE_URL}/list", params={'prefix': prefix})
        data = resp.json()
        
        print(f"✅ Total files: {data['total']}")
        if data['files']:
            print(f"✅ First file: {data['files'][0]['name']}")
        return True
    except Exception as e:
        print(f"❌ List failed: {e}")
        return False

def test_extract_text():
    """Test 4: Extract text from PDF"""
    print("\n" + "="*60)
    print("TEST 4: Extract Text from PDF")
    print("="*60)
    try:
        if not Path(TEST_FILE).exists():
            print(f"❌ Test file not found: {TEST_FILE}")
            return False
        
        with open(TEST_FILE, 'rb') as f:
            files = {'file': f}
            resp = requests.post(f"{BASE_URL}/extract-text", files=files)
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ Text extraction successful!")
                print(f"✅ Pages: {data['pages']}")
                print(f"✅ Characters: {data['character_count']}")
                print(f"✅ Words: {data['word_count']}")
                print(f"📝 First 200 chars: {data['text'][:200]}...")
                return True
            else:
                print(f"❌ Extraction failed: {resp.status_code}")
                print(f"❌ Response: {resp.text}")
                return False
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return False

def test_download(file_path):
    """Test 5: Download file"""
    print("\n" + "="*60)
    print("TEST 5: Download File")
    print("="*60)
    if not file_path:
        print("⏭️  Skipping (no file path from upload)")
        return False
    
    try:
        resp = requests.get(f"{BASE_URL}/download", params={'file_path': file_path})
        
        if resp.status_code == 200:
            print(f"✅ Download successful!")
            print(f"✅ File size: {len(resp.content)} bytes")
            return True
        else:
            print(f"❌ Download failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False

def test_delete(file_path):
    """Test 6: Delete file"""
    print("\n" + "="*60)
    print("TEST 6: Delete File")
    print("="*60)
    if not file_path:
        print("⏭️  Skipping (no file path to delete)")
        return False
    
    try:
        resp = requests.delete(f"{BASE_URL}/delete", params={'file_path': file_path})
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Delete successful!")
            print(f"✅ Message: {data['message']}")
            return True
        else:
            print(f"❌ Delete failed: {resp.status_code}")
            print(f"❌ Response: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return False

def main():
    print("\n" + "🔧"*30)
    print("    REFACTORED STORAGE-SERVICE TEST")
    print("    Simple CRUD API")
    print("🔧"*30)
    
    results = {}
    
    # Test 1
    results['health'] = test_health()
    if not results['health']:
        print("\n❌ Service not responding. Exiting.")
        return
    
    # Test 2
    file_path = test_upload()
    results['upload'] = file_path is not None
    
    # Test 3
    results['list'] = test_list()
    
    # Test 4
    results['extract_text'] = test_extract_text()
    
    # Test 5
    results['download'] = test_download(file_path)
    
    # Test 6 (DELETE LAST!)
    results['delete'] = test_delete(file_path)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8} {test_name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED! Storage-Service is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")

if __name__ == "__main__":
    main()
