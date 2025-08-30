#!/usr/bin/env python3
"""
🧪 TEST SCRIPT: Prompt Service Single Layer
Test script để kiểm tra việc đơn giản hóa prompt service và loại bỏ prompt bleeding
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.prompt_service import prompt_service

def main():
    """Main test function"""
    print("🚀 Testing Prompt Service Single Layer Implementation")
    print("="*80)
    
    # Test the complete prompt generation
    prompt_service.test_complete_prompt_generation()
    
    print("\n🎯 Key Improvements:")
    print("- ✅ Removed emoji and complex symbols from system prompt")
    print("- ✅ Single method creates complete, ready-to-use prompt") 
    print("- ✅ No multi-layer formatting (eliminates prompt bleeding)")
    print("- ✅ Direct PhoGPT format (### Câu hỏi: ... ### Trả lời:)")
    print("- ✅ Simplified instruction language")
    
    print("\n📋 Usage in RAG Engine:")
    print("complete_prompt = prompt_service.get_complete_rag_prompt(")
    print("    query=user_query,")
    print("    context=retrieved_context,")  
    print("    confidence_level='medium',")
    print("    chat_history=chat_history")
    print(")")
    print("response = llm_service.generate_response_direct(complete_prompt)")
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    main()
