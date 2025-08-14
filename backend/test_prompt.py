#!/usr/bin/env python3
"""
Test script để kiểm tra prompt mới
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.language_model import LLMService

def test_new_prompt():
    print("🧪 Testing New Prompt for LLM-based Question Generation")
    print("=" * 60)
    
    # Initialize LLM
    llm = LLMService()
    
    # Test data
    document_title = "Đăng ký khai sinh"
    document_summary = "Đối tượng: Cá nhân. Cơ quan thực hiện: UBND cấp phường/xã. Thời gian xử lý: Ngay khi nhận đủ hồ sơ hợp lệ. Lệ phí: Miễn phí"
    
    # New approach - let LLM respond naturally, then extract
    user_query = f"""Tạo câu hỏi cho thủ tục: {document_title}

Mô tả thủ tục: {document_summary}

Hãy tạo:
1. Một câu hỏi chính
2. Ba câu hỏi biến thể khác

Trả lời ngắn gọn, mỗi câu hỏi một dòng:"""

    # Simple system prompt
    system_prompt = "Bạn tạo câu hỏi về thủ tục pháp luật. Trả lời ngắn gọn."
    
    print("📝 USER QUERY:")
    print(user_query)
    print("\n🧠 SYSTEM PROMPT:")
    print(system_prompt)
    print("\n🤖 LLM RESPONSE:")
    
    # Call LLM
    response = llm.generate_response(
        user_query=user_query,
        system_prompt=system_prompt,
        max_tokens=300,
        temperature=0.1
    )
    
    response_text = response.get('response', '')
    print(response_text)
    print("\n" + "=" * 60)
    
    # Try to extract JSON with new logic
    import re
    
    # Strategy: Extract questions from text response
    lines = [line.strip() for line in response_text.split('\n') if line.strip()]
    questions = []
    
    # Lọc ra những dòng chứa câu hỏi (kết thúc bằng dấu ?)
    for line in lines:
        # Remove numbering và bullet points
        cleaned_line = re.sub(r'^[\d\-\*\+\.\)]\s*', '', line).strip()
        if cleaned_line.endswith('?') and len(cleaned_line) > 5:
            questions.append(cleaned_line)
    
    if len(questions) >= 1:
        main_question = questions[0]
        question_variants = questions[1:] if len(questions) > 1 else []
        
        # Tạo JSON object
        result = {
            "main_question": main_question,
            "question_variants": question_variants
        }
        print("✅ QUESTIONS EXTRACTED SUCCESSFULLY:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("❌ NO QUESTIONS FOUND IN RESPONSE")

if __name__ == "__main__":
    test_new_prompt()
