#!/usr/bin/env python3
"""
Debug variants của document lưu động
"""

import pickle
import os

def check_luu_dong_variants():
    print("🔍 CHECKING LƯU ĐỘNG VARIANTS THAT CAUSE MISMATCH")
    print("=" * 60)
    
    cache_file = "data/cache/router_embeddings.pkl"
    
    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        # Get DOC_031 data
        ho_tich_collection = cache_data['collections'].get('quy_trinh_cap_ho_tich_cap_xa', {})
        doc_031 = ho_tich_collection.get('DOC_031', {})
        
        if not doc_031:
            print("❌ DOC_031 not found!")
            return
        
        print(f"📄 Document: DOC_031 (Kết hôn lưu động)")
        print(f"❓ Main Question: {doc_031.get('main_question', 'N/A')}")
        print()
        
        # Load embedding model
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        
        model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", 
                                   cache_folder="data/models/hf_cache", 
                                   device="cpu")
        
        test_query = "đăng ký kết hôn cần giấy tờ gì"
        query_embedding = model.encode([test_query])
        
        print(f"🧪 Testing query: '{test_query}'")
        print("=" * 60)
        
        # Test main question
        main_similarity = 0.0
        main_q = doc_031.get('main_question', '')
        if main_q.strip():
            main_embedding = model.encode([main_q])
            main_similarity = cosine_similarity(query_embedding, main_embedding)[0][0]
            print(f"📊 Main Question Similarity: {main_similarity:.4f}")
            print(f"   '{main_q}'")
            print()
        
        # Test each variant
        variants = doc_031.get('question_variants', [])
        print(f"🔄 Testing {len(variants)} variants:")
        print("-" * 40)
        
        variant_similarities = []
        
        for i, variant in enumerate(variants, 1):
            if variant.strip():
                variant_embedding = model.encode([variant])
                similarity = cosine_similarity(query_embedding, variant_embedding)[0][0]
                
                variant_similarities.append({
                    'index': i,
                    'question': variant,
                    'similarity': similarity
                })
        
        # Sort by similarity
        variant_similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Show top 10 variants
        print("🏆 TOP 10 VARIANTS BY SIMILARITY:")
        for j, var in enumerate(variant_similarities[:10], 1):
            marker = "🔥" if var['similarity'] > main_similarity else "  "
            print(f"{marker} {j}. {var['similarity']:.4f} - V{var['index']}")
            print(f"      '{var['question']}'")
            print()
        
        # Find problematic variants
        high_sim_variants = [v for v in variant_similarities if v['similarity'] > main_similarity]
        
        if high_sim_variants:
            print("🚨 PROBLEM FOUND!")
            print(f"❌ {len(high_sim_variants)} variants have HIGHER similarity than main question")
            print(f"📊 Main question: {main_similarity:.4f}")
            print(f"📊 Highest variant: {high_sim_variants[0]['similarity']:.4f}")
            print()
            print("💡 SOLUTION NEEDED: These variants are confusing the router!")
            
            for var in high_sim_variants[:3]:
                print(f"   🔥 {var['similarity']:.4f}: '{var['question']}'")
        else:
            print("✅ No problematic variants found")
        
        # Compare with DOC_011 best variant
        print("\n" + "=" * 60)
        print("🆚 COMPARISON WITH DOC_011 (CORRECT DOCUMENT)")
        
        doc_011 = ho_tich_collection.get('DOC_011', {})
        if doc_011:
            variants_011 = doc_011.get('question_variants', [])
            
            best_011_similarity = 0
            best_011_question = ""
            
            for variant in variants_011:
                if variant.strip():
                    variant_embedding = model.encode([variant])
                    similarity = cosine_similarity(query_embedding, variant_embedding)[0][0]
                    
                    if similarity > best_011_similarity:
                        best_011_similarity = similarity
                        best_011_question = variant
            
            print(f"✅ DOC_011 best variant: {best_011_similarity:.4f}")
            print(f"   '{best_011_question}'")
            
            if variant_similarities and variant_similarities[0]['similarity'] > best_011_similarity:
                print(f"❌ DOC_031 wins: {variant_similarities[0]['similarity']:.4f} > {best_011_similarity:.4f}")
                print("🔧 This explains why router chooses wrong document!")
            else:
                print("✅ DOC_011 should win correctly")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_luu_dong_variants()
