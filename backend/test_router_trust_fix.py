"""
Test script để verify Router Trust Fix
Kiểm tra xem reranker có respect high-confidence router decisions không
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.router import QueryRouter
from app.services.reranker import RerankerService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_router_trust_fix():
    """Test router trust mode với high confidence"""
    
    print("🧪 TESTING ROUTER TRUST FIX")
    print("="*50)
    
    # Initialize services
    router = QueryRouter()
    reranker = RerankerService()
    
    # Test query
    query = "đăng ký kết hôn cần giấy tờ gì"
    
    print(f"📝 Test Query: {query}")
    print()
    
    # Step 1: Test router decision
    print("1️⃣ ROUTER DECISION:")
    routing_result = router.route_query(query)
    
    router_confidence = routing_result.get('confidence', 0.0)
    router_confidence_level = routing_result.get('confidence_level', 'low')
    recommended_documents = routing_result.get('recommended_documents', [])
    
    print(f"   🎯 Router Confidence: {router_confidence:.4f} ({router_confidence_level})")
    print(f"   📄 Recommended Documents: {len(recommended_documents)}")
    
    if recommended_documents:
        top_doc = recommended_documents[0]
        print(f"   🏆 Top Document: {top_doc.get('document_id', 'Unknown')} (score: {top_doc.get('score', 0.0):.4f})")
    
    print()
    
    # Step 2: Test reranker with router trust
    print("2️⃣ RERANKER WITH ROUTER TRUST:")
    
    if recommended_documents and len(recommended_documents) >= 5:
        # Test get_consensus_document với router confidence
        consensus_result = reranker.get_consensus_document(
            query=query,
            documents=recommended_documents[:5],  # Top 5
            top_k=5,
            consensus_threshold=0.6,
            min_rerank_score=-0.5,
            router_confidence=router_confidence,
            router_confidence_level=router_confidence_level
        )
        
        if consensus_result:
            consensus_doc_id = None
            # Extract document ID from consensus result
            if 'metadata' in consensus_result:
                metadata = consensus_result['metadata']
                if 'document_path' in metadata:
                    doc_path = metadata['document_path']
                    # Extract DOC_XXX from path
                    import re
                    match = re.search(r'DOC_(\d+)', doc_path)
                    if match:
                        consensus_doc_id = f"DOC_{match.group(1)}"
            
            print(f"   ✅ Consensus Result: {consensus_doc_id or 'Unknown'}")
            
            # Check if router trust mode was triggered
            if router_confidence > 0.85:
                expected_doc_id = top_doc.get('document_id', 'Unknown')
                if consensus_doc_id == expected_doc_id:
                    print(f"   🎯 ✅ ROUTER TRUST MODE WORKING: High confidence {router_confidence:.3f} > 0.85")
                    print(f"   📄 Reranker respected router decision: {consensus_doc_id}")
                else:
                    print(f"   ❌ ROUTER TRUST MODE FAILED: Expected {expected_doc_id}, got {consensus_doc_id}")
            else:
                print(f"   📊 Normal reranking mode (confidence {router_confidence:.3f} <= 0.85)")
        else:
            print("   ❌ No consensus result")
    else:
        print("   ⚠️  Not enough documents for consensus test")
    
    print()
    
    # Step 3: Summary
    print("3️⃣ TEST SUMMARY:")
    
    expected_doc = "DOC_011"  # Normal marriage registration
    avoid_doc = "DOC_031"     # Mobile marriage registration
    
    if recommended_documents:
        top_router_doc = recommended_documents[0].get('document_id', 'Unknown')
        
        if top_router_doc == expected_doc:
            print(f"   ✅ Router correctly selected: {expected_doc}")
        else:
            print(f"   ❌ Router selected wrong document: {top_router_doc} (expected {expected_doc})")
        
        if router_confidence > 0.85:
            print(f"   ✅ High confidence detected: {router_confidence:.3f} > 0.85")
            print(f"   🎯 Router trust mode should be active")
        else:
            print(f"   📊 Normal confidence: {router_confidence:.3f} <= 0.85")
    
    print("="*50)

if __name__ == "__main__":
    test_router_trust_fix()
