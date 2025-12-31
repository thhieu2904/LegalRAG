"""
Script để lấy chunk_id thực từ database và cập nhật test_set.json
"""
import json
import subprocess
import re

def run_psql_query(query):
    """Chạy query PostgreSQL qua docker"""
    cmd = [
        'docker', 'exec', 'legalrag-postgres',
        'psql', '-U', 'legalrag', '-d', 'legalrag',
        '-t', '-A', '-F', '|',
        '-c', query
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return result.stdout.strip()

def get_all_documents():
    """Lấy danh sách documents"""
    query = "SELECT id, title FROM documents ORDER BY title;"
    output = run_psql_query(query)
    docs = {}
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 2:
                doc_id, title = parts[0], parts[1]
                docs[title.strip()] = doc_id.strip()
    return docs

def get_chunks_for_document(doc_id, doc_title):
    """Lấy chunks cho document"""
    query = f"""
    SELECT c.id, c.chunk_index, LEFT(c.content, 200) as preview 
    FROM chunks c 
    WHERE c.document_id = '{doc_id}' 
    ORDER BY c.chunk_index;
    """
    output = run_psql_query(query)
    chunks = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 3:
                chunk_id, chunk_index, preview = parts[0], parts[1], parts[2]
                chunks.append({
                    'chunk_id': chunk_id.strip(),
                    'chunk_index': int(chunk_index.strip()) if chunk_index.strip().isdigit() else 0,
                    'preview': preview.strip()[:100]
                })
    return chunks

def find_relevant_chunks(query_text, category, chunks):
    """
    Tìm chunks relevant dựa trên query và category.
    Đây là heuristic đơn giản - có thể cần điều chỉnh manual.
    """
    relevant = []
    query_lower = query_text.lower()
    
    # Keywords theo category
    category_keywords = {
        'ho-so': ['hồ sơ', 'giấy tờ', 'thành phần', 'bản sao', 'tờ khai', 'nộp'],
        'thoi-gian': ['thời hạn', 'thời gian', 'ngày', 'trong ngày', 'làm việc'],
        'le-phi': ['lệ phí', 'phí', 'miễn phí', 'đồng', 'tiền'],
        'dia-diem': ['ở đâu', 'địa điểm', 'ủy ban', 'cấp xã', 'cấp huyện', 'trung tâm'],
        'dieu-kien': ['điều kiện', 'yêu cầu', 'đủ điều kiện', 'được phép'],
        'thu-tuc': ['thủ tục', 'quy trình', 'bước', 'cách thức', 'trình tự']
    }
    
    keywords = category_keywords.get(category, [])
    
    for chunk in chunks:
        preview_lower = chunk['preview'].lower()
        
        # Kiểm tra keywords
        for kw in keywords:
            if kw in preview_lower:
                if chunk['chunk_id'] not in relevant:
                    relevant.append(chunk['chunk_id'])
                break
        
        # Luôn include chunk 0 (thường là thông tin chung)
        if chunk['chunk_index'] == 0 and len(relevant) < 3:
            if chunk['chunk_id'] not in relevant:
                relevant.append(chunk['chunk_id'])
    
    # Giới hạn 3 chunks relevant
    return relevant[:3]

def main():
    print("=" * 60)
    print("CẬP NHẬT CHUNK IDs TỪ DATABASE")
    print("=" * 60)
    
    # Load test_set.json
    with open('test_set.json', 'r', encoding='utf-8') as f:
        test_set = json.load(f)
    
    # Get all documents
    print("\n📚 Đang lấy danh sách documents...")
    docs = get_all_documents()
    print(f"   Tìm thấy {len(docs)} documents")
    
    # Process each query
    updated_count = 0
    for query in test_set['queries']:
        expected_doc = query.get('expected_document', '')
        query_text = query.get('query', '')
        category = query.get('category', 'other')
        
        print(f"\n[{query['id']}] {query_text[:50]}...")
        print(f"    Expected: {expected_doc}")
        
        # Find document in database
        doc_id = None
        for title, did in docs.items():
            if expected_doc.lower() in title.lower() or title.lower() in expected_doc.lower():
                doc_id = did
                print(f"    ✅ Found doc: {title} ({did[:8]}...)")
                break
        
        if not doc_id:
            print(f"    ❌ Document not found in database!")
            query['relevant_chunk_ids'] = []
            continue
        
        # Get chunks
        chunks = get_chunks_for_document(doc_id, expected_doc)
        print(f"    📄 {len(chunks)} chunks")
        
        # Find relevant chunks
        relevant = find_relevant_chunks(query_text, category, chunks)
        print(f"    🎯 Relevant chunks: {len(relevant)}")
        
        # Update query
        query['relevant_chunk_ids'] = relevant
        updated_count += 1
        
        # Show chunk previews
        for chunk in chunks[:3]:
            marker = "✓" if chunk['chunk_id'] in relevant else " "
            print(f"      [{marker}] {chunk['chunk_index']}: {chunk['preview'][:60]}...")
    
    # Save updated test_set
    with open('test_set.json', 'w', encoding='utf-8') as f:
        json.dump(test_set, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ Đã cập nhật {updated_count} queries")
    print("📁 Saved to test_set.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
