#!/usr/bin/env python3
"""
Debug Router Cache - CHECK CACHE DATA
=====================================

Script để debug cache data và hiểu format
"""

import sys
import os
import json
import pickle
import numpy as np
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def debug_cache():
    """Debug cache data"""
    
    cache_file = backend_dir / "data" / "cache" / "router_embeddings.pkl"
    
    print("🔍 DEBUGGING ROUTER CACHE")
    print("=" * 40)
    
    if not cache_file.exists():
        print(f"❌ Cache file not found: {cache_file}")
        return
    
    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        print("📊 CACHE STRUCTURE:")
        print(f"Top-level keys: {list(cache_data.keys())}")
        
        if 'metadata' in cache_data:
            metadata = cache_data['metadata']
            print(f"\nMETADATA:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
        
        if 'embeddings' in cache_data:
            embeddings = cache_data['embeddings']
            print(f"\nEMBEDDINGS:")
            print(f"Collections: {list(embeddings.keys())}")
            
            for collection_name, collection_data in embeddings.items():
                print(f"\n📁 {collection_name}:")
                print(f"  Keys: {list(collection_data.keys())}")
                
                if 'count' in collection_data:
                    print(f"  Count: {collection_data['count']}")
                
                if 'vectors' in collection_data:
                    vectors = collection_data['vectors']
                    print(f"  Vectors type: {type(vectors)}")
                    print(f"  Vectors shape: {vectors.shape if hasattr(vectors, 'shape') else 'No shape'}")
                
                if 'examples' in collection_data:
                    examples = collection_data['examples']
                    print(f"  Examples type: {type(examples)}")
                    print(f"  Examples length: {len(examples) if hasattr(examples, '__len__') else 'No length'}")
                    
                    # Try to access first example
                    try:
                        if len(examples) > 0:
                            first_example = examples[0]
                            print(f"  First example type: {type(first_example)}")
                            print(f"  First example: {first_example}")
                    except Exception as e:
                        print(f"  ❌ Error accessing first example: {e}")
                        print(f"  Examples content: {examples}")
        
    except Exception as e:
        print(f"❌ Error loading cache: {e}")
        import traceback
        traceback.print_exc()

def check_router_questions():
    """Check router questions in new structure"""
    
    print("\n🔍 CHECKING ROUTER QUESTIONS IN NEW STRUCTURE")
    print("=" * 50)
    
    storage_dir = backend_dir / "data" / "storage" / "collections"
    
    if not storage_dir.exists():
        print(f"❌ Storage directory not found: {storage_dir}")
        return
    
    total_questions = 0
    
    for collection_dir in storage_dir.iterdir():
        if not collection_dir.is_dir():
            continue
            
        collection_name = collection_dir.name
        print(f"\n📁 {collection_name}:")
        
        documents_dir = collection_dir / "documents"
        if not documents_dir.exists():
            print(f"  ❌ No documents directory")
            continue
        
        collection_questions = 0
        
        for doc_dir in documents_dir.iterdir():
            if not doc_dir.is_dir():
                continue
                
            router_file = doc_dir / "router_questions.json"
            if not router_file.exists():
                continue
            
            try:
                with open(router_file, 'r', encoding='utf-8') as f:
                    router_data = json.load(f)
                
                # Count questions
                questions = router_data.get('question_variants', [])
                collection_questions += len(questions)
                
                print(f"  📝 {doc_dir.name}: {len(questions)} questions")
                
                # Show sample di chúc questions
                if 'di chúc' in str(router_data).lower():
                    print(f"    🎯 Contains 'di chúc' content")
                    for i, q in enumerate(questions[:2], 1):
                        if 'di chúc' in q.lower():
                            print(f"    {i}. {q}")
                
            except Exception as e:
                print(f"  ❌ Error loading {router_file}: {e}")
        
        print(f"  📊 Total questions: {collection_questions}")
        total_questions += collection_questions
    
    print(f"\n📊 TOTAL QUESTIONS ACROSS ALL COLLECTIONS: {total_questions}")

def main():
    print("🚀 ROUTER CACHE DIAGNOSTIC")
    print("=" * 50)
    
    # Check cache
    debug_cache()
    
    # Check source data
    check_router_questions()

if __name__ == "__main__":
    main()
