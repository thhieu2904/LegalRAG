#!/usr/bin/env python3
"""
Test script nâng cao cho Enhanced Consensus Reranker
Kiểm tra trường hợp "scattered chunks" (3 chunks từ 3 documents khác nhau)
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.app.services.result_reranker import RerankerService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_scattered_test_documents():
    """Tạo test documents với 3 chunks từ 3 documents khác nhau (scattered scenario)"""
    test_docs = [
        # Document A - 1 chunk
        {
            "id": "chunk_a1",
            "content": "Thủ tục đăng ký kết hôn cần có giấy tờ: CMND, hộ khẩu, giấy xác nhận độc thân.",
            "source": {"file_path": "document_A.json", "document_title": "Hướng dẫn kết hôn"},
            "metadata": {"source": {"file_path": "document_A.json"}},
            "similarity": 0.85
        },
        # Document B - 1 chunk
        {
            "id": "chunk_b1",
            "content": "Quy trình ly hôn theo quy định pháp luật hiện hành cần tuân thủ nhiều bước.",
            "source": {"file_path": "document_B.json", "document_title": "Hướng dẫn ly hôn"},
            "metadata": {"source": {"file_path": "document_B.json"}},
            "similarity": 0.82
        },
        # Document C - 1 chunk
        {
            "id": "chunk_c1",
            "content": "Thủ tục nuôi con nuôi yêu cầu hồ sơ đầy đủ và kiểm tra điều kiện gia đình.",
            "source": {"file_path": "document_C.json", "document_title": "Hướng dẫn nuôi con nuôi"},
            "metadata": {"source": {"file_path": "document_C.json"}},
            "similarity": 0.80
        },
        # Document D - 1 chunk (lower score to test filtering)
        {
            "id": "chunk_d1",
            "content": "Các loại hình doanh nghiệp và cách thành lập công ty.",
            "source": {"file_path": "document_D.json", "document_title": "Hướng dẫn thành lập doanh nghiệp"},
            "metadata": {"source": {"file_path": "document_D.json"}},
            "similarity": 0.70
        },
        # Document E - 1 chunk (lower score)
        {
            "id": "chunk_e1",
            "content": "Quy định về thuế thu nhập cá nhân và các khoản miễn giảm.",
            "source": {"file_path": "document_E.json", "document_title": "Hướng dẫn thuế thu nhập"},
            "metadata": {"source": {"file_path": "document_E.json"}},
            "similarity": 0.68
        }
    ]
    
    return test_docs

def create_consensus_test_documents():
    """Tạo test documents với consensus rõ ràng (3 chunks từ cùng 1 document)"""
    test_docs = [
        # Document A - 3 chunks (should win consensus)
        {
            "id": "chunk_a1",
            "content": "Thủ tục đăng ký kết hôn cần có giấy tờ: CMND, hộ khẩu, giấy xác nhận độc thân.",
            "source": {"file_path": "document_A.json", "document_title": "Hướng dẫn kết hôn"},
            "metadata": {"source": {"file_path": "document_A.json"}},
            "similarity": 0.85
        },
        {
            "id": "chunk_a2", 
            "content": "Lệ phí đăng ký kết hôn là 20,000 VNĐ. Thời gian xử lý là 5 ngày làm việc.",
            "source": {"file_path": "document_A.json", "document_title": "Hướng dẫn kết hôn"},
            "metadata": {"source": {"file_path": "document_A.json"}},
            "similarity": 0.83
        },
        {
            "id": "chunk_a3",
            "content": "Địa điểm nộp hồ sơ: UBND phường/xã nơi cư trú của một trong hai bên.",
            "source": {"file_path": "document_A.json", "document_title": "Hướng dẫn kết hôn"},
            "metadata": {"source": {"file_path": "document_A.json"}},
            "similarity": 0.81
        },
        # Document B - 2 chunks (should lose consensus)
        {
            "id": "chunk_b1",
            "content": "Quy trình ly hôn theo quy định pháp luật hiện hành cần tuân thủ nhiều bước.",
            "source": {"file_path": "document_B.json", "document_title": "Hướng dẫn ly hôn"},
            "metadata": {"source": {"file_path": "document_B.json"}},
            "similarity": 0.82
        },
        {
            "id": "chunk_b2",
            "content": "Thủ tục ly hôn đơn phương yêu cầu có đơn khởi kiện và bằng chứng.",
            "source": {"file_path": "document_B.json", "document_title": "Hướng dẫn ly hôn"},
            "metadata": {"source": {"file_path": "document_B.json"}},
            "similarity": 0.80
        }
    ]
    
    return test_docs

def test_scattered_chunks_scenario():
    """Test trường hợp scattered chunks (3 chunks từ 3 documents khác nhau)"""
    logger.info("🧪 TESTING Scattered Chunks Scenario")
    
    reranker = RerankerService()
    test_docs = create_scattered_test_documents()
    query = "thủ tục pháp luật"
    
    logger.info(f"📝 Test query: '{query}'")
    logger.info(f"📊 Test documents: {len(test_docs)} chunks from {len(test_docs)} different documents")
    
    # Test consensus method với scattered chunks
    logger.info("\n🎯 Testing consensus method on scattered chunks:")
    try:
        consensus_doc = reranker.get_consensus_document(
            query=query,
            documents=test_docs,
            top_k=5,
            consensus_threshold=0.6,  # 3/5 = 60%
            min_rerank_score=-0.5  # Low threshold for legal documents
        )
        
        if consensus_doc:
            doc_source = consensus_doc.get('source', {}).get('file_path', 'unknown')
            logger.info(f"✅ Consensus method selected: {doc_source}")
            logger.info(f"   Rerank score: {consensus_doc.get('rerank_score', 'N/A')}")
        else:
            logger.warning("❌ Consensus method returned None")
            
    except Exception as e:
        logger.error(f"❌ Consensus method failed: {e}")
    
    return True

def test_consensus_vs_scattered():
    """So sánh kết quả giữa consensus scenario và scattered scenario"""
    logger.info("\n🔬 COMPARATIVE TEST: Consensus vs Scattered")
    
    reranker = RerankerService()
    query = "thủ tục đăng ký kết hôn"
    
    # Test 1: Consensus scenario
    logger.info("\n📊 SCENARIO 1: Strong Consensus (3 chunks from same document)")
    consensus_docs = create_consensus_test_documents()
    
    consensus_result = reranker.get_consensus_document(
        query=query,
        documents=consensus_docs,
        top_k=5,
        consensus_threshold=0.6,
        min_rerank_score=-0.5
    )
    
    if consensus_result:
        consensus_source = consensus_result.get('source', {}).get('file_path', 'unknown')
        logger.info(f"✅ Consensus scenario selected: {consensus_source}")
    
    # Test 2: Scattered scenario  
    logger.info("\n📊 SCENARIO 2: Scattered Chunks (chunks from different documents)")
    scattered_docs = create_scattered_test_documents()
    
    scattered_result = reranker.get_consensus_document(
        query=query,
        documents=scattered_docs,
        top_k=5,
        consensus_threshold=0.6,
        min_rerank_score=-0.5
    )
    
    if scattered_result:
        scattered_source = scattered_result.get('source', {}).get('file_path', 'unknown')
        logger.info(f"✅ Scattered scenario selected: {scattered_source}")
    
    return True

def test_threshold_sensitivity():
    """Test độ nhạy của consensus threshold"""
    logger.info("\n🔧 TESTING Threshold Sensitivity")
    
    reranker = RerankerService()
    test_docs = create_consensus_test_documents()
    query = "thủ tục đăng ký kết hôn"
    
    thresholds = [0.4, 0.5, 0.6, 0.7, 0.8]
    
    for threshold in thresholds:
        try:
            result = reranker.get_consensus_document(
                query=query,
                documents=test_docs,
                top_k=5,
                consensus_threshold=threshold,
                min_rerank_score=-0.5
            )
            
            if result:
                doc_source = result.get('source', {}).get('file_path', 'unknown')
                logger.info(f"✅ Threshold {threshold}: Selected {doc_source}")
            else:
                logger.info(f"❌ Threshold {threshold}: No consensus found")
                
        except Exception as e:
            logger.error(f"❌ Threshold {threshold} failed: {e}")
    
    return True

if __name__ == "__main__":
    logger.info("🚀 Starting Advanced Consensus Reranker Tests")
    
    # Test scattered chunks scenario
    test_scattered_chunks_scenario()
    
    # Test consensus vs scattered comparison
    test_consensus_vs_scattered()
    
    # Test threshold sensitivity
    test_threshold_sensitivity()
    
    logger.info("\n✅ All advanced tests completed!")
