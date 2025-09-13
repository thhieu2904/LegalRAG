#!/usr/bin/env python3

import requests
import json

response = requests.post('http://localhost:8000/api/v1/query', json={
    'query': 'phí là bao nhiêu khi làm thủ tục',
    'session_id': 'direct-test-123',
    'force_collection': 'quy_trinh_cap_ho_tich_cap_xa',
    'force_document': 'DOC_011'
})

result = response.json()
print(f'Type: {result.get("type")}')
print(f'Answer: {len(result.get("answer", ""))} chars')
print(f'Time: {result.get("processing_time", 0):.3f}s')

if result.get('context_info'):
    print(f'Context: {json.dumps(result["context_info"], indent=2)}')
else:
    print('No context info')
    
print(f'\nFull response:')
print(json.dumps(result, indent=2, ensure_ascii=False))