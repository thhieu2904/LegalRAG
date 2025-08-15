#!/usr/bin/env python3
"""
Test script cho prompt mới với nhiều câu hỏi hơn
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.language_model import LLMService

def test_enhanced_prompt():
    print("🧪 Testing Enhanced Prompt for Multiple Questions Generation")
    print("=" * 70)
    
    # Initialize LLM
    llm = LLMService()
    
    # Test data
    document_title = "Đăng ký khai sinh"
    document_summary = """Đối tượng: Cá nhân, Tổ chức. Cơ quan thực hiện: UBND cấp phường/xã. 
Thời gian xử lý: Ngay khi nhận đủ hồ sơ hợp lệ. Lệ phí: Miễn phí. 
Cách nộp hồ sơ: Trực tiếp, Trực tuyến. Cách nhận kết quả: Trực tiếp, Bưu chính.
Thành phần hồ sơ: Đơn đăng ký khai sinh theo mẫu, Giấy chứng sinh hoặc giấy ra viện,
Giấy tờ tùy thân của cha mẹ, Giấy chứng nhận kết hôn của cha mẹ..."""

    # Simplified enhanced user query
    user_query = f"""Tạo 10 câu hỏi khác nhau về thủ tục "{document_title}":

THÔNG TIN: {document_summary}

CÁC LOẠI CÂU HỎI CẦN TẠO:
- Thủ tục là gì? Ai làm được?
- Cần giấy tờ gì?
- Làm ở đâu? 
- Chi phí bao nhiêu?
- Mất bao lâu?
- Làm online được không?
- Nhận kết quả thế nào?
- Điều kiện gì?
- Quy trình ra sao?
- Lưu ý gì?

TẠO 10 CÂU HỎI NGẮN GỌN:"""

    # Simplified system prompt
    system_prompt = "Tạo câu hỏi ngắn. Mỗi câu 1 dòng, đánh số. Không lặp lại."
    
    print("📝 USER QUERY:")
    print(user_query[:500] + "...")
    print("\n🧠 SYSTEM PROMPT:")
    print(system_prompt)
    print("\n🤖 LLM RESPONSE:")
    
    # Call LLM với settings mới
    response = llm.generate_response(
        user_query=user_query,
        system_prompt=system_prompt,
        max_tokens=500,
        temperature=0.3
    )
    
    response_text = response.get('response', '')
    print(response_text)
    print("\n" + "=" * 70)
    
    # Extract questions với logic chống trùng lặp
    import re
    lines = [line.strip() for line in response_text.split('\n') if line.strip()]
    questions = []
    seen_questions = set()  # Để tránh trùng lặp
    
    for line in lines:
        # Remove numbering và bullet points
        cleaned_line = re.sub(r'^[\d\-\*\+\.\)]\s*', '', line).strip()
        if cleaned_line.endswith('?') and len(cleaned_line) > 5:
            # Tránh trùng lặp
            if cleaned_line.lower() not in seen_questions:
                questions.append(cleaned_line)
                seen_questions.add(cleaned_line.lower())
    
    if len(questions) >= 1:
        # Chọn câu hỏi chính - ưu tiên câu hỏi tổng quan
        main_question = questions[0]
        for q in questions[:3]:
            if any(keyword in q.lower() for keyword in ["là gì", "như thế nào", "thủ tục", "quy trình"]):
                main_question = q
                break
        
        # Lấy variants
        question_variants = [q for q in questions if q != main_question][:10]
        
        result = {
            "main_question": main_question,
            "question_variants": question_variants
        }
        
        print("✅ QUESTIONS EXTRACTED SUCCESSFULLY:")
        print(f"📊 Total questions: {len(questions)}")
        print(f"🎯 Main question: {main_question}")
        print(f"🔢 Variants: {len(question_variants)}")
        print("\n📋 FULL RESULT:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("❌ NO QUESTIONS FOUND IN RESPONSE")

if __name__ == "__main__":
    test_enhanced_prompt()
