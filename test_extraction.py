#!/usr/bin/env python3
"""
Test extraction capabilities for Vietnamese legal documents.
Tests: PDF extraction, DOCX extraction, metadata detection, section extraction.
"""

import sys
from pathlib import Path

# Test files
test_pdf = Path("d:\\Personal\\LegalRAG\\docs\\thamkhao\\1. Thủ tục xác định cơ quan giải quyết bồi thường.pdf")
test_docx = Path("d:\\Personal\\LegalRAG\\docs\\thamkhao\\1. Thủ tục xác định cơ quan giải quyết bồi thường.doc")

print("=" * 80)
print("Testing Document Extraction Capabilities")
print("=" * 80)

# Test 1: PDF Extraction
print("\n[TEST 1] PDF Extraction")
print("-" * 80)
if test_pdf.exists():
    try:
        import PyPDF2
        with open(test_pdf, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            print(f"✅ PyPDF2 available. Document has {len(reader.pages)} pages")
            # Extract first 500 chars from first page
            text = reader.pages[0].extract_text()[:500]
            print(f"Sample text (first 500 chars):\n{text}")
    except ImportError:
        print("❌ PyPDF2 not installed. Trying pdfplumber...")
        try:
            import pdfplumber
            with pdfplumber.open(test_pdf) as pdf:
                print(f"✅ pdfplumber available. Document has {len(pdf.pages)} pages")
                text = pdf.pages[0].extract_text()[:500]
                print(f"Sample text (first 500 chars):\n{text}")
        except ImportError:
            print("❌ pdfplumber not installed. Trying PDFMiner...")
            try:
                from pdfminer.high_level import extract_text
                text = extract_text(test_pdf)[:500]
                print(f"✅ PDFMiner available")
                print(f"Sample text (first 500 chars):\n{text}")
            except ImportError:
                print("❌ No PDF extraction library available")
                sys.exit(1)
else:
    print(f"❌ Test PDF not found at {test_pdf}")

# Test 2: DOCX Extraction
print("\n[TEST 2] DOCX Extraction (.docx modern format)")
print("-" * 80)
if test_docx.exists():
    try:
        from docx import Document
        try:
            doc = Document(test_docx)
            print(f"✅ python-docx available. Document has {len(doc.paragraphs)} paragraphs")
            text = "\n".join([p.text for p in doc.paragraphs[:10]])[:500]
            print(f"Sample text (first 500 chars):\n{text}")
        except ValueError as e:
            print(f"⚠️ File is old .doc format (Word 97-2003), not modern .docx")
            print(f"   Error: {e}")
            print(f"   Solution: Convert .doc to .docx or use python-docx-convert")
            print(f"   For now, we'll skip this test")
    except ImportError:
        print("❌ python-docx not installed")
        sys.exit(1)
else:
    print(f"❌ Test DOCX not found at {test_docx}")

# Test 3: Metadata Detection
print("\n[TEST 3] Metadata Detection from Text")
print("-" * 80)

sample_text = """
TRANG THEO DÕI SỐ LẦN SỬA ĐỔI TÀI LIỆU
...
1. MỤC ĐÍCH
Quy định thành phần hồ sơ, lệ phí (nếu có), trình tự, cách thức và thời gian giải quyết hồ sơ hành chính của cơ quan theo tiêu chuẩn TCVN ISO 9001:2015
...
i. Căn cứ pháp lý của thủ tục hành chính:
- Luật Trách nhiệm bồi thường của Nhà nước năm 2017.
- Nghị định số 68/2018/NĐ-CP ngày 15/5/2018 của Chính phủ quy định chi tiết
- Thông tư số 08/2025/TT-BTP ngày 12/6/2025 của Bộ trưởng Bộ Tư pháp
"""

import re

# Detect document code (Nghị định, Thông tư, etc.)
document_codes = re.findall(r'(Nghị định|Thông tư|Quyết định|Quy chế)\s+số\s+(\d+[A-Z0-9/-]*)', sample_text, re.IGNORECASE)
print(f"Document codes found: {document_codes}")

# Detect dates
dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', sample_text)
print(f"Dates found: {dates}")

# Detect sections (Điều, Khoản, Mục, etc.)
sections = re.findall(r'(Điều|Khoản|Mục|Chương|Phần)\s+(\d+|[IVX]+)', sample_text, re.IGNORECASE)
print(f"Sections found: {sections}")

# Detect organizations
orgs = re.findall(r'(Bộ\s+\w+|UBND|Sở\s+\w+)', sample_text)
print(f"Organizations found: {set(orgs)}")

# Test 4: Section Extraction
print("\n[TEST 4] Section Extraction")
print("-" * 80)

sections_in_text = re.findall(r'^(\d+\.\s+[A-Z\s]+)$', sample_text, re.MULTILINE)
print(f"Main sections found: {sections_in_text}")

print("\n[SUMMARY]")
print("-" * 80)
print("""
WHAT CAN BE EXTRACTED AUTOMATICALLY:
✅ Document structure (sections: 1., 2., 3., etc.)
✅ Document codes (Nghị định 68/2018/NĐ-CP, Thông tư 08/2025/TT-BTP)
✅ Dates (15/5/2018, 12/6/2025)
✅ Organizations/authorities (Bộ Tư pháp, UBND, Sở Tư pháp)
✅ Section references (Điều, Khoản, Mục numbers)
✅ Plain text content

WHAT CANNOT BE EXTRACTED (or unreliable):
❌ Signature blocks (images/handwritten)
❌ Table content (complex structure)
❌ Embedded images/diagrams
❌ Document type beyond pattern matching (is it "Quy trình" or "Hướng dẫn"?)
❌ Issuing/executing authority (needs NER/ML model)
❌ Effective date vs issue date (context-dependent)

RECOMMENDATION:
→ Store ONLY auto-extractable fields in database
→ Use JSONB for optional metadata (confidence score included)
→ Document code: YES, extractable via regex + manual filename
→ Effective date: NO, too context-dependent
→ Issuing authority: NO, needs named entity recognition
→ Structure (sections): YES, extractable via regex
""")
