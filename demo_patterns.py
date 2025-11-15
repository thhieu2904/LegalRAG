#!/usr/bin/env python3
"""
Demo: Metadata Extraction Patterns - Interactive Testing

Cách dùng:
1. python demo_patterns.py
2. Chọn một pattern để test
3. Nhập text hoặc dùng example
4. Xem kết quả extraction
"""

import re
from typing import Optional, List, Dict, Any

class LegalMetadataExtractor:
    """Extract metadata from Vietnamese legal documents"""
    
    # Existing patterns
    DOCUMENT_CODE_PATTERNS = [
        r'(\d+/\d{4}/NĐ-CP)',
        r'(\d+/\d{4}/QĐ-)',
        r'(\d+/\d{4}/TT-)',
        r'(QT\s*0?\d+/)',
    ]
    
    DATE_PATTERNS = [
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})',
    ]
    
    ORGANIZATION_PATTERNS = [
        r'(Bộ\s+\w+)',
        r'(Sở\s+\w+)',
        r'(Cục\s+\w+)',
        r'(Văn phòng\s+\w+)',
    ]
    
    SECTION_PATTERNS = [
        r'(Điều\s+\d+)',
        r'(Mục\s+\d+\.\d+)',
        r'(Chương\s+[IVX]+)',
    ]
    
    # New patterns for contracts
    CONTRACT_PATTERNS = {
        "party_a": r'Bên\s+A\s*:\s*([^(\n]+)',
        "party_b": r'Bên\s+B\s*:\s*([^(\n]+)',
        "contract_points": r'Điểm\s+(\d+)',
        "signing_date": r'Ngày\s+ký\s*:\s*(\d+/\d+/\d{4})',
        "signing_location": r'Nơi\s+ký\s*:\s*([^\n]+)',
    }
    
    @staticmethod
    def test_pattern(pattern: str, text: str) -> List[str]:
        """Test a regex pattern and return matches"""
        matches = re.findall(pattern, text)
        return matches
    
    @staticmethod
    def test_search_pattern(pattern: str, text: str) -> Optional[str]:
        """Test regex search (single match)"""
        match = re.search(pattern, text)
        return match.group(1) if match else None


def print_section(title: str):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def demo_document_code():
    """Demo document code extraction"""
    print_section("DEMO 1: Document Code Pattern")
    
    extractor = LegalMetadataExtractor()
    
    examples = [
        ("Nghị định", "Theo Nghị định số 68/2018/NĐ-CP...", r'(\d+/\d{4}/NĐ-CP)'),
        ("Quyết định", "Quyết định số 1205/2020/QĐ-TTg...", r'(\d+/\d{4}/QĐ-)'),
        ("Quy trình", "Mã hiệu: QT 0 1/BTNN", r'(QT\s*0?\d+/)'),
    ]
    
    for name, text, pattern in examples:
        print(f"\n📌 {name}:")
        print(f"  Text: {text}")
        print(f"  Pattern: {pattern}")
        matches = extractor.test_pattern(pattern, text)
        print(f"  Result: {matches}")


def demo_dates():
    """Demo date extraction"""
    print_section("DEMO 2: Date Pattern")
    
    extractor = LegalMetadataExtractor()
    
    examples = [
        ("Format DD/MM/YYYY", "Ngày ban hành: 01/7/2025", r'(\d{1,2}/\d{1,2}/\d{4})'),
        ("Format DD tháng MM năm YYYY", "Hôm nay là 15 tháng 3 năm 2024", r'(\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4})'),
        ("Multiple dates", "Từ 01/01/2025 đến 31/12/2025", r'(\d{1,2}/\d{1,2}/\d{4})'),
    ]
    
    for name, text, pattern in examples:
        print(f"\n📌 {name}:")
        print(f"  Text: {text}")
        print(f"  Pattern: {pattern}")
        matches = extractor.test_pattern(pattern, text)
        print(f"  Result: {matches}")


def demo_organizations():
    """Demo organization extraction"""
    print_section("DEMO 3: Organization Pattern")
    
    extractor = LegalMetadataExtractor()
    
    text = """
    SỞ TƯ PHÁP thông báo:
    Bộ Tư pháp công bố...
    Sở Lao động tỉnh A...
    Cục Thuế trung ương...
    Văn phòng UBND thành phố...
    """
    
    print(f"\nText:\n{text}")
    
    all_matches = []
    for i, pattern in enumerate(extractor.ORGANIZATION_PATTERNS):
        print(f"\n📌 Pattern {i+1}: {pattern}")
        matches = extractor.test_pattern(pattern, text)
        print(f"  Matches: {matches}")
        all_matches.extend(matches)
    
    print(f"\n✅ All organizations found: {list(set(all_matches))}")


def demo_sections():
    """Demo section extraction"""
    print_section("DEMO 4: Section Pattern")
    
    extractor = LegalMetadataExtractor()
    
    text = """
    Chương I - Nguyên tắc chung
    Điều 1 - Mục đích
    Mục 1.1 - Định nghĩa
    Điều 2 - Phạm vi
    Chương II - Bộ máy tổ chức
    Điều 32 - Quyền và nghĩa vụ
    Mục 2.1 - Trách nhiệm
    Điều 41 - Xử phạt
    """
    
    print(f"\nText:\n{text}")
    
    all_matches = []
    for i, pattern in enumerate(extractor.SECTION_PATTERNS):
        print(f"\n📌 Pattern {i+1}: {pattern}")
        matches = extractor.test_pattern(pattern, text)
        print(f"  Matches: {matches}")
        all_matches.extend(matches)
    
    print(f"\n✅ All sections found: {list(set(all_matches))}")


