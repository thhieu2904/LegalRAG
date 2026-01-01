"""
Script để lấy chunk_id thực từ database và cập nhật test_set.json
Version 2: Cải thiện matching và tìm relevant chunks
"""
import json
import subprocess
import re

def run_psql_query(query):
    """Chạy query PostgreSQL qua docker"""
    cmd = [
        'docker', 'exec', 'legalrag-postgres',
        'psql', '-U', 'legalrag', '-d', 'legalrag',
        '-t', '-A', '-F', '||',  # Use double pipe as separator
        '-c', query
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return result.stdout.strip()

def get_all_documents():
    """Lấy danh sách documents với id"""
    query = "SELECT id, title FROM documents ORDER BY title;"
    output = run_psql_query(query)
    docs = {}
    for line in output.split('\n'):
        if '||' in line:
            parts = line.split('||')
            if len(parts) >= 2:
                doc_id, title = parts[0].strip(), parts[1].strip()
                docs[title] = doc_id
    return docs

def get_chunks_for_document(doc_id):
    """Lấy chunks cho document với content đầy đủ hơn"""
    query = f"""
    SELECT c.id, c.chunk_index, c.content
    FROM chunks c 
    WHERE c.document_id = '{doc_id}' 
    ORDER BY c.chunk_index;
    """
    output = run_psql_query(query)
    chunks = []
    for line in output.split('\n'):
        if '||' in line:
            parts = line.split('||', 2)  # Split into max 3 parts
            if len(parts) >= 3:
                chunk_id, chunk_index, content = parts[0].strip(), parts[1].strip(), parts[2].strip()
                chunks.append({
                    'chunk_id': chunk_id,
                    'chunk_index': int(chunk_index) if chunk_index.isdigit() else 0,
                    'content': content.replace('\n', ' ')[:500]  # First 500 chars
                })
    return chunks

def find_best_document_match(expected_doc, docs):
    """Tìm document match tốt nhất"""
    expected_lower = expected_doc.lower()
    
    # Exact match
    if expected_doc in docs:
        return expected_doc, docs[expected_doc]
    
    # Partial match
    for title, doc_id in docs.items():
        title_lower = title.lower()
        # Check if expected is substring of title or vice versa
        if expected_lower in title_lower or title_lower in expected_lower:
            return title, doc_id
        
        # Check key words match
        expected_words = set(expected_lower.split())
        title_words = set(title_lower.split())
        overlap = len(expected_words & title_words) / len(expected_words) if expected_words else 0
        if overlap > 0.7:
            return title, doc_id
    
    return None, None

def find_relevant_chunks_smart(query_text, category, chunks):
    """
    Tìm chunks relevant dựa trên nội dung query và category.
    Sử dụng keyword matching thông minh hơn.
    """
    query_lower = query_text.lower()
    relevant = []
    scores = []
    
    # Keywords theo category - mở rộng
    category_keywords = {
        'ho-so': ['hồ sơ', 'giấy tờ', 'thành phần', 'bản sao', 'tờ khai', 'nộp', 'đính kèm', 'cung cấp', 'xuất trình'],
        'thoi-gian': ['thời hạn', 'thời gian', 'ngày', 'trong ngày', 'làm việc', 'kể từ', 'sau khi'],
        'le-phi': ['lệ phí', 'phí', 'miễn phí', 'đồng', 'tiền', 'miễn lệ phí', 'chi phí'],
        'dia-diem': ['ở đâu', 'địa điểm', 'ủy ban', 'cấp xã', 'cấp huyện', 'trung tâm', 'nơi'],
        'dieu-kien': ['điều kiện', 'yêu cầu', 'đủ điều kiện', 'được phép', 'phải', 'cần'],
        'thu-tuc': ['thủ tục', 'quy trình', 'bước', 'cách thức', 'trình tự', 'thực hiện']
    }
    
    # Extract keywords from query
    query_keywords = []
    if 'giấy tờ' in query_lower or 'hồ sơ' in query_lower:
        query_keywords.extend(['hồ sơ', 'giấy tờ', 'thành phần', 'nộp'])
    if 'thời hạn' in query_lower or 'bao lâu' in query_lower:
        query_keywords.extend(['thời hạn', 'ngày', 'làm việc'])
    if 'lệ phí' in query_lower or 'bao nhiêu' in query_lower:
        query_keywords.extend(['lệ phí', 'phí', 'miễn', 'đồng'])
    if 'ở đâu' in query_lower or 'địa điểm' in query_lower:
        query_keywords.extend(['ủy ban', 'cấp xã', 'trung tâm'])
    if 'điều kiện' in query_lower:
        query_keywords.extend(['điều kiện', 'yêu cầu', 'phải'])
    if 'thủ tục' in query_lower or 'như thế nào' in query_lower:
        query_keywords.extend(['bước', 'trình tự', 'thực hiện'])
    
    # Add category keywords
    query_keywords.extend(category_keywords.get(category, []))
    query_keywords = list(set(query_keywords))
    
    # Score each chunk
    for chunk in chunks:
        content_lower = chunk['content'].lower()
        score = 0
        
        for kw in query_keywords:
            if kw in content_lower:
                score += 1
        
        # Soft bonus for intro chunk to keep when relevant, not forced
        if chunk['chunk_index'] == 0:
            score += 0.5
        
        scores.append((chunk['chunk_id'], score, chunk['chunk_index']))
    
    # Sort by score descending, then by chunk_index
    scores.sort(key=lambda x: (-x[1], x[2]))
    
    # Take top 3 with score > 0
    for chunk_id, score, idx in scores:
        if score > 0 and len(relevant) < 3:
            relevant.append(chunk_id)
    
    # Fallback: if nothing matched, use chunk 0 (overview) or first chunk
    if not relevant:
        for chunk in chunks:
            if chunk['chunk_index'] == 0:
                relevant.append(chunk['chunk_id'])
                break
    if not relevant and chunks:
        relevant.append(chunks[0]['chunk_id'])
    
    return relevant[:3]

def main():
    print("=" * 70)
    print("CẬP NHẬT CHUNK IDs TỪ DATABASE (VERSION 2)")
    print("=" * 70)
    
    # Load test_set.json
    with open('test_set.json', 'r', encoding='utf-8') as f:
        test_set = json.load(f)
    
    # Get all documents
    print("\n📚 Đang lấy danh sách documents từ database...")
    docs = get_all_documents()
    print(f"   Tìm thấy {len(docs)} documents:")
    for title in sorted(docs.keys()):
        print(f"   - {title}")
    
    print("\n" + "-" * 70)
    
    # Process each query
    updated_count = 0
    not_found = []
    
    # Handle both array format and dict with 'queries' key
    queries = test_set if isinstance(test_set, list) else test_set.get('queries', [])
    
    for query in queries:
        expected_doc = query.get('expected_document', '')
        query_text = query.get('query', '')
        category = query.get('category', 'other')
        
        print(f"\n[{query['id']:2d}] {query_text[:55]}...")
        print(f"     Expected: {expected_doc}")
        
        # Find best matching document
        actual_title, doc_id = find_best_document_match(expected_doc, docs)
        
        if not doc_id:
            print(f"     ❌ Document NOT FOUND!")
            query['relevant_chunk_ids'] = []
            not_found.append((query['id'], expected_doc))
            continue
        
        if actual_title != expected_doc:
            print(f"     🔄 Matched to: {actual_title}")
            query['expected_document'] = actual_title  # Update to actual title
        else:
            print(f"     ✅ Exact match")
        
        # Get chunks
        chunks = get_chunks_for_document(doc_id)
        print(f"     📄 {len(chunks)} chunks available")
        
        # Find relevant chunks
        relevant = find_relevant_chunks_smart(query_text, category, chunks)
        query['relevant_chunk_ids'] = relevant
        updated_count += 1
        
        print(f"     🎯 Selected {len(relevant)} relevant chunks:")
        for rid in relevant:
            for chunk in chunks:
                if chunk['chunk_id'] == rid:
                    preview = chunk['content'][:80].replace('\n', ' ')
                    print(f"        - [{chunk['chunk_index']}] {preview}...")
                    break
    
    # Save updated test_set
    with open('test_set.json', 'w', encoding='utf-8') as f:
        json.dump(test_set, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print(f"✅ Đã cập nhật {updated_count}/{len(queries)} queries")
    
    if not_found:
        print(f"\n⚠️  {len(not_found)} documents không tìm thấy:")
        for qid, title in not_found:
            print(f"   [{qid}] {title}")
    
    print("\n📁 Saved to test_set.json")
    print("=" * 70)

if __name__ == "__main__":
    main()
