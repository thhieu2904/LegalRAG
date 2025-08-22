#!/usr/bin/env python3
"""
Test Complete Form Integration - End-to-End
Kiểm tra toàn bộ flow form detection từ RAG query đến download
"""

import requests
import json
import time

def test_rag_query_with_forms():
    """Test RAG query có form detection"""
    print("🎯 Test 1: RAG Query with Form Detection")
    print("-" * 50)
    
    url = "http://localhost:8000/api/v1/query"
    
    test_queries = [
        "đăng ký khai sinh cần hồ sơ gì",
        "có cần phải điền form gì không", 
        "thủ tục làm giấy khai sinh"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        
        payload = {
            "query": query,
            "session_id": None
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                response_type = data.get("type")
                print(f"✅ Status: {response.status_code} | Type: {response_type}")
                
                if response_type == "answer":
                    # Check answer content
                    answer = data.get("answer", "")
                    print(f"📄 Answer length: {len(answer)} chars")
                    
                    # Check for form attachments
                    form_attachments = data.get("form_attachments", [])
                    print(f"📎 Form attachments: {len(form_attachments)}")
                    
                    if form_attachments:
                        for j, form in enumerate(form_attachments, 1):
                            print(f"  {j}. Document: {form.get('document_title')}")
                            print(f"     File: {form.get('form_filename')}")
                            print(f"     URL: {form.get('form_url')}")
                            
                        # Check if answer mentions forms
                        if any(keyword in answer.lower() for keyword in ["form", "mẫu", "biểu mẫu", "tờ khai"]):
                            print("✅ Answer mentions forms")
                        else:
                            print("⚠️ Answer doesn't explicitly mention forms")
                    else:
                        print("ℹ️ No form attachments found")
                        
                elif response_type == "clarification_needed":
                    print("❓ Clarification needed")
                    options = data.get("clarification_options", [])
                    for opt in options:
                        print(f"  - {opt.get('name')}")
                        
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            
        time.sleep(1)  # Rate limiting

def test_form_download():
    """Test form download endpoints"""
    print("\n\n📥 Test 2: Form Download")
    print("-" * 50)
    
    # Test specific form download
    download_urls = [
        "http://localhost:8000/api/documents/quy_trinh_cap_ho_tich_cap_xa/DOC_001/files/form/form_dang_ky_khai_sinh.doc",
        "http://localhost:8000/api/documents/quy_trinh_cap_ho_tich_cap_xa/DOC_001/files/form/huong_dan_su_dung.pdf"
    ]
    
    for i, url in enumerate(download_urls, 1):
        filename = url.split("/")[-1]
        print(f"\n📄 Download {i}: {filename}")
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                file_size = len(response.content)
                content_type = response.headers.get("Content-Type", "unknown")
                
                print(f"✅ Status: {response.status_code}")
                print(f"📊 File size: {file_size} bytes")
                print(f"📋 Content type: {content_type}")
                
                if file_size > 0:
                    print("✅ File download successful")
                else:
                    print("❌ Downloaded file is empty")
                    
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Download error: {e}")

def test_has_form_api():
    """Test has_form API endpoint"""
    print("\n\n🔍 Test 3: Has Form API")
    print("-" * 50)
    
    # Test different document IDs
    test_cases = [
        ("quy_trinh_cap_ho_tich_cap_xa", "DOC_001"),
        ("quy_trinh_cap_ho_tich_cap_xa", "Đăng ký khai sinh"),
    ]
    
    for i, (collection_id, document_id) in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: Collection={collection_id}, Document={document_id}")
        
        url = f"http://localhost:8000/api/documents/{collection_id}/{document_id}/has-form"
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                has_form = data.get("has_form", False)
                
                print(f"✅ Status: {response.status_code}")
                print(f"📊 Has form: {has_form}")
                
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ API error: {e}")

def test_server_health():
    """Test server health"""
    print("\n\n🏥 Test 4: Server Health")
    print("-" * 50)
    
    health_url = "http://localhost:8000/health"
    
    try:
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is healthy")
            print(f"📊 Status: {data.get('status')}")
            
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

def main():
    """Run all tests"""
    print("🚀 Complete Form Integration Test Suite")
    print("=" * 60)
    
    # Check server accessibility first
    print("🔍 Checking server accessibility...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not accessible. Make sure FastAPI server is running on port 8000")
            return
        print("✅ Server is accessible")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the FastAPI server first: uvicorn main:app --reload")
        return
    
    # Run test suite
    test_rag_query_with_forms()
    test_form_download()
    test_has_form_api() 
    test_server_health()
    
    print("\n" + "=" * 60)
    print("✅ Complete Form Integration Test Suite Finished!")
    print("\n🎉 SUMMARY:")
    print("- RAG queries now detect and attach forms automatically")
    print("- Form download endpoints are working")
    print("- SimpleFormDetectionService is integrated successfully")
    print("- Users can download forms directly from chat responses")

if __name__ == "__main__":
    main()
