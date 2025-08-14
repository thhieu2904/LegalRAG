"""
Test chỉ với vector search + rerank, không có LLM generation
"""

import os
import sys
import time
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

def test_without_llm_generation():
    """Test chỉ tới bước rerank, không generate answer"""
    
    try:
        print("🚫 TESTING WITHOUT LLM GENERATION")
        print("=" * 50)
        
        from app.core.config import settings
        from app.services.vector_database import VectorDBService
        from app.services.result_reranker import RerankerService
        
        print(f"✅ Config - BROAD_SEARCH_K: {settings.broad_search_k}")
        
        # Initialize services
        print("🔧 Initializing services...")
        start_init = time.time()
        
        vectordb_service = VectorDBService()
        reranker_service = RerankerService()
        
        init_time = time.time() - start_init
        print(f"✅ Services initialized: {init_time:.2f}s")
        
        # Test full retrieval pipeline without LLM
        query = "đăng ký khai sinh có tốn phí không"
        
        print(f"\n🎯 RETRIEVAL PIPELINE: {query}")
        print("-" * 40)
        
        start_query = time.time()
        
        # Step 1: Vector search
        print("🔍 Step 1: Vector search...")
        search_start = time.time()
        
        search_results = vectordb_service.search_in_collection(
            collection_name="ho_tich_cap_xa",
            query=query,
            top_k=settings.broad_search_k,
            similarity_threshold=settings.similarity_threshold
        )
        
        search_time = time.time() - search_start
        print(f"   ⏱️ Vector search: {search_time:.2f}s ({len(search_results)} docs)")
        
        # Step 2: Reranking
        print("🔥 Step 2: Reranking...")
        rerank_start = time.time()
        
        reranked_results = reranker_service.rerank_documents(
            query=query,
            documents=search_results,
            top_k=1
        )
        
        rerank_time = time.time() - rerank_start
        print(f"   ⏱️ Reranking: {rerank_time:.2f}s")
        
        total_retrieval_time = time.time() - start_query
        
        print(f"\n📊 RETRIEVAL RESULTS:")
        print(f"  ⏱️ Total retrieval time: {total_retrieval_time:.2f}s")
        print(f"  📊 Search: {search_time:.2f}s")
        print(f"  🔥 Rerank: {rerank_time:.2f}s")
        print(f"  📄 Best result score: {reranked_results[0].get('rerank_score', 0):.4f}")
        print(f"  📝 Best content length: {len(reranked_results[0].get('content', ''))} chars")
        
        # Performance comparison
        print(f"\n🔍 ANALYSIS:")
        print(f"  Retrieval only: {total_retrieval_time:.2f}s")
        print(f"  Full RAG pipeline: ~18.16s")
        print(f"  LLM + Context overhead: ~{18.16 - total_retrieval_time:.2f}s")
        
        if total_retrieval_time < 3:
            print(f"  ✅ Retrieval is fast - problem is in LLM/Context stage")
        else:
            print(f"  ⚠️ Retrieval is also slow")
            
        return total_retrieval_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    timing = test_without_llm_generation()
    
    if timing:
        print(f"\n🎯 DIAGNOSIS:")
        if timing < 2:
            print(f"✅ Retrieval pipeline is optimized")
            print(f"🔍 Focus on optimizing:")
            print(f"   - Context building")
            print(f"   - LLM prompt construction") 
            print(f"   - LLM generation with long context")
        else:
            print(f"⚠️ Retrieval pipeline needs optimization too")
