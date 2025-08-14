"""
Test riêng biệt từng component để xác định điểm nghẽn chính xác
"""

import os
import sys
import time
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

def test_reranker_only():
    """Test chỉ riêng reranker component"""
    
    try:
        print("🔥 TESTING RERANKER COMPONENT ONLY")
        print("=" * 50)
        
        from app.services.result_reranker import RerankerService
        
        # Initialize reranker
        print("🔧 Initializing reranker...")
        start = time.time()
        reranker = RerankerService()
        init_time = time.time() - start
        print(f"✅ Reranker initialized: {init_time:.2f}s")
        
        # Sample documents
        sample_docs = []
        for i in range(8):  # Test with 8 docs (same as BROAD_SEARCH_K)
            sample_docs.append({
                'content': f"Tài liệu {i}: Thủ tục đăng ký khai sinh bao gồm nhiều bước quan trọng. Về phí lệ phí, đăng ký khai sinh đúng hạn được miễn phí hoàn toàn. Giấy tờ cần thiết gồm có giấy chứng sinh từ bệnh viện và chứng minh nhân dân của cha mẹ.",
                'similarity': 0.8 - (i * 0.05),
                'metadata': {'source': f'doc_{i}'}
            })
        
        query = "đăng ký khai sinh có tốn phí không"
        
        # Test reranking
        print(f"🎯 Testing rerank with {len(sample_docs)} documents...")
        start = time.time()
        
        reranked = reranker.rerank_documents(
            query=query,
            documents=sample_docs,
            top_k=1
        )
        
        rerank_time = time.time() - start
        print(f"⏱️ Rerank time: {rerank_time:.2f}s")
        print(f"📊 Results: {len(reranked)} documents")
        
        if reranked:
            print(f"🏆 Best score: {reranked[0].get('rerank_score', 0):.4f}")
        
        # Performance analysis
        if rerank_time < 2.0:
            print("🚀 EXCELLENT: Reranker is fast!")
        elif rerank_time < 5.0:
            print("✅ GOOD: Reranker performance is acceptable")
        else:
            print("⚠️ SLOW: Reranker is the bottleneck")
            
        return rerank_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_vector_search_only():
    """Test chỉ riêng vector search"""
    
    try:
        print("\n🔍 TESTING VECTOR SEARCH COMPONENT ONLY")
        print("=" * 50)
        
        from app.services.vector_database import VectorDBService
        from app.core.config import settings
        
        # Initialize vectordb
        print("🔧 Initializing vector database...")
        start = time.time()
        vectordb = VectorDBService()
        init_time = time.time() - start
        print(f"✅ VectorDB initialized: {init_time:.2f}s")
        
        query = "đăng ký khai sinh có tốn phí không"
        
        # Test vector search
        print(f"🎯 Testing vector search with k={settings.broad_search_k}...")
        start = time.time()
        
        results = vectordb.search_in_collection(
            collection_name="ho_tich_cap_xa",
            query=query,
            top_k=settings.broad_search_k,
            similarity_threshold=settings.similarity_threshold
        )
        
        search_time = time.time() - start
        print(f"⏱️ Vector search time: {search_time:.2f}s")
        print(f"📊 Results: {len(results)} documents")
        
        if search_time < 1.0:
            print("🚀 EXCELLENT: Vector search is very fast!")
        elif search_time < 3.0:
            print("✅ GOOD: Vector search is acceptable")
        else:
            print("⚠️ SLOW: Vector search might be slow")
            
        return search_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_llm_only():
    """Test chỉ riêng LLM generation"""
    
    try:
        print("\n🧠 TESTING LLM COMPONENT ONLY")
        print("=" * 50)
        
        from app.services.language_model import LLMService
        
        # Initialize LLM
        print("🔧 Initializing LLM...")
        start = time.time()
        llm = LLMService()
        init_time = time.time() - start
        print(f"✅ LLM initialized: {init_time:.2f}s")
        
        prompt = """Dựa vào thông tin sau:

Thủ tục đăng ký khai sinh:
- Phí: Đăng ký khai sinh đúng hạn được MIỄN PHÍ
- Giấy tờ: Giấy chứng sinh, CMND cha mẹ
- Thời gian: Ngay trong ngày

Câu hỏi: đăng ký khai sinh có tốn phí không

Trả lời:"""
        
        # Test generation
        print("🎯 Testing LLM generation...")
        start = time.time()
        
        response = llm.generate_response(
            user_query="đăng ký khai sinh có tốn phí không",
            context="""Thủ tục đăng ký khai sinh:
- Phí: Đăng ký khai sinh đúng hạn được MIỄN PHÍ
- Giấy tờ: Giấy chứng sinh, CMND cha mẹ
- Thời gian: Ngay trong ngày""",
            max_tokens=512,
            temperature=0.1
        )
        
        generation_time = time.time() - start
        print(f"⏱️ LLM generation time: {generation_time:.2f}s")
        print(f"📝 Response length: {len(str(response))} chars")
        print(f"💬 Response: {str(response)[:100]}...")
        
        if generation_time < 3.0:
            print("🚀 EXCELLENT: LLM is fast!")
        elif generation_time < 8.0:
            print("✅ GOOD: LLM performance is acceptable")
        else:
            print("⚠️ SLOW: LLM might be the bottleneck")
            
        return generation_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🧪 COMPONENT-BY-COMPONENT PERFORMANCE TEST")
    print("=" * 60)
    
    # Test each component
    rerank_time = test_reranker_only()
    search_time = test_vector_search_only() 
    llm_time = test_llm_only()
    
    # Summary
    print("\n📊 PERFORMANCE BREAKDOWN")
    print("=" * 40)
    if rerank_time: print(f"🔥 Reranker:      {rerank_time:.2f}s")
    if search_time:  print(f"🔍 Vector Search: {search_time:.2f}s")
    if llm_time:     print(f"🧠 LLM Generate:  {llm_time:.2f}s")
    
    total_estimated = (rerank_time or 0) + (search_time or 0) + (llm_time or 0)
    print(f"⏱️ Total Estimated: {total_estimated:.2f}s")
    
    print("\n🎯 BOTTLENECK ANALYSIS")
    components = [
        ("Reranker", rerank_time),
        ("Vector Search", search_time), 
        ("LLM Generation", llm_time)
    ]
    
    valid_components = [(name, time) for name, time in components if time is not None]
    if valid_components:
        bottleneck = max(valid_components, key=lambda x: x[1])
        print(f"🐌 Main bottleneck: {bottleneck[0]} ({bottleneck[1]:.2f}s)")
        
        for name, comp_time in valid_components:
            if comp_time == bottleneck[1]:
                print(f"   ❗ {name} is taking the most time!")
            elif comp_time > total_estimated * 0.3:
                print(f"   ⚠️ {name} is also significant")
            else:
                print(f"   ✅ {name} is optimized")
