#!/usr/bin/env python3
"""
Test Script for Confirmation Clarification Title Fix
===================================================

Test specifically the confirmation flow to ensure document titles
are displayed correctly instead of DOC_xxx IDs.
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Add the rag_service directory to Python path
rag_service_path = Path(__file__).parent.parent / "rag_service"
sys.path.insert(0, str(rag_service_path))

from app.services.clarification import ClarificationService

class TestConfirmationTitleFix(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.clarification_service = ClarificationService()

    def test_confirmation_clarification_uses_titles(self):
        """Test that confirmation clarification uses document titles not IDs"""
        print("\\n🧪 Testing confirmation clarification with document titles...")
        
        # Mock medium-high confidence routing result (triggers confirmation)
        routing_result = {
            "best_match": {
                "collection": "quy_trinh_cap_ho_tich_cap_xa",
                "document": "DOC_011",
                "question": "Thủ tục đăng ký kết hôn được thực hiện như thế nào?",
                "confidence": 0.746
            },
            "target_collection": "quy_trinh_cap_ho_tich_cap_xa",
            "query": "Thủ tục đăng ký kết hôn được thực hiện như thế nào?",
            "confidence": 0.746,
            "status": "found"
        }
        
        result = self.clarification_service.generate_clarification(
            confidence=0.746,
            routing_result=routing_result,
            query="Thủ tục đăng ký kết hôn được thực hiện như thế nào?",
            session_id="test_confirmation_001"
        )
        
        # Convert to dict if it's a Pydantic object
        if hasattr(result, 'dict'):
            result_dict = result.dict()
        else:
            result_dict = result
            
        print(f"Response type: {result_dict.get('type')}")
        print(f"Clarification style: {result_dict.get('clarification', {}).get('style')}")
        
        # Should get confirmation style
        self.assertEqual(result_dict.get('type'), 'clarification_needed')
        clarification = result_dict.get('clarification', {})
        self.assertEqual(clarification.get('style'), 'confirmation')
        
        # Check all options for document titles
        options = clarification.get('options', [])
        self.assertGreater(len(options), 0, "Should have options")
        
        print("\\n📋 Checking all options for document titles...")
        for i, option in enumerate(options):
            print(f"Option {i+1}: {option.get('title', '')[:60]}...")
            
            document_field = option.get('document', '')
            procedure_field = option.get('procedure', '')
            
            print(f"  Document: '{document_field}'")
            print(f"  Procedure: '{procedure_field}'")
            
            # Only check options that should have document info
            if option.get('action') in ['proceed_with_question', 'show_document_questions']:
                # Document field should NOT contain DOC_xxx
                self.assertNotIn('DOC_', str(document_field), 
                               f"Document field should not contain ID format: {document_field}")
                
                # Should contain actual title
                if document_field and document_field != 'None':
                    self.assertIn('kết hôn', document_field.lower(), 
                                f"Document field should contain title keywords: {document_field}")
        
        print("✅ All confirmation options use document titles correctly")

    def test_json_response_structure(self):
        """Test that the JSON response structure matches what frontend expects"""
        print("\\n🧪 Testing JSON response structure for frontend...")
        
        routing_result = {
            "best_match": {
                "collection": "quy_trinh_cap_ho_tich_cap_xa",
                "document": "DOC_011",
                "question": "Thủ tục đăng ký kết hôn được thực hiện như thế nao?",
                "confidence": 0.746
            },
            "target_collection": "quy_trinh_cap_ho_tich_cap_xa",
            "query": "kết hôn",
            "confidence": 0.746
        }
        
        result = self.clarification_service.generate_clarification(
            confidence=0.746,
            routing_result=routing_result,
            query="kết hôn",
            session_id="test_json_001"
        )
        
        # Convert to dict if it's a Pydantic object
        if hasattr(result, 'dict'):
            json_result = result.dict()
        else:
            json_result = result
        
        print("\\n🔍 JSON Response Analysis:")
        print(f"Type: {json_result.get('type')}")
        print(f"Style: {json_result.get('clarification', {}).get('style')}")
        
        clarification = json_result.get('clarification', {})
        options = clarification.get('options', [])
        
        # Find the proceed option
        proceed_option = None
        show_all_option = None
        
        for option in options:
            if option.get('action') == 'proceed_with_question':
                proceed_option = option
            elif option.get('action') == 'show_document_questions':
                show_all_option = option
        
        if proceed_option:
            print(f"\\n✅ Proceed option found:")
            print(f"  Document: '{proceed_option.get('document')}'")
            print(f"  Procedure: '{proceed_option.get('procedure')}'")
            
            # Validate it's not DOC_xxx
            document = proceed_option.get('document', '')
            self.assertNotEqual(document, 'DOC_011', "Should not be document ID")
            self.assertNotIn('DOC_', document, "Should not contain DOC_ prefix")
        
        if show_all_option:
            print(f"\\n✅ Show all option found:")
            print(f"  Document: '{show_all_option.get('document')}'")
            print(f"  Procedure: '{show_all_option.get('procedure')}'")
            
            # Validate it's not DOC_xxx
            document = show_all_option.get('document', '')
            self.assertNotEqual(document, 'DOC_011', "Should not be document ID")
            self.assertNotIn('DOC_', document, "Should not contain DOC_ prefix")

def run_tests():
    """Run all tests"""
    print("🚀 Starting Confirmation Title Fix Tests...")
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