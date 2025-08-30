#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script convert 15 JSON files trong quy_trinh_chung_thuc sang cấu trúc chuẩn mới
"""

import json
import os
from datetime import datetime
import re

def convert_metadata(old_metadata):
    """Convert metadata sang cấu trúc chuẩn mới"""
    # Extract document ID from source path
    source_path = old_metadata.get('source', '')
    doc_match = re.search(r'DOC_(\d+)', source_path)
    doc_id = f"DOC_{doc_match.group(1)}" if doc_match else "DOC_UNKNOWN"

    # Extract keywords from title and content
    title = old_metadata.get('title', '')
    keywords = extract_keywords(title)

    # Convert legal_basis_references to references
    legal_refs = old_metadata.get('legal_basis_references', [])
    references = legal_refs if legal_refs else []

    return {
        "document_id": doc_id,
        "document_code": old_metadata.get('code', ''),
        "title": title,
        "version": old_metadata.get('version', '01'),
        "issue_date": old_metadata.get('effective_date', ''),
        "document_type": "Quy trình hành chính",
        "issuing_authority": old_metadata.get('issuing_authority', ''),
        "applicable_scope": extract_applicable_scope(title),
        "purpose": extract_purpose(title),
        "keywords": keywords,
        "references": references,
        "created_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "updated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "status": "active"
    }

def extract_keywords(text):
    """Extract keywords from text"""
    keywords = []

    # Common legal keywords
    legal_terms = [
        "chứng thực", "bản sao", "bản chính", "hộ tịch", "công chứng",
        "giấy tờ", "văn bản", "lệ phí", "thủ tục", "hành chính",
        "ủy ban nhân dân", "sở tư pháp", "phòng công chứng",
        "cá nhân", "tổ chức", "thời hạn", "giải quyết"
    ]

    for term in legal_terms:
        if term.lower() in text.lower():
            keywords.append(term)

    return keywords[:10]  # Limit to 10 keywords

def extract_applicable_scope(title):
    """Extract applicable scope from title"""
    if "cá nhân" in title.lower() or "tổ chức" in title.lower():
        return "Áp dụng đối với cá nhân và tổ chức có nhu cầu thực hiện thủ tục hành chính"
    return "Áp dụng theo quy định của pháp luật"

def extract_purpose(title):
    """Extract purpose from title"""
    return "Quy định trình tự, thủ tục, thời hạn và lệ phí thực hiện thủ tục hành chính theo quy định của pháp luật"

def convert_fee_structure(old_fee):
    """Convert fee_structure sang cấu trúc chuẩn mới"""
    base_fee = 0
    additional_fees = []
    exemptions = []
    payment_methods = ["Tiền mặt", "Chuyển khoản"]
    fee_notes = ""

    # Handle old fee_structure format
    if 'main_fee' in old_fee:
        main_fee = old_fee['main_fee']
        if isinstance(main_fee, dict) and 'direct' in main_fee:
            # Extract fee amount from string like "2.000đ/trang"
            fee_text = main_fee.get('direct', '0')
            amount_match = re.search(r'(\d+(?:\.\d+)?)', fee_text.replace(',', '').replace('.', ''))
            if amount_match:
                base_fee = int(float(amount_match.group(1)))

    if 'additional_fees' in old_fee:
        additional_fees = old_fee['additional_fees']

    if 'exemptions' in old_fee:
        exemptions = old_fee['exemptions']

    return {
        "base_fee": base_fee,
        "additional_fees": additional_fees,
        "exemptions": exemptions,
        "payment_methods": payment_methods,
        "fee_notes": fee_notes
    }

def convert_form_logic(old_form):
    """Convert form_logic sang cấu trúc chuẩn mới"""
    required_forms = []
    optional_forms = []
    form_requirements = []
    submission_methods = ["Nộp trực tiếp tại cơ quan"]
    form_notes = ""

    # Extract from old format
    if old_form.get('has_paper_form'):
        required_forms.append("Giấy tờ, văn bản gốc")
        submission_methods.append("Nộp hồ sơ giấy")

    if old_form.get('has_electronic_form'):
        submission_methods.append("Nộp hồ sơ điện tử")

    return {
        "required_forms": required_forms,
        "optional_forms": optional_forms,
        "form_requirements": form_requirements,
        "submission_methods": submission_methods,
        "form_notes": form_notes
    }

def convert_content_chunks(old_chunks):
    """Convert content_chunks sang cấu trúc chuẩn mới"""
    new_chunks = []

    chunk_type_mapping = {
        "Thông tin cơ bản": "header",
        "Định nghĩa": "references_definitions",
        "Thành phần": "procedure_details",
        "Thời hạn": "procedure_details",
        "Đối tượng": "procedure_details",
        "Kết quả": "procedure_details",
        "Yêu cầu": "procedure_details",
        "Căn cứ": "references_definitions",
        "Quy trình": "procedure_details",
        "Biểu mẫu": "forms_documents",
        "Hồ sơ lưu": "forms_documents"
    }

    for i, chunk in enumerate(old_chunks):
        chunk_id = f"chunk_{i+1:03d}_{chunk.get('section_title', f'chunk_{i+1}').lower().replace(' ', '_').replace('và', 'va').replace('đ', 'd')}"

        # Determine chunk type
        section_title = chunk.get('section_title', '')
        chunk_type = "procedure_details"  # default
        for key, value in chunk_type_mapping.items():
            if key in section_title:
                chunk_type = value
                break

        # Calculate importance score
        importance_scores = {
            "header": 0.9,
            "purpose_scope": 0.95,
            "references_definitions": 0.8,
            "procedure_details": 1.0,
            "forms_documents": 0.7
        }
        importance_score = importance_scores.get(chunk_type, 0.8)

        new_chunk = {
            "chunk_id": chunk_id,
            "title": chunk.get('section_title', f'Chunk {i+1}'),
            "content": chunk.get('content', ''),
            "keywords": chunk.get('keywords', []),
            "source_reference": chunk.get('source_reference', f'DOC - Chunk {i+1}'),
            "chunk_type": chunk_type,
            "importance_score": importance_score
        }
        new_chunks.append(new_chunk)

    return new_chunks

def convert_json_file(file_path):
    """Convert single JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert each section
        new_data = {
            "metadata": convert_metadata(data.get('metadata', {})),
            "fee_structure": convert_fee_structure(data.get('fee_structure', {})),
            "form_logic": convert_form_logic(data.get('form_logic', {})),
            "content_chunks": convert_content_chunks(data.get('content_chunks', []))
        }

        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

        return True, f"Converted {os.path.basename(file_path)}"

    except Exception as e:
        return False, f"Error converting {os.path.basename(file_path)}: {str(e)}"

def main():
    """Main function"""
    print("🔄 Converting 15 JSON files to new standard format")
    print("=" * 60)

    base_path = "backend/data/storage/collections/quy_trinh_chung_thuc/documents"

    success_count = 0
    error_count = 0

    for i in range(1, 16):  # DOC_001 to DOC_015
        doc_folder = f"DOC_{i:02d}"
        json_files = []

        # Find JSON files in the folder
        folder_path = os.path.join(base_path, doc_folder)
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith('.json') and not file.startswith('questions'):
                    json_files.append(os.path.join(folder_path, file))

        # Convert each JSON file found
        for json_file in json_files:
            success, message = convert_json_file(json_file)
            if success:
                success_count += 1
                print(f"✅ {message}")
            else:
                error_count += 1
                print(f"❌ {message}")

    print("\n" + "=" * 60)
    print(f"📊 Conversion Summary:")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📁 Total files processed: {success_count + error_count}")

    if success_count > 0:
        print("\n🎉 Conversion completed! All files now use the new standard format.")
    else:
        print("\n💥 No files were converted. Please check the file paths.")

if __name__ == "__main__":
    main()
