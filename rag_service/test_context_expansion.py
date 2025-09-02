#!/usr/bin/env python3
"""
Test script để kiểm tra chi tiết về context expansion và form detection
"""

import requests
import json
import sys
from pprint import pprint

def test_context_expansion(query, session_id="test_debug_context"):
    """Gửi truy vấn và kiểm tra chi tiết về context expansion"""
    print(f"🔍 Testing context expansion for: '{query}'")
    
    test_data = {
        'query': query,
        'session_id': session_id,
        'debug': True  # Yêu cầu thông tin debug chi tiết
    }
    
    try:
        response = requests.post('http://localhost:8000/api/v1/query', json=test_data, timeout=30)
        result = response.json()
        
        # Lấy thông tin chi tiết về context
        context_info = result.get('context_info', {})
        metadata = context_info.get('metadata', {})
        
        print("\n=== CONTEXT EXPANSION DETAILS ===")
        
        # Kiểm tra thông tin về document
        nucleus_chunks = context_info.get('nucleus_chunks', 0)
        print(f"Nucleus chunks: {nucleus_chunks}")
        
        if metadata:
            print("\n=== DOCUMENT METADATA ===")
            for key, value in metadata.items():
                if key == 'source_paths':
                    print("Source paths:")
                    for path in value:
                        print(f"  - {path}")
                else:
                    print(f"{key}: {value}")
        
        # Kiểm tra form detection
        forms = result.get('forms', [])
        if forms:
            print("\n=== FORM DETECTION DETAILS ===")
            for i, form in enumerate(forms):
                print(f"Form {i+1}:")
                for key, value in form.items():
                    print(f"  {key}: {value}")
        
        # Hiển thị câu trả lời
        print("\n=== ANSWER ===")
        print(result.get('answer', 'No answer provided'))
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_form_paths(query, session_id="test_form_paths"):
    """Kiểm tra chi tiết về đường dẫn của form trong RAG"""
    print(f"🔍 Testing form paths for: '{query}'")
    
    test_data = {
        'query': query,
        'session_id': session_id,
        'debug': True
    }
    
    try:
        response = requests.post('http://localhost:8000/api/v1/query', json=test_data, timeout=30)
        result = response.json()
        
        forms = result.get('forms', [])
        if forms:
            print("\n=== FORM PATHS DETAILS ===")
            for i, form in enumerate(forms):
                form_id = form.get('id', 'Unknown')
                form_path = form.get('path', 'Unknown')
                form_name = form.get('name', 'Unknown')
                print(f"Form {i+1}: {form_name}")
                print(f"  ID: {form_id}")
                print(f"  Path: {form_path}")
                print(f"  Exists: {form.get('exists', False)}")
        else:
            print("\nNo forms found")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Test các truy vấn liên quan đến đăng ký kết hôn
    test_context_expansion("thủ tục đăng ký kết hôn")
    print("\n" + "="*50 + "\n")
    test_form_paths("mẫu đơn đăng ký kết hôn")
