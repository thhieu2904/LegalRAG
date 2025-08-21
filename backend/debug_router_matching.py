#!/usr/bin/env python3
"""
DEBUG ROUTER MATCHING - Find why nuoi_con_nuoi scores higher than chung_thuc
"""

import sys
import os
import pickle
import numpy as np
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def debug_matching():
    """Debug why router matches wrong collection"""
    
    print("🔍 DEBUGGING ROUTER MATCHING")
    print("=" * 50)
    
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Load model and cache
        model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", device="cpu")
        
        cache_file = backend_dir / "data" / "cache" / "router_embeddings.pkl"
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        test_query = "Xin chào tôi muốn hỏi lập di chúc thì cần phải đón..."
        print(f"📝 Test query: {test_query}")
        
        # Encode query
        query_vector = model.encode([test_query])
        
        embeddings = cache_data.get('embeddings', {})
        
        # Check each collection in detail
        for collection_name, collection_data in embeddings.items():
            print(f"\n📁 {collection_name.upper()}:")
            print("-" * 40)
            
            examples = collection_data.get('examples', [])
            vectors = collection_data.get('vectors')
            
            if len(vectors) > 0:
                similarities = cosine_similarity(query_vector, vectors)[0]
                
                # Find top 3 matches in this collection
                top_indices = np.argsort(similarities)[-3:][::-1]
                
                for i, idx in enumerate(top_indices, 1):
                    score = similarities[idx]
                    example_text = examples[idx]['text']
                    
                    print(f"  {i}. Score: {score:.3f}")
                    print(f"     Text: {example_text}")
                    
                    # Check if this example contains keywords related to di chúc
                    keywords = ['di chúc', 'chúc thư', 'thừa kế', 'tài sản', 'chứng thực']
                    found_keywords = [kw for kw in keywords if kw in example_text.lower()]
                    if found_keywords:
                        print(f"     🎯 Keywords: {found_keywords}")
                    print()
                
                best_score = np.max(similarities)
                best_idx = np.argmax(similarities)
                best_example = examples[best_idx]['text']
                
                print(f"  📊 Best score: {best_score:.3f}")
                print(f"  📝 Best example: {best_example}")
                
                # Show why this might be matching
                if collection_name == 'quy_trinh_nuoi_con_nuoi' and best_score > 0.59:
                    print(f"  ⚠️  WHY HIGH SCORE? Analyzing...")
                    
                    # Check for common words
                    query_words = set(test_query.lower().split())
                    example_words = set(best_example.lower().split())
                    common_words = query_words.intersection(example_words)
                    
                    print(f"     Common words: {common_words}")
                    
                elif collection_name == 'quy_trinh_chung_thuc':
                    print(f"  ✅ Should be the correct match")
                    
                    # Find di chúc examples
                    di_chuc_examples = [(i, ex) for i, ex in enumerate(examples) if 'di chúc' in ex['text'].lower()]
                    if di_chuc_examples:
                        print(f"  📝 Di chúc examples found: {len(di_chuc_examples)}")
                        for i, (idx, ex) in enumerate(di_chuc_examples[:3], 1):
                            score = similarities[idx]
                            print(f"    {i}. Score: {score:.3f} - {ex['text'][:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_router_questions_content():
    """Check what's actually in the router questions"""
    
    print("\n🔍 CHECKING ROUTER QUESTIONS CONTENT")
    print("=" * 50)
    
    storage_dir = backend_dir / "data" / "storage" / "collections"
    
    # Check nuoi_con_nuoi collection
    nuoi_con_dir = storage_dir / "quy_trinh_nuoi_con_nuoi" / "documents"
    
    print("📁 QUY_TRINH_NUOI_CON_NUOI examples:")
    
    for doc_dir in nuoi_con_dir.iterdir():
        if not doc_dir.is_dir():
            continue
        
        router_file = doc_dir / "router_questions.json"
        if not router_file.exists():
            continue
        
        try:
            import json
            with open(router_file, 'r', encoding='utf-8') as f:
                router_data = json.load(f)
            
            questions = router_data.get('question_variants', [])
            title = router_data.get('metadata', {}).get('title', doc_dir.name)
            
            print(f"\n  📄 {doc_dir.name}: {title}")
            
            # Show a few examples
            for i, q in enumerate(questions[:3], 1):
                print(f"    {i}. {q}")
            
            if len(questions) > 3:
                print(f"    ... và {len(questions) - 3} câu hỏi khác")
            
        except Exception as e:
            print(f"  ❌ Error loading {router_file}: {e}")

def main():
    print("🚀 DEBUG ROUTER MATCHING ISSUE")
    print("=" * 60)
    
    # Debug matching scores
    debug_ok = debug_matching()
    
    if debug_ok:
        # Check content
        check_router_questions_content()

if __name__ == "__main__":
    main()
