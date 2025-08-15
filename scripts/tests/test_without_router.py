"""
Test với router bị tắt để xác nhận đây là bottleneck
"""

import os
import sys
import time
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

def test_without_router():
    """Test với ambiguous detection tắt (không dùng router)"""
    
    try:
        print("🚫 TESTING WITHOUT QUERY ROUTER")
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
        print(f"✅ Session created: {session_id}")
        
        # Test query WITHOUT ambiguous detection (tắt router)
        query = "đăng ký khai sinh có tốn phí không"
        
        print(f"\n🎯 QUERY WITHOUT ROUTER: {query}")
        print("-" * 40)
        
        start_query = time.time()
        
        result = rag_service.enhanced_query(
            query=query,
            session_id=session_id,
            max_context_length=3000,
            use_ambiguous_detection=False  # 🚫 TẮT ROUTER!
        )
        
        query_time = time.time() - start_query
        
        print(f"\n📊 RESULTS WITHOUT ROUTER:")
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
        print(f"  Without Router: {query_time:.2f}s")
        print(f"  With Router (previous): ~16.76s")
        print(f"  Router overhead: ~{16.76 - query_time:.2f}s")
        
        if query_time < 5:
            print(f"  🎉 CONFIRMED: Router is the bottleneck!")
            print(f"  💡 Consider optimizing router or using fallback mode")
        
        return query_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    timing = test_without_router()
    
    if timing:
        print(f"\n🎯 RECOMMENDATION:")
        if timing < 5:
            print(f"✅ Without router: {timing:.2f}s is EXCELLENT!")
            print(f"🔧 Consider disabling router for production speed")
            print(f"💡 Or optimize router caching/processing")
        else:
            print(f"⚠️ Still slow without router: {timing:.2f}s")
            print(f"🔍 Need to investigate other components")
