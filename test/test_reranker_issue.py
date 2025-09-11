#!/usr/bin/env python3
"""
Test script để debug vấn đề reranker score thấp
"""

import sys
import os
from pathlib import Path

# Add rag_service directory to path
rag_service_path = str(Path(__file__).parent.parent / "rag_service")
sys.path.append(rag_service_path)

from app.services.reranker import RerankerService

def test_reranker_debug():
    """Test reranker với query có vấn đề"""
    
    print("🔍 TESTING RERANKER DEBUG")
    print("=" * 80)
    
    # Initialize reranker service
    reranker = RerankerService()
    
    query = "đăng ký khai sinh mà có mẹ là người nước ngoài thì cần giấy tờ gì"
    
    # Sample documents (simplified)
    documents = [
        "Thành phần hồ sơ đăng ký khai sinh có yếu tố nước ngoài: Tờ khai đăng ký khai sinh, Giấy chứng sinh, Văn bản thỏa thuận về quốc tịch, Giấy tờ chứng minh nhập cảnh hợp pháp",
        "Đăng ký kết hôn cần chuẩn bị: Đơn đăng ký kết hôn, Căn cước công dân, Giấy xác nhận tình trạng hôn nhân",
        "Thủ tục đăng ký khai sinh kết hợp nhận cha mẹ con có yếu tố nước ngoài: Đơn đăng ký, Giấy tờ chứng minh quan hệ cha con, Hộ chiếu"
    ]
    
    print(f"📝 Query: {query}")
    print(f"📄 Testing {len(documents)} documents")
    print("-" * 50)
    
    try:
        # Test reranking
        scores = reranker.rerank_documents(query, documents)
        
        print("📊 RERANK RESULTS:")
        for i, (doc, score) in enumerate(zip(documents, scores)):
            print(f"  Doc {i+1}: Score = {score:.4f}")
            print(f"    Content: {doc[:100]}...")
            print()
        
        # Analyze scores
        max_score = max(scores)
        min_score = min(scores)
        avg_score = sum(scores) / len(scores)
        
        print("📈 SCORE ANALYSIS:")
        print(f"  - Max score: {max_score:.4f}")
        print(f"  - Min score: {min_score:.4f}")
        print(f"  - Avg score: {avg_score:.4f}")
        print(f"  - Score range: {max_score - min_score:.4f}")
        
        if max_score < 0.1:
            print("⚠️  ALL SCORES ARE LOW - Possible reranker issue")
        elif max_score < 0.3:
            print("⚠️  LOW SCORES - May need score threshold adjustment")
        else:
            print("✅ GOOD SCORES - Reranker working properly")
            
    except Exception as e:
        print(f"❌ RERANKER ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_embedding_similarity():
    """Test embedding similarity for the same query"""
    
    print("\n🔍 TESTING EMBEDDING SIMILARITY")
    print("=" * 80)
    
    try:
        from app.services.vector import VectorDBService
        
        vectordb = VectorDBService("D:/Personal/LegalRAG_OCR/rag_service/data/vectordb")
        
        query = "đăng ký khai sinh mà có mẹ là người nước ngoài thì cần giấy tờ gì"
        
        # Test search in collection
        collection_name = "quy_trinh_cap_ho_tich_cap_xa"
        
        print(f"📝 Query: {query}")
        print(f"📊 Collection: {collection_name}")
        print("-" * 50)
        
        # Get collection
        collection = vectordb.get_collection(collection_name)
        
        # Search
        results = vectordb.search_in_collection(
            collection_name=collection_name,
            query=query,
            k=10,
            similarity_threshold=0.3
        )
        
        print("📊 VECTOR SEARCH RESULTS:")
        for i, result in enumerate(results):
            print(f"  Result {i+1}:")
            print(f"    - Similarity: {result.get('similarity', 'N/A'):.4f}")
            print(f"    - Document: {result.get('source', 'N/A')}")
            print(f"    - Content: {result.get('content', 'N/A')[:100]}...")
            print()
        
        # Analyze similarities
        similarities = [r.get('similarity', 0) for r in results]
        if similarities:
            max_sim = max(similarities)
            min_sim = min(similarities)
            avg_sim = sum(similarities) / len(similarities)
            
            print("📈 SIMILARITY ANALYSIS:")
            print(f"  - Max similarity: {max_sim:.4f}")
            print(f"  - Min similarity: {min_sim:.4f}")
            print(f"  - Avg similarity: {avg_sim:.4f}")
            print(f"  - Results count: {len(results)}")
            
    except Exception as e:
        print(f"❌ VECTOR SEARCH ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reranker_debug()
    test_embedding_similarity()
