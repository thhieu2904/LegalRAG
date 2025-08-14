"""
Test với context expansion tắt để xác nhận đây là bottleneck
"""

import os
import sys
import time
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

def test_without_context_expansion():
    """Test với context expansion đơn giản hóa"""
    
    try:
        print("🚫 TESTING WITH MINIMAL CONTEXT EXPANSION")
        print("=" * 50)
        
        from app.core.config import settings
        from app.services.vector_database import VectorDBService
        from app.services.language_model import LLMService  
        from app.services.rag_engine import OptimizedEnhancedRAGService
        
        # Initialize services
        print("🔧 Initializing services...")
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
        
        # Test query với use_full_document_expansion=False 
        query = "đăng ký khai sinh có tốn phí không"
        
        print(f"\n🎯 QUERY WITH MINIMAL EXPANSION: {query}")
        print("-" * 40)
        
        start_query = time.time()
        
        result = rag_service.enhanced_query(
            query=query,
            session_id=session_id,
            max_context_length=1000,  # Giảm context length
            use_ambiguous_detection=False,  # Tắt router
            use_full_document_expansion=False  # 🚫 TẮT FULL DOCUMENT EXPANSION!
        )
        
        query_time = time.time() - start_query
        
        print(f"\n📊 RESULTS WITH MINIMAL EXPANSION:")
        print(f"  ⏱️ Query time: {query_time:.2f}s")
        print(f"  🎯 Type: {result.get('type', 'unknown')}")
        
        if result.get('type') == 'answer':
            context_info = result.get('context_info', {})
            print(f"  📄 Nucleus chunks: {context_info.get('nucleus_chunks', 0)}")
            print(f"  📝 Context length: {context_info.get('context_length', 0)} chars")
            print(f"  🗂️ Collections: {context_info.get('source_collections', [])}")
            print(f"  ✅ Answer length: {len(result.get('answer', ''))}")
            
        # Performance comparison  
        print(f"\n🔍 PERFORMANCE COMPARISON:")
        print(f"  Minimal expansion: {query_time:.2f}s")
        print(f"  Full expansion (previous): ~16.47s")
        print(f"  Context expansion overhead: ~{16.47 - query_time:.2f}s")
        
        if query_time < 5:
            print(f"  🎉 CONFIRMED: Context expansion is the bottleneck!")
            print(f"  💡 Consider optimizing file I/O or caching")
        
        return query_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    timing = test_without_context_expansion()
    
    if timing:
        print(f"\n🎯 RECOMMENDATION:")
        if timing < 5:
            print(f"✅ With minimal expansion: {timing:.2f}s is EXCELLENT!")
            print(f"🔧 Optimize context expansion:")
            print(f"   - Cache loaded documents")
            print(f"   - Use async file I/O")
            print(f"   - Preload common documents")
        else:
            print(f"⚠️ Still slow: {timing:.2f}s - investigate other components")
