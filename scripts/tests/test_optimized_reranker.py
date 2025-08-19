"""
Test script tối ưu hóa reranker performance
Chạy bằng: C:/Users/thhieu/miniconda3/Scripts/conda.exe run -p D:\\env\\conda\\LegalRAG_v1 --no-capture-output python test_optimized_reranker.py
"""

import os
import sys
import time
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

def test_optimized_system():
    """Test toàn bộ hệ thống sau khi tối ưu hóa reranker"""
    
    try:
        print("🚀 TESTING OPTIMIZED RERANKER SYSTEM")
        print("=" * 60)
        
        # Import services
        from app.core.config import settings
        from app.services.vector_database import VectorDBService
        from app.services.language_model import LLMService  
        from app.services.rag_engine import OptimizedEnhancedRAGService
        
        print(f"✅ Config loaded - BROAD_SEARCH_K: {settings.broad_search_k}")
        
        # Initialize services
        print("🔧 Initializing services...")
        start_init = time.time()
        
        # VectorDB Service (CPU embedding)
        vectordb_service = VectorDBService()
        print(f"✅ VectorDB initialized: {time.time() - start_init:.2f}s")
        
        # LLM Service (GPU)
        llm_service = LLMService()
        print(f"✅ LLM initialized: {time.time() - start_init:.2f}s")
        
        # RAG Service
        documents_dir = settings.base_dir / "data" / "documents"
        rag_service = OptimizedEnhancedRAGService(
            documents_dir=str(documents_dir),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        print(f"✅ RAG service initialized: {time.time() - start_init:.2f}s")
        
        # Test queries - focus on reranker performance
        test_queries = [
            "đăng ký khai sinh có tốn phí không",
            "thủ tục chứng thực hợp đồng cần giấy tờ gì",
            "lệ phí đăng ký kết hôn là bao nhiêu"
        ]
        
        print("\n🎯 TESTING RERANKER PERFORMANCE")
        print("-" * 40)
        
        total_rerank_time = 0
        total_query_time = 0
        
        # =================================================================
        # TẠO SESSION MỘT LẦN DUY NHẤT
        # =================================================================
        session_id = rag_service.create_session()
        print(f"✅ Session created: {session_id}")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query}")
            
            # Measure query time (CHỈ ĐO THỜI GIAN QUERY, KHÔNG BAO GỒM KHỞI TẠO)
            start_query = time.time()
            
            # Run query - TÁI SỬ DỤNG SESSION VÀ SERVICE ĐÃ CÓ
            result = rag_service.enhanced_query(
                query=query,
                session_id=session_id,  # Tái sử dụng session
                max_context_length=3000,
                use_ambiguous_detection=True
            )
            
            query_time = time.time() - start_query
            total_query_time += query_time
            
            print(f"  ⏱️ Total query time: {query_time:.2f}s")
            print(f"  📊 Type: {result.get('type', 'unknown')}")
            
            if result.get('type') == 'answer':
                context_info = result.get('context_info', {})
                print(f"  📄 Nucleus chunks: {context_info.get('nucleus_chunks', 0)}")
                print(f"  📝 Context length: {context_info.get('context_length', 0)} chars")
                print(f"  🗂️ Collections: {context_info.get('source_collections', [])}")
                print(f"  ✅ Answer: {result['answer'][:100]}...")
            
            # Performance comparison
            if query_time < 5.0:
                print(f"  🚀 FAST: {query_time:.2f}s (good performance)")
            elif query_time < 10.0:
                print(f"  ⚡ OK: {query_time:.2f}s (acceptable)")
            else:
                print(f"  🐌 SLOW: {query_time:.2f}s (needs optimization)")
        
        # Summary
        avg_time = total_query_time / len(test_queries)
        print(f"\n📊 PERFORMANCE SUMMARY")
        print(f"Total time: {total_query_time:.2f}s")
        print(f"Average time per query: {avg_time:.2f}s")
        print(f"Queries per minute: {60/avg_time:.1f}")
        
        # Performance analysis
        if avg_time < 4.0:
            print("🎉 EXCELLENT performance - Reranker optimization successful!")
        elif avg_time < 7.0:
            print("✅ GOOD performance - Significant improvement achieved")
        else:
            print("⚠️ Still slow - May need further optimization")
        
        # System stats
        health = rag_service.get_health_status()
        print(f"\n🔧 SYSTEM STATUS")
        print(f"Collections: {health.get('total_collections', 0)}")
        print(f"Documents: {health.get('total_documents', 0)}")
        print(f"LLM loaded: {health.get('llm_loaded', False)}")
        print(f"Reranker loaded: {health.get('reranker_loaded', False)}")
        
        print("\n✅ OPTIMIZATION TEST COMPLETED")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimized_system()
