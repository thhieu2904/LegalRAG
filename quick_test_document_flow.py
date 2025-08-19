#!/usr/bin/env python3
"""
Quick Test for Document Selection Flow
"""

import os
import sys
from pathlib import Path

# Add backend to path and change working directory
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))
os.chdir(str(backend_dir))

from app.services.rag_engine import OptimizedEnhancedRAGService
from app.services.vector_database import VectorDBService 
from app.services.language_model import LLMService

def test_quick():
    print("🧪 Quick Document Selection Test")
    
    # Initialize services
    vectordb = VectorDBService()
    llm = LLMService()
    rag = OptimizedEnhancedRAGService("data/documents", vectordb, llm)
    
    # Step 1: Get collection clarification
    print("\n📝 Step 1: Ambiguous query")
    result1 = rag.enhanced_query("tôi muốn làm giấy tờ", session_id="test123")
    print(f"Type: {result1.get('type')}")
    
    if result1.get('clarification') and result1['clarification'].get('options'):
        options = result1['clarification']['options']
        print(f"Options: {[opt['title'] for opt in options[:3]]}")
        
        # Step 2: Select first collection 
        print("\n📂 Step 2: Select collection")
        first_collection = options[0]
        print(f"Selecting: {first_collection['title']}")
        
        result2 = rag.handle_clarification(
            session_id="test123",
            selected_option=first_collection,
            original_query="tôi muốn làm giấy tờ"
        )
        
        print(f"Type: {result2.get('type')}")
        if result2.get('clarification') and result2['clarification'].get('suggestions'):
            docs = [s for s in result2['clarification']['suggestions'] if s.get('action') == 'proceed_with_document']
            print(f"Documents available: {len(docs)}")
            if docs:
                print(f"First doc: {docs[0]['title']}")
                
                # Step 3: Select first document
                print("\n📄 Step 3: Select document")
                result3 = rag.handle_clarification(
                    session_id="test123",
                    selected_option=docs[0],
                    original_query="tôi muốn làm giấy tờ"
                )
                
                print(f"Type: {result3.get('type')}")
                if result3.get('clarification') and result3['clarification'].get('suggestions'):
                    questions = [s for s in result3['clarification']['suggestions'] if s.get('action') == 'proceed_with_question']
                    manual_opts = [s for s in result3['clarification']['suggestions'] if s.get('action') == 'manual_input']
                    print(f"Questions available: {len(questions)}")
                    print(f"Manual input option: {'YES' if manual_opts else 'NO'}")
                    
                    if manual_opts:
                        # Step 4: Test manual input
                        print("\n🔧 Step 4: Test manual input")
                        result4 = rag.handle_clarification(
                            session_id="test123",
                            selected_option=manual_opts[0],
                            original_query="tôi muốn làm giấy tờ"
                        )
                        print(f"Manual input type: {result4.get('type')}")
                        print(f"Context preserved: {result4.get('context_preserved')}")
                        print(f"Document preserved: {result4.get('preserved_document')}")
                        
                        if result4.get('preserved_document'):
                            print("✅ SUCCESS: Document context preserved!")
                            return True
    
    print("❌ Test incomplete")
    return False

if __name__ == "__main__":
    success = test_quick()
    print(f"\n🎯 Result: {'PASSED' if success else 'FAILED'}")
    exit(0 if success else 1)
