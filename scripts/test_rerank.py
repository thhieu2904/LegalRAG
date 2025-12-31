"""
Test rerank service to see actual scores
"""
import requests

query = 'lệ phí đăng ký khai sinh là bao nhiêu'

# Simulate chunks from 2 documents
chunks = [
    # Doc 1: Đăng ký khai sinh thường
    'Miễn lệ phí đối với các trường hợp sau: Đăng ký hộ tịch cho người thuộc hộ nghèo; người cao tuổi; Đăng ký khai sinh, khai tử đúng hạn. Đối với trường hợp đăng ký khai sinh không đúng hạn nộp trực tiếp: 5.000 đồng; nộp trực tuyến 4.000 đồng',
    'Quy định thành phần hồ sơ, lệ phí (nếu có), trình tự đăng ký khai sinh',
    # Doc 2: Có yếu tố nước ngoài
    '50.000 đồng/trường hợp (nộp trực tiếp), 40.000 đồng/trường hợp (nộp trực tuyến). Miễn lệ phí đối với các trường hợp sau: Đăng ký hộ tịch cho người thuộc hộ nghèo',
    'Đăng ký khai sinh có yếu tố nước ngoài cho người đã có hồ sơ, giấy tờ cá nhân'
]

doc_ids = ['doc_normal', 'doc_normal', 'doc_nuocngoai', 'doc_nuocngoai']
doc_titles = [
    '01. Đăng ký khai sinh', 
    '01. Đăng ký khai sinh', 
    '10. Đăng ký khai sinh có yếu tố nước ngoài', 
    '10. Đăng ký khai sinh có yếu tố nước ngoài'
]

try:
    response = requests.post('http://localhost:8013/rerank', json={
        'query': query,
        'documents': chunks,
        'document_ids': doc_ids,
        'document_titles': doc_titles,
        'top_k': 4,
        'include_document_scores': True
    }, timeout=120)
    
    if response.status_code == 200:
        data = response.json()
        print('=== CHUNK SCORES ===')
        for r in data.get('results', []):
            idx = r['index']
            title_short = doc_titles[idx][:40]
            print(f"Chunk {idx} ({title_short}): {r['score']:.4f}")
        
        print('')
        print('=== DOCUMENT SCORES (from rerank) ===')
        for ds in data.get('document_scores', []):
            print(f"{ds['document_id']}: avg={ds['avg_score']:.4f}, max={ds['max_score']:.4f}")
        
        # Apply heuristics manually
        print('')
        print('=== AFTER HEURISTICS (20% penalty for "nước ngoài") ===')
        for ds in data.get('document_scores', []):
            score = ds['avg_score']
            if 'nuocngoai' in ds['document_id']:
                score -= 0.20
                print(f"{ds['document_id']}: {ds['avg_score']:.4f} - 0.20 = {score:.4f} (PENALIZED)")
            else:
                print(f"{ds['document_id']}: {score:.4f} (no penalty)")
                
        # Determine winner
        print('')
        scores_after = []
        for ds in data.get('document_scores', []):
            score = ds['avg_score']
            if 'nuocngoai' in ds['document_id']:
                score -= 0.20
            scores_after.append((ds['document_id'], score))
        
        scores_after.sort(key=lambda x: x[1], reverse=True)
        print(f"=== WINNER: {scores_after[0][0]} with score {scores_after[0][1]:.4f} ===")
        
    else:
        print(f'Error: {response.status_code} - {response.text}')
except Exception as e:
    print(f'Error: {e}')
