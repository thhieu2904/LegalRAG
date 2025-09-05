from docx import Document
from pathlib import Path

# Check the filled form
file_path = Path("filled_form_final_test.docx")

if file_path.exists():
    print("=== CHECKING FILLED FORM ===")
    doc = Document(str(file_path))
    
    # Check if data is filled correctly
    filled_data = {
        "Nguyen Van A": False,
        "01/01/1990": False, 
        "123 Nguyen Trai, Quan 1, TP.HCM": False,
        "123456789012": False,
        "Nam": False
    }
    
    print("\n--- DOCUMENT CONTENT ---")
    for i, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if text:
            print(f"Line {i+1}: {text}")
            
            # Check for filled data
            for data_item in filled_data.keys():
                if data_item in text:
                    filled_data[data_item] = True
    
    print("\n--- DATA FILL CHECK ---")
    for data_item, found in filled_data.items():
        status = "✅" if found else "❌"
        print(f"{status} {data_item}: {'Found' if found else 'Missing'}")
    
    all_found = all(filled_data.values())
    print(f"\n{'✅ SUCCESS' if all_found else '❌ SOME DATA MISSING'}: Template filling {'completed!' if all_found else 'has issues'}")
    
else:
    print("❌ File not found: filled_form_final_test.docx")
