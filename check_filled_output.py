from docx import Document

# Check filled output file
print("=== CHECKING FILLED KHAI SINH OUTPUT ===")
try:
    doc = Document('khai_sinh_filled_test.docx')
    print(f"Total paragraphs: {len(doc.paragraphs)}")
    
    # Look for CCCD data in the filled document
    cccd_data_found = {
        "Trần Thảo Ly": False,
        "02/03/1977": False, 
        "Ấp Trang, Đại Phước, Cần Giờ, Trà Vinh": False,
        "084177012353": False,
        "Nữ": False
    }
    
    print("\n=== DOCUMENT CONTENT ===")
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            print(f"Line {i+1}: {text}")
            
            # Check for filled CCCD data
            for data_item in cccd_data_found.keys():
                if data_item in text:
                    cccd_data_found[data_item] = True
    
    print("\n=== CCCD DATA FILL CHECK ===")
    for data_item, found in cccd_data_found.items():
        status = "✅" if found else "❌"
        print(f"{status} {data_item}: {'Found' if found else 'Missing'}")
    
    all_found = all(cccd_data_found.values())
    print(f"\n{'✅ SUCCESS' if all_found else '⚠️ PARTIAL SUCCESS'}: Template filling {'completed!' if all_found else 'partially completed'}")
        
except Exception as e:
    print(f"Error reading filled document: {e}")

# Also check original template to see the structure
print("\n" + "="*60)
print("=== CHECKING ORIGINAL TEMPLATE STRUCTURE ===")
try:
    template_doc = Document('d:/Personal/LegalRAG_OCR/rag_service/data/storage/collections/quy_trinh_cap_ho_tich_cap_xa/documents/DOC_001/templates/Khai_sinh_template.docx')
    print(f"Template paragraphs: {len(template_doc.paragraphs)}")
    
    # Look for placeholder patterns
    placeholder_lines = []
    for i, para in enumerate(template_doc.paragraphs):
        text = para.text.strip()
        if text and ('{' in text or 'tên' in text.lower() or 'sinh' in text.lower() or 'địa chỉ' in text.lower()):
            print(f"Template Line {i+1}: {text}")
            placeholder_lines.append(text)
    
    if placeholder_lines:
        print(f"\n✅ Found {len(placeholder_lines)} potential placeholder lines in template")
    else:
        print("\n❌ No placeholder patterns found in template")
        
except Exception as e:
    print(f"Error reading template: {e}")
