#!/usr/bin/env python3
"""
Check router cache structure
"""

import pickle
import os

def check_cache():
    print("🔍 CHECKING ROUTER CACHE STRUCTURE...")
    print("=" * 50)
    
    cache_file = "data/cache/router_embeddings.pkl"
    
    if not os.path.exists(cache_file):
        print("❌ Cache file not found!")
        return
    
    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        print(f"📦 Cache Type: {type(cache_data)}")
        
        if isinstance(cache_data, dict):
            print(f"🔑 Cache Keys: {list(cache_data.keys())}")
            
            if 'metadata' in cache_data:
                print(f"📊 Metadata: {cache_data['metadata']}")
            
            if 'collections' in cache_data:
                collections = cache_data['collections']
                print(f"📚 Collections: {len(collections)}")
                
                for collection_name, docs in collections.items():
                    print(f"  📁 {collection_name}: {len(docs)} docs")
                    for doc_name, doc_data in list(docs.items())[:2]:  # Show first 2
                        print(f"    📄 {doc_name}: {list(doc_data.keys())}")
                        if 'main_question' in doc_data:
                            print(f"        ❓ Main: {doc_data['main_question'][:50]}...")
                        if 'question_variants' in doc_data:
                            print(f"        🔄 Variants: {len(doc_data['question_variants'])}")
            
            # ⚠️ CHECK FOR EMBEDDINGS
            if 'embeddings' in cache_data:
                print("✅ EMBEDDINGS FOUND in cache!")
                embeddings = cache_data['embeddings']
                print(f"🎯 Embeddings type: {type(embeddings)}")
                if isinstance(embeddings, dict):
                    for key in list(embeddings.keys())[:3]:
                        print(f"  🔢 {key}: {type(embeddings[key])}")
            else:
                print("❌ NO EMBEDDINGS in cache - this is the problem!")
                print("🔧 Cache only contains text, embeddings computed each time")
        
        # File size
        file_size = os.path.getsize(cache_file) / (1024 * 1024)  # MB
        print(f"📏 Cache file size: {file_size:.2f} MB")
        
        if file_size < 5:
            print("⚠️  Cache file is small - probably no embeddings")
        else:
            print("✅ Cache file is large - probably contains embeddings")
    
    except Exception as e:
        print(f"❌ Error reading cache: {e}")

if __name__ == "__main__":
    check_cache()
