#!/usr/bin/env python3
"""
TEST PHASE 1 ROUTER OPTIMIZATION
================================

Test script to verify that Phase 1 signal optimization fixes the router confusion
between DOC_008 vs DOC_002 for Vietnamese birth registration queries.

Key test case:
- Query: "tôi cần làm giấy khai sinh cho con trai tôi, cha nó là người nước ngoài"
- Expected: Should route to DOC_002 (simple birth registration)
- Previous: Was incorrectly routing to DOC_008 (complex procedures)
"""

import sys
import os
import json
from pathlib import Path
import logging

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.router import QueryRouter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_router_optimization():
    """Test Phase 1 router optimization"""
    logger.info("🧪 TESTING PHASE 1 ROUTER OPTIMIZATION")
    logger.info("=" * 50)
    
    try:
        # Initialize router
        logger.info("🔄 Initializing QueryRouter...")
        # Load embedding model
        from sentence_transformers import SentenceTransformer
        from app.core.config import settings
        
        logger.info("Loading Vietnamese embedding model...")
        model_path = Path(backend_dir) / "data/models/hf_cache/hub/models--AITeamVN--Vietnamese_Embedding_v2/snapshots/18b44161e041bf1d3a333ab5144b5b7b93f914d2"
        if model_path.exists():
            embedding_model = SentenceTransformer(str(model_path))
            logger.info("✅ Loaded local Vietnamese embedding model")
        else:
            embedding_model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2")
            logger.info("✅ Loaded Vietnamese embedding model from HuggingFace")
        
        # Change working directory to backend for proper paths
        original_dir = os.getcwd()
        os.chdir(backend_dir)
        
        router = QueryRouter(embedding_model=embedding_model)
        
        # Test cases
        test_cases = [
            {
                "query": "tôi cần làm giấy khai sinh cho con trai tôi, cha nó là người nước ngoài",
                "expected_collection": "quy_trinh_cap_ho_tich_cap_xa",
                "expected_doc": "DOC_002",  # Should be simple birth registration
                "description": "Birth registration for child with foreign father"
            },
            {
                "query": "làm giấy khai sinh cho trẻ em có cha mẹ nước ngoài",
                "expected_collection": "quy_trinh_cap_ho_tich_cap_xa", 
                "expected_doc": "DOC_002",
                "description": "Birth registration for child with foreign parents"
            },
            {
                "query": "thủ tục khai sinh khi có cha nước ngoài",
                "expected_collection": "quy_trinh_cap_ho_tich_cap_xa",
                "expected_doc": "DOC_002", 
                "description": "Birth registration procedure with foreign father"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n📝 Test Case {i}: {test_case['description']}")
            logger.info(f"Query: '{test_case['query']}'")
            logger.info(f"Expected: {test_case['expected_collection']}/{test_case['expected_doc']}")
            
            try:
                # Route query
                route_result = router.route_query(test_case['query'])
                
                # Extract results
                collection = route_result.get('target_collection')
                best_match = route_result.get('best_match', {})
                doc_id = best_match.get('document')
                confidence = route_result.get('confidence', 0)
                status = route_result.get('status', 'unknown')
                
                logger.info(f"Result: {collection}/{doc_id}")
                logger.info(f"Confidence: {confidence:.4f}")
                logger.info(f"Status: {status}")
                
                # Check if correct
                is_correct = (collection == test_case['expected_collection'] and 
                            doc_id == test_case['expected_doc'])
                
                result = {
                    'test_case': i,
                    'query': test_case['query'],
                    'expected': f"{test_case['expected_collection']}/{test_case['expected_doc']}",
                    'actual': f"{collection}/{doc_id}",
                    'confidence': confidence,
                    'status': status,
                    'correct': is_correct,
                    'description': test_case['description']
                }
                
                results.append(result)
                
                if is_correct:
                    logger.info("✅ CORRECT - Router selected expected document")
                else:
                    logger.info("❌ INCORRECT - Router confusion detected")
                    
                    # Try to understand why it failed
                    if collection != test_case['expected_collection']:
                        logger.info(f"   Collection mismatch: got {collection}, expected {test_case['expected_collection']}")
                    if doc_id != test_case['expected_doc']:
                        logger.info(f"   Document mismatch: got {doc_id}, expected {test_case['expected_doc']}")
                
            except Exception as e:
                logger.error(f"❌ Error testing case {i}: {e}")
                result = {
                    'test_case': i,
                    'query': test_case['query'],
                    'expected': f"{test_case['expected_collection']}/{test_case['expected_doc']}",
                    'actual': f"ERROR: {str(e)}",
                    'confidence': 0,
                    'status': 'error',
                    'correct': False,
                    'description': test_case['description']
                }
                results.append(result)
        
        # Summary
        logger.info("\n📊 PHASE 1 OPTIMIZATION TEST SUMMARY")
        logger.info("=" * 50)
        
        correct_count = sum(1 for r in results if r['correct'])
        total_count = len(results)
        success_rate = (correct_count / total_count) * 100 if total_count > 0 else 0
        
        logger.info(f"Total Test Cases: {total_count}")
        logger.info(f"Correct Routes: {correct_count}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        # Show detailed results
        logger.info("\n📋 DETAILED RESULTS:")
        for result in results:
            status = "✅" if result['correct'] else "❌"
            logger.info(f"{status} Case {result['test_case']}: {result['description']}")
            logger.info(f"   Expected: {result['expected']}")
            logger.info(f"   Actual: {result['actual']}")
            logger.info(f"   Confidence: {result['confidence']:.4f}")
            logger.info("")
        
        # Phase 1 assessment
        if success_rate >= 80:
            logger.info("🎉 PHASE 1 OPTIMIZATION: SUCCESS!")
            logger.info("Router confusion significantly reduced")
        elif success_rate >= 50:
            logger.info("⚠️ PHASE 1 OPTIMIZATION: PARTIAL SUCCESS")
            logger.info("Some improvement detected, but more work needed")
        else:
            logger.info("❌ PHASE 1 OPTIMIZATION: NEEDS MORE WORK")
            logger.info("Router confusion still present")
        
        # Restore original directory
        os.chdir(original_dir)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Fatal error in router test: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Main test function"""
    results = test_router_optimization()
    
    # Save results to file
    results_file = Path(__file__).parent / "phase1_test_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n💾 Results saved to: {results_file}")

if __name__ == "__main__":
    main()
