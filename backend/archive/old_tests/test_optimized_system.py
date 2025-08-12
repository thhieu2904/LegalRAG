#!/usr/bin/env python3
"""
Test Optimized RAG System with GPU Support and Anti-Repetition
Tests both performance and response quality improvements
"""

import asyncio
import json
import time
from app.services.rag_service import RAGService
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService
from app.core.config import settings

async def test_optimized_rag():
    """Test RAG system với GPU acceleration và anti-repetition"""
    
    print("="*70)
    print("🚀 TESTING OPTIMIZED RAG SYSTEM")
    print("="*70)
    print(f"📊 Config Summary:")
    print(f"   • GPU Layers: {settings.n_gpu_layers} (-1 = all on GPU)")
    print(f"   • CPU Threads: {settings.n_threads}")
    print(f"   • Batch Size: {settings.n_batch}")
    print(f"   • Max Tokens: {settings.max_tokens}")
    print(f"   • Temperature: {settings.temperature}")
    print()
    
    try:
        # Khởi tạo services
        print("🔧 Initializing services...")
        vectordb_service = VectorDBService()
        llm_service = LLMService()
        
        print(f"   ✅ VectorDB: {vectordb_service.embedding_model_name}")
        print(f"   ✅ LLM: {'GPU-accelerated' if settings.n_gpu_layers != 0 else 'CPU-only'}")
        print()
        
        rag_service = RAGService(
            documents_dir=str(settings.documents_path),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        
        # Health check
        health = rag_service.get_health_status()
        print(f"🏥 System Health: {health['status']}")
        print(f"   • Collections: {health['total_collections']}")
        print(f"   • Documents: {health['total_documents']}")
        print(f"   • GPU Available: {health['model_info'].get('n_gpu_layers', 0) != 0}")
        print()
        
        # Test queries với focus vào repetition problem
        test_queries = [
            "thủ tục nuôi con nuôi",  # Query gây lặp trước đây
            "cách đăng ký khai sinh",
            "thủ tục chứng thực bản sao"
        ]
        
        results = []
        for i, query in enumerate(test_queries, 1):
            print(f"🔍 Test {i}/3: '{query}'")
            print("-" * 50)
            
            start_time = time.time()
            result = rag_service.query(
                question=query,
                max_tokens=256,  # Giới hạn để test anti-repetition
                temperature=0.3   # Tăng để tránh lặp
            )
            processing_time = time.time() - start_time
            
            # Extract key metrics
            answer = result['answer']
            sources_count = len(result.get('sources', []))
            tokens_used = result.get('tokens_used', 0)
            llm_time = result.get('llm_processing_time', 0)
            
            # Check for repetition issues
            answer_lines = answer.split('\n')
            repetitive_lines = sum(1 for line in answer_lines if answer_lines.count(line) > 2 and line.strip())
            
            print(f"   ⚡ Total Time: {processing_time:.2f}s")
            print(f"   🧠 LLM Time: {llm_time:.2f}s")
            print(f"   📝 Tokens: {tokens_used}")
            print(f"   📚 Sources: {sources_count}")
            print(f"   🔄 Repetitive Lines: {repetitive_lines}")
            print(f"   📏 Answer Length: {len(answer)} chars")
            print()
            print(f"   💬 Answer Preview:")
            preview = answer[:300].replace('\n', ' ')
            print(f"   {preview}{'...' if len(answer) > 300 else ''}")
            print()
            
            results.append({
                'query': query,
                'processing_time': processing_time,
                'llm_time': llm_time,
                'tokens': tokens_used,
                'sources': sources_count,
                'repetitive_lines': repetitive_lines,
                'answer_length': len(answer),
                'has_repetition_issue': repetitive_lines > 0,
                'answer': answer
            })
        
        # Summary report
        print("="*70)
        print("📊 PERFORMANCE & QUALITY SUMMARY")
        print("="*70)
        
        avg_total_time = sum(r['processing_time'] for r in results) / len(results)
        avg_llm_time = sum(r['llm_time'] for r in results) / len(results)
        total_repetition_issues = sum(1 for r in results if r['has_repetition_issue'])
        
        print(f"⚡ Average Performance:")
        print(f"   • Total Processing: {avg_total_time:.2f}s")
        print(f"   • LLM Generation: {avg_llm_time:.2f}s")
        print(f"   • GPU/CPU Ratio: ~{(1 - avg_llm_time/avg_total_time)*100:.0f}% non-LLM / {(avg_llm_time/avg_total_time)*100:.0f}% LLM")
        print()
        
        print(f"🔄 Quality Assessment:")
        print(f"   • Queries with Repetition Issues: {total_repetition_issues}/{len(results)}")
        print(f"   • System Status: {'✅ FIXED' if total_repetition_issues == 0 else '❌ STILL HAS ISSUES'}")
        
        # Performance recommendations
        print()
        print("🎯 Performance Analysis:")
        if avg_llm_time > 10:
            print("   ⚠️  LLM processing still slow - check GPU utilization")
        elif avg_llm_time < 2:
            print("   ✅ Excellent LLM performance - GPU acceleration working")
        else:
            print("   ✅ Good LLM performance")
            
        if total_repetition_issues == 0:
            print("   ✅ Anti-repetition measures successful")
        else:
            print("   ⚠️  Still has repetition issues - need further tuning")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_optimized_rag())
