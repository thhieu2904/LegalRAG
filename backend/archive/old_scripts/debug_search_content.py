#!/usr/bin/env python3
"""
Script debug search results - Hiển thị đầy đủ nội dung và phân tích
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.vectordb_service import VectorDBService

def analyze_search_results(query: str, top_k: int = 10, similarity_threshold: float = 0.2):
    """
    Phân tích kết quả tìm kiếm chi tiết
    """
    print(f"🔍 PHÂN TÍCH KẾT QUẢ TÌM KIẾM")
    print("=" * 80)
    print(f"Query: '{query}'")
    print(f"Top K: {top_k}, Similarity Threshold: {similarity_threshold}")
    print()
    
    # Setup service
    settings.setup_environment()
    vectordb_service = VectorDBService()
    
    # Search across all collections
    all_results = []
    
    # Get all collections
    collections = vectordb_service.client.list_collections()
    print(f"📚 Available Collections: {[c.name for c in collections]}")
    print()
    
    for collection in collections:
        collection_name = collection.name
        print(f"🔎 Searching in collection: {collection_name}")
        
        results = vectordb_service.search_in_collection(
            collection_name=collection_name,
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        print(f"   Found: {len(results)} results")
        
        for result in results:
            result['collection'] = collection_name
            all_results.append(result)
    
    # Sort by similarity
    all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    
    print(f"\n📊 TỔNG KẾT: {len(all_results)} kết quả tìm được")
    print("=" * 80)
    
    # Analyze results
    for i, result in enumerate(all_results, 1):
        print(f"\n🎯 KẾT QUẢ {i}")
        print("-" * 50)
        
        # Basic info
        similarity = result.get('similarity', 0)
        collection = result.get('collection', 'unknown')
        print(f"📊 Similarity: {similarity:.4f}")
        print(f"📁 Collection: {collection}")
        
        # Metadata analysis
        metadata = result.get('metadata', {})
        print(f"📄 Document Title: {metadata.get('document_title', 'N/A')}")
        print(f"📝 Section Title: {metadata.get('section_title', 'N/A')}")
        print(f"🆔 Chunk ID: {metadata.get('chunk_id', 'N/A')}")
        print(f"📍 Chunk Index: {metadata.get('chunk_index_num', 'N/A')}")
        
        # Content analysis
        content = result.get('content', '')
        print(f"📏 Content Length: {len(content)} characters")
        print()
        print("📖 FULL CONTENT:")
        print("─" * 60)
        print(content)
        print("─" * 60)
        
        # Keywords analysis
        keywords = result.get('keywords', [])
        if keywords:
            print(f"🏷️  Keywords: {', '.join(keywords)}")
        
        # Source info
        source = result.get('source', {})
        file_path = source.get('file_path', 'N/A')
        print(f"📂 Source File: {Path(file_path).name if file_path != 'N/A' else 'N/A'}")
        
        print("\n" + "=" * 80)
    
    # Summary analysis
    print(f"\n📈 PHÂN TÍCH TỔNG KẾT")
    print("=" * 80)
    
    # Collection distribution
    collection_counts = {}
    document_titles = {}
    
    for result in all_results:
        coll = result.get('collection', 'unknown')
        collection_counts[coll] = collection_counts.get(coll, 0) + 1
        
        title = result.get('metadata', {}).get('document_title', 'N/A')
        document_titles[title] = document_titles.get(title, 0) + 1
    
    print("📊 Distribution by Collection:")
    for coll, count in collection_counts.items():
        print(f"   - {coll}: {count} results")
    
    print("\n📑 Distribution by Document:")
    for title, count in sorted(document_titles.items(), key=lambda x: x[1], reverse=True):
        if title != 'N/A':
            print(f"   - {title}: {count} results")
    
    # Similarity analysis
    if all_results:
        similarities = [r.get('similarity', 0) for r in all_results]
        print(f"\n🎯 Similarity Scores:")
        print(f"   - Highest: {max(similarities):.4f}")
        print(f"   - Lowest: {min(similarities):.4f}")
        print(f"   - Average: {sum(similarities)/len(similarities):.4f}")

def interactive_search():
    """
    Interactive search để user có thể test nhiều queries
    """
    print("🚀 INTERACTIVE SEARCH DEBUG")
    print("=" * 50)
    print("Nhập query để tìm kiếm (hoặc 'quit' để thoát)")
    print("Ví dụ: 'thủ tục khai sinh', 'khai sinh thông thường', etc.")
    print()
    
    while True:
        try:
            query = input("🔍 Query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Bye!")
                break
                
            if not query:
                print("⚠️  Vui lòng nhập query!")
                continue
            
            print()
            analyze_search_results(query, top_k=5, similarity_threshold=0.1)
            print("\n" + "="*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Bye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug search results')
    parser.add_argument('--query', '-q', type=str, help='Search query')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--top-k', '-k', type=int, default=10, help='Number of results')
    parser.add_argument('--threshold', '-t', type=float, default=0.2, help='Similarity threshold')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_search()
    elif args.query:
        analyze_search_results(args.query, args.top_k, args.threshold)
    else:
        # Default test
        test_query = "thủ tục khai sinh"
        analyze_search_results(test_query, top_k=5, similarity_threshold=0.1)
