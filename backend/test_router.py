#!/usr/bin/env python3
"""
Test script to verify the router fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.router import QueryRouter

def test_router():
    router = QueryRouter(None)
    docs = router.get_collection_documents_directly('quy_trinh_pbgdpl_htpldn')

    print(f"Documents found: {len(docs)}")
    print("\nFirst 3 documents:")
    for doc in docs[:3]:
        print(f"  {doc['filename']}: {doc['title']}")

if __name__ == "__main__":
    test_router()
