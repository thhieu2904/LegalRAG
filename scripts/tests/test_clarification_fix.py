#!/usr/bin/env python3
"""
Test script for clarification system fix
========================================

Test the new embedding-based similarity matching in Step 2→3 clarification flow
"""

import sys
import os
import logging
import time
import json
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rag_engine import OptimizedEnhancedRAGService
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClarificationFixTester:
    """Test the embedding-based clarification fix"""
    
    def __init__(self):
        logger.info("🚀 Initializing Clarification Fix Tester...")
        
        # Initialize RAG service
        self.rag_service = OptimizedEnhancedRAGService()
        
        logger.info("✅ RAG Service initialized")
    
    def test_death_registration_scenario(self):
        """
        Test the specific scenario from user's report:
        - Original query about death registration
        - Should show relevant death procedures, not birth registration
        """
        logger.info("\n" + "="*80)
        logger.info("🧪 TESTING: Death Registration Clarification Scenario")
        logger.info("="*80)
        
        # Step 1: Send ambiguous query that should trigger clarification
        original_query = "làm sao để khai tử người thân"
        logger.info(f"📝 Original Query: {original_query}")
        
        try:
            # Make initial query that should trigger clarification
            result = self.rag_service.enhanced_query(original_query)
            
            logger.info(f"📊 Result type: {result.get('type')}")
            
            if result.get('type') == 'clarification_needed':
                # Extract session ID and clarification options
                session_id = result.get('session_id')
                clarification = result.get('clarification', {})
                options = clarification.get('options', [])
                
                logger.info(f"🔑 Session ID: {session_id}")
                logger.info(f"💬 Clarification message: {clarification.get('message', 'N/A')}")
                logger.info(f"📋 Available options: {len(options)}")
                
                # Find and select the ho_tich_cap_xa collection option
                selected_option = None
                for option in options:
                    if option.get('collection') == 'ho_tich_cap_xa':
                        selected_option = option
                        break
                
                if selected_option:
                    logger.info(f"✅ Found ho_tich_cap_xa option: {selected_option.get('title')}")
                    
                    # Step 2→3: Send clarification response to get question suggestions
                    logger.info("\n🎯 STEP 2→3: Testing embedding-based question suggestions...")
                    
                    clarification_result = self.rag_service.handle_clarification(
                        session_id=session_id,
                        selected_option=selected_option,
                        original_query=original_query
                    )
                    
                    logger.info(f"📊 Clarification result type: {clarification_result.get('type')}")
                    
                    if clarification_result.get('type') == 'clarification_needed':
                        step3_clarification = clarification_result.get('clarification', {})
                        step3_options = step3_clarification.get('options', [])
                        similarity_used = step3_clarification.get('similarity_used', False)
                        
                        logger.info(f"🔍 Similarity-based matching used: {similarity_used}")
                        logger.info(f"📋 Question suggestions: {len(step3_options)}")
                        
                        # Analyze the suggestions
                        logger.info(f"\n📝 QUESTION SUGGESTIONS ANALYSIS:")
                        logger.info(f"-" * 60)
                        
                        death_related_count = 0
                        birth_related_count = 0
                        
                        for i, option in enumerate(step3_options[:5]):  # Skip "Other" option
                            title = option.get('title', '')
                            description = option.get('description', '')
                            similarity = option.get('similarity', 'N/A')
                            
                            logger.info(f"{i+1}. {title}")
                            logger.info(f"   Description: {description}")
                            if isinstance(similarity, float):
                                logger.info(f"   Similarity: {similarity:.3f}")
                            
                            # Check if suggestion is relevant to death registration
                            if any(keyword in title.lower() for keyword in ['tử', 'chết', 'qua đời', 'khai tử']):
                                death_related_count += 1
                                logger.info(f"   ✅ RELEVANT to death registration")
                            elif any(keyword in title.lower() for keyword in ['sinh', 'khai sinh', 'birth']):
                                birth_related_count += 1
                                logger.info(f"   ❌ NOT RELEVANT (birth registration)")
                            else:
                                logger.info(f"   ⚪ Other procedure")
                            
                            logger.info("")
                        
                        # Evaluation
                        logger.info(f"\n📊 EVALUATION RESULTS:")
                        logger.info(f"   Death-related suggestions: {death_related_count}")
                        logger.info(f"   Birth-related suggestions: {birth_related_count}")
                        logger.info(f"   Embedding similarity used: {similarity_used}")
                        
                        if similarity_used and death_related_count > birth_related_count:
                            logger.info(f"✅ SUCCESS: Fix working correctly! More relevant suggestions found.")
                        elif not similarity_used:
                            logger.info(f"⚠️  WARNING: Embedding similarity not used, using fallback")
                        else:
                            logger.info(f"❌ ISSUE: Still showing irrelevant suggestions")
                        
                        return {
                            'success': similarity_used and death_related_count > 0,
                            'similarity_used': similarity_used,
                            'death_related_count': death_related_count,
                            'birth_related_count': birth_related_count,
                            'suggestions': step3_options[:5]
                        }
                    
                    else:
                        logger.error(f"❌ Unexpected clarification result type: {clarification_result.get('type')}")
                        return {'success': False, 'error': 'Unexpected result type'}
                
                else:
                    logger.error(f"❌ Could not find ho_tich_cap_xa collection option")
                    logger.info(f"Available options: {[opt.get('collection') for opt in options]}")
                    return {'success': False, 'error': 'Collection option not found'}
                    
            else:
                logger.warning(f"⚠️  Query did not trigger clarification (type: {result.get('type')})")
                return {'success': False, 'error': 'No clarification triggered'}
                
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def test_smart_router_similarity_method(self):
        """Test the new get_similar_procedures_for_collection method directly"""
        logger.info("\n" + "="*80)
        logger.info("🧪 TESTING: Smart Router Similarity Method")
        logger.info("="*80)
        
        try:
            smart_router = self.rag_service.smart_router
            
            # Test with death registration query
            reference_query = "làm sao để khai tử người thân"
            collection_name = "ho_tich_cap_xa"
            
            logger.info(f"📝 Reference Query: {reference_query}")
            logger.info(f"🗂️  Collection: {collection_name}")
            
            # Get similar procedures
            similar_procedures = smart_router.get_similar_procedures_for_collection(
                collection_name=collection_name,
                reference_query=reference_query,
                top_k=5
            )
            
            logger.info(f"📊 Found {len(similar_procedures)} similar procedures")
            
            if similar_procedures:
                logger.info(f"\n🔍 SIMILARITY RESULTS:")
                logger.info(f"-" * 60)
                
                for i, proc in enumerate(similar_procedures):
                    logger.info(f"{i+1}. {proc['text'][:80]}...")
                    logger.info(f"   Similarity: {proc['similarity']:.3f}")
                    logger.info(f"   Source: {proc['source']}")
                    logger.info("")
                
                return {
                    'success': True,
                    'procedure_count': len(similar_procedures),
                    'top_similarity': similar_procedures[0]['similarity'] if similar_procedures else 0,
                    'procedures': similar_procedures
                }
            else:
                logger.warning(f"⚠️  No similar procedures found")
                return {'success': False, 'error': 'No similar procedures found'}
                
        except Exception as e:
            logger.error(f"❌ Similarity method test failed: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def run_all_tests(self):
        """Run all tests and provide summary"""
        logger.info("\n🚀 RUNNING ALL CLARIFICATION FIX TESTS")
        logger.info("=" * 80)
        
        results = {}
        
        # Test 1: Smart router similarity method
        results['similarity_method'] = self.test_smart_router_similarity_method()
        
        # Test 2: Full clarification scenario
        results['clarification_scenario'] = self.test_death_registration_scenario()
        
        # Summary
        logger.info("\n📊 TEST SUMMARY")
        logger.info("=" * 80)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result.get('success') else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
            
            if not result.get('success') and result.get('error'):
                logger.info(f"  Error: {result['error']}")
        
        overall_success = all(result.get('success') for result in results.values())
        
        if overall_success:
            logger.info(f"\n🎉 ALL TESTS PASSED! The clarification fix is working correctly.")
        else:
            logger.info(f"\n⚠️  SOME TESTS FAILED. Please check the issues above.")
        
        return overall_success, results

def main():
    """Main test function"""
    logger.info("🧪 LegalRAG Clarification System Fix Test")
    logger.info("=" * 80)
    
    try:
        tester = ClarificationFixTester()
        success, results = tester.run_all_tests()
        
        # Save results to file
        results_file = Path(__file__).parent / "test_results_clarification_fix.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📁 Test results saved to: {results_file}")
        
        if success:
            logger.info(f"\n✅ CONCLUSION: Clarification fix is working correctly!")
            return 0
        else:
            logger.info(f"\n❌ CONCLUSION: Some issues detected, please review test results")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
