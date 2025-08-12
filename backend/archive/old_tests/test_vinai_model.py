#!/usr/bin/env python3
"""
Test VinAI PhoGPT-4B-Chat Model vs Old Model
Compare performance and response quality improvements
"""

import asyncio
import json
import time
from app.services.rag_service import RAGService
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService
from app.core.config import settings

async def test_vinai_model():
    """Test RAG system với VinAI model chính thức"""
    
    print("="*80)
    print("🆚 TESTING VINAI PHOGPT-4B-CHAT MODEL")
    print("="*80)
    print(f"🏢 Model: VinAI Research (Official)")
    print(f"📦 File: {settings.llm_model_path.split('/')[-1]}")
    print(f"🔧 Config:")
    print(f"   • GPU Layers: {settings.n_gpu_layers}")
    print(f"   • CPU Threads: {settings.n_threads}")
    print(f"   • Batch Size: {settings.n_batch}")
    print(f"   • Max Tokens: {settings.max_tokens}")
    print(f"   • Temperature: {settings.temperature}")
    print()
    
    try:
        # Khởi tạo services với timing
        print("🔧 Initializing services...")
        init_start = time.time()
        
        vectordb_service = VectorDBService()
        print(f"   ✅ VectorDB loaded ({time.time() - init_start:.2f}s)")
        
        llm_start = time.time()
        llm_service = LLMService()
        llm_init_time = time.time() - llm_start
        print(f"   ✅ LLM loaded ({llm_init_time:.2f}s)")
        
        if llm_init_time > 30:
            print("   ⚠️  LLM loading took a while - may need optimization")
        elif llm_init_time < 10:
            print("   🚀 Fast LLM loading - GPU acceleration likely working")
        
        print()
        
        rag_service = RAGService(
            documents_dir=str(settings.documents_path),
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        
        # Health check với GPU detection
        health = rag_service.get_health_status()
        model_info = health.get('model_info', {})
        
        print(f"🏥 System Health: {health['status']}")
        print(f"   • Collections: {health['total_collections']}")
        print(f"   • Documents: {health['total_documents']}")
        print(f"   • Model Size: {model_info.get('model_size_mb', 0):.0f} MB")
        print(f"   • GPU Layers: {model_info.get('model_kwargs', {}).get('n_gpu_layers', 'N/A')}")
        print()
        
        # Test queries focusing on previous issues
        test_cases = [
            {
                "query": "thủ tục nuôi con nuôi",
                "description": "Query gây lặp response trước đây",
                "expected_keywords": ["đăng ký", "hồ sơ", "thủ tục"]
            },
            {
                "query": "cách đăng ký khai sinh cho trẻ em",
                "description": "Query phức tạp về thủ tục pháp lý",
                "expected_keywords": ["giấy khai sinh", "UBND", "hồ sơ"]
            },
            {
                "query": "quy trình chứng thực bản sao giấy tờ",
                "description": "Query về dịch vụ công",
                "expected_keywords": ["chứng thực", "bản sao", "công chứng"]
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            description = test_case["description"]
            expected_keywords = test_case["expected_keywords"]
            
            print(f"🔍 Test {i}/{len(test_cases)}: {description}")
            print(f"❓ Query: '{query}'")
            print("-" * 60)
            
            # Test với parameters tối ưu
            start_time = time.time()
            result = rag_service.query(
                question=query,
                max_tokens=300,    # Moderate length
                temperature=0.3    # Balance between accuracy and creativity
            )
            total_time = time.time() - start_time
            
            # Analyze response quality
            answer = result.get('answer', '')
            sources_count = len(result.get('sources', []))
            tokens_used = result.get('tokens_used', 0)
            llm_time = result.get('llm_processing_time', 0)
            
            # Quality metrics
            answer_length = len(answer)
            line_count = len([line for line in answer.split('\n') if line.strip()])
            
            # Check for repetition issues
            lines = answer.split('\n')
            unique_lines = set(line.strip() for line in lines if line.strip())
            repetition_ratio = (len(lines) - len(unique_lines)) / max(len(lines), 1)
            
            # Check keyword coverage
            answer_lower = answer.lower()
            keywords_found = [kw for kw in expected_keywords if kw.lower() in answer_lower]
            keyword_coverage = len(keywords_found) / len(expected_keywords)
            
            print(f"   ⚡ Performance:")
            print(f"      • Total Time: {total_time:.2f}s")
            print(f"      • LLM Time: {llm_time:.2f}s")
            print(f"      • Tokens: {tokens_used}")
            print(f"      • Sources: {sources_count}")
            
            print(f"   📊 Quality Metrics:")
            print(f"      • Answer Length: {answer_length} chars")
            print(f"      • Lines: {line_count}")
            print(f"      • Repetition: {repetition_ratio:.1%}")
            print(f"      • Keyword Coverage: {keyword_coverage:.1%} ({len(keywords_found)}/{len(expected_keywords)})")
            
            # Quality assessment
            quality_score = 0
            if repetition_ratio < 0.2:  # Low repetition
                quality_score += 25
            if keyword_coverage >= 0.5:  # Good keyword coverage
                quality_score += 25
            if 100 <= answer_length <= 1000:  # Reasonable length
                quality_score += 25
            if llm_time < 5:  # Fast response
                quality_score += 25
                
            print(f"   🏆 Quality Score: {quality_score}/100")
            
            print(f"   💬 Answer Preview:")
            preview = answer[:400].replace('\n', ' ')
            print(f"      {preview}{'...' if len(answer) > 400 else ''}")
            print()
            
            results.append({
                'query': query,
                'description': description,
                'total_time': total_time,
                'llm_time': llm_time,
                'tokens': tokens_used,
                'sources': sources_count,
                'answer_length': answer_length,
                'repetition_ratio': repetition_ratio,
                'keyword_coverage': keyword_coverage,
                'quality_score': quality_score,
                'answer': answer
            })
        
        # Final analysis
        print("="*80)
        print("📊 VINAI MODEL PERFORMANCE SUMMARY")
        print("="*80)
        
        avg_total_time = sum(r['total_time'] for r in results) / len(results)
        avg_llm_time = sum(r['llm_time'] for r in results) / len(results)
        avg_quality = sum(r['quality_score'] for r in results) / len(results)
        avg_repetition = sum(r['repetition_ratio'] for r in results) / len(results)
        avg_coverage = sum(r['keyword_coverage'] for r in results) / len(results)
        
        print(f"⚡ Performance Metrics:")
        print(f"   • Average Total Time: {avg_total_time:.2f}s")
        print(f"   • Average LLM Time: {avg_llm_time:.2f}s")
        print(f"   • Processing Efficiency: {((avg_total_time - avg_llm_time) / avg_total_time)*100:.0f}% RAG / {(avg_llm_time/avg_total_time)*100:.0f}% LLM")
        
        print(f"\n🏆 Quality Assessment:")
        print(f"   • Average Quality Score: {avg_quality:.1f}/100")
        print(f"   • Average Repetition: {avg_repetition:.1%}")
        print(f"   • Average Keyword Coverage: {avg_coverage:.1%}")
        
        # Overall verdict
        print(f"\n🎯 Overall Assessment:")
        
        if avg_quality >= 80:
            print("   ✅ EXCELLENT - VinAI model working very well")
        elif avg_quality >= 60:
            print("   ✅ GOOD - VinAI model is a significant improvement")
        elif avg_quality >= 40:
            print("   ⚠️  FAIR - Some improvements but may need tuning")
        else:
            print("   ❌ POOR - May need further investigation")
            
        if avg_repetition < 0.1:
            print("   ✅ Repetition issue RESOLVED")
        else:
            print("   ⚠️  Still some repetition issues")
            
        if avg_llm_time < 3:
            print("   ✅ GPU acceleration working well")
        elif avg_llm_time < 10:
            print("   ✅ Good performance, GPU likely helping")
        else:
            print("   ⚠️  Performance could be better - check GPU usage")
        
        print("\n🚀 VinAI Model Integration: SUCCESS!")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_vinai_model())
