"""
Quick test để kiểm tra Conservative Strategy logic
"""

import os
import sys
import logging
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

def test_conservative_logic():
    """Test logic của Conservative Strategy"""
    
    # Simulate rerank scores
    test_cases = [
        {"score": 0.05, "expected_strategy": "CONSERVATIVE", "description": "Very low score"},
        {"score": 0.15, "expected_strategy": "CONSERVATIVE", "description": "Low score"},
        {"score": 0.25, "expected_strategy": "FULL", "description": "Medium score"},
        {"score": 0.80, "expected_strategy": "FULL", "description": "High score"}
    ]
    
    print("🧪 TESTING CONSERVATIVE STRATEGY LOGIC")
    print("=" * 60)
    
    for test in test_cases:
        score = test["score"]
        expected = test["expected_strategy"]
        desc = test["description"]
        
        # Apply the logic we implemented
        if score < 0.2:
            actual_strategy = "CONSERVATIVE"
            use_full_document_expansion = False
            max_context_length = 800
        else:
            actual_strategy = "FULL"
            use_full_document_expansion = True
            max_context_length = 3000
        
        status = "✅ PASS" if actual_strategy == expected else "❌ FAIL"
        
        print(f"{status} Score: {score:.2f} ({desc})")
        print(f"   Expected: {expected}, Got: {actual_strategy}")
        print(f"   Settings: use_full_document_expansion={use_full_document_expansion}, max_context={max_context_length}")
        print()

def test_context_filtering():
    """Test context filtering logic"""
    
    print("🎯 TESTING CONTEXT FILTERING")
    print("=" * 60)
    
    # Sample chunk content
    chunk_content = """
    Thủ tục đăng ký khai sinh bao gồm nhiều bước. 
    Về phí: đăng ký khai sinh đúng hạn được miễn lệ phí.
    Giấy tờ cần thiết gồm giấy chứng sinh và CMND.
    Thời gian xử lý là ngay trong ngày.
    """
    
    query_keywords = ['phí', 'tiền', 'lệ phí', 'miễn', 'cost', 'fee']
    sentences = chunk_content.split('.')
    relevant_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and any(keyword in sentence.lower() for keyword in query_keywords):
            relevant_sentences.append(sentence)
            print(f"✅ Relevant sentence: {sentence}")
    
    print(f"\n📊 Summary: {len(relevant_sentences)}/{len([s for s in sentences if s.strip()])} sentences are relevant")
    print(f"📝 Filtered content: {'. '.join(relevant_sentences)}")

if __name__ == "__main__":
    test_conservative_logic()
    print()
    test_context_filtering()
