#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to fix all corrupted JSON files in quy_trinh_cap_ho_tich_cap_xa collection
"""

import os
import json
import win32com.client as win32
from pathlib import Path

def extract_word_content(doc_path):
    """Extract content from Word document"""
    try:
        word = win32.Dispatch("Word.Application")
        word.Visible = False

        doc = word.Documents.Open(str(doc_path))
        content = doc.Content.Text
        doc.Close(False)

        word.Quit()
        return content
    except Exception as e:
        print(f"Error extracting content from {doc_path}: {e}")
        return None

def create_structured_json(doc_name, content, doc_code, doc_dir_name):
    """Create properly structured JSON content"""

    # Extract title from filename
    title = Path(doc_name).stem

    # Generate procedure code
    procedure_code = f"QT {doc_code}/CX-HT"

    # Create the JSON structure
    json_data = {
        "metadata": {
            "source": f"data/documents/quy_trinh_cap_ho_tich_cap_xa/{doc_dir_name}/{doc_name}",
            "title": title,
            "code": procedure_code,
            "issuing_authority": "UBND cấp xã",
            "effective_date": "2025-08-29",
            "executing_agency": "UBND cấp xã",
            "applicant_type": ["Cá nhân"],
            "processing_time_text": "Theo quy định pháp luật",
            "fee_vnd": 0,
            "fee_text": "Miễn phí hoặc theo quy định của UBND cấp tỉnh",
            "has_form": True,
            "requirements_conditions": "Theo quy định của pháp luật về hộ tịch",
            "legal_basis_references": [
                "Luật Hộ tịch năm 2014",
                "Nghị định số 123/2015/NĐ-CP ngày 15/11/2015",
                "Nghị định số 104/2022/NĐ-CP ngày 21/12/2022"
            ]
        },
        "fee_structure": {
            "base_fee": 0,
            "additional_fees": [],
            "exemptions": ["Theo quy định pháp luật"]
        },
        "content_chunks": [
            {
                "chunk_id": 1,
                "section_title": "Nội dung quy trình",
                "content": content.replace('"', '\\"').replace('\n', '\\n').replace('\r', ''),
                "source_reference": f"{procedure_code} - Chunk 1",
                "keywords": ["hộ tịch", "quy trình", "thủ tục"]
            }
        ]
    }

    return json_data

def main():
    collection_path = Path(r"D:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents")

    print(f"Starting to fix all corrupted JSON files in collection: {collection_path}")

    # Get all DOC_XXX directories
    doc_dirs = [d for d in collection_path.iterdir() if d.is_dir() and d.name.startswith("DOC_")]
    doc_dirs.sort()

    fixed_count = 0
    error_count = 0

    for doc_dir in doc_dirs:
        print(f"\nProcessing directory: {doc_dir.name}")

        # Find the .doc file in this directory
        doc_files = list(doc_dir.glob("*.doc"))

        if doc_files:
            doc_file = doc_files[0]
            print(f"  Found document: {doc_file.name}")

            try:
                # Extract content from Word document
                content = extract_word_content(doc_file)

                if content:
                    # Generate JSON filename
                    json_filename = doc_file.stem + ".json"
                    json_path = doc_dir / json_filename

                    # Create structured JSON content
                    doc_code = doc_dir.name.replace("DOC_", "")
                    json_data = create_structured_json(doc_file.name, content, doc_code, doc_dir.name)

                    # Write the JSON file
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)

                    print(f"  ✓ Created corrected JSON: {json_filename}")
                    fixed_count += 1
                else:
                    print(f"  ✗ Failed to extract content from {doc_file.name}")
                    error_count += 1

            except Exception as e:
                print(f"  ✗ Error processing {doc_file.name}: {e}")
                error_count += 1
        else:
            print(f"  ✗ No .doc file found in {doc_dir.name}")
            error_count += 1

    print("\n=== Summary ===")
    print(f"Fixed files: {fixed_count}")
    print(f"Errors: {error_count}")
    print(f"Total processed: {fixed_count + error_count}")

if __name__ == "__main__":
    main()
