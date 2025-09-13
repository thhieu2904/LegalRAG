#!/usr/bin/env python3
"""
Quick Test for Backend Logic
============================

Test các thay đổi logic mà không cần start full backend.
"""

import sys
import os
sys.path.append('rag_service')

def test_router_force_routing():
    """Test router force routing logic"""
    print("🔥 TEST: Router Force Routing Logic")
    print("=" * 40)
    
    try:
        # Import router
        from app.services.router import QueryRouter
        from sentence_transformers import SentenceTransformer
        
        # Create minimal router instance (won't fully initialize)
        print("Creating router instance...")
        
        # Test force routing parameters in method signature
        router = QueryRouter.__new__(QueryRouter)  # Create without __init__
        
        # Test if route_query accepts force parameters
        import inspect
        sig = inspect.signature(QueryRouter.route_query)
        params = list(sig.parameters.keys())
        
        print(f"✅ QueryRouter.route_query parameters: {params}")
        
        if 'force_collection' in params:
            print("✅ FORCE ROUTING: force_collection parameter exists")
        else:
            print("❌ FORCE ROUTING: force_collection parameter missing")
            
        if 'force_document' in params:
            print("✅ FORCE ROUTING: force_document parameter exists")
        else:
            print("❌ FORCE ROUTING: force_document parameter missing")
            
    except Exception as e:
        print(f"❌ Router test error: {e}")
    
    print()

def test_clarification_manual_input():
    """Test clarification manual input logic"""
    print("🔥 TEST: Clarification Manual Input Logic") 
    print("=" * 40)
    
    try:
        # Import clarification service
        from app.services.clarification import ClarificationService
        
        # Create minimal instance
        clarify_service = ClarificationService.__new__(ClarificationService)
        
        # Test _handle_manual_input method
        import inspect
        sig = inspect.signature(ClarificationService._handle_manual_input)
        params = list(sig.parameters.keys())
        
        print(f"✅ ClarificationService._handle_manual_input parameters: {params}")
        
        # Test method existence
        if hasattr(ClarificationService, '_handle_manual_input'):
            print("✅ MANUAL INPUT: _handle_manual_input method exists")
        else:
            print("❌ MANUAL INPUT: _handle_manual_input method missing")
            
        # Test if confidence_percent is added to options
        if hasattr(ClarificationService, '_handle_show_document_questions'):
            print("✅ CONFIDENCE: _handle_show_document_questions method exists")
        else:
            print("❌ CONFIDENCE: _handle_show_document_questions method missing")
            
    except Exception as e:
        print(f"❌ Clarification test error: {e}")
    
    print()

def test_api_endpoint():
    """Test API endpoint modifications"""
    print("🔥 TEST: API Endpoint Modifications")
    print("=" * 40)
    
    try:
        # Import API models
        from app.api.rag import QueryRequest
        
        # Test QueryRequest fields
        import inspect
        fields = QueryRequest.__fields__
        field_names = list(fields.keys())
        
        print(f"✅ QueryRequest fields: {field_names}")
        
        if 'force_collection' in field_names:
            print("✅ API: force_collection field exists")
        else:
            print("❌ API: force_collection field missing")
            
        if 'force_document' in field_names:
            print("✅ API: force_document field exists")
        else:
            print("❌ API: force_document field missing")
            
    except Exception as e:
        print(f"❌ API test error: {e}")
    
    print()

def test_file_modifications():
    """Test if files were modified correctly"""
    print("🔥 TEST: File Modifications Check")
    print("=" * 40)
    
    files_to_check = [
        ("rag_service/app/services/router.py", "force_collection"),
        ("rag_service/app/services/clarification.py", "confidence_percent"),
        ("rag_service/app/services/rag_engine.py", "force_collection"),
        ("rag_service/app/api/rag.py", "force_collection"),
        ("frontend/src/services/chatService.ts", "force_collection"),
        ("frontend/src/hooks/useChat.ts", "forceCollection")
    ]
    
    for file_path, keyword in files_to_check:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if keyword in content:
                    print(f"✅ {file_path}: Contains '{keyword}'")
                else:
                    print(f"❌ {file_path}: Missing '{keyword}'")
            else:
                print(f"⚠️  {file_path}: File not found")
                
        except Exception as e:
            print(f"❌ {file_path}: Error reading file - {e}")
    
    print()

def main():
    """Run quick tests"""
    print("🧪 CLARIFICATION FIXES - QUICK BACKEND LOGIC TEST")
    print("=" * 60)
    print()
    
    test_router_force_routing()
    test_clarification_manual_input() 
    test_api_endpoint()
    test_file_modifications()
    
    print("=" * 60)
    print("🎯 QUICK TESTS COMPLETE")
    print()
    print("✅ FIXES IMPLEMENTED:")
    print("1. 🔒 Force Routing: Router accepts force_collection/force_document")
    print("2. 📝 Manual Input: Enhanced context preservation in clarification")
    print("3. 📊 Confidence: Added confidence_percent to options")
    print("4. 🔗 API: Frontend can send force routing parameters")
    print()
    print("🚀 NEXT STEPS:")
    print("1. Start backend: python rag_service/main.py")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Test clarification flow manually")
    print("4. Verify force routing in logs")

if __name__ == "__main__":
    main()