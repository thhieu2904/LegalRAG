#!/usr/bin/env python3
"""Test RAG với query nuôi con nuôi"""

import sys
import os
sys.path.append('.')

from app.services.rag_service import RAGService
from app.services.vectordb_service import VectorDBService  
from app.services.llm_service import LLMService
from app.core.config import settings

def test_query():
    print("🧪 Testing RAG with nuôi con nuôi query...")
    
    vectordb_service = VectorDBService()
    llm_service = LLMService()
    rag_service = RAGService(str(settings.documents_path), vectordb_service, llm_service)
    
    # Test với câu hỏi về nuôi con nuôi
    query = "thủ tục nuôi con nuôi"
    print(f"🔍 Query: {query}")
    
    result = rag_service.query(query)
    
    print(f"✅ Answer preview: {result['answer'][:200]}...")
    print(f"📁 Source files: {list(result.get('source_files', []))[:2]}")
    print(f"⏱️  Processing time: {result.get('processing_time', 0):.2f}s")

if __name__ == "__main__":
    test_query()
