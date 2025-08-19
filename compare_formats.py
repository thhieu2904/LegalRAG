#!/usr/bin/env python3
"""
Simple test để so sánh trực tiếp format cũ vs format mới
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.language_model import LLMService

def test_old_vs_new_format():
    """So sánh format cũ với format mới"""
    
    print("📋 SO SÁNH FORMAT CŨ VÀ MỚI")
    print("=" * 80)
    
    # Setup data
    system_prompt = "Bạn là trợ lý AI chuyên về pháp luật. CHỈ trả lời dựa trên tài liệu."
    user_query = "Lệ phí đăng ký khai sinh là bao nhiêu?"
    context = "Đăng ký khai sinh đúng hạn: MIỄN LỆ PHÍ. Đăng ký quá hạn: 50.000 VNĐ."
    
    # OLD FORMAT (WRONG - Prompt Bleeding)
    print("❌ FORMAT CŨ (SAI - GÂY PROMPT BLEEDING):")
    print("-" * 50)
    
    old_format = f"""{system_prompt}

THÔNG TIN TÀI LIỆU:
{context}

CÂUHỎI: {user_query}

TRẢ LỜI:"""
    
    print(old_format)
    
    print("\n" + "=" * 80)
    
    # NEW FORMAT (CORRECT - ChatML)
    print("✅ FORMAT MỚI (ĐÚNG - CHATML):")
    print("-" * 50)
    
    llm_service = LLMService()
    new_format = llm_service._format_prompt(
        system_prompt=system_prompt,
        user_query=user_query,
        context=context,
        chat_history=None
    )
    
    print(new_format)
    
    print("\n" + "=" * 80)
    print("🔍 PHÂN TÍCH KHÁC BIỆT:")
    print("=" * 80)
    
    print("❌ Format cũ có VẤN ĐỀ:")
    print("   1. System prompt và context bị trộn lẫn")
    print("   2. Model không phân biệt được đâu là instruction, đâu là data")
    print("   3. ### Câu hỏi: ### Trả lời: không phù hợp với chat model")
    print("   4. Dẫn đến Prompt Bleeding - model bối rối về vai trò")
    
    print("\n✅ Format mới GIẢI QUYẾT:")
    print("   1. System prompt riêng biệt với role 'system'")
    print("   2. Context được đặt trong user message, có ranh giới rõ ràng")
    print("   3. Sử dụng đúng ChatML template của PhoGPT-Chat")
    print("   4. Model hiểu rõ vai trò và không bị bleeding")
    
    print("\n🎯 KẾT QUẢ MONG ĐỢI:")
    print("   - Giảm hallucination")
    print("   - Câu trả lời chính xác hơn") 
    print("   - Tuân thủ system instruction tốt hơn")
    print("   - Không tự tạo thông tin không có trong tài liệu")

if __name__ == "__main__":
    test_old_vs_new_format()
