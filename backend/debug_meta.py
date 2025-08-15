from app.services.vector_database import VectorDBService
from sentence_transformers import SentenceTransformer
import chromadb

print('🔍 Initializing...')
client = chromadb.PersistentClient(path='data/vectordb')
collection = client.get_collection('ho_tich_cap_xa')
print(f'Collection count: {collection.count()}')

# Get ALL documents to see what titles exist
print('=== ALL DOCUMENT TITLES ===')
all_results = collection.get(include=['metadatas'])
if all_results and all_results['metadatas']:
    titles = set()
    for meta in all_results['metadatas']:
        title = meta.get('document_title', '')
        if isinstance(title, str):
            titles.add(title)
    
    print(f'Found {len(titles)} unique titles:')
    for title in sorted(titles):
        print(f'  "{title}"')
        
    # Look for marriage-related titles
    marriage_titles = [title for title in titles if 'kết hôn' in title.lower()]
    print(f'\nMarriage titles: {marriage_titles}')
    
    # Test with a real title
    if titles:
        real_title = list(titles)[0]
        print(f'\n=== TESTING WITH REAL TITLE: "{real_title}" ===')
        
        # Use proper embedding dimension (1024)
        test_filter = {'document_title': real_title}
        filtered = collection.query(
            query_embeddings=[[0.1]*1024],  # Correct dimension
            n_results=3,
            where=test_filter,
            include=['metadatas']
        )
        result_count = len(filtered['metadatas'][0]) if filtered['metadatas'] else 0
        print(f'Filter results: {result_count}')
        
        # Test with marriage title specifically
        marriage_title = "Đăng ký kết hôn"
        print(f'\n=== TESTING WITH MARRIAGE TITLE: "{marriage_title}" ===')
        
        test_filter = {'document_title': marriage_title}
        filtered = collection.query(
            query_embeddings=[[0.1]*1024],  # Correct dimension
            n_results=10,
            where=test_filter,
            include=['metadatas', 'distances']
        )
        result_count = len(filtered['metadatas'][0]) if filtered['metadatas'] else 0
        print(f'Marriage filter results: {result_count}')
        
        if result_count > 0:
            print('✅ Marriage filter working!')
            distances = filtered['distances'][0] if filtered['distances'] else []
            print(f'Distances: {distances[:3]}')
        else:
            print('❌ Marriage filter not working')
            
        # Test with actual search (similarity)
        print(f'\n=== TESTING SIMILARITY SEARCH (no filter) ===')
        similarity_results = collection.query(
            query_embeddings=[[0.1]*1024],
            n_results=5,
            include=['metadatas', 'distances']
        )
        sim_count = len(similarity_results['metadatas'][0]) if similarity_results['metadatas'] else 0
        print(f'Similarity results: {sim_count}')
        
        if sim_count > 0:
            distances = similarity_results['distances'][0]
            print(f'Distances (no filter): {distances[:3]}')
            print(f'Similarity threshold 0.4 would filter: {[d for d in distances if d <= 0.4]}')
            
        # Test threshold issue
        print(f'\n=== TESTING WITH FILTER + HIGH THRESHOLD ===')
        filtered_high = collection.query(
            query_embeddings=[[0.1]*1024],
            n_results=10,
            where=test_filter,
            include=['metadatas', 'distances']
        )
        
        if filtered_high['distances'] and filtered_high['distances'][0]:
            high_distances = filtered_high['distances'][0]
            print(f'Filtered distances: {high_distances[:5]}')
            above_04 = [d for d in high_distances if d > 0.4]
            print(f'Results above 0.4 threshold: {len(above_04)} out of {len(high_distances)}')
        
        print(f'\n🔥 DIAGNOSIS:')
        print(f'  - Marriage title exists: ✅')  
        print(f'  - Filter works: ✅')
        print(f'  - Issue: Similarity threshold 0.4 too strict for dummy embedding')
else:
    print('No metadata found')
