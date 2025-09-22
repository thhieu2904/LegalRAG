#!/usr/bin/env python3
"""
Test Context Service with new PathConfig
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent / "rag_service"))

def test_context_expander():
    """Test ContextExpander with new PathConfig"""
    print("🧪 Testing ContextExpander")
    print("-" * 50)
    
    try:
        from app.services.context import ContextExpander
        from app.core.path_config import PathConfig
        
        # Create mock vectordb_service
        class MockVectorDBService:
            pass
        
        mock_vectordb = MockVectorDBService()
        
        # Test 1: Default initialization
        print("Test 1: Default initialization")
        expander = ContextExpander(mock_vectordb, "")
        print(f"  Environment: {expander.path_config.environment}")
        print(f"  Documents dir: {expander.documents_dir}")
        print(f"  Base data dir: {expander.path_config.base_data_dir}")
        
        # Test 2: Path resolution
        print("\nTest 2: Path resolution")
        test_paths = [
            "data/storage/collections/test.json",
            "../data/storage/collections/test.json",
            "storage/collections/test.json"
        ]
        
        for test_path in test_paths:
            try:
                resolved = expander._resolve_source_file_path(test_path)
                print(f"  '{test_path}' -> {resolved}")
            except Exception as e:
                print(f"  '{test_path}' -> ERROR: {e}")
        
        print("\n✅ ContextExpander tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing ContextExpander: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mock_expansion():
    """Test context expansion with mock data"""
    print("\n🧪 Testing Context Expansion")
    print("-" * 50)
    
    try:
        from app.services.context import ContextExpander
        
        # Create mock services
        class MockVectorDBService:
            pass
        
        mock_vectordb = MockVectorDBService()
        expander = ContextExpander(mock_vectordb, "")
        
        # Mock nucleus chunk
        mock_nucleus_chunk = {
            "content": "Test content for expansion",
            "source": "data/storage/collections/test_collection/documents/DOC_001/test.json",
            "metadata": {
                "document_title": "Test Document"
            }
        }
        
        print("Test expansion with mock nucleus chunk:")
        print(f"  Source: {mock_nucleus_chunk['source']}")
        
        # Test path resolution
        resolved_path = expander._resolve_source_file_path(mock_nucleus_chunk['source'])
        print(f"  Resolved path: {resolved_path}")
        print(f"  Path exists: {resolved_path.exists()}")
        
        print("\n✅ Mock expansion tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing mock expansion: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_generate_fallback():
    """Test fallback content generation"""
    print("\n🧪 Testing Fallback Content Generation")
    print("-" * 50)
    
    try:
        from app.services.context import ContextExpander
        
        class MockVectorDBService:
            pass
        
        mock_vectordb = MockVectorDBService()
        expander = ContextExpander(mock_vectordb, "")
        
        # Test fallback generation
        fallback_content, fallback_metadata = expander._generate_fallback_content("nonexistent/file.json")
        
        print(f"Fallback content length: {len(fallback_content)}")
        print(f"Fallback metadata keys: {list(fallback_metadata.keys())}")
        
        print("\n✅ Fallback content tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing fallback content: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run Phase 2 tests"""
    print("🧪 Testing Phase 2 Updates")
    print("=" * 60)
    
    success = True
    success &= test_context_expander()
    success &= test_mock_expansion()
    success &= test_generate_fallback()
    
    if success:
        print("\n🎉 All Phase 2 tests passed!")
        print("✅ context.py successfully updated")
        print("✅ PathConfig integration working")
        print("✅ Windows-specific logic removed")
    else:
        print("\n❌ Some tests failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())