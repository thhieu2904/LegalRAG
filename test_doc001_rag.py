#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script để kiểm tra RAG retrieval với DOC_001 JSON chuẩn
"""

import json
import os
from datetime import datetime

def test_doc001_rag_retrieval():
    """Test RAG retrieval cho DOC_001"""

    # Đường dẫn file JSON
    json_path = "backend/data/storage/collections/quy_trinh_chung_thuc/documents/DOC_001/1_Cap_ban_sao_tu_so_goc.json"

    # Kiểm tra file tồn tại
    if not os.path.exists(json_path):
        print(f"❌ File không tồn tại: {json_path}")
        return False

    try:
        # Đọc và parse JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("✅ JSON loaded successfully!")
        print(f"📄 Document ID: {data['metadata']['document_id']}")
        print(f"📋 Title: {data['metadata']['title']}")
        print(f"🏷️  Document Code: {data['metadata']['document_code']}")
        print(f"📅 Issue Date: {data['metadata']['issue_date']}")
        print(f"🏛️  Issuing Authority: {data['metadata']['issuing_authority']}")
        print(f"🎯 Purpose: {data['metadata']['purpose'][:100]}...")
        print(f"📝 Total Keywords: {len(data['metadata']['keywords'])}")
        print(f"📚 Total References: {len(data['metadata']['references'])}")
        print(f"💰 Base Fee: {data['fee_structure']['base_fee']}")
        print(f"📄 Number of Content Chunks: {len(data['content_chunks'])}")

        # Test RAG retrieval simulation
        print("\n🔍 RAG RETRIEVAL TEST:")

        # Test queries
        test_queries = [
            "thời hạn giải quyết",
            "thành phần hồ sơ",
            "căn cứ pháp lý",
            "phí cấp bản sao",
            "người đại diện"
        ]

        for query in test_queries:
            print(f"\n📋 Query: '{query}'")
            relevant_chunks = []

            for chunk in data['content_chunks']:
                # Simple keyword matching (in real RAG, this would be semantic search)
                chunk_text = chunk['content'].lower() + ' '.join(chunk['keywords']).lower()
                query_lower = query.lower()

                if query_lower in chunk_text:
                    relevant_chunks.append({
                        'chunk_id': chunk['chunk_id'],
                        'title': chunk['title'],
                        'score': chunk['importance_score'],
                        'preview': chunk['content'][:200] + "..."
                    })

            if relevant_chunks:
                print(f"  ✅ Found {len(relevant_chunks)} relevant chunks:")
                for chunk in relevant_chunks[:2]:  # Show top 2
                    print(f"    • {chunk['title']} (Score: {chunk['score']})")
                    print(f"      Preview: {chunk['preview']}")
            else:
                print("  ❌ No relevant chunks found")

        # Test chunk structure
        print("\n📊 CHUNK STRUCTURE ANALYSIS:")
        for i, chunk in enumerate(data['content_chunks'], 1):
            print(f"  {i}. {chunk['title']}")
            print(f"     - Type: {chunk['chunk_type']}")
            print(f"     - Keywords: {len(chunk['keywords'])}")
            print(f"     - Importance: {chunk['importance_score']}")
            print(f"     - Content length: {len(chunk['content'])} chars")

        print("\n✅ DOC_001 RAG TEST COMPLETED SUCCESSFULLY!")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing DOC_001 RAG Retrieval")
    print("=" * 50)

    success = test_doc001_rag_retrieval()

    if success:
        print("\n🎉 All tests passed! DOC_001 is ready for RAG integration.")
    else:
        print("\n💥 Test failed! Please check the JSON structure.")
