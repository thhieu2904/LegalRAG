#!/usr/bin/env python3
"""Quick test for LLM response quality"""

import sys
import os
import logging
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.rag_service import RAGService
from app.services.vectordb_service import VectorDBService
from app.services.llm_service import LLMService
from app.core.config import settings

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    print('🧪 Quick test with new system prompt...')
    
    setup_logging()
    logger = logging.getLogger()
    
    # Initialize services
    print("Initializing services...")
    llm_service = LLMService()
    vectordb_service = VectorDBService()
    
    documents_dir = os.path.join(settings.base_dir, "data", "documents")
    rag_service = RAGService(
        documents_dir=documents_dir,
        vectordb_service=vectordb_service,
        llm_service=llm_service
    )
    
    # Test query
    question = 'thủ tục đăng ký khai sinh'
    print(f'🔍 Testing query: {question}')
    
    start_time = datetime.now()
    result = rag_service.query(question)
    end_time = datetime.now()
    
    processing_time = (end_time - start_time).total_seconds()
    
    print(f'✅ Success: {result.get("success", True)}')
    print(f'📊 Processing time: {processing_time:.2f}s')
    print(f'📏 Answer length: {len(result.get("answer", ""))} chars')
    print('💬 Answer:')
    print('-' * 60)
    print(result.get("answer", "No answer"))
    print('-' * 60)

if __name__ == "__main__":
    main()
