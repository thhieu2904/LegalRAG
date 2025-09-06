from docx import Document

# Check Khai_sinh template structure
print("=== KHAI SINH TEMPLATE CHECK ===")
try:
    doc = Document('test_khai_sinh_template.docx')
    print(f"Total paragraphs: {len(doc.paragraphs)}")
    
    # Find CCCD-related placeholders
    cccd_placeholders = []
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text and ('{{' in text or 'cccd' in text.lower() or 'tên' in text.lower() or 'sinh' in text.lower()):
            print(f"Line {i+1}: {text}")
            if '{{' in text and '}}' in text:
                cccd_placeholders.append(text)
    
    print(f"\n=== FOUND PLACEHOLDERS ===")
    if cccd_placeholders:
        for placeholder in cccd_placeholders:
            print(f"✅ {placeholder}")
    else:
        print("❌ No CCCD placeholders found. Template may need to be updated.")
        
    # Check if template needs CCCD placeholders
    print(f"\n=== SUGGESTION ===")
    expected_placeholders = [
        '{{ scan_ho_ten }}',
        '{{ scan_ngay_sinh }}', 
        '{{ scan_dia_chi }}',
        '{{ scan_cccd }}',
        '{{ scan_gioi_tinh }}'
    ]
    
    print("Template should contain these placeholders:")
    for placeholder in expected_placeholders:
        print(f"  {placeholder}")
        
except Exception as e:
    print(f"Error reading template: {e}")
