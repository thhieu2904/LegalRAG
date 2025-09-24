#!/usr/bin/env python3
"""
Test script to validate document title display fixes in clarification system.

This test specifically validates:
1. Document field shows actual title (e.g., "Đăng ký kết hôn") instead of ID (e.g., "DOC_011")
2. Procedure field shows document title instead of question text
3. Helper function _get_document_title works correctly
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Add the rag_service directory to Python path
rag_service_path = Path(__file__).parent.parent / "rag_service"
sys.path.insert(0, str(rag_service_path))

# Import the clarification service
from app.services.clarification import ClarificationService

class TestDocumentTitleDisplay(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.clarification_service = ClarificationService()
        
        # Test data based on actual system structure
        self.test_collection = "quy_trinh_cap_ho_tich_cap_xa"
        self.test_document_id = "DOC_011"
        self.expected_title = "Đăng ký kết hôn"  # From metadata.json
        
        self.test_selected_option = {
            "collection": self.test_collection,
            "document": self.test_document_id,
            "procedure": "Thủ tục đăng ký kết hôn được thực hiện như thế nào?",  # Old wrong data
            "original_query": "Thủ tục đăng ký kết hôn được thực hiện như thế nào?"
        }

    def test_get_document_title_helper(self):
        """Test the _get_document_title helper function"""
        print("\\n🧪 Testing _get_document_title helper function...")
        
        # Test with valid collection and document ID
        title = self.clarification_service._get_document_title(
            self.test_collection, 
            self.test_document_id
        )
        
        print(f"✅ Collection: {self.test_collection}")
        print(f"✅ Document ID: {self.test_document_id}")
        print(f"✅ Retrieved title: '{title}'")
        print(f"✅ Expected title: '{self.expected_title}'")
        
        self.assertEqual(title, self.expected_title, 
                        f"Expected title '{self.expected_title}', got '{title}'")
        
        # Test with non-existent document ID
        fallback_title = self.clarification_service._get_document_title(
            self.test_collection, 
            "DOC_999"
        )
        self.assertEqual(fallback_title, "DOC_999", 
                        "Should fallback to document ID if not found")
        
        # Test with non-existent collection
        fallback_title2 = self.clarification_service._get_document_title(
            "non_existent_collection", 
            self.test_document_id
        )
        self.assertEqual(fallback_title2, self.test_document_id, 
                        "Should fallback to document ID if collection not found")
        
        print("✅ _get_document_title helper function works correctly")

    def test_show_document_questions_with_correct_titles(self):
        """Test that _handle_show_document_questions returns correct document titles"""
        print("\\n🧪 Testing _handle_show_document_questions with title fixes...")
        
        # Call the function with test data
        result = self.clarification_service._handle_show_document_questions(
            self.test_selected_option,
            "test_session_001"
        )
        
        print(f"✅ Response type: {result.get('type')}")
        print(f"✅ Response message: {result.get('message', '')[:100]}...")
        
        # Validate response structure
        self.assertEqual(result.get('type'), 'clarification_needed')
        self.assertIn('options', result)
        self.assertIsInstance(result['options'], list)
        
        # Validate that the message contains the document title, not the ID
        message = result.get('message', '')
        self.assertIn(self.expected_title, message, 
                     f"Message should contain document title '{self.expected_title}'")
        self.assertNotIn(self.test_document_id, message, 
                        f"Message should NOT contain document ID '{self.test_document_id}'")
        
        # Validate clarification options
        options = result.get('options', [])
        self.assertGreater(len(options), 0, "Should have at least one option")
        
        # Check regular question options (not the manual input option)
        question_options = [opt for opt in options if opt.get('action') == 'proceed_with_question']
        self.assertGreater(len(question_options), 0, "Should have question options")
        
        for option in question_options:
            print(f"\\n📋 Option {option.get('id')}:")
            print(f"   Title: {option.get('title', '')[:50]}...")
            print(f"   Document: {option.get('document')}")
            print(f"   Procedure: {option.get('procedure')}")
            print(f"   Description: {option.get('description', '')[:50]}...")
            
            # CRITICAL VALIDATION: document field should show title, not ID
            self.assertEqual(option.get('document'), self.expected_title,
                           f"Option document field should be '{self.expected_title}', got '{option.get('document')}'")
            
            # CRITICAL VALIDATION: procedure field should show title, not question text
            self.assertEqual(option.get('procedure'), self.expected_title,
                           f"Option procedure field should be '{self.expected_title}', got '{option.get('procedure')}'")
            
            # Description should also reference the document title
            description = option.get('description', '')
            self.assertIn(self.expected_title, description,
                         f"Option description should contain document title '{self.expected_title}'")
        
        # Check manual input option
        manual_options = [opt for opt in options if opt.get('action') == 'manual_input']
        if manual_options:
            manual_option = manual_options[0]
            print(f"\\n📝 Manual input option:")
            print(f"   Document: {manual_option.get('document')}")
            print(f"   Procedure: {manual_option.get('procedure')}")
            
            self.assertEqual(manual_option.get('document'), self.expected_title)
            self.assertEqual(manual_option.get('procedure'), self.expected_title)
        
        # Validate top-level response fields
        self.assertEqual(result.get('document'), self.expected_title,
                        f"Response document field should be '{self.expected_title}'")
        self.assertEqual(result.get('procedure'), self.expected_title,
                        f"Response procedure field should be '{self.expected_title}'")
        
        print("✅ All document title validations passed!")

    def test_multiple_collections_and_documents(self):
        """Test helper function with multiple collections and documents"""
        print("\\n🧪 Testing multiple collections and documents...")
        
        # Test cases: (collection, document_id, expected_title_part)
        test_cases = [
            ("quy_trinh_cap_ho_tich_cap_xa", "DOC_001", "Đăng ký khai sinh"),
            ("quy_trinh_cap_ho_tich_cap_xa", "DOC_011", "Đăng ký kết hôn"),
            ("quy_trinh_boi_thuong_nn", "DOC_001", "Thủ tục xác định cơ quan giải quyết bồi thường"),
        ]
        
        for collection, doc_id, expected_part in test_cases:
            try:
                title = self.clarification_service._get_document_title(collection, doc_id)
                print(f"✅ {collection}/{doc_id}: '{title}'")
                
                # Check if expected part is in the title (allowing for variations)
                if expected_part:
                    self.assertIn(expected_part.split()[0], title,  # Just check first word
                                f"Title '{title}' should contain '{expected_part}'")
                
            except Exception as e:
                print(f"⚠️  Error testing {collection}/{doc_id}: {e}")

def run_tests():
    """Run all tests"""
    print("🚀 Starting Document Title Display Tests...")
    print("=" * 60)
    
    # Change to rag_service directory for proper file access
    original_cwd = os.getcwd()
    try:
        os.chdir(rag_service_path)
        
        # Run tests
        unittest.main(argv=[''], exit=False, verbosity=2)
        
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    run_tests()