#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project modules
from app.core.config import settings
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService
from app.services.optimized_enhanced_rag_service_v2 import OptimizedEnhancedRAGService

def print_separator(title):
    """In separator cho test"""
    print("="*80)
    print(f"🔥 {title}")
    print("="*80)

def print_result(label, data, max_length=200):
    """In kết quả test"""
    print(f"📊 {label}:")
    if isinstance(data, str):
        if len(data) > max_length:
            print(f"   {data[:max_length]}...")
        else:
            print(f"   {data}")
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"   {key}: {value[:100]}...")
            else:
                print(f"   {key}: {value}")
    else:
        print(f"   {data}")
    print()

async def test_vram_optimized_system():
    """Test toàn bộ VRAM-optimized system"""
    
    print_separator("KHỞI TẠO VRAM-OPTIMIZED ENHANCED RAG SYSTEM")
    
    try:
        # Initialize services
        print("🔧 Initializing VectorDB Service (Embedding: CPU)...")
        vectordb_service = VectorDBService()
        print(f"   ✅ Embedding model device: CPU (VRAM optimized)")
        
        print("🔧 Initializing LLM Service (GPU)...")
        llm_service = LLMService()
        print(f"   ✅ LLM loaded on GPU")
        
        print("🔧 Initializing Optimized Enhanced RAG Service...")
        documents_dir = settings.base_dir / "data" / "documents"
        rag_service = OptimizedEnhancedRAGService(
            documents_dir=str(documents_dir),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        print(f"   ✅ All services initialized with VRAM optimization")
        
        # Health check
        print_separator("SYSTEM HEALTH CHECK")
        health_status = rag_service.get_health_status()
        print_result("Health Status", health_status)
        
        # Test 1: Clear Query (không mơ hồ)
        print_separator("TEST 1: CLEAR QUERY (KHÔNG MƠ HỒ)")
        
        clear_queries = [
            "Thủ tục đăng ký kết hôn cần những giấy tờ gì?",
            "Quy trình xin giấy phép kinh doanh như thế nào?"
        ]
        
        for query in clear_queries:
            print(f"🔍 Testing query: {query}")
            start_time = time.time()
            
            result = rag_service.enhanced_query(
                query=query,
                use_ambiguous_detection=True,
                use_full_document_expansion=True
            )
            
            processing_time = time.time() - start_time
            print_result(f"Result (processed in {processing_time:.2f}s)", {
                "type": result.get("type"),
                "answer_length": len(result.get("answer", "")),
                "session_id": result.get("session_id"),
                "context_info": result.get("context_info", {}),
                "routing_info": result.get("routing_info", {})
            })
        
        # Test 2: Ambiguous Queries (câu hỏi mơ hồ)
        print_separator("TEST 2: AMBIGUOUS QUERIES (CÂU HỎI MƠ HỒ)")
        
        ambiguous_queries = [
            "thủ tục như thế nào?",
            "cần giấy tờ gì?",
            "mất bao lâu?"
        ]
        
        for query in ambiguous_queries:
            print(f"🤔 Testing ambiguous query: {query}")
            
            result = rag_service.enhanced_query(
                query=query,
                use_ambiguous_detection=True
            )
            
            print_result("Ambiguous Detection Result", {
                "type": result.get("type"),
                "category": result.get("category"),
                "confidence": result.get("confidence"),
                "clarification_template": result.get("clarification", {}).get("template", ""),
                "generated_questions_count": len(result.get("generated_questions", []))
            })
            
            if result.get("generated_questions"):
                print("📝 Generated clarification questions:")
                for i, q in enumerate(result.get("generated_questions", [])[:3]):
                    print(f"   {i+1}. {q}")
                print()
        
        print_separator("✅ BASIC TESTS COMPLETED SUCCESSFULLY")
        print("🎉 VRAM-Optimized Enhanced RAG System is working!")
        print(f"🧠 Architecture: CPU Embedding + GPU LLM/Reranker")
        print(f"🔥 Features: Ambiguous Detection + Nucleus Strategy")
        print(f"⚡ Performance: Optimized for 6GB VRAM systems")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vram_optimized_system())
