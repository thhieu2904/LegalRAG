"""
Test với detailed logging để tìm ra chính xác thời gian bị mất ở đâu
"""

import os
import sys
import time
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

def test_full_pipeline_with_timing():
    """Test toàn bộ pipeline với timing chi tiết"""
    
    try:
        print("🕒 DETAILED TIMING ANALYSIS")
        print("=" * 50)
        
        from app.core.config import settings
        from app.services.vector_database import VectorDBService
        from app.services.language_model import LLMService  
        from app.services.rag_engine import OptimizedEnhancedRAGService
        
        print(f"✅ Config - BROAD_SEARCH_K: {settings.broad_search_k}")
        
        # Initialize services với timing
        total_start = time.time()
        
        print("🔧 Initializing services...")
        
        # VectorDB
        start = time.time()
        vectordb_service = VectorDBService()
        vectordb_time = time.time() - start
        print(f"  📊 VectorDB: {vectordb_time:.2f}s")
        
        # LLM
        start = time.time()
        llm_service = LLMService()
        llm_init_time = time.time() - start
        print(f"  🧠 LLM: {llm_init_time:.2f}s")
        
        # RAG Service
        start = time.time()
        documents_dir = settings.base_dir / "data" / "documents"
        rag_service = OptimizedEnhancedRAGService(
            documents_dir=str(documents_dir),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        rag_init_time = time.time() - start
        print(f"  ⚡ RAG Service: {rag_init_time:.2f}s")
        
        total_init = time.time() - total_start
        print(f"📊 Total initialization: {total_init:.2f}s")
        
        # Create session
        start = time.time()
        session_id = rag_service.create_session()
        session_time = time.time() - start
        print(f"🔧 Session creation: {session_time:.2f}s")
        
        # Test một query đơn lẻ với timing chi tiết
        query = "đăng ký khai sinh có tốn phí không"
        
        print(f"\n🎯 ANALYZING QUERY: {query}")
        print("-" * 40)
        
        # Turn on detailed logging để theo dõi từng bước
        import logging
        logging.getLogger().setLevel(logging.INFO)
        
        query_start = time.time()
        
        result = rag_service.enhanced_query(
            query=query,
            session_id=session_id,
            max_context_length=3000,
            use_ambiguous_detection=True
        )
        
        total_query_time = time.time() - query_start
        
        print(f"\n📊 FINAL RESULTS:")
        print(f"  ⏱️ Total query time: {total_query_time:.2f}s")
        print(f"  🎯 Type: {result.get('type', 'unknown')}")
        
        if result.get('type') == 'answer':
            context_info = result.get('context_info', {})
            processing_time = result.get('processing_time', 0)
            
            print(f"  📄 Nucleus chunks: {context_info.get('nucleus_chunks', 0)}")
            print(f"  📝 Context length: {context_info.get('context_length', 0)} chars")
            print(f"  🗂️ Collections: {context_info.get('source_collections', [])}")
            print(f"  ⏱️ Reported processing time: {processing_time:.2f}s")
            print(f"  ✅ Answer length: {len(result.get('answer', ''))}")
            
            # So sánh với component test
            print(f"\n🔍 COMPONENT COMPARISON:")
            print(f"  Expected (from component test): ~2.5s")
            print(f"  Actual (full pipeline): {total_query_time:.2f}s")
            print(f"  Overhead: {total_query_time - 2.5:.2f}s")
            
            if total_query_time > 5:
                print(f"  ⚠️ Có {total_query_time - 2.5:.2f}s overhead cần tìm hiểu!")
                print(f"  🔍 Có thể là: Router, Context Expansion, hoặc Session processing")
            
        return total_query_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    timing = test_full_pipeline_with_timing()
    
    if timing:
        print(f"\n🎯 CONCLUSION:")
        if timing < 5:
            print(f"✅ GOOD: {timing:.2f}s is acceptable for legal RAG")
        elif timing < 10:
            print(f"⚠️ OK: {timing:.2f}s could be optimized further")
        else:
            print(f"🐌 SLOW: {timing:.2f}s needs investigation")
            
    print(f"\n💡 Next steps:")
    print(f"  1. Check router processing time")
    print(f"  2. Check context expansion overhead") 
    print(f"  3. Consider disabling some features for speed")
