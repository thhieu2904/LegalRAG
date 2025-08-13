"""
Test để kiểm tra prompt format của PhoGPT model
"""

import os
import sys
import logging
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

from app.services.language_model import LLMService

def test_prompt_formats():
    """Test các prompt format khác nhau để tìm format đúng"""
    
    llm_service = LLMService()
    
    query = "muốn đăng ký khai sinh thì có cần đóng tiền không"
    context = "Thủ tục đăng ký khai sinh là MIỄN PHÍ theo quy định."
    system_prompt = "Trả lời ngắn gọn dựa trên thông tin được cung cấp."
    
    # Test format hiện tại
    print("🧪 TESTING DIFFERENT PROMPT FORMATS")
    print("=" * 60)
    
    # Format 1: Current format
    print("\n📝 FORMAT 1 (Current):")
    current_format = f"### Câu hỏi: {system_prompt}\n\nNgữ cảnh thông tin:\n{context}\n\nCâu hỏi của người dùng: {query}\n### Trả lời:"
    print(current_format[:200] + "...")
    
    try:
        result = llm_service.model(
            current_format,
            max_tokens=100,
            temperature=0.1,
            stop=["### Câu hỏi:", "### Trả lời:", "\n\n###"],
            echo=False
        )
        response = result['choices'][0]['text'].strip()
        print(f"🤖 Response: {response[:150]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Format 2: Simpler format
    print("\n📝 FORMAT 2 (Simpler):")
    simple_format = f"{system_prompt}\n\nContext: {context}\n\nQuestion: {query}\n\nAnswer:"
    print(simple_format[:200] + "...")
    
    try:
        result = llm_service.model(
            simple_format,
            max_tokens=100,
            temperature=0.1,
            stop=["\n\nQuestion:", "\n\nContext:", "Question:", "Answer:"],
            echo=False
        )
        response = result['choices'][0]['text'].strip()
        print(f"🤖 Response: {response[:150]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Format 3: Chat format
    print("\n📝 FORMAT 3 (Chat):")
    chat_format = f"<|system|>\n{system_prompt}\n\n{context}<|end|>\n<|user|>\n{query}<|end|>\n<|assistant|>\n"
    print(chat_format[:200] + "...")
    
    try:
        result = llm_service.model(
            chat_format,
            max_tokens=100,
            temperature=0.1,
            stop=["<|user|>", "<|system|>", "<|end|>"],
            echo=False
        )
        response = result['choices'][0]['text'].strip()
        print(f"🤖 Response: {response[:150]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Format 4: Plain format (no special tokens)
    print("\n📝 FORMAT 4 (Plain):")
    plain_format = f"Instruction: {system_prompt}\n\nContext: {context}\n\nUser: {query}\n\nAssistant:"
    print(plain_format[:200] + "...")
    
    try:
        result = llm_service.model(
            plain_format,
            max_tokens=100,
            temperature=0.1,
            stop=["User:", "Instruction:", "Context:", "Assistant:"],
            echo=False
        )
        response = result['choices'][0]['text'].strip()
        print(f"🤖 Response: {response[:150]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_prompt_formats()
