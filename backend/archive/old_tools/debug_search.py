#!/usr/bin/env python3
"""
Debug Vector Search Issues
"""

from app.core.config import settings
from app.services.vectordb_service import VectorDBService

def main():
    print("🔍 DEBUGGING VECTOR SEARCH")
    print("=" * 50)
    
    # Initialize VectorDB
    vectordb = VectorDBService(
        persist_directory=settings.chroma_persist_directory,
        embedding_model=settings.embedding_model
    )
    
    # Test 1: Basic search với threshold rất thấp
    print("\n📊 Test 1: Basic search với threshold thấp")
    result = vectordb.search_in_collection(
        collection_name='ho_tich_cap_xa',
        query='khai sinh',
        top_k=3,
        similarity_threshold=0.1  # Rất thấp
    )
    
    print(f"Results count: {len(result)}")
    if result:
        print("First result keys:", list(result[0].keys()))
        for i, r in enumerate(result[:2]):
            similarity = r.get('similarity', 'N/A')
            distance = r.get('distance', 'N/A') 
            print(f"  Result {i+1}: similarity={similarity}, distance={distance}")
            print(f"    Content: {r['content'][:100]}...")
    else:
        print("  ❌ NO RESULTS even with threshold=0.1!")
    
    # Test 2: Kiểm tra raw ChromaDB search
    print("\n📊 Test 2: Raw ChromaDB search")
    try:
        collection = vectordb.client.get_collection('ho_tich_cap_xa')
        
        # Get query embedding trực tiếp
        query_embedding = vectordb.embedding_model.encode(['khai sinh'])
        print(f"Query embedding shape: {query_embedding.shape}")
        
        # ChromaDB query trực tiếp
        chroma_results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=3,
            include=['distances', 'documents', 'metadatas']
        )
        
        print(f"ChromaDB raw results: {len(chroma_results['documents'][0])}")
        if chroma_results['distances'][0]:
            distances = chroma_results['distances'][0]
            print(f"Distance range: {min(distances):.4f} - {max(distances):.4f}")
            
            # Chuyển distance thành similarity (ChromaDB dùng cosine distance)
            similarities = [1 - d for d in distances]
            print(f"Similarity range: {min(similarities):.4f} - {max(similarities):.4f}")
            
            # Check threshold hiện tại
            print(f"Current threshold: {settings.similarity_threshold}")
            above_threshold = [s for s in similarities if s >= settings.similarity_threshold]
            print(f"Results above threshold {settings.similarity_threshold}: {len(above_threshold)}")
            
    except Exception as e:
        print(f"Error in raw search: {e}")
    
    # Test 3: Thử query khác
    print("\n📊 Test 3: Different queries")
    test_queries = ['thủ tục', 'hồ sơ', 'đăng ký']
    
    # Test 4: Test với threshold mới
    print(f"\n📊 Test 4: Test với threshold mới = {settings.similarity_threshold}")
    result = vectordb.search_in_collection(
        'ho_tich_cap_xa', 'khai sinh', top_k=3, similarity_threshold=settings.similarity_threshold
    )
    print(f"Results với threshold {settings.similarity_threshold}: {len(result)}")
    
    if result:
        for i, r in enumerate(result):
            print(f"  Result {i+1}: similarity={r['similarity']:.3f}")
            print(f"    Content: {r['content'][:150]}...")
    
    # Test 5: Analyze chunk quality
    print(f"\n📊 Test 5: Analyze chunk quality")
    collection = vectordb.client.get_collection('ho_tich_cap_xa')
    sample_docs = collection.get(limit=5, include=['documents', 'metadatas'])
    
    if sample_docs['documents']:
        chunk_lengths = [len(doc) for doc in sample_docs['documents']]
        print(f"Sample chunk lengths: {chunk_lengths}")
        print(f"Average chunk length: {sum(chunk_lengths)/len(chunk_lengths):.0f} chars")
        
        # Show 1 sample chunk
        print(f"Sample chunk:")
        print(f"  {sample_docs['documents'][0][:200]}...")

if __name__ == "__main__":
    main()
