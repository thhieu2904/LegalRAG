#!/usr/bin/env python3
"""
🔄 MIGRATION PLAN: Single Service Approach
Kế hoạch chuyển đổi từ Multi-layer sang Single-layer prompt management
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.prompt_service import prompt_service
from app.services.language_model import LLMService
from app.core.config import settings

def compare_approaches():
    """So sánh 2 approaches: old vs new"""
    
    # Test data
    test_query = "đăng ký kết hôn cần giấy tờ gì"
    test_context = """
    11. ĐĂNG KÝ KẾT HÔN
    HỒ SƠ BAO GỒM:
    1. Tờ khai đăng ký kết hôn theo mẫu
    2. Căn cước công dân/Hộ chiếu của hai bên
    3. Giấy tờ chứng minh về cư trú (nếu cần)
    
    PHÍ: Miễn lệ phí đăng ký kết hôn. Phí cấp bản sao trích lục: 8.000 đồng
    """
    
    print("🔍 COMPARISON: Multi-layer vs Single-layer Approaches")
    print("="*80)
    
    # ❌ OLD APPROACH (Multi-layer)
    print("\n❌ OLD APPROACH (Multi-layer):")
    print("-" * 40)
    
    try:
        old_system_prompt = prompt_service.get_legal_rag_prompt("medium")
        print(f"📝 System prompt length: {len(old_system_prompt)} chars")
        print(f"🔍 System prompt preview: {old_system_prompt[:200]}...")
        
        # Simulate old _format_prompt behavior
        instruction_parts = []
        instruction_parts.append(old_system_prompt)
        if test_context:
            instruction_parts.append(f"Thông tin tham khảo:\n{test_context}")
        instruction_parts.append(f"Câu hỏi cần trả lời: {test_query}")
        
        old_final_prompt = f"### Câu hỏi: {chr(10).join(instruction_parts)}\n### Trả lời:"
        print(f"📏 Final prompt length: {len(old_final_prompt)} chars")
        
    except Exception as e:
        print(f"❌ Error in old approach: {e}")
    
    # ✅ NEW APPROACH (Single-layer)
    print("\n✅ NEW APPROACH (Single-layer):")
    print("-" * 40)
    
    try:
        new_complete_prompt = prompt_service.get_complete_rag_prompt(
            query=test_query,
            context=test_context,
            confidence_level="medium",
            chat_history=[{"role": "user", "content": "test previous question"}]
        )
        print(f"📝 Complete prompt length: {len(new_complete_prompt)} chars")
        print(f"📏 Estimated tokens: {len(new_complete_prompt) // 3}")
        
    except Exception as e:
        print(f"❌ Error in new approach: {e}")
    
    # COMPARISON
    print("\n🎯 COMPARISON RESULTS:")
    print("-" * 40)
    
    if 'old_final_prompt' in locals() and 'new_complete_prompt' in locals():
        print(f"📊 Old approach length: {len(old_final_prompt)} chars")
        print(f"📊 New approach length: {len(new_complete_prompt)} chars")
        print(f"📊 Difference: {len(new_complete_prompt) - len(old_final_prompt)} chars")
        
        # Check for formatting consistency
        old_count = old_final_prompt.count("### Câu hỏi:")
        new_count = new_complete_prompt.count("### Câu hỏi:")
        
        print(f"🔍 Old approach '### Câu hỏi:' count: {old_count}")
        print(f"🔍 New approach '### Câu hỏi:' count: {new_count}")
        
        if old_count == new_count == 1:
            print("✅ Both approaches have consistent formatting")
        else:
            print("⚠️ Formatting inconsistency detected")

def analyze_benefits():
    """Phân tích lợi ích của Single Service Approach"""
    
    print("\n🎯 SINGLE SERVICE BENEFITS ANALYSIS:")
    print("="*80)
    
    benefits = [
        {
            'category': '🔧 Maintainability',
            'items': [
                'Single Source of Truth cho prompt formatting',
                'No logic duplication between services',  
                'Clear separation of concerns',
                'Easier to debug and troubleshoot'
            ]
        },
        {
            'category': '📈 Performance', 
            'items': [
                'Direct path từ prompt service → LLM',
                'No intermediate formatting steps',
                'Less memory allocation',
                'Faster execution time'
            ]
        },
        {
            'category': '🐛 Bug Prevention',
            'items': [
                'Eliminates prompt bleeding issues',
                'Consistent prompt structure',
                'Predictable LLM input',
                'No multi-layer formatting conflicts'
            ]
        },
        {
            'category': '🎯 Standardization',
            'items': [
                'One way to create prompts',
                'Consistent developer experience', 
                'Easier onboarding for new developers',
                'Better code review process'
            ]
        }
    ]
    
    for benefit in benefits:
        print(f"\n{benefit['category']}:")
        for item in benefit['items']:
            print(f"  ✅ {item}")

def migration_checklist():
    """Checklist cho việc migration"""
    
    print("\n📋 MIGRATION CHECKLIST:")
    print("="*80)
    
    steps = [
        "✅ Created get_complete_rag_prompt() method",
        "✅ Created generate_response_direct() method", 
        "✅ Updated rag_engine.py to use new approach",
        "✅ Added deprecation warning to old methods",
        "⚠️ TODO: Search for all generate_response() calls and replace",
        "⚠️ TODO: Remove _format_prompt() method after testing",
        "⚠️ TODO: Remove generate_response() method after migration",
        "⚠️ TODO: Update any remaining direct calls to prompt_service.get_legal_rag_prompt()",
        "⚠️ TODO: Add comprehensive tests for new approach"
    ]
    
    for step in steps:
        print(f"  {step}")
    
    print(f"\n🎯 NEXT ACTIONS:")
    print("1. Test new approach thoroughly with real RAG queries")
    print("2. Monitor for any prompt bleeding or formatting issues") 
    print("3. Complete migration of all remaining calls")
    print("4. Remove deprecated methods after confident in new approach")

def main():
    """Main analysis function"""
    
    compare_approaches()
    analyze_benefits() 
    migration_checklist()
    
    print(f"\n✅ Analysis completed!")
    print(f"🎯 RECOMMENDATION: Complete the migration to Single Service Approach")
    print(f"📈 Expected outcome: Better maintainability, no prompt bleeding, improved performance")

if __name__ == "__main__":
    main()
