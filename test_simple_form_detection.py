#!/usr/bin/env python3
"""
Test Simple Form Detection Service
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_simple_form_detection():
    """Test SimpleFormDetectionService"""
    print("🧪 Testing Simple Form Detection Service...")
    
    try:
        from app.services.simple_form_detection import SimpleFormDetectionService
        
        # Initialize service
        form_service = SimpleFormDetectionService()
        print("✅ SimpleFormDetectionService initialized")
        
        # Test với document đăng ký khai sinh
        collection_id = "quy_trinh_cap_ho_tich_cap_xa"
        document_title = "Đăng ký khai sinh"
        
        print(f"\n📋 Testing document: {document_title}")
        
        # Test check_document_has_form
        has_form = form_service.check_document_has_form(collection_id, document_title)
        print(f"✅ Document has form: {has_form}")
        
        if has_form:
            # Test get_form_files
            form_files = form_service.get_form_files(collection_id, document_title)
            print(f"📁 Form files found: {len(form_files)}")
            
            for form_file in form_files:
                print(f"  - {form_file.name} ({form_file.stat().st_size} bytes)")
                
                # Test generate download URL
                download_url = form_service.generate_form_download_url(collection_id, document_title, form_file)
                print(f"    Download URL: {download_url}")
        
        # Test with mock RAG response
        print(f"\n🔄 Testing enhance_rag_response_with_forms...")
        
        mock_rag_response = {
            "type": "answer",
            "answer": "Để đăng ký khai sinh, bạn cần chuẩn bị hồ sơ gồm...",
            "context_info": {
                "source_documents": ["01. Đăng ký khai sinh.json"],
                "source_collections": [collection_id]
            }
        }
        
        enhanced_response = form_service.enhance_rag_response_with_forms(mock_rag_response)
        
        # Check results
        form_attachments = enhanced_response.get("form_attachments", [])
        print(f"📎 Form attachments in response: {len(form_attachments)}")
        
        for form in form_attachments:
            print(f"  - Document: {form['document_title']}")
            print(f"    File: {form['form_filename']}")
            print(f"    URL: {form['form_url']}")
        
        # Check if answer was enhanced
        enhanced_answer = enhanced_response.get("answer", "")
        if "biểu mẫu" in enhanced_answer.lower():
            print("✅ Answer was enhanced with form reference")
        else:
            print("⚠️ Answer was not enhanced")
            
        print("\n✅ Simple Form Detection Service test completed!")
        
    except Exception as e:
        print(f"❌ Error testing Simple Form Detection Service: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API endpoints...")
    
    import requests
    
    # Test check has form
    url = "http://localhost:8000/api/documents/quy_trinh_cap_ho_tich_cap_xa/DOC_001/has-form"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"📊 Check has form - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ API test error: {e}")
    
    # Test form download
    download_url = "http://localhost:8000/api/documents/quy_trinh_cap_ho_tich_cap_xa/DOC_001/files/form/form_dang_ky_khai_sinh.doc"
    
    try:
        response = requests.get(download_url, timeout=10)
        print(f"📊 Form download - Status: {response.status_code}")
        
        if response.status_code == 200:
            content_length = len(response.content)
            print(f"✅ Form downloaded: {content_length} bytes")
        else:
            print(f"❌ Download error: {response.text}")
            
    except Exception as e:
        print(f"❌ Download test error: {e}")

def test_full_rag_integration():
    """Test full RAG với form detection"""
    print("\n🎯 Testing Full RAG Integration...")
    
    import requests
    
    url = "http://localhost:8000/api/v1/query"
    
    payload = {
        "query": "đăng ký khai sinh cần form gì",
        "session_id": None
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"📊 RAG Query - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Response Type: {data.get('type')}")
            
            if data.get('answer'):
                print(f"✅ Answer: {data['answer'][:200]}...")
            
            form_attachments = data.get('form_attachments', [])
            print(f"📎 Form Attachments: {len(form_attachments)}")
            
            for form in form_attachments:
                print(f"  - {form.get('document_title')}: {form.get('form_filename')}")
                
        else:
            print(f"❌ RAG Error: {response.text}")
            
    except Exception as e:
        print(f"❌ RAG Integration test error: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Simple Form Detection Tests")
    print("=" * 60)
    
    # Test 1: Simple Form Detection Service
    test_simple_form_detection()
    
    # Test 2: API Endpoints 
    test_api_endpoints()
    
    # Test 3: Full RAG Integration
    test_full_rag_integration()
    
    print("\n" + "=" * 60)
    print("✅ All Simple Form Detection Tests Complete!")

if __name__ == "__main__":
    main()
