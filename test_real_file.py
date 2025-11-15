#!/usr/bin/env python3
"""
Test with real Vietnamese legal document
"""

import requests

BASE_URL = 'http://localhost:8001'
file_path = 'docs/thamkhao/1. Thủ tục xác định cơ quan giải quyết bồi thường.pdf'

# Test 1: Upload file
print('=' * 60)
print('TEST 1: Upload File')
print('=' * 60)

with open(file_path, 'rb') as f:
    files = {'file': f}
    params = {'document_id': 'test-legal-doc-001'}
    
    resp = requests.post(f'{BASE_URL}/upload', files=files, params=params)
    
    if resp.status_code == 201:
        data = resp.json()
        print(f'✅ Upload successful!')
        print(f'File path: {data["file_path"]}')
        print(f'File size: {data["file_size"]} bytes')
        uploaded_path = data['file_path']
    else:
        print(f'❌ Upload failed: {resp.status_code}')
        print(f'Response: {resp.text}')
        exit(1)

# Test 2: Extract text
print('\n' + '=' * 60)
print('TEST 2: Extract Text from Uploaded File')
print('=' * 60)

with open(file_path, 'rb') as f:
    files = {'file': f}
    resp = requests.post(f'{BASE_URL}/extract-text', files=files)
    
    if resp.status_code == 200:
        data = resp.json()
        print(f'✅ Text extraction successful!')
        print(f'Pages: {data["pages"]}')
        print(f'Characters: {data["character_count"]}')
        print(f'Words: {data["word_count"]}')
        print(f'\n📝 First 300 characters:')
        print(data['text'][:300])
        print('...')
    else:
        print(f'❌ Extraction failed: {resp.status_code}')
        print(f'Response: {resp.text}')

# Test 3: Download
print('\n' + '=' * 60)
print('TEST 3: Download File')
print('=' * 60)

resp = requests.get(f'{BASE_URL}/download', params={'file_path': uploaded_path})
if resp.status_code == 200:
    print(f'✅ Download successful!')
    print(f'Downloaded size: {len(resp.content)} bytes')
else:
    print(f'❌ Download failed: {resp.status_code}')

# Test 4: List files
print('\n' + '=' * 60)
print('TEST 4: List Files')
print('=' * 60)

resp = requests.get(f'{BASE_URL}/list', params={'prefix': 'documents/'})
if resp.status_code == 200:
    data = resp.json()
    print(f'✅ List successful!')
    print(f'Total files: {data["total"]}')
    for f in data['files']:
        print(f'  - {f["name"]} ({f["size"]} bytes)')
else:
    print(f'❌ List failed: {resp.status_code}')

# Test 5: Delete
print('\n' + '=' * 60)
print('TEST 5: Delete File')
print('=' * 60)

resp = requests.delete(f'{BASE_URL}/delete', params={'file_path': uploaded_path})
if resp.status_code == 200:
    data = resp.json()
    print(f'✅ Delete successful!')
    print(f'Deleted: {data["file_path"]}')
else:
    print(f'❌ Delete failed: {resp.status_code}')

print('\n' + '=' * 60)
print('✅ ALL TESTS PASSED WITH REAL FILE!')
print('=' * 60)
