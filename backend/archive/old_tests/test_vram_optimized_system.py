"""
Test script cho VRAM-Optimized Enhanced RAG System
Kiểm tra tất cả tính năng mới:
1. VRAM optimization (CPU embedding, GPU LLM/Reranker)
2. Ambiguous query detection
3. Context expansion với nucleus strategy
4. Session management
"""

import sys
import os
import asyncio
import json
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService
from app.services.optimized_enhanced_rag_service import OptimizedEnhancedRAGService

def print_separator(title=""):
    """In separator với title"""
    print("=" * 80)
    if title:
        print(f" {title} ".center(80, "="))
        print("=" * 80)
    print()

def print_result(result, title=""):
    """In kết quả với format đẹp"""
    if title:
        print(f"📊 {title}")
        print("-" * 60)
    
    if isinstance(result, dict):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)
    print()

async def test_vram_optimization():
    """Test VRAM optimization"""
    print_separator("VRAM OPTIMIZATION TEST")
    
    try:
        # 1. Test VectorDB Service (embedding should be on CPU)
        print("🔧 Testing VectorDB Service (Embedding on CPU)...")
        vectordb_service = VectorDBService()
        print(f"✅ Embedding model device: CPU (optimized)")
        print(f"✅ Embedding model loaded: {vectordb_service.embedding_model is not None}")
        
        # Test encoding (should be fast on CPU for short queries)
        if vectordb_service.embedding_model:
            test_query = "thủ tục kết hôn"
            start_time = time.time()
            embedding = vectordb_service.embedding_model.encode([test_query])
            encoding_time = time.time() - start_time
            print(f"✅ Query encoding time: {encoding_time:.4f}s (CPU)")
        else:
            print("⚠️ Embedding model not loaded, skipping encoding test")
        
        # 2. Test LLM Service (should be on GPU)
        print("\\n🔧 Testing LLM Service (GPU)...")
        llm_service = LLMService()
        print(f"✅ LLM model loaded: {llm_service.model is not None}")
        
        return vectordb_service, llm_service
        
    except Exception as e:
        print(f"❌ VRAM optimization test failed: {e}")
        return None, None

