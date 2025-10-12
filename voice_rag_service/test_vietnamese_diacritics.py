"""
Test Vietnamese diacritics preservation in F5-TTS
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "f5_tts"))

from f5_tts.model.utils import convert_char_to_pinyin

# Test Vietnamese text with various diacritics
test_texts = [
    "Xin chào, đây là hệ thống tư vấn pháp luật bằng tiếng Việt",
    "Chúng tôi cung cấp dịch vụ tư vấn pháp luật miễn phí",
    "Các quy định về bảo hiểm xã hội và nghĩa vụ thuế"
]

print("=" * 80)
print("Testing Vietnamese Diacritics Preservation")
print("=" * 80)

for i, text in enumerate(test_texts, 1):
    result = convert_char_to_pinyin([text])
    converted = "".join(result[0])
    
    print(f"\n{i}. Original: {text}")
    print(f"   Result:   {converted}")
    
    # Check if diacritics preserved
    if text == converted:
        print("   ✅ PERFECT MATCH - Diacritics preserved!")
    else:
        print("   ⚠️  CHANGED - Comparing:")
        for orig_char, conv_char in zip(text, converted):
            if orig_char != conv_char:
                print(f"      '{orig_char}' → '{conv_char}' (ord {ord(orig_char)} → {ord(conv_char)})")

print("\n" + "=" * 80)
