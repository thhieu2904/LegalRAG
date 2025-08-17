#!/usr/bin/env python3
"""
Test Document Selection Flow - 3-Step Clarific            result2 = self.rag_service.handle_clarification(
                session_id="test_3step",
                selected_option=first_collection,
                original_query="tôi muốn hỏi về việc làm giấy tờ"
            )Process
Kiểm tra luồng mới: Collection → Document → Question
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.rag_engine import OptimizedEnhancedRAGService
from app.services.vector_database import VectorDBService 
from app.services.language_model import LLMService
from app.core.config import settings

class TestDocumentSelectionFlow:
    """Test the 3-step clarification flow"""
    
    def __init__(self):
        self.rag_service = None
        
    def setup(self):
        """Initialize services"""
        print("🔧 Initializing test services...")
        
        # Initialize services
        vectordb_service = VectorDBService()
        llm_service = LLMService()
        
        # Change working directory to backend for correct relative paths
        os.chdir(str(backend_dir))
        
        self.rag_service = OptimizedEnhancedRAGService(
            documents_dir="data/documents",
            vectordb_service=vectordb_service,
            llm_service=llm_service
        )
        
        print("✅ Services initialized successfully")
        
    def test_3_step_flow(self):
        """Test complete 3-step flow: Collection → Document → Question"""
        print("\n" + "="*60)
        print("🔍 Testing 3-Step Document Selection Flow")
        print("="*60)
        
        # Step 1: Send ambiguous query → Get collection suggestions
        print("\n📝 STEP 1: Ambiguous query → Collection selection")
        
        result1 = self.rag_service.enhanced_query(
            query="tôi muốn hỏi về việc làm giấy tờ",
            session_id="test_3step"
        )
        
        print(f"Full result1: {result1}")
        print(f"Type: {result1.get('type')}")
        if result1.get('clarification'):
            suggestions = result1['clarification'].get('suggestions') or result1['clarification'].get('options', [])
            collections = [s['title'] for s in suggestions]
            print(f"Collections offered: {collections}")
        
        # Step 2: Select collection → Get document suggestions  
        print("\n📂 STEP 2: Select collection → Document selection")
        
        # Simulate user selecting first collection
        if result1.get('clarification') and (result1['clarification'].get('suggestions') or result1['clarification'].get('options')):
            suggestions = result1['clarification'].get('suggestions') or result1['clarification'].get('options', [])
            first_collection = suggestions[0]
            
            result2 = self.rag_service.handle_clarification({
                "session_id": "test_3step",
                "action": "proceed_with_collection",
                "selected_option": first_collection,
                "original_query": "Tôi muốn đăng ký giấy tờ"
            })
            
            print(f"Type: {result2.get('type')}")
            if result2.get('clarification'):
                documents = [s['title'] for s in result2['clarification']['suggestions'] if s.get('action') == 'proceed_with_document']
                print(f"Documents offered: {documents[:3]}...")  # Show first 3
                print(f"Total documents: {len(documents)}")
                
                # Step 3: Select document → Get question suggestions
                print("\n📄 STEP 3: Select document → Question selection")
                
                if documents:
                    first_doc_suggestion = None
                    for suggestion in result2['clarification']['suggestions']:
                        if suggestion.get('action') == 'proceed_with_document':
                            first_doc_suggestion = suggestion
                            break
                    
                    if first_doc_suggestion:
                        result3 = self.rag_service.handle_clarification_response({
                            "session_id": "test_3step",
                            "action": "proceed_with_document",
                            "selected_option": first_doc_suggestion,
                            "original_query": "Tôi muốn đăng ký giấy tờ"
                        })
                        
                        print(f"Type: {result3.get('type')}")
                        if result3.get('clarification'):
                            questions = [s['title'] for s in result3['clarification']['suggestions'] if s.get('action') == 'proceed_with_question']
                            print(f"Questions offered: {questions[:2]}...")  # Show first 2
                            print(f"Total questions: {len(questions)}")
                            
                            # Check manual input option
                            manual_options = [s for s in result3['clarification']['suggestions'] if s.get('action') == 'manual_input']
                            if manual_options:
                                print(f"✅ Manual input option available: {manual_options[0]['title']}")
                            else:
                                print("❌ No manual input option found")
                            
                            return True
        
        return False
    
    def test_manual_input_case2(self):
        """Test Case 2: Manual input from document level with context preservation"""
        print("\n" + "="*60)
        print("🔍 Testing Case 2: Document-level Manual Input")
        print("="*60)
        
        # Setup: Go through steps 1-3 to reach document level
        result1 = self.rag_service.enhanced_query(
            query="Tôi muốn đăng ký giấy tờ",
            session_id="test_case2"
        )
        
        if not result1.get('clarification'):
            print("❌ No clarification received in step 1")
            return False
            
        # Step 1→2: Select collection
        first_collection = result1['clarification']['suggestions'][0]
        result2 = self.rag_service.handle_clarification_response({
            "session_id": "test_case2",
            "action": "proceed_with_collection", 
            "selected_option": first_collection,
            "original_query": "Tôi muốn đăng ký giấy tờ"
        })
        
        if not result2.get('clarification'):
            print("❌ No clarification received in step 2")
            return False
            
        # Step 2→3: Select document
        first_doc = None
        for suggestion in result2['clarification']['suggestions']:
            if suggestion.get('action') == 'proceed_with_document':
                first_doc = suggestion
                break
                
        if not first_doc:
            print("❌ No document found in step 2")
            return False
            
        result3 = self.rag_service.handle_clarification_response({
            "session_id": "test_case2",
            "action": "proceed_with_document",
            "selected_option": first_doc,
            "original_query": "Tôi muốn đăng ký giấy tờ"
        })
        
        if not result3.get('clarification'):
            print("❌ No clarification received in step 3")
            return False
            
        # Step 3→Manual: Select manual input at document level
        manual_option = None
        for suggestion in result3['clarification']['suggestions']:
            if suggestion.get('action') == 'manual_input':
                manual_option = suggestion
                break
                
        if not manual_option:
            print("❌ No manual input option found at document level")
            return False
            
        print(f"📄 Document selected: {first_doc['document_title']}")
        print(f"🔧 Testing manual input: {manual_option['title']}")
        
        # Trigger manual input
        manual_result = self.rag_service.handle_clarification_response({
            "session_id": "test_case2",
            "action": "manual_input",
            "selected_option": manual_option,
            "original_query": "Tôi muốn đăng ký giấy tờ"
        })
        
        print(f"Manual input type: {manual_result.get('type')}")
        print(f"Context preserved: {manual_result.get('context_preserved')}")
        print(f"Preserved collection: {manual_result.get('preserved_collection')}")
        print(f"Preserved document: {manual_result.get('preserved_document')}")
        
        if manual_result.get('context_preserved') and manual_result.get('preserved_document'):
            print("✅ CASE 2: Document context preserved successfully!")
            
            # Test follow-up query uses document context
            print("\n🔄 Testing follow-up query with document context...")
            
            followup_result = self.rag_service.enhanced_query(
                query="Cần giấy tờ gì để làm thủ tục này?",
                session_id="test_case2"
            )
            
            print(f"Follow-up result type: {followup_result.get('type')}")
            if followup_result.get('type') != 'clarification_needed':
                print("✅ Follow-up query processed directly (using preserved context)")
                return True
            else:
                print("⚠️ Follow-up query still needs clarification")
                return False
        else:
            print("❌ CASE 2: Document context NOT preserved")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Document Selection Flow Tests")
        print("="*60)
        
        self.setup()
        
        # Test 1: 3-step flow
        test1_passed = self.test_3_step_flow()
        
        # Test 2: Manual input Case 2
        test2_passed = self.test_manual_input_case2()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        print(f"✅ 3-Step Flow: {'PASSED' if test1_passed else 'FAILED'}")
        print(f"✅ Case 2 Manual Input: {'PASSED' if test2_passed else 'FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 ALL TESTS PASSED! Document selection flow working correctly.")
        else:
            print("\n❌ Some tests failed. Check implementation.")
            
        return test1_passed and test2_passed

def main():
    """Main test function"""
    tester = TestDocumentSelectionFlow()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
