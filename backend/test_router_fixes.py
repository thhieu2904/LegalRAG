#!/usr/bin/env python3
"""
🧪 Test Router Fixes for Clarification System
"""

from app.services.router import QueryRouter
from sentence_transformers import SentenceTransformer

def test_router_fixes():
    print('🧪 Testing QueryRouter fixes...')
    
    try:
        # Load model and router
        model = SentenceTransformer('AITeamVN/Vietnamese_Embedding_v2', device='cpu')
        router = QueryRouter(model)
        
        print(f'✅ Router loaded with {len(router.collection_mappings)} collections')
        
        # Test collection mapping
        collections = router.get_collections()
        print(f'✅ get_collections(): {len(collections)} collections')
        for col in collections:
            print(f'   - {col["name"]}: {col["description"]} ({col["file_count"]} docs)')
        
        # Test question retrieval with mapping
        questions = router.get_example_questions_for_collection('ho_tich_cap_xa')
        print(f'✅ get_example_questions_for_collection(ho_tich_cap_xa): {len(questions)} questions')
        
        if questions:
            print(f'   Sample question: {questions[0]["text"][:50]}...')
            print(f'   Sample source: {questions[0]["source"]}')
        
        # Test direct collection name
        questions2 = router.get_example_questions_for_collection('quy_trinh_cap_ho_tich_cap_xa')
        print(f'✅ get_example_questions_for_collection(quy_trinh_cap_ho_tich_cap_xa): {len(questions2)} questions')
        
        print('🎉 All tests passed!')
        return True
        
    except Exception as e:
        print(f'❌ Test failed: {e}')
        return False

if __name__ == "__main__":
    test_router_fixes()
