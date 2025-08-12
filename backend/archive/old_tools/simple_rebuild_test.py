#!/usr/bin/env python3
"""
Simple Rebuild Test for Content-Aware Chunking
"""

import sys
import shutil
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.services.document_processor import DocumentProcessor

def rebuild_test():
    print("🔄 TESTING CONTENT-AWARE DOCUMENT PROCESSING")
    print("=" * 60)
    
    # Initialize document processor
    processor = DocumentProcessor()
    
    print(f"📁 Processing documents from: {settings.documents_dir}")
    
    # Process directory
    collections_data = processor.process_directory(str(settings.documents_dir))
    
    if collections_data:
        print("✅ SUCCESS!")
        print(f"📊 Collections processed: {len(collections_data)}")
        
        total_chunks = 0
        for collection_name, chunks in collections_data.items():
            chunk_count = len(chunks)
            total_chunks += chunk_count
            print(f"   - {collection_name}: {chunk_count} chunks")
            
            # Show sample chunk quality
            if chunks:
                sample = chunks[0]
                content = sample.get('content', '')
                lines = content.count('\n') + 1
                length = len(content)
                
                print(f"     Sample chunk: {lines} lines, {length} chars")
                if lines > 1:
                    print(f"     ✅ Multi-line chunk")
                else:
                    print(f"     ⚠️  Single-line chunk")
        
        print(f"\n📈 TOTAL: {total_chunks} chunks across {len(collections_data)} collections")
        
        # Quality summary
        all_chunks = []
        for chunks in collections_data.values():
            all_chunks.extend(chunks)
        
        if all_chunks:
            multi_line = sum(1 for chunk in all_chunks if chunk.get('content', '').count('\n') > 0)
            proper_endings = sum(1 for chunk in all_chunks 
                               if chunk.get('content', '').strip().endswith(('.', '!', '?', ':')))
            
            print(f"\n🎯 QUALITY METRICS:")
            print(f"   Multi-line chunks: {multi_line}/{len(all_chunks)} ({multi_line/len(all_chunks)*100:.1f}%)")
            print(f"   Proper endings: {proper_endings}/{len(all_chunks)} ({proper_endings/len(all_chunks)*100:.1f}%)")
            
            # Compare with old results (from analyze_chunks.py)
            print(f"\n📊 IMPROVEMENT COMPARISON:")
            print(f"   Before (old chunking): 0% multi-line, 50% proper endings")
            print(f"   After (content-aware): {multi_line/len(all_chunks)*100:.1f}% multi-line, {proper_endings/len(all_chunks)*100:.1f}% proper endings")
            
            if multi_line/len(all_chunks) > 0.5:
                print(f"   🎉 SIGNIFICANT IMPROVEMENT in chunk quality!")
            else:
                print(f"   ⚠️  Still needs improvement")
    else:
        print("❌ No collections processed!")

if __name__ == "__main__":
    rebuild_test()
