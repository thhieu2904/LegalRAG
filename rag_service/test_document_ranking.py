#!/usr/bin/env python3
"""
Test script to verify document ranking for birth vs death queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_engine import RAGService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_document_ranking():
    """Test document ranking for birth certificate queries"""
    
    logger.info("🧪 Testing document ranking for birth vs death queries")
    
    # Initialize RAG service
    try:
        # Initialize with default None values to use auto-initialization
        rag_service = RAGService(
            documents_dir=None,
            vectordb_service=None,
            llm_service=None
        )
        logger.info("✅ RAG Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG Service: {e}")
        return
    
    # Test queries
    test_queries = [
        "tôi muốn xin giấy khai sinh cho con",
        "làm thủ tục khai sinh em bé",
        "đăng ký khai sinh",
        "giấy tờ cần thiết để khai sinh",
        "quy trình khai sinh như thế nào"
    ]
    
    for query in test_queries:
        logger.info(f"\n{'='*50}")
        logger.info(f"🔍 Testing query: '{query}'")
        logger.info(f"{'='*50}")
        
        try:
            # Test routing
            routing_result = rag_service.smart_router.route_query(query)
            
            logger.info(f"📍 Routing result:")
            logger.info(f"  - Target collection: {routing_result.get('target_collection')}")
            logger.info(f"  - Confidence: {routing_result.get('confidence', 0):.3f}")
            logger.info(f"  - Status: {routing_result.get('status')}")
            
            if routing_result.get('target_collection'):
                # Test document ranking within collection
                collection = routing_result['target_collection']
                
                # Get document similarities
                if hasattr(rag_service.smart_router, 'get_document_similarities_in_collection'):
                    ranked_docs = rag_service.smart_router.get_document_similarities_in_collection(
                        collection, query, limit=5
                    )
                    
                    logger.info(f"\n📊 Document ranking in collection '{collection}':")
                    for i, (doc_info, score) in enumerate(ranked_docs, 1):
                        confidence_percent = doc_info.get('confidence_percent', round(score * 100, 1))
                        logger.info(f"  {i}. {doc_info['title'][:50]}... → {score:.3f} ({confidence_percent}%)")
                        
                        # Check if "khai tử" documents appear before "khai sinh"
                        if "khai tử" in doc_info['title'].lower() and i <= 3:
                            logger.warning(f"⚠️  'Khai tử' document ranked high for birth query!")
                        elif "khai sinh" in doc_info['title'].lower() and i <= 3:
                            logger.info(f"✅ 'Khai sinh' document correctly ranked high")
                else:
                    logger.warning("❌ get_document_similarities_in_collection method not found")
            
        except Exception as e:
            logger.error(f"❌ Error testing query '{query}': {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info("✅ Document ranking test completed")

if __name__ == "__main__":
    test_document_ranking()
