#!/usr/bin/env python3
"""
SIMPLE ROUTER TEST
==================

Test router directly để kiểm tra matching với di chúc
"""

import sys
import os
from pathlib import Path
import json

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_router_cache():
    """Test xem router cache có load được không"""
    
    print("🔍 TESTING ROUTER CACHE")
    print("=" * 40)
    
    cache_file = backend_dir / "data" / "cache" / "router_embeddings.pkl"
    
    if not cache_file.exists():
        print(f"❌ Cache file not found: {cache_file}")
        return False
    
    try:
        import pickle
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        print("✅ Router cache loaded successfully")
        print(f"📊 Structure type: {cache_data['metadata'].get('structure_type')}")
        print(f"📊 Total examples: {cache_data['metadata'].get('total_examples')}")
        print(f"📊 Collections: {list(cache_data['embeddings'].keys())}")
        
        # Check chung_thuc collection
        if 'quy_trinh_chung_thuc' in cache_data['embeddings']:
            chung_thuc_data = cache_data['embeddings']['quy_trinh_chung_thuc']
            print(f"✅ Found 'quy_trinh_chung_thuc': {chung_thuc_data['count']} examples")
            
            # Show some examples về di chúc
            examples = chung_thuc_data['examples']
            di_chuc_examples = [ex for ex in examples if 'di chúc' in ex['text'].lower()]
            
            print(f"📝 Di chúc examples: {len(di_chuc_examples)}")
            for i, ex in enumerate(di_chuc_examples[:3], 1):
                print(f"  {i}. {ex['text'][:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading cache: {e}")
        return False

def test_router_direct():
    """Test router trực tiếp"""
    
    print("\n🎯 TESTING ROUTER DIRECT MATCHING")
    print("=" * 45)
    
    try:
        from sentence_transformers import SentenceTransformer
        from app.services.router import QueryRouter
        
        # Load model
        print("🔄 Loading embedding model...")
        model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", device="cpu")
        
        # Initialize router
        print("🔄 Initializing router...")
        router = QueryRouter(model)
        
        # Test queries
        test_queries = [
            "Xin chào tôi muốn hỏi lập di chúc thì cần phải đón...",
            "Tôi muốn chứng thực di chúc",
            "Hồ sơ để chứng thực di chúc gồm những giấy tờ nào?",
            "Thủ tục chứng thực di chúc được thực hiện như thế nào?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query}")
            print("-" * 60)
            
            try:
                result = router.route_query(query, session=None)
                
                print(f"Target Collection: {result.get('target_collection')}")
                print(f"Confidence: {result.get('confidence', 0):.3f}")
                print(f"Confidence Level: {result.get('confidence_level')}")
                print(f"Source Procedure: {result.get('source_procedure', 'N/A')}")
                
                # Show top 3 scores
                all_scores = result.get('all_scores', {})
                if all_scores:
                    sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:3]
                    print("Top 3 scores:")
                    for collection, score in sorted_scores:
                        print(f"  {collection}: {score:.3f}")
                
                # Check if correct
                if result.get('target_collection') == 'quy_trinh_chung_thuc':
                    print("✅ CORRECT: Routed to chung_thuc")
                else:
                    print("❌ INCORRECT: Should route to chung_thuc")
                    
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in router test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 ROUTER DIAGNOSTIC TEST")
    print("=" * 50)
    
    # Test 1: Cache
    cache_ok = test_router_cache()
    
    if cache_ok:
        # Test 2: Router matching
        router_ok = test_router_direct()
    else:
        print("⚠️  Skipping router test due to cache issues")
        router_ok = False
    
    print("\n📋 SUMMARY:")
    print(f"Cache: {'✅' if cache_ok else '❌'}")
    print(f"Router: {'✅' if router_ok else '❌'}")

if __name__ == "__main__":
    main()
