#!/usr/bin/env python3
"""
Test script to verify cache is working
"""

import sys
import os
import pickle
from pathlib import Path

# Add backend to Python path  
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def test_cache():
    """Test cache loading and validation"""
    cache_file = "../data/cache/router_embeddings.pkl"
    
    if not os.path.exists(cache_file):
        print("❌ Cache file not found!")
        return False
    
    try:
        print("🔍 Loading cache...")
        with open(cache_file, 'rb') as f:
            cache_container = pickle.load(f)
        
        # Handle both old and new cache formats
        if isinstance(cache_container, dict) and 'data' in cache_container:
            cache_data = cache_container['data']
            metadata = cache_container.get('metadata', {})
            print(f"✅ Cache metadata: {metadata}")
        else:
            cache_data = cache_container
            print("📋 Legacy cache format detected")
        
        # Basic validation
        if not isinstance(cache_data, dict):
            print("❌ Cache data invalid format")
            return False
        
        total_docs = sum(len(docs) for docs in cache_data.values())
        print(f"✅ Cache loaded successfully: {len(cache_data)} collections, {total_docs} documents")
        
        # Test a sample document
        for collection_name, documents in cache_data.items():
            for doc_name, doc_data in documents.items():
                print(f"📄 Sample: {collection_name}/{doc_name}")
                print(f"   - Has embeddings: {'embeddings' in doc_data and doc_data['embeddings'] is not None}")
                print(f"   - Has fused_text: {'fused_text' in doc_data}")
                print(f"   - Cache type: {doc_data.get('cache_type', 'unknown')}")
                if 'fused_text' in doc_data:
                    print(f"   - Fused text length: {len(doc_data['fused_text'])} chars")
                break
            break
        
        return True
        
    except Exception as e:
        print(f"❌ Cache loading error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING CACHE")
    success = test_cache()
    if success:
        print("🎉 Cache test passed!")
    else:
        print("❌ Cache test failed!")
        sys.exit(1)
