#!/usr/bin/env python3
"""
Simple Verification Test - Check our fixes in the code
"""

import os
import re

def verify_backend_fixes():
    """Verify our fixes are in the code"""
    print("🔍 Verifying Backend Fixes in Code")
    print("=" * 50)
    
    rag_engine_path = "backend/app/services/rag_engine.py"
    
    if not os.path.exists(rag_engine_path):
        print("❌ RAG engine file not found")
        return False
    
    with open(rag_engine_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_verified = []
    
    # Check 1: All clarification responses use "clarification_needed" type
    clarification_type_pattern = r'"type":\s*"clarification_needed"'
    clarification_matches = re.findall(clarification_type_pattern, content)
    
    # Should NOT find old "clarification" type (without _needed)
    old_type_pattern = r'"type":\s*"clarification"[^_]'
    old_matches = re.findall(old_type_pattern, content)
    
    print(f"✅ Found {len(clarification_matches)} 'clarification_needed' types")
    if old_matches:
        print(f"❌ Found {len(old_matches)} old 'clarification' types")
        fixes_verified.append(False)
    else:
        print("✅ No old 'clarification' types found")
        fixes_verified.append(True)
    
    # Check 2: Document and question responses use "options" not "suggestions"
    options_pattern = r'"options":\s*[a-zA-Z_]+'
    options_matches = re.findall(options_pattern, content)
    
    suggestions_pattern = r'"suggestions":\s*[a-zA-Z_]+'
    suggestions_matches = re.findall(suggestions_pattern, content)
    
    print(f"✅ Found {len(options_matches)} 'options' usages")
    if suggestions_matches:
        print(f"❌ Found {len(suggestions_matches)} 'suggestions' usages (should be 'options')")
        fixes_verified.append(False)
    else:
        print("✅ No 'suggestions' usages found in clarification responses")
        fixes_verified.append(True)
    
    # Check 3: Look for specific fixed sections
    document_section = '"message": f"Bạn đã chọn \'{collection}\'. Hãy chọn tài liệu cụ thể:"'
    question_section = '"message": f"Bạn đã chọn tài liệu \'{document_title}\'. Hãy chọn câu hỏi phù hợp:"'
    
    if document_section in content:
        print("✅ Document selection message found")
        fixes_verified.append(True)
    else:
        print("❌ Document selection message not found")
        fixes_verified.append(False)
    
    if question_section in content:
        print("✅ Question selection message found") 
        fixes_verified.append(True)
    else:
        print("❌ Question selection message not found")
        fixes_verified.append(False)
    
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 30)
    
    all_good = all(fixes_verified)
    if all_good:
        print("✅ ALL FIXES VERIFIED IN CODE!")
        print("✅ Backend should work correctly when started")
        print("\n🔧 Expected behavior:")
        print("  - Step 1: Returns type='clarification_needed' with collection options")
        print("  - Step 2: Returns type='clarification_needed' with document options")  
        print("  - Step 3: Returns type='clarification_needed' with question options")
        print("  - Frontend should display all steps correctly")
    else:
        print("❌ SOME FIXES NOT VERIFIED!")
        failed_checks = [i for i, check in enumerate(fixes_verified) if not check]
        print(f"Failed checks: {failed_checks}")
    
    return all_good

def create_expected_response_examples():
    """Show what the responses should look like"""
    print("\n📋 Expected Response Format Examples")
    print("=" * 50)
    
    step1_example = {
        "type": "clarification_needed",
        "clarification": {
            "message": "Câu hỏi của bạn không đủ cụ thể...",
            "options": [
                {
                    "id": "1",
                    "title": "Hộ tịch cấp xã", 
                    "action": "proceed_with_collection",
                    "collection": "ho_tich_cap_xa"
                }
            ]
        },
        "session_id": "xxx",
        "processing_time": 0.123
    }
    
    step2_example = {
        "type": "clarification_needed", 
        "clarification": {
            "message": "Bạn đã chọn 'ho_tich_cap_xa'. Hãy chọn tài liệu cụ thể:",
            "options": [
                {
                    "id": "1",
                    "title": "Đăng ký khai sinh",
                    "action": "proceed_with_document",
                    "collection": "ho_tich_cap_xa",
                    "document_title": "Đăng ký khai sinh"
                }
            ]
        },
        "session_id": "xxx", 
        "processing_time": 0.123
    }
    
    step3_example = {
        "type": "clarification_needed",
        "clarification": {
            "message": "Bạn đã chọn tài liệu 'Đăng ký khai sinh'. Hãy chọn câu hỏi phù hợp:",
            "options": [
                {
                    "id": "1", 
                    "title": "Điều kiện đăng ký khai sinh?",
                    "action": "answer_question",
                    "question_text": "Điều kiện đăng ký khai sinh?"
                },
                {
                    "id": "2",
                    "title": "Nhập câu hỏi khác", 
                    "action": "manual_input"
                }
            ]
        },
        "session_id": "xxx",
        "processing_time": 0.123
    }
    
    print("Step 1 (Collection Selection):")
    print(f"  Type: {step1_example['type']}")
    print(f"  Has options: {bool(step1_example['clarification']['options'])}")
    print(f"  First option action: {step1_example['clarification']['options'][0]['action']}")
    
    print("\nStep 2 (Document Selection):")
    print(f"  Type: {step2_example['type']}")
    print(f"  Has options: {bool(step2_example['clarification']['options'])}")
    print(f"  First option action: {step2_example['clarification']['options'][0]['action']}")
    
    print("\nStep 3 (Question Selection):")
    print(f"  Type: {step3_example['type']}")
    print(f"  Has options: {bool(step3_example['clarification']['options'])}")
    print(f"  First option action: {step3_example['clarification']['options'][0]['action']}")

if __name__ == "__main__":
    print("🚀 Simple Backend Fix Verification")
    print("=" * 60)
    
    success = verify_backend_fixes()
    
    if success:
        create_expected_response_examples()
        print("\n🎉 READY TO TEST WITH RUNNING BACKEND!")
        print("Start the backend and frontend should show document selection correctly")
    else:
        print("\n💥 FIXES NEED ATTENTION!")
        print("Check the verification output above")
