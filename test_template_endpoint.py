"""
Test script để kiểm tra template endpoint
"""
import requests
import sys

def test_template_endpoint():
    collection_id = "quy_trinh_cap_ho_tich_cap_xa"
    document_id = "DOC_001"
    
    # Test list templates
    list_url = f"http://localhost:8000/api/documents/{collection_id}/{document_id}/templates"
    print(f"Testing: {list_url}")
    
    try:
        response = requests.get(list_url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error listing templates: {e}")
    
    # Test get template
    get_url = f"http://localhost:8000/api/documents/{collection_id}/{document_id}/template"
    print(f"\nTesting: {get_url}")
    
    try:
        response = requests.get(get_url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Length: {len(response.content)} bytes")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error getting template: {e}")

if __name__ == "__main__":
    test_template_endpoint()
