#!/usr/bin/env python3
"""
Test Script cho Form Integration Complete Pipeline
Kiểm tra toàn bộ flow từ RAG đến form attachment

Test flow:
1. Khởi tạo RAG service 
2. Test query về thủ tục có form (đăng ký khai sinh)
3. Kiểm tra form detection
4. Verify API response có form_attachments
5. Test form download endpoint
"""

import sys
import os
import requests
import json
import time
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_rag_query_with_forms():
    """Test RAG query về thủ tục có form"""
    print("\n🧪 Testing RAG Query with Form Detection...")
    
    # RAG endpoint
    url = "http://localhost:8000/api/v1/query"
    
    # Test query về đăng ký khai sinh (có form)
    test_query = "các mẫu kê khai Đo là những form như nào hả bạn có không Gửi cho mình với"
    
    payload = {
        "query": test_query,
        "session_id": None,
        "max_context_length": 8000,
        "use_ambiguous_detection": True,
        "use_full_document_expansion": True
    }
    
    print(f"📝 Query: {test_query}")
    print(f"🔗 URL: {url}")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Response Type: {data.get('type')}")
            
            # Check if answer exists
            if data.get('type') == 'answer' and data.get('answer'):
                print(f"✅ Answer: {data['answer'][:200]}...")
                
                # Check form attachments
                form_attachments = data.get('form_attachments', [])
                print(f"📎 Form Attachments Found: {len(form_attachments)}")
                
                if form_attachments:
                    print("\n📋 Form Attachment Details:")
                    for i, form in enumerate(form_attachments, 1):
                        print(f"  {i}. Document: {form.get('document_title')}")
                        print(f"     Form File: {form.get('form_filename')}")
                        print(f"     Download URL: {form.get('form_url')}")
                        print(f"     Collection: {form.get('collection_id')}")
                        print()
                    
                    # Test form download
                    test_form_download(form_attachments[0])
                else:
                    print("⚠️ No form attachments found in response")
                    
            elif data.get('type') == 'clarification_needed':
                print("🤔 Clarification needed - this is normal for ambiguous queries")
                
            else:
                print(f"❌ Unexpected response type or no answer: {data}")
                
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during RAG query test: {e}")

def test_form_download(form_attachment):
    """Test form download endpoint"""
    print(f"\n📥 Testing Form Download...")
    
    form_url = form_attachment.get('form_url')
    if not form_url:
        print("❌ No form URL found")
        return
        
    # Convert relative URL to full URL
    if form_url.startswith('/'):
        form_url = f"http://localhost:8000{form_url}"
    
    print(f"🔗 Download URL: {form_url}")
    
    try:
        response = requests.get(form_url, timeout=30)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_length = len(response.content)
            
            print(f"✅ Form downloaded successfully")
            print(f"📄 Content Type: {content_type}")
            print(f"📏 Content Length: {content_length} bytes")
            
            # Save to temp file for verification
            temp_file = Path("temp_form_download.dat")
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            print(f"💾 Saved to: {temp_file}")
            
            # Clean up
            temp_file.unlink()
            print("🧹 Cleaned up temp file")
            
        else:
            print(f"❌ Download failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during form download test: {e}")

def test_form_detection_service():
    """Test form detection service independently"""
    print("\n🔍 Testing Form Detection Service...")
    
    try:
        from app.services.form_detection_service import FormDetectionService
        
        # Initialize service
        form_service = FormDetectionService(migration_phase=1)
        print("✅ Form Detection Service initialized")
        
        # Test context extraction
        mock_context = {
            "source_documents": ["01. Đăng ký khai sinh.json"],
            "source_collections": ["quy_trinh_cap_ho_tich_cap_xa"]
        }
        
        documents = form_service.extract_documents_from_context(mock_context)
        print(f"📄 Extracted documents: {len(documents)}")
        
        for doc in documents:
            print(f"  - Title: {doc['title']}")
            print(f"    Collection: {doc['collection_id']}")
        
        # Test form detection
        mock_rag_response = {
            "type": "answer",
            "answer": "Test answer",
            "context_info": mock_context
        }
        
        enhanced_response = form_service.enhance_rag_response_with_forms(mock_rag_response)
        form_attachments = enhanced_response.get("form_attachments", [])
        
        print(f"📎 Form attachments detected: {len(form_attachments)}")
        for form in form_attachments:
            print(f"  - {form['document_title']}: {form['form_filename']}")
        
    except Exception as e:
        print(f"❌ Error testing form detection service: {e}")

def test_hybrid_document_service():
    """Test hybrid document service form methods"""
    print("\n🔧 Testing Hybrid Document Service...")
    
    try:
        from app.services.hybrid_document_service import HybridDocumentService
        
        # Initialize service
        hybrid_service = HybridDocumentService(migration_phase=1)
        print("✅ Hybrid Document Service initialized")
        
        # Test has_form_file
        collection_id = "quy_trinh_cap_ho_tich_cap_xa"
        document_title = "Đăng ký khai sinh"
        
        has_form = hybrid_service.has_form_file(collection_id, document_title)
        print(f"📋 Document '{document_title}' has form: {has_form}")
        
        if has_form:
            # Test get_form_file_path
            form_path = hybrid_service.get_form_file_path(collection_id, document_title)
            print(f"📁 Form path: {form_path}")
            
            if form_path and Path(form_path).exists():
                print(f"✅ Form file exists at: {form_path}")
                print(f"📏 File size: {Path(form_path).stat().st_size} bytes")
            else:
                print(f"❌ Form file not found at: {form_path}")
        
    except Exception as e:
        print(f"❌ Error testing hybrid document service: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Form Integration Complete Pipeline Test")
    print("=" * 60)
    
    # Test 1: Hybrid Document Service
    test_hybrid_document_service()
    
    # Test 2: Form Detection Service
    test_form_detection_service()
    
    # Test 3: RAG Query with Forms
    test_rag_query_with_forms()
    
    print("\n" + "=" * 60)
    print("✅ Form Integration Pipeline Test Complete!")

if __name__ == "__main__":
    main()
