#!/usr/bin/env python3
"""
Script to fix JSON structure in collections to match quy_trinh_cong_chung format
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

def extract_metadata_from_content(content_chunks):
    """Extract metadata information from content chunks"""
    metadata = {
        "source": "",
        "title": "",
        "code": "",
        "issuing_authority": "UBND cấp xã",
        "effective_date": datetime.now().strftime("%Y-%m-%d"),
        "executing_agency": "UBND cấp xã",
        "applicant_type": ["Cá nhân"],
        "processing_time_text": "Theo quy định pháp luật",
        "fee_vnd": None,
        "fee_text": "Theo quy định của pháp luật",
        "has_form": True,
        "requirements_conditions": "",
        "legal_basis_references": []
    }

    # Try to extract information from content
    all_content = " ".join([chunk.get("content", "") for chunk in content_chunks])

    # Extract legal references
    legal_patterns = [
        r'Luật\s+[^,\n]+(?:\d{4})?',
        r'Nghị định\s+số\s+\d+/\d+/[^\s]+',
        r'Thông tư\s+số\s+\d+/\d+/[^\s]+',
        r'Quyết định\s+số\s+\d+/\d+/[^\s]+'
    ]

    for pattern in legal_patterns:
        matches = re.findall(pattern, all_content, re.IGNORECASE)
        metadata["legal_basis_references"].extend(matches)

    # Remove duplicates
    metadata["legal_basis_references"] = list(set(metadata["legal_basis_references"]))

    return metadata

def create_fee_structure():
    """Create default fee structure"""
    return {
        "main_fee": {
            "direct": "Theo quy định",
            "online": "Theo quy định",
            "description": "Theo quy định của pháp luật"
        },
        "exemptions": [],
        "additional_fees": []
    }

def fix_json_structure(json_file_path):
    """Fix the JSON structure to match quy_trinh_cong_chung format"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract title from filename if not present
        if "title" not in data:
            filename = Path(json_file_path).stem
            # Remove numbering prefix like "01. "
            title = re.sub(r'^\d+\.\s*', '', filename)
            data["title"] = title

        # Create metadata section
        metadata = extract_metadata_from_content(data.get("content_chunks", []))
        metadata["title"] = data.get("title", "")
        metadata["source"] = f"data/documents/{Path(json_file_path).parent.parent.parent.name}/{Path(json_file_path).stem}.doc"

        # Create fee structure
        fee_structure = create_fee_structure()

        # Update content chunks structure
        if "content_chunks" in data:
            for chunk in data["content_chunks"]:
                if "source_reference" not in chunk:
                    chunk["source_reference"] = f"{data.get('procedure_code', 'Unknown')} - Chunk {chunk.get('chunk_id', 'N/A')}"
                if "keywords" not in chunk:
                    chunk["keywords"] = []

        # Create new structure
        new_data = {
            "metadata": metadata,
            "fee_structure": fee_structure,
            "content_chunks": data.get("content_chunks", [])
        }

        # Preserve any additional fields that might be useful
        for key, value in data.items():
            if key not in ["title", "description", "procedure_code", "processing_time", "content_chunks"]:
                new_data[key] = value

        # Write back the fixed structure
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

        print(f"Fixed: {json_file_path}")
        return True

    except Exception as e:
        print(f"Error fixing {json_file_path}: {str(e)}")
        return False

def fix_collection(collection_path):
    """Fix all JSON files in a collection"""
    collection_name = Path(collection_path).name
    print(f"Processing collection: {collection_name}")

    documents_path = Path(collection_path) / "documents"

    if not documents_path.exists():
        print(f"No documents folder found in {collection_path}")
        return

    fixed_count = 0
    total_count = 0

    # Walk through all DOC_XXX folders
    for doc_folder in documents_path.iterdir():
        if doc_folder.is_dir() and doc_folder.name.startswith("DOC_"):
            # Find JSON files in this folder
            for json_file in doc_folder.glob("*.json"):
                if not json_file.name.endswith(".backup_simple") and not json_file.name.endswith(".backup_final"):
                    total_count += 1
                    if fix_json_structure(json_file):
                        fixed_count += 1

    print(f"Collection {collection_name}: Fixed {fixed_count}/{total_count} files")

def main():
    """Main function to fix all collections"""
    collections_base = Path("d:/Personal/LegalRAG_Fixed/backend/data/storage/collections")

    if not collections_base.exists():
        print(f"Collections path not found: {collections_base}")
        return

    # Skip quy_trinh_cong_chung as it's already correct
    collections_to_fix = [
        "quy_trinh_boi_thuong_nn",
        "quy_trinh_cap_ho_tich_cap_xa",
        "quy_trinh_dau_gia_tai_san",
        "quy_trinh_ho_tich_cap_tp",
        "quy_trinh_luat_su",
        "quy_trinh_nuoi_con_nuoi",
        "quy_trinh_pbgdpl_htpldn",
        "quy_trinh_quan_tai_vien",
        "quy_trinh_thua_phat_lai",
        "quy_trinh_trong_tai_thuong_mai",
        "quy_trinh_tu_van_phap_luat"
    ]

    total_fixed = 0
    total_processed = 0

    for collection_name in collections_to_fix:
        collection_path = collections_base / collection_name
        if collection_path.exists():
            fix_collection(collection_path)
        else:
            print(f"Collection not found: {collection_name}")

    print(f"\nCompleted fixing collections. Total files processed: {total_processed}, Fixed: {total_fixed}")

if __name__ == "__main__":
    main()
