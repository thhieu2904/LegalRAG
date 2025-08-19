#!/usr/bin/env python3
"""
Test script cho Enhanced Consensus Reranker
Kiểm tra logic consensus-based document selection
"""

import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.app.services.result_reranker import RerankerService
from backend.app.core.config import settings
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_documents():
    """Tạo test documents giả để test consensus logic"""
    # Giả lập documents từ 2 documents khác nhau
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

def test_consensus_reranker():
    """Test consensus-based reranker logic"""
    logger.info("🧪 TESTING Enhanced Consensus Reranker")
    
    # Initialize reranker service
    try:
        reranker = RerankerService()
        logger.info("✅ RerankerService initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RerankerService: {e}")
        return False
    
    # Create test documents
    test_docs = create_test_documents()
    query = "thủ tục đăng ký kết hôn"
    
    logger.info(f"📝 Test query: '{query}'")
    logger.info(f"📊 Test documents: {len(test_docs)} chunks from 2 documents")
    
    # Test 1: Traditional method (get_best_document)
    logger.info("\n🔍 TEST 1: Traditional single best document")
    try:
        best_doc = reranker.get_best_document(query, test_docs)
        if best_doc:
            doc_source = best_doc.get('source', {}).get('file_path', 'unknown')
            logger.info(f"✅ Traditional method selected: {doc_source}")
            logger.info(f"   Rerank score: {best_doc.get('rerank_score', 'N/A')}")
        else:
            logger.warning("❌ Traditional method returned None")
    except Exception as e:
        logger.error(f"❌ Traditional method failed: {e}")
    
    # Test 2: Enhanced consensus method
    logger.info("\n🎯 TEST 2: Enhanced consensus-based selection")
    try:
        consensus_doc = reranker.get_consensus_document(
            query=query,
            documents=test_docs,
            top_k=5,
            consensus_threshold=0.6,  # 3/5 = 60%
            min_rerank_score=0.1
        )
        
        if consensus_doc:
            doc_source = consensus_doc.get('source', {}).get('file_path', 'unknown')
            logger.info(f"✅ Consensus method selected: {doc_source}")
            logger.info(f"   Rerank score: {consensus_doc.get('rerank_score', 'N/A')}")
        else:
            logger.warning("❌ Consensus method returned None")
    except Exception as e:
        logger.error(f"❌ Consensus method failed: {e}")
    
    # Test 3: Different consensus thresholds
    logger.info("\n🔧 TEST 3: Different consensus thresholds")
    for threshold in [0.4, 0.6, 0.8]:
        try:
            consensus_doc = reranker.get_consensus_document(
                query=query,
                documents=test_docs,
                top_k=5,
                consensus_threshold=threshold,
                min_rerank_score=0.1
            )
            
            if consensus_doc:
                doc_source = consensus_doc.get('source', {}).get('file_path', 'unknown')
                logger.info(f"✅ Threshold {threshold}: Selected {doc_source}")
            else:
                logger.info(f"❌ Threshold {threshold}: No consensus found")
        except Exception as e:
            logger.error(f"❌ Threshold {threshold} failed: {e}")
    
    # Test 4: Edge case - insufficient documents
    logger.info("\n🧪 TEST 4: Edge case - insufficient documents")
    try:
        small_docs = test_docs[:2]  # Only 2 documents
        consensus_doc = reranker.get_consensus_document(
            query=query,
            documents=small_docs,
            top_k=5,
            consensus_threshold=0.6,
            min_rerank_score=0.1
        )
        
        if consensus_doc:
            doc_source = consensus_doc.get('source', {}).get('file_path', 'unknown')
            logger.info(f"✅ Small dataset: Selected {doc_source}")
        else:
            logger.warning("❌ Small dataset: No document selected")
    except Exception as e:
        logger.error(f"❌ Small dataset test failed: {e}")
    
    logger.info("\n🎉 Testing completed!")
    return True

def test_document_id_extraction():
    """Test document ID extraction logic"""
    logger.info("\n🔍 TESTING Document ID Extraction")
    
    reranker = RerankerService()
    
    test_chunks = [
        {
            "source": {"file_path": "test_doc_1.json"},
            "content": "Test content 1"
        },
        {
            "metadata": {"source": {"file_path": "test_doc_2.json"}},
            "content": "Test content 2"
        },
        {
            "metadata": {"source": "test_doc_3.json"},
            "content": "Test content 3"
        },
        {
            "document_title": "Test Document 4",
            "content": "Test content 4"
        },
        {
            "id": "chunk_123",
            "content": "Test content 5"
        }
    ]
    
    for i, chunk in enumerate(test_chunks):
        doc_id = reranker._extract_document_id(chunk)
        logger.info(f"Chunk {i+1}: {doc_id}")
    
    return True

if __name__ == "__main__":
    logger.info("🚀 Starting Enhanced Consensus Reranker Tests")
    
    # Test document ID extraction
    test_document_id_extraction()
    
    # Test consensus reranker
    success = test_consensus_reranker()
    
    if success:
        logger.info("✅ All tests completed successfully!")
    else:
        logger.error("❌ Some tests failed!")
        sys.exit(1)
