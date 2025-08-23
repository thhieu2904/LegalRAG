#!/usr/bin/env python3
"""
Debug router mismatch - kiểm tra câu hỏi examples
"""

import pickle
import os

def check_marriage_questions():
    print("🔍 CHECKING MARRIAGE-RELATED QUESTIONS IN CACHE")
    print("=" * 60)
    
    cache_file = "data/cache/router_embeddings.pkl"
    
    if not os.path.exists(cache_file):
        print("❌ Cache file not found!")
        return
    
    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        if 'collections' not in cache_data:
            print("❌ No collections in cache!")
            return
        
        # Focus on ho_tich_cap_xa collection
        ho_tich_collection = cache_data['collections'].get('quy_trinh_cap_ho_tich_cap_xa', {})
        
        print(f"📊 Found {len(ho_tich_collection)} documents in ho_tich_cap_xa")
        print()
        
        # Look for marriage-related documents
        marriage_docs = []
        
        for doc_name, doc_data in ho_tich_collection.items():
            doc_title = ""
            if 'main_question' in doc_data:
                doc_title = doc_data['main_question']
            
            # Check if related to marriage
            if any(word in doc_name.lower() or word in doc_title.lower() 
                   for word in ['kết hôn', 'ket hon', 'marriage']):
                marriage_docs.append((doc_name, doc_data))
        
        print(f"🔍 Found {len(marriage_docs)} marriage-related documents:")
        print("=" * 60)
        
        for doc_name, doc_data in marriage_docs:
            print(f"\n📄 Document: {doc_name}")
            print(f"❓ Main Question: {doc_data.get('main_question', 'N/A')}")
            
            variants = doc_data.get('question_variants', [])
            print(f"🔄 Variants ({len(variants)}):")
            for i, variant in enumerate(variants[:5], 1):  # Show first 5
                print(f"   {i}. {variant}")
            if len(variants) > 5:
                print(f"   ... và {len(variants)-5} variants khác")
            
            # Check for keyword density
            all_questions = [doc_data.get('main_question', '')] + variants
            text_combined = ' '.join(all_questions).lower()
            
            ket_hon_count = text_combined.count('kết hôn') + text_combined.count('ket hon')
            luu_dong_count = text_combined.count('lưu động') + text_combined.count('luu dong')
            
            print(f"📊 Keywords: 'kết hôn' x{ket_hon_count}, 'lưu động' x{luu_dong_count}")
            print("-" * 40)
        
        # Test query similarity manually
        print("\n🧪 TESTING QUERY SIMILARITY:")
        print("=" * 60)
        
        test_query = "đăng ký kết hôn cần giấy tờ gì"
        print(f"Query: '{test_query}'")
        print()
        
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Load embedding model
        model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", 
                                   cache_folder="data/models/hf_cache", 
                                   device="cpu")
        
        query_embedding = model.encode([test_query])
        
        similarities = []
        
        for doc_name, doc_data in marriage_docs[:5]:  # Test top 5
            main_q = doc_data.get('main_question', '')
            if main_q.strip():
                main_embedding = model.encode([main_q])
                similarity = cosine_similarity(query_embedding, main_embedding)[0][0]
                
                similarities.append({
                    'doc': doc_name,
                    'question': main_q,
                    'similarity': similarity
                })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        print("📊 SIMILARITY RANKINGS:")
        for i, sim in enumerate(similarities, 1):
            print(f"{i}. {sim['similarity']:.4f} - {sim['doc']}")
            print(f"   Q: {sim['question'][:80]}...")
            print()
        
        if similarities and 'lưu động' in similarities[0]['doc'].lower():
            print("❌ PROBLEM CONFIRMED: 'lưu động' document has highest similarity!")
            print("💡 This confirms the routing issue.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_marriage_questions()