def demo_contract():
    """Demo contract pattern extraction"""
    print_section("DEMO 5: Contract Pattern (New)")
    
    extractor = LegalMetadataExtractor()
    
    text = """
    HỢPĐỒNG DỊCH VỤ
    
    Bên A: Công ty Cổ phần ABC (gọi tắt là "Bên A")
    Bên B: Ông Nguyễn Văn X, sinh năm 1990 (gọi tắt là "Bên B")
    
    Thỏa thuận như sau:
    
    Điểm 1: Nội dung công việc
    Điểm 2: Thời gian thực hiện
    Điểm 3: Thanh toán
    Điểm 4: Bảo mật
    
    Ngày ký: 15/01/2025
    Nơi ký: Tại văn phòng Công ty ABC
    """
    
    print(f"\nText:\n{text}")
    
    # Extract each field
    print("\n🔍 Extracting contract fields:\n")
    
    # Party A
    print("📌 Pattern: r'Bên\\s+A\\s*:\\s*([^(\\n]+)'")
    result = extractor.test_search_pattern(
        extractor.CONTRACT_PATTERNS["party_a"], 
        text
    )
    print(f"  Result (Party A): {result}")
    
    # Party B
    print("\n📌 Pattern: r'Bên\\s+B\\s*:\\s*([^(\\n]+)'")
    result = extractor.test_search_pattern(
        extractor.CONTRACT_PATTERNS["party_b"], 
        text
    )
    print(f"  Result (Party B): {result}")
    
    # Contract points
    print("\n📌 Pattern: r'Điểm\\s+(\\d+)'")
    matches = extractor.test_pattern(
        extractor.CONTRACT_PATTERNS["contract_points"], 
        text
    )
    print(f"  Result (Points): {matches}")
    
    # Signing date
    print("\n📌 Pattern: r'Ngày\\s+ký\\s*:\\s*(\\d+/\\d+/\\d{{4}})'")
    result = extractor.test_search_pattern(
        extractor.CONTRACT_PATTERNS["signing_date"], 
        text
    )
    print(f"  Result (Signing Date): {result}")
    
    # Signing location
    print("\n📌 Pattern: r'Nơi\\s+ký\\s*:\\s*([^\\n]+)'")
    result = extractor.test_search_pattern(
        extractor.CONTRACT_PATTERNS["signing_location"], 
        text
    )
    print(f"  Result (Signing Location): {result}")


def demo_regex_basics():
    """Demo regex basics"""
    print_section("REGEX BASICS")
    
    print("""
    Regex Syntax:
    ─────────────────────────────────────────────
    \\d       = Digit (0-9)
    \\w       = Word character (a-z, A-Z, 0-9, _)
    \\s       = Whitespace (space, tab)
    +        = 1 or more
    *        = 0 or more
    ?        = Optional (0 or 1)
    [...]    = Character class
    [^...]   = NOT character class
    (...)    = Capture group
    |        = OR
    
    Examples:
    ─────────────────────────────────────────────
    r'\\d{4}'            → 4 digits (like 2025)
    r'\\d{1,2}/\\d{1,2}' → DD/MM format
    r'Bộ\\s+\\w+'       → "Bộ " + word
    r'[^(\\n]+'          → Any char except "(" or newline
    r'Ngày\\s+ký\\s*:'  → "Ngày ký:" with optional spaces
    """)


def interactive_test():
    """Interactive pattern testing"""
    print_section("INTERACTIVE PATTERN TESTER")
    
    extractor = LegalMetadataExtractor()
    
    while True:
        print("\n📋 Choose pattern type to test:")
        print("  1. Document Code")
        print("  2. Date")
        print("  3. Organization")
        print("  4. Section")
        print("  5. Contract")
        print("  6. Custom Pattern")
        print("  7. Regex Basics")
        print("  0. Exit")
        
        choice = input("\n👉 Enter choice (0-7): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            demo_document_code()
        elif choice == "2":
            demo_dates()
        elif choice == "3":
            demo_organizations()
        elif choice == "4":
            demo_sections()
        elif choice == "5":
            demo_contract()
        elif choice == "6":
            print("\n📌 Custom Pattern Tester:")
            pattern = input("Enter regex pattern: ").strip()
            text = input("Enter text to search: ").strip()
            try:
                matches = extractor.test_pattern(pattern, text)
                print(f"✅ Matches: {matches}")
            except Exception as e:
                print(f"❌ Error: {e}")
        elif choice == "7":
            demo_regex_basics()
        else:
            print("❌ Invalid choice!")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  METADATA EXTRACTION PATTERNS - DEMO")
    print("="*70)
    
    # Run all demos automatically
    demo_document_code()
    demo_dates()
    demo_organizations()
    demo_sections()
    demo_contract()
    demo_regex_basics()
    
    # Interactive section
    print("\n" + "="*70)
    print("  Continue with interactive testing?")
    print("="*70)
    
    ans = input("\n👉 Run interactive tester? (y/n): ").strip().lower()
    if ans == "y":
        interactive_test()
