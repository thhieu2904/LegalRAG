#!/usr/bin/env python3
"""
Test script để debug vấn đề routing sai DOC_008 thay vì DOC_002
"""

import sys
import os
from pathlib import Path

# Add rag_service directory to path
rag_service_path = str(Path(__file__).parent.parent / "rag_service")
sys.path.append(rag_service_path)

import requests
import json

def test_routing_debug():
    """Test routing với query về khai sinh có yếu tố nước ngoài"""
    
    query = "đăng ký khai sinh mà có mẹ là người nước ngoài thì cần giấy tờ gì"
    
    print("🔍 TESTING ROUTING DEBUG")
    print(f"📝 Query: {query}")
    print("=" * 80)
    
    test_data = {
        'query': query,
        'session_id': 'debug_session'
    }
    
    try:
        response = requests.post('http://localhost:8000/api/v1/query', json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ SUCCESS - Response received")
            print("=" * 50)
            
            # Debug routing info
            if 'routing_info' in result:
                routing = result['routing_info']
                print("🎯 ROUTING INFO:")
                print(f"  - Collection: {routing.get('collection', 'N/A')}")
                print(f"  - Confidence: {routing.get('confidence', 'N/A')}")
                print(f"  - Winner Document: {routing.get('winner_document', 'N/A')}")
                print(f"  - Winner Question: {routing.get('winner_question', 'N/A')}")
            
            # Debug context info
            if 'context_info' in result:
                context = result['context_info']
                print("\n📄 CONTEXT INFO:")
                print(f"  - Strategy: {context.get('strategy', 'N/A')}")
                print(f"  - Total chars: {context.get('total_chars', 'N/A')}")
                print(f"  - Documents: {len(context.get('source_documents', []))}")
                
                # Show source documents
                for i, doc in enumerate(context.get('source_documents', [])):
                    print(f"  - Document {i+1}: {Path(doc).name}")
                    
            # Debug form attachments
            if 'form_attachments' in result:
                forms = result['form_attachments']
                print(f"\n📎 FORM ATTACHMENTS: {len(forms)} files")
                for form in forms:
                    print(f"  - {form.get('filename', 'Unknown')}")
            
            # Show answer preview
            answer = result.get('answer', '')
            print(f"\n💬 ANSWER PREVIEW:")
            print(f"  {answer[:200]}...")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

def test_documents_comparison():
    """So sánh nội dung DOC_002 vs DOC_008"""
    
    print("\n🔍 COMPARING DOC_002 vs DOC_008")
    print("=" * 80)
    
    # Read DOC_002
    doc_002_path = Path(__file__).parent.parent / "rag_service/data/storage/collections/quy_trinh_cap_ho_tich_cap_xa/documents/DOC_002/02. ĐKKS có yếu tố nước ngoài.json"
    doc_008_path = Path(__file__).parent.parent / "rag_service/data/storage/collections/quy_trinh_cap_ho_tich_cap_xa/documents/DOC_008/08. Đăng ký khai sinh kết hợp đăng ký nhận cha, mẹ, con có yếu tố nước ngoài.json"
    
    if doc_002_path.exists():
        with open(doc_002_path, 'r', encoding='utf-8') as f:
            doc_002 = json.load(f)
        print("📄 DOC_002:")
        print(f"  - Title: {doc_002.get('title', 'N/A')}")
        print(f"  - Code: {doc_002.get('code', 'N/A')}")
        print(f"  - Content chunks: {len(doc_002.get('content_chunks', []))}")
        
        # Show content preview
        if 'content_chunks' in doc_002 and doc_002['content_chunks']:
            first_chunk = doc_002['content_chunks'][0]
            if isinstance(first_chunk, str):
                print(f"  - First chunk: {first_chunk[:150]}...")
            else:
                print(f"  - First chunk: {str(first_chunk)[:150]}...")
    else:
        print("❌ DOC_002 not found")
    
    if doc_008_path.exists():
        with open(doc_008_path, 'r', encoding='utf-8') as f:
            doc_008 = json.load(f)
        print("\n📄 DOC_008:")
        print(f"  - Title: {doc_008.get('title', 'N/A')}")
        print(f"  - Code: {doc_008.get('code', 'N/A')}")
        print(f"  - Content chunks: {len(doc_008.get('content_chunks', []))}")
        
        # Show content preview
        if 'content_chunks' in doc_008 and doc_008['content_chunks']:
            first_chunk = doc_008['content_chunks'][0]
            if isinstance(first_chunk, str):
                print(f"  - First chunk: {first_chunk[:150]}...")
            else:
                print(f"  - First chunk: {str(first_chunk)[:150]}...")
    else:
        print("❌ DOC_008 not found")

if __name__ == "__main__":
    test_documents_comparison()
    print("\n" + "="*80)
    test_routing_debug()
