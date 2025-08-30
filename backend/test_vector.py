#!/usr/bin/env python3
"""
Test script to check vector DB metadata
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.vector import VectorDBService

def test_vector_db():
    vector_service = VectorDBService()
    collection = vector_service.get_collection('quy_trinh_pbgdpl_htpldn')

    if collection:
        results = collection.get(limit=3, include=['metadatas'])
        if results and results.get('metadatas'):
            print("Vector DB document_title values:")
            for i, metadata in enumerate(results['metadatas']):
                doc_title = metadata.get('document_title', 'None')
                print(f"  Doc {i+1}: {doc_title}")
        else:
            print("No metadata found in vector DB")
    else:
        print("Collection not found")

if __name__ == "__main__":
    test_vector_db()
