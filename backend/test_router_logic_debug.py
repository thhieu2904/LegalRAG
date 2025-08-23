#!/usr/bin/env python3
"""
Test router logic trực tiếp với cached embeddings
"""

import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

def test_router_logic():
    print("🔍 TESTING ROUTER LOGIC WITH CACHED EMBEDDINGS")
    print("=" * 60)
    
    # Load cache
    cache_file = "data/cache/router_embeddings.pkl"
    
    with open(cache_file, 'rb') as f:
        cache_data = pickle.load(f)
    
    # Load embedding model
    model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", 
                               cache_folder="data/models/hf_cache", 
                               device="cpu")
    
    # Test query
    test_query = "đăng ký kết hôn cần giấy tờ gì"
    query_embedding = model.encode([test_query])
    
    print(f"🧪 Query: '{test_query}'")
    print("=" * 60)
    
    # Test specific collection
    collection_name = 'quy_trinh_cap_ho_tich_cap_xa'
    collection_data = cache_data['embeddings'][collection_name]
    
    collection_similarities = []
    
    # Focus on marriage documents
    target_docs = ['DOC_011', 'DOC_031']
    
    for doc_name in target_docs:
        if doc_name in collection_data:
            doc_data = collection_data[doc_name]
            cached_embeddings = doc_data['embeddings']
            questions = doc_data['questions']
            
            print(f"\n📄 Document: {doc_name}")
            print(f"🔢 Total questions: {len(questions)}")
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, cached_embeddings)[0]
            
            # Get best similarity
            max_similarity = float(max(similarities))
            best_question_idx = int(similarities.argmax())
            best_question = questions[best_question_idx]
            
            print(f"🏆 Max Similarity: {max_similarity:.4f}")
            print(f"🎯 Best Question: '{best_question}'")
            print(f"📍 Index: {best_question_idx} ({'main' if best_question_idx == 0 else 'variant'})")
            
            collection_similarities.append({
                'similarity': max_similarity,
                'document': doc_name,
                'best_question': best_question,
                'question_type': 'main' if best_question_idx == 0 else 'variant',
                'all_similarities': similarities
            })
            
            # Show top 5 similarities for this doc
            sorted_sims = [(i, sim) for i, sim in enumerate(similarities)]
            sorted_sims.sort(key=lambda x: x[1], reverse=True)
            
            print("   Top 5 questions:")
            for rank, (idx, sim) in enumerate(sorted_sims[:5], 1):
                marker = "👑" if idx == best_question_idx else "  "
                q_type = "main" if idx == 0 else f"v{idx}"
                print(f"   {marker} {rank}. {sim:.4f} ({q_type}) - {questions[idx][:60]}...")
    
    # Determine winner
    print("\n" + "=" * 60)
    print("🏆 COLLECTION WINNER DETERMINATION")
    print("=" * 60)
    
    if collection_similarities:
        best_doc = max(collection_similarities, key=lambda x: x['similarity'])
        
        print("📊 Document Scores:")
        for doc_sim in collection_similarities:
            marker = "🏆" if doc_sim['document'] == best_doc['document'] else "  "
            print(f"{marker} {doc_sim['document']}: {doc_sim['similarity']:.4f}")
        
        print(f"\n✅ Winner: {best_doc['document']} with score {best_doc['similarity']:.4f}")
        print(f"🎯 Winning question: '{best_doc['best_question']}'")
        
        # Check if this matches expectations
        if best_doc['document'] == 'DOC_011':
            print("✅ CORRECT: Router should choose DOC_011")
        else:
            print("❌ WRONG: Router chose wrong document")
            print("🔧 Need to investigate why DOC_031 won")
    
    print("\n" + "=" * 60)
    print("🧮 DETAILED ANALYSIS")
    print("=" * 60)
    
    # Analyze why one wins over the other
    if len(collection_similarities) == 2:
        doc_011 = next(d for d in collection_similarities if d['document'] == 'DOC_011')
        doc_031 = next(d for d in collection_similarities if d['document'] == 'DOC_031')
        
        print(f"DOC_011 (correct): {doc_011['similarity']:.4f}")
        print(f"DOC_031 (wrong):   {doc_031['similarity']:.4f}")
        print(f"Difference: {doc_011['similarity'] - doc_031['similarity']:.4f}")
        
        if doc_011['similarity'] > doc_031['similarity']:
            print("✅ DOC_011 should win - logic is correct!")
            print("🤔 But why did router choose DOC_031 in practice?")
        else:
            print("❌ DOC_031 wins in theory too - need to fix questions")

if __name__ == "__main__":
    test_router_logic()
