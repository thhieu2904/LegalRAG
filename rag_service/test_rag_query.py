#!/usr/bin/env python3
"""
Test script để kiểm tra việc sửa lỗi đường dẫn trong metadata
"""

import requests
import json
import sys

def test_query(query, session_id="test_session"):
    """Gửi truy vấn tới RAG service và hiển thị kết quả chi tiết"""
    print(f"🔍 Testing query: '{query}'")
    
    test_data = {
        'query': query,
        'session_id': session_id
    }
    
    try:
        response = requests.post('http://localhost:8000/api/v1/query', json=test_data, timeout=30)
        result = response.json()
        
        # Hiển thị thông tin về nguồn dữ liệu
        print("\n=== CONTEXT INFO ===")
        context_info = result.get('context_info', {})
        source_docs = context_info.get('source_documents', [])
        
        print(f"Context length: {context_info.get('context_length', 0)}")
        print(f"Nucleus chunks: {context_info.get('nucleus_chunks', 0)}")
        print(f"Number of source documents: {len(source_docs)}")
        
        if source_docs:
            print("\n=== SOURCE DOCUMENTS ===")
            for i, doc in enumerate(source_docs):
                print(f"Document {i+1}: {doc}")
        
        # Hiển thị thông tin về biểu mẫu đính kèm
        forms = result.get('forms', [])
        if forms:
            print("\n=== ATTACHED FORMS ===")
            for i, form in enumerate(forms):
                form_id = form.get('id', 'Unknown')
                form_name = form.get('name', 'Unknown')
                print(f"Form {i+1}: {form_name} (ID: {form_id})")
        else:
            print("\nNo forms attached")
        
        # Hiển thị câu trả lời
        print("\n=== ANSWER ===")
        print(result.get('answer', 'No answer provided'))
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Kiểm tra các truy vấn liên quan đến đăng ký kết hôn
    test_query("đăng ký kết hôn cần giấy tờ gì")
    print("\n" + "="*50 + "\n")
    test_query("quy trình đăng ký kết hôn như thế nào")
