#!/usr/bin/env python3
"""
Script kiểm tra đường dẫn và cấu trúc metadata trong vector database
"""

import requests
import json
import os
from pprint import pprint

def get_document_details(collection_name, document_id):
    """Lấy thông tin chi tiết về một document trong vector database"""
    print(f"🔍 Checking document: {document_id} in collection: {collection_name}")
    
    try:
        url = f"http://localhost:8000/api/v1/collections/{collection_name}/documents/{document_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n=== DOCUMENT DETAILS ===")
            print(f"ID: {result.get('id', 'Unknown')}")
            print(f"Title: {result.get('title', 'Unknown')}")
            
            # Kiểm tra metadata
            metadata = result.get('metadata', {})
            print("\n=== METADATA ===")
            for key, value in metadata.items():
                print(f"{key}: {value}")
            
            # Kiểm tra đường dẫn
            source_path = metadata.get('source', 'Unknown')
            print(f"\nSource path: {source_path}")
            
            # Kiểm tra liệu file thực sự tồn tại
            base_dir = "D:/Personal/LegalRAG_OCR/rag_service"
            absolute_path = os.path.join(base_dir, source_path)
            exists = os.path.exists(absolute_path)
            print(f"File exists: {exists}")
            
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def list_marriage_documents():
    """Tìm các document liên quan đến đăng ký kết hôn"""
    print("🔍 Searching for marriage registration documents")
    
    try:
        # Lấy tất cả collection
        collections_response = requests.get("http://localhost:8000/api/v1/collections", timeout=10)
        collections = collections_response.json().get('collections', [])
        
        marriage_docs = []
        
        # Tìm kiếm trong mỗi collection
        for collection in collections:
            collection_name = collection.get('name')
            
            # Lấy danh sách documents
            docs_url = f"http://localhost:8000/api/v1/collections/{collection_name}/documents"
            docs_response = requests.get(docs_url, timeout=10)
            
            if docs_response.status_code == 200:
                documents = docs_response.json().get('documents', [])
                
                # Lọc các document có tiêu đề liên quan đến kết hôn
                for doc in documents:
                    title = doc.get('title', '').lower()
                    if 'kết hôn' in title:
                        marriage_docs.append({
                            'collection': collection_name,
                            'id': doc.get('id'),
                            'title': doc.get('title')
                        })
        
        print(f"\nFound {len(marriage_docs)} documents related to marriage registration:")
        for i, doc in enumerate(marriage_docs):
            print(f"{i+1}. {doc['title']} (Collection: {doc['collection']}, ID: {doc['id']})")
        
        # Kiểm tra chi tiết của document đầu tiên nếu có
        if marriage_docs:
            first_doc = marriage_docs[0]
            print("\n" + "="*50 + "\n")
            get_document_details(first_doc['collection'], first_doc['id'])
        
        return marriage_docs
            
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    # Tìm kiếm các document liên quan đến đăng ký kết hôn
    marriage_docs = list_marriage_documents()
    
    # Nếu có document cụ thể, hãy kiểm tra chi tiết
    if marriage_docs:
        print("\n" + "="*50 + "\n")
        print("Checking additional document details...")
        
        # Kiểm tra document thứ hai nếu có
        if len(marriage_docs) > 1:
            second_doc = marriage_docs[1]
            get_document_details(second_doc['collection'], second_doc['id'])
