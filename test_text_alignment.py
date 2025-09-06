#!/usr/bin/env python3
"""
Test text-alignment detection trong Mammoth conversion
"""

import re
from pathlib import Path
import sys
import os

# Add app directory to path
current_dir = Path(__file__).parent
app_dir = current_dir / "identifill_service" / "app"
sys.path.insert(0, str(app_dir))

def test_alignment_regex():
    """Test regex patterns cho text alignment"""
    
    # Sample HTML patterns that might come from Mammoth
    test_cases = [
        '<p>Làm tại: Hà Nội, ngày 10 tháng 9 năm 2024</p>',
        '<p>    Làm tại: UBND xã ABC</p>',
        '<p style="text-align: right;">Làm tại: Hà Nội</p>',
        '<p class="right">Làm tại: HCM</p>',
        '<p>Nơi khác: content</p>',
        '<p>Làm tại Hà Nội</p>',  # No colon
    ]
    
    # Current regex from form_renderer.py
    current_pattern = r'<p>([\s]*Làm tại:[^<]*)</p>'
    
    print("🧪 Testing current regex pattern:")
    print(f"Pattern: {current_pattern}")
    print("-" * 50)
    
    for test_case in test_cases:
        match = re.search(current_pattern, test_case)
        if match:
            print(f"✅ MATCH: {test_case}")
            print(f"   Captured: '{match.group(1)}'")
        else:
            print(f"❌ NO MATCH: {test_case}")
        print()
    
    # Test broader patterns
    print("\n🔍 Testing broader patterns:")
    broader_patterns = [
        r'<p[^>]*>(.*Làm tại[^<]*)</p>',  # Any <p> with "Làm tại"
        r'<p[^>]*>(.*ngày.*tháng.*năm[^<]*)</p>',  # Date patterns
    ]
    
    for pattern in broader_patterns:
        print(f"\nPattern: {pattern}")
        for test_case in test_cases:
            match = re.search(pattern, test_case)
            if match:
                print(f"✅ {test_case} → '{match.group(1)}'")

def check_mammoth_classes():
    """Check if Mammoth generates CSS classes for alignment"""
    
    # Mammoth might generate these class patterns
    mammoth_patterns = [
        '<p class="center">',
        '<p class="right">',
        '<p class="left">',
        '<p class="justify">',
    ]
    
    print("\n📋 Mammoth CSS class patterns:")
    for pattern in mammoth_patterns:
        print(f"  {pattern}")

if __name__ == "__main__":
    test_alignment_regex()
    check_mammoth_classes()
    
    print("\n💡 Recommendations:")
    print("1. Use broader regex: r'<p[^>]*>(.*Làm tại[^<]*)</p>'")
    print("2. Add patterns for date-based right alignment")
    print("3. Test with actual Mammoth output")
