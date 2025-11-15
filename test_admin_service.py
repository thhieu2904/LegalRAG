#!/usr/bin/env python3
"""
Test Admin-Service endpoint: POST /admin/process-document

This tests the simple synchronous orchestration:
1. Upload file to Storage-Service
2. Extract text from Storage-Service
3. Extract metadata locally in Admin-Service
4. Return all results
"""

import requests
import json

ADMIN_URL = "http://localhost:8002"
file_path = "docs/thamkhao/1. Thủ tục xác định cơ quan giải quyết bồi thường.pdf"

print("=" * 70)
print("TEST: Admin-Service /admin/process-document Endpoint")
print("=" * 70)

try:
    with open(file_path, 'rb') as f:
        files = {'file': f}
        params = {'document_id': 'test-doc-001'}
        
        print(f"\n📤 Sending request to {ADMIN_URL}/admin/process-document")
        print(f"📄 File: {file_path}")
        print(f"🆔 Document ID: test-doc-001")
        
        resp = requests.post(
            f"{ADMIN_URL}/admin/process-document",
            files=files,
            params=params,
            timeout=60
        )
        
        print(f"\n📊 Response Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            
            print("\n" + "=" * 70)
            print("✅ SUCCESS!")
            print("=" * 70)
            
            print(f"\n📋 File Information:")
            print(f"  File ID: {data['file_id']}")
            print(f"  File Path: {data['file_path']}")
            print(f"  File Size: {data['file_size']} bytes")
            
            print(f"\n📊 Text Statistics:")
            for key, value in data['text_stats'].items():
                print(f"  {key}: {value}")
            
            print(f"\n🔍 Extracted Metadata:")
            metadata = data['metadata']
            print(f"  Document Code: {metadata['document_code']}")
            print(f"  Dates: {metadata['dates']}")
            print(f"  Organizations: {metadata['organizations']}")
            print(f"  Sections: {metadata['sections']}")
            print(f"  Extraction Confidence: {metadata['extraction_confidence']:.2%}")
            
            print(f"\n📝 First 500 characters of text:")
            print(f"  {data['text'][:500]}...")
            
            print(f"\n✅ Message: {data['message']}")
            
        else:
            print(f"\n❌ Error: {resp.status_code}")
            print(f"Response: {resp.text}")

except FileNotFoundError:
    print(f"❌ File not found: {file_path}")
except requests.exceptions.ConnectionError:
    print(f"❌ Cannot connect to Admin Service at {ADMIN_URL}")
    print("   Make sure Admin-Service is running on port 8002")
except Exception as e:
    print(f"❌ Error: {e}")
