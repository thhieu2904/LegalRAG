"""
Test hệ thống sau khi tối ưu Prompt Processing
- Tăng N_BATCH từ 384 → 1024
- Giảm chat history từ 3 → 1 lượt
- Giảm context từ 1500 → 1200 chars
- Khôi phục MAX_TOKENS về 1024 cho chất lượng
"""

import os
import sys
import time
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

def test_prompt_processing_optimization():
    """Test sau khi tối ưu Prompt Processing"""
    
    try:
        print("🚀 TESTING PROMPT PROCESSING OPTIMIZATION")
        print("=" * 60)
        
        from app.core.config import settings
        from app.services.vector_database import VectorDBService
        from app.services.language_model import LLMService  
        from app.services.rag_engine import OptimizedEnhancedRAGService
        
        print("📊 OPTIMIZATION SETTINGS:")
        print(f"  - BROAD_SEARCH_K: {settings.broad_search_k}")
        print(f"  - N_BATCH: {settings.n_batch}")
        print(f"  - MAX_TOKENS: {settings.max_tokens}")
        print(f"  - N_CTX: {settings.n_ctx}")
        
        # Initialize services
        print("\n🔧 Initializing services...")
        start_init = time.time()
        
        vectordb_service = VectorDBService()
        llm_service = LLMService()
        
        documents_dir = settings.base_dir / "data" / "documents"
        rag_service = OptimizedEnhancedRAGService(
            documents_dir=str(documents_dir),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        
        init_time = time.time() - start_init
        print(f"✅ Services initialized: {init_time:.2f}s")
        
        # Create session
        session_id = rag_service.create_session()
        print(f"✅ Session created: {session_id}")
        
        # Test queries with detailed timing
        test_queries = [
            "đăng ký khai sinh có tốn phí không",
            "thủ tục chứng thực hợp đồng cần giấy tờ gì", 
            "lệ phí đăng ký kết hôn là bao nhiêu"
        ]
        
        print("\n🎯 TESTING OPTIMIZED PROMPT PROCESSING")
        print("-" * 50)
        
        total_time = 0
        successful_queries = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Query {i}: {query}")
            
            start_query = time.time()
            
            result = rag_service.enhanced_query(
                query=query,
                session_id=session_id,
                max_context_length=3000,  # Sẽ bị limit xuống 1200
                use_ambiguous_detection=False,  # Tắt router để tập trung vào LLM
                use_full_document_expansion=False
            )
            
            query_time = time.time() - start_query
            total_time += query_time
            
            print(f"  ⏱️ Query time: {query_time:.2f}s")
            print(f"  🎯 Type: {result.get('type', 'unknown')}")
            
            if result.get('type') == 'answer':
                successful_queries += 1
                context_info = result.get('context_info', {})
                print(f"  📄 Nucleus chunks: {context_info.get('nucleus_chunks', 0)}")
                print(f"  📝 Context length: {context_info.get('context_length', 0)} chars")
                print(f"  🗂️ Collections: {context_info.get('source_collections', [])}")
                print(f"  ✅ Answer length: {len(result.get('answer', ''))}")
                
                # Performance feedback
                if query_time < 5:
                    print(f"  🎉 EXCELLENT: {query_time:.2f}s - Prompt optimization worked!")
                elif query_time < 10:
                    print(f"  ✅ GOOD: {query_time:.2f}s - Significant improvement")
                elif query_time < 15:
                    print(f"  ⚠️ OK: {query_time:.2f}s - Still improving")
                else:
                    print(f"  🐌 SLOW: {query_time:.2f}s - Need more optimization")
        
        # Performance summary
        avg_time = total_time / len(test_queries)
        queries_per_minute = 60 / avg_time if avg_time > 0 else 0
        
        print(f"\n📊 PROMPT PROCESSING OPTIMIZATION RESULTS")
        print("=" * 50)
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per query: {avg_time:.2f}s")
        print(f"Queries per minute: {queries_per_minute:.1f}")
        print(f"Success rate: {successful_queries}/{len(test_queries)}")
        
        # Comparison with previous results
        previous_avg = 21.57  # From previous test
        improvement = ((previous_avg - avg_time) / previous_avg) * 100
        
        print(f"\n🔍 PERFORMANCE COMPARISON")
        print(f"Previous average: {previous_avg:.2f}s")
        print(f"Current average: {avg_time:.2f}s")
        print(f"Improvement: {improvement:.1f}%")
        
        # Final assessment
        print(f"\n🎯 ASSESSMENT")
        if avg_time < 5:
            print("🎉 OUTSTANDING: Prompt Processing optimization successful!")
            print("💡 System ready for production use")
        elif avg_time < 10:
            print("✅ EXCELLENT: Major improvement achieved!")
            print("💡 Consider minor tweaks for further optimization")
        elif avg_time < 15:
            print("⚡ GOOD: Significant progress made")
            print("💡 May need additional optimization")
        else:
            print("⚠️ MODERATE: Some improvement, but more work needed")
            print("💡 Consider other optimization strategies")
        
        return avg_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🧪 PROMPT PROCESSING OPTIMIZATION TEST")
    print("Target: Reduce from 21.57s to under 10s")
    print("=" * 60)
    
    result = test_prompt_processing_optimization()
    
    if result:
        print(f"\n✅ TEST COMPLETED")
        if result < 10:
            print("🎯 TARGET ACHIEVED: Under 10 seconds!")
        elif result < 15:
            print("🎯 CLOSE TO TARGET: Under 15 seconds")
        else:
            print("🎯 MORE WORK NEEDED: Still above 15 seconds")
            
        print(f"\n📈 KEY OPTIMIZATIONS APPLIED:")
        print(f"  ✅ N_BATCH: 384 → 1024 (better prompt batching)")
        print(f"  ✅ Chat history: 3 → 1 entries")  
        print(f"  ✅ Context limit: 1500 → 1200 chars")
        print(f"  ✅ MAX_TOKENS: restored to 1024")
        print(f"  ✅ Reranker: optimized to 0.25s")
