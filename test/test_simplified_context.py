#!/usr/bin/env python3
"""
Test simplified context loading
"""

import sys
import os
from pathlib import Path

# Add rag_service directory to path
rag_service_path = str(Path(__file__).parent.parent / "rag_service")
sys.path.append(rag_service_path)

from app.services.context import ContextExpander

def test_simplified_context():
    """Test the new simplified context loading"""
    
    # Mock vectordb service (not needed for this test)
    class MockVectorDB:
        def list_collections(self):
            return []
    
    # Initialize service
    context_service = ContextExpander(
        vectordb_service=MockVectorDB(),
        documents_dir="data/storage/collections"
    )
    
    # Test file
    test_file = "d:/Personal/LegalRAG_OCR/rag_service/data/storage/collections/quy_trinh_cap_ho_tich_cap_xa/documents/DOC_002/02. ĐKKS có yếu tố nước ngoài.json"
    test_query = "đăng ký khai sinh mà có mẹ là người nước ngoài thì cần giấy tờ gì"
    
    print("🧪 Testing simplified context loading...")
    print(f"📁 File: {test_file}")
    print(f"❓ Query: {test_query}")
    print("="*80)
    
    try:
        # Test the new method
        content, metadata = context_service._load_full_document_and_metadata(test_file, test_query)
        
        print(f"✅ Content length: {len(content)} chars")
        print(f"✅ Metadata keys: {list(metadata.keys())}")
        print("="*80)
        print("📄 CONTENT PREVIEW:")
        print("="*80)
        print(content[:1000] + "..." if len(content) > 1000 else content)
        print("="*80)
        print("📋 METADATA:")
        print("="*80)
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simplified_context()
