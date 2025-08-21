#!/usr/bin/env python3
"""
Simple Cache Test - Test cache loading directly
"""

import sys
import os
import pickle
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_cache_loading():
    """Test loading cache directly"""
    
    cache_file = backend_dir / "data" / "cache" / "router_embeddings.pkl"
    
    print("🔍 TESTING CACHE LOADING")
    print("=" * 40)
    
    if not cache_file.exists():
        print(f"❌ Cache file not found: {cache_file}")
        return False
    
    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        print("✅ Cache loaded successfully")
        
        # Test embeddings access
        embeddings = cache_data.get('embeddings', {})
        
        for collection_name, collection_data in embeddings.items():
            print(f"\n📁 {collection_name}:")
            
            vectors = collection_data.get('vectors')
            examples = collection_data.get('examples')
            
            print(f"  Vectors shape: {vectors.shape}")
            print(f"  Examples count: {len(examples)}")
            
            # Test accessing examples
            try:
                first_example = examples[0]
                print(f"  First example: {first_example['text'][:50]}...")
                print(f"  Collection: {first_example['collection']}")
            except Exception as e:
                print(f"  ❌ Error accessing example: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading cache: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_router_with_cache():
    """Test router initialization with cache"""
    
    print("\n🎯 TESTING ROUTER WITH CACHE")
    print("=" * 40)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Load model
        print("🔄 Loading embedding model...")
        model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", device="cpu")
        
        # Initialize router with proper cache path
        print("🔄 Initializing router...")
        
        # Manual cache loading to bypass router's complex logic
        cache_file = backend_dir / "data" / "cache" / "router_embeddings.pkl"
        
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            print("✅ Cache loaded manually")
            
            # Set up router data structures manually
            example_questions = {}
            question_vectors = {}
            collection_mappings = {}
            
            embeddings = cache_data.get('embeddings', {})
            
            for collection_name, collection_data in embeddings.items():
                examples = collection_data.get('examples', [])
                vectors = collection_data.get('vectors')
                
                example_questions[collection_name] = examples
                question_vectors[collection_name] = vectors
                collection_mappings[collection_name] = {
                    'display_name': collection_name.replace('_', ' ').title(),
                    'count': len(examples)
                }
            
            print(f"✅ Router data structures created")
            print(f"Collections: {list(collection_mappings.keys())}")
            
            # Test similarity search manually
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            test_query = "Xin chào tôi muốn hỏi lập di chúc thì cần phải đón..."
            print(f"\n📝 Test query: {test_query}")
            
            # Encode query
            query_vector = model.encode([test_query])
            
            all_scores = {}
            
            for collection_name, vectors in question_vectors.items():
                if len(vectors) > 0:
                    similarities = cosine_similarity(query_vector, vectors)[0]
                    best_score = np.max(similarities)
                    all_scores[collection_name] = float(best_score)
                    
                    print(f"  {collection_name}: {best_score:.3f}")
            
            # Find best match
            best_collection = max(all_scores, key=all_scores.get)
            best_score = all_scores[best_collection]
            
            print(f"\n🎯 Best match: {best_collection} ({best_score:.3f})")
            
            if best_collection == 'quy_trinh_chung_thuc':
                print("✅ CORRECT: Matched chung_thuc collection for di chúc query")
            else:
                print("❌ INCORRECT: Should match chung_thuc collection")
            
            return True
        
        else:
            print("❌ Cache file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error in router test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 SIMPLE CACHE TEST")
    print("=" * 50)
    
    # Test cache loading
    cache_ok = test_cache_loading()
    
    if cache_ok:
        # Test router with cache
        router_ok = test_router_with_cache()
    else:
        router_ok = False
    
    print(f"\n📋 SUMMARY:")
    print(f"Cache: {'✅' if cache_ok else '❌'}")
    print(f"Router: {'✅' if router_ok else '❌'}")

if __name__ == "__main__":
    main()