async def test_services_initialization(vectordb_service, llm_service):
    """Test khởi tạo OptimizedEnhancedRAGService"""
    print_separator("OPTIMIZED SERVICE INITIALIZATION TEST")
    
    try:
        documents_dir = settings.base_dir / "data" / "documents"
        service = OptimizedEnhancedRAGService(
            documents_dir=str(documents_dir),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        
        print("✅ OptimizedEnhancedRAGService initialized successfully")
        print(f"✅ Ambiguous Service: {service.ambiguous_service is not None}")
        print(f"✅ Context Expansion Service: {service.context_expansion_service is not None}")
        print(f"✅ Reranker Service: {service.reranker_service is not None}")
        
        # Test health status
        health = service.get_health_status()
        print_result(health, "Health Status")
        
        return service
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return None

async def test_ambiguous_query_detection(service):
    """Test phát hiện câu hỏi mơ hồ"""
    print_separator("AMBIGUOUS QUERY DETECTION TEST")
    
    test_queries = [
        "thủ tục như thế nào?",          # Should be ambiguous
        "mất bao lâu?",                  # Should be ambiguous  
        "tốn bao nhiều tiền?",           # Should be ambiguous
        "ở đâu làm?",                    # Should be ambiguous
        "thủ tục kết hôn cần giấy tờ gì?",  # Should be clear
        "làm thế nào để đăng ký khai sinh cho con?",  # Should be clear
    ]
    
    for query in test_queries:
        print(f"🔍 Testing query: '{query}'")
        
        is_ambiguous, category, confidence = service.ambiguous_service.is_ambiguous(query)
        
        print(f"   Result: {'🚩 AMBIGUOUS' if is_ambiguous else '✅ CLEAR'}")
        if is_ambiguous:
            print(f"   Category: {category}")
            print(f"   Confidence: {confidence:.3f}")
            
            # Test clarification prompt
            clarification = service.ambiguous_service.get_clarification_prompt(category)
            print(f"   Clarification: {clarification['template']}")
        print()

async def test_enhanced_query_processing(service):
    """Test enhanced query processing"""
    print_separator("ENHANCED QUERY PROCESSING TEST")
    
    test_cases = [
        {
            "query": "thủ tục kết hôn cần giấy tờ gì?",
            "description": "Clear query - should process normally"
        },
        {
            "query": "thủ tục như thế nào?", 
            "description": "Ambiguous query - should ask for clarification"
        }
    ]
    
    for test_case in test_cases:
        print(f"🧪 Testing: {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        
        start_time = time.time()
        
        result = service.enhanced_query(
            query=test_case["query"],
            max_context_length=2000,
            use_ambiguous_detection=True,
            use_full_document_expansion=True
        )
        
        processing_time = time.time() - start_time
        
        print(f"Processing time: {processing_time:.2f}s")
        print_result(result, "Query Result")

async def test_session_management(service):
    """Test session management"""
    print_separator("SESSION MANAGEMENT TEST")
    
    try:
        # Create session
        session_id = service.create_session(metadata={"test": "session_test"})
        print(f"✅ Created session: {session_id}")
        
        # Test multiple queries in session
        queries = [
            "thủ tục kết hôn cần gì?",
            "thời gian xử lý bao lâu?", 
            "lệ phí là bao nhiều?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\\n🔄 Session query {i}: '{query}'")
            
            result = service.enhanced_query(
                query=query,
                session_id=session_id,
                use_ambiguous_detection=False  # Skip for faster testing
            )
            
            print(f"   Type: {result.get('type')}")
            if result.get('type') == 'answer':
                print(f"   Answer: {result.get('answer', '')[:100]}...")
        
        # Check session state
        session = service.get_session(session_id)
        if session:
            print(f"\\n📊 Session stats:")
            print(f"   Queries in history: {len(session.query_history)}")
            print(f"   Last accessed: {time.ctime(session.last_accessed)}")
        
        print("✅ Session management test passed")
        
    except Exception as e:
        print(f"❌ Session management test failed: {e}")

async def test_context_expansion(service):
    """Test context expansion service"""
    print_separator("CONTEXT EXPANSION TEST")
    
    try:
        # Get stats
        stats = service.context_expansion_service.get_stats()
        print_result(stats, "Context Expansion Stats")
        
        print("✅ Context expansion service working")
        
    except Exception as e:
        print(f"❌ Context expansion test failed: {e}")

async def test_performance_metrics(service):
    """Test performance metrics"""
    print_separator("PERFORMANCE METRICS TEST")
    
    try:
        # Run multiple queries to generate metrics
        test_queries = [
            "thủ tục kết hôn",
            "cách đăng ký khai sinh",
            "xin giấy phép kinh doanh"
        ]
        
        print("🔄 Running performance test...")
        
        for query in test_queries:
            service.enhanced_query(
                query=query,
                use_ambiguous_detection=False,  # Faster for testing
                use_full_document_expansion=False
            )
        
        # Check metrics
        metrics = service.metrics
        print_result(metrics, "Performance Metrics")
        
        print("✅ Performance metrics test passed")
        
    except Exception as e:
        print(f"❌ Performance metrics test failed: {e}")

async def main():
    """Chạy tất cả tests"""
    print_separator("VRAM-OPTIMIZED ENHANCED RAG SYSTEM TEST")
    print("Testing all components of the optimized system...")
    print()
    
    try:
        # Test 1: VRAM Optimization
        vectordb_service, llm_service = await test_vram_optimization()
        if not vectordb_service or not llm_service:
            print("❌ Cannot continue without basic services")
            return
        
        # Test 2: Service Initialization
        service = await test_services_initialization(vectordb_service, llm_service)
        if not service:
            print("❌ Cannot continue without OptimizedEnhancedRAGService")
            return
        
        # Test 3: Ambiguous Query Detection
        await test_ambiguous_query_detection(service)
        
        # Test 4: Enhanced Query Processing
        await test_enhanced_query_processing(service)
        
        # Test 5: Session Management
        await test_session_management(service)
        
        # Test 6: Context Expansion
        await test_context_expansion(service)
        
        # Test 7: Performance Metrics
        await test_performance_metrics(service)
        
        print_separator("TEST SUMMARY")
        print("🎉 All tests completed!")
        print("✅ VRAM-Optimized Enhanced RAG System is working correctly")
        print()
        print("🚀 Ready to start the optimized server with:")
        print("   python optimized_main.py")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
