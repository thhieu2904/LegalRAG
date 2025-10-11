"""
📄 Test Document Preview Functionality
=======================================

Tests both DOC and JSON preview endpoints to ensure they work correctly.
"""

import requests
import json
from typing import Dict, Any

# API Base URLs
ADMIN_API = "http://localhost:8001/api"
RAG_API = "http://localhost:8000"

# Test data
COLLECTION = "quy_trinh_boi_thuong_nn"
DOC_ID = "DOC_001"

def test_docx_preview():
    """Test DOCX preview endpoint"""
    print("\n" + "="*60)
    print("🧪 TEST 1: DOCX Preview")
    print("="*60)
    
    url = f"{ADMIN_API}/collections/{COLLECTION}/documents/{DOC_ID}/preview/docx"
    print(f"📡 URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success')}")
            print(f"📄 Type: {data.get('type')}")
            print(f"🎨 Rendered by: {data.get('rendered_by')}")
            print(f"📝 HTML length: {len(data.get('html', ''))} chars")
            
            # Show first 200 chars of HTML
            html = data.get('html', '')
            print(f"\n📋 HTML Preview (first 200 chars):")
            print(html[:200])
            print("...")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_json_preview():
    """Test JSON preview endpoint"""
    print("\n" + "="*60)
    print("🧪 TEST 2: JSON Preview")
    print("="*60)
    
    url = f"{ADMIN_API}/collections/{COLLECTION}/documents/{DOC_ID}/preview/json"
    print(f"📡 URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success')}")
            print(f"📄 Type: {data.get('type')}")
            
            # Show JSON structure
            json_data = data.get('data', {})
            print(f"\n📋 JSON Keys: {list(json_data.keys())}")
            
            # Show sample data
            if 'title' in json_data:
                print(f"📌 Title: {json_data['title']}")
            if 'id' in json_data:
                print(f"🆔 ID: {json_data['id']}")
            if 'sections' in json_data:
                print(f"📑 Sections: {len(json_data['sections'])} items")
            
            # Pretty print JSON (first 500 chars)
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
            print(f"\n📋 JSON Preview (first 500 chars):")
            print(json_str[:500])
            print("...")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_rag_internal_endpoints():
    """Test RAG Service internal endpoints"""
    print("\n" + "="*60)
    print("🧪 TEST 3: RAG Internal Endpoints (Direct)")
    print("="*60)
    
    # Test DOCX file endpoint
    print("\n📄 Testing DOCX file endpoint...")
    url = f"{RAG_API}/internal/documents/collections/{COLLECTION}/documents/{DOC_ID}/file"
    print(f"📡 URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ DOCX file served: {len(response.content)} bytes")
            
            # Check file signature
            signature = response.content[:2]
            if signature == b'PK':
                print("📦 Format: .docx (Office 2007+ ZIP)")
            elif signature == b'\xD0\xCF':
                print("📦 Format: .doc (Office 97-2003 OLE2)")
            else:
                print(f"📦 Unknown format: {signature.hex()}")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test JSON endpoint
    print("\n📋 Testing JSON endpoint...")
    url = f"{RAG_API}/internal/documents/collections/{COLLECTION}/documents/{DOC_ID}/json"
    print(f"📡 URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ JSON served: {data.get('success')}")
            content = data.get('content', {})
            print(f"📋 Keys: {list(content.keys())}")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 Document Preview Tests")
    print("="*60)
    print(f"📍 Collection: {COLLECTION}")
    print(f"🆔 Document: {DOC_ID}")
    print(f"🔧 Admin API: {ADMIN_API}")
    print(f"🔧 RAG API: {RAG_API}")
    
    # Run tests
    results = {
        "DOCX Preview": test_docx_preview(),
        "JSON Preview": test_json_preview(),
    }
    
    # Test RAG direct endpoints
    test_rag_internal_endpoints()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED!")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
