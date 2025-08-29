#!/usr/bin/env python3
"""
Script to fix JSON structures to match quy_trinh_cong_chung format
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

def extract_legal_references(content_chunks):
    """Extract legal references from content chunks"""
    legal_refs = []

    # Common legal document patterns
    patterns = [
        r'Luật\s+[^,\n]+(?:\d{4})?',
        r'Nghị định\s+số\s+\d+/\d+/[^\s]+',
        r'Thông tư\s+số\s+\d+/\d+/[^\s]+',
        r'Quyết định\s+số\s+\d+/\d+/[^\s]+',
        r'Luật\s+[^\n,]+',
        r'Nghị định\s+[^\n,]+',
        r'Thông tư\s+[^\n,]+'
    ]

    all_content = " ".join([chunk.get("content", "") for chunk in content_chunks])

    for pattern in patterns:
        matches = re.findall(pattern, all_content, re.IGNORECASE)
        legal_refs.extend(matches)

    # Remove duplicates and clean
    legal_refs = list(set(legal_refs))
    return legal_refs

def create_full_metadata(title, content_chunks, collection_name):
    """Create full metadata section based on content analysis"""

    # Default metadata structure
    metadata = {
        "source": f"data/documents/{collection_name}/processed_content.json",
        "title": title,
        "code": "QT 01/UNKNOWN",
        "issuing_authority": "Sở Tư pháp",
        "effective_date": datetime.now().strftime("%Y-%m-%d"),
        "executing_agency": "Sở Tư pháp cấp tỉnh",
        "applicant_type": ["Cá nhân", "Tổ chức"],
        "processing_time_text": "Theo quy định pháp luật",
        "fee_vnd": None,
        "fee_text": "Theo quy định của pháp luật",
        "has_form": True,
        "requirements_conditions": "Thủ tục hành chính được thực hiện theo quy định của pháp luật",
        "legal_basis_references": extract_legal_references(content_chunks)
    }

    # Customize based on collection type
    if "ho_tich" in collection_name:
        metadata.update({
            "issuing_authority": "UBND cấp xã",
            "executing_agency": "UBND cấp xã",
            "fee_text": "Theo quy định của UBND cấp tỉnh",
            "requirements_conditions": "Công dân Việt Nam có nhu cầu thực hiện thủ tục hộ tịch"
        })
    elif "luat_su" in collection_name:
        metadata.update({
            "issuing_authority": "Bộ Tư pháp",
            "executing_agency": "Bộ Tư pháp",
            "fee_text": "Theo Thông tư 250/2016/TT-BTC",
            "requirements_conditions": "Người đã hoàn thành đào tạo nghề luật sư và tập sự hành nghề luật sư"
        })
    elif "cong_chung" in collection_name:
        metadata.update({
            "issuing_authority": "Sở Tư pháp",
            "executing_agency": "Sở Tư pháp cấp tỉnh",
            "fee_text": "Theo quy định của pháp luật",
            "requirements_conditions": "Công chứng viên, tổ chức hành nghề công chứng đáp ứng điều kiện theo quy định"
        })

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

def fix_simple_structure(json_file_path, collection_name):
    """Fix simple structure JSON files"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract existing data
        title = data.get("title", "Unknown")
        content_chunks = data.get("content_chunks", [])

        # Create new structure
        metadata = create_full_metadata(title, content_chunks, collection_name)
        fee_structure = create_fee_structure()

        # Update content chunks with better source references
        for chunk in content_chunks:
            if "source_reference" not in chunk:
                chunk["source_reference"] = f"{metadata['code']} - Chunk {chunk.get('chunk_id', 'N/A')}"
            if "keywords" not in chunk:
                chunk["keywords"] = []

        new_data = {
            "metadata": metadata,
            "fee_structure": fee_structure,
            "content_chunks": content_chunks
        }

        # Write back
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"Error fixing {json_file_path}: {str(e)}")
        return False

def fix_basic_with_fee_structure(json_file_path, collection_name):
    """Fix basic_with_fee structure JSON files"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract existing data
        title = data.get("title", "Unknown")
        content_chunks = data.get("content_chunks", [])
        existing_fee = data.get("fee_structure", {})

        # Create metadata
        metadata = create_full_metadata(title, content_chunks, collection_name)

        # Convert existing fee structure to new format
        fee_structure = create_fee_structure()

        # If existing fee structure has direct/online info, preserve it
        if isinstance(existing_fee, dict):
            if "direct" in existing_fee:
                fee_structure["main_fee"]["direct"] = existing_fee["direct"]
            if "online" in existing_fee:
                fee_structure["main_fee"]["online"] = existing_fee["online"]
            if "description" in existing_fee:
                fee_structure["main_fee"]["description"] = existing_fee["description"]

        # Update content chunks
        for chunk in content_chunks:
            if "source_reference" not in chunk:
                chunk["source_reference"] = f"{metadata['code']} - Chunk {chunk.get('chunk_id', 'N/A')}"
            if "keywords" not in chunk:
                chunk["keywords"] = []

        new_data = {
            "metadata": metadata,
            "fee_structure": fee_structure,
            "content_chunks": content_chunks
        }

        # Write back
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"Error fixing {json_file_path}: {str(e)}")
        return False

def fix_collection(collection_path, structure_type):
    """Fix all JSON files in a collection"""
    collection_name = Path(collection_path).name
    documents_path = Path(collection_path) / "documents"

    print(f"\n🔧 Processing collection: {collection_name}")
    print(f"   Structure type: {structure_type}")

    if not documents_path.exists():
        print(f"   No documents folder found")
        return 0, 0

    fixed_count = 0
    total_count = 0

    # Process each DOC folder
    for doc_folder in sorted(documents_path.glob("DOC_*")):
        if doc_folder.is_dir():
            json_files = list(doc_folder.glob("*.json"))
            # Skip backup files
            json_files = [f for f in json_files if not f.name.endswith(".backup_simple") and not f.name.endswith(".backup_final")]

            for json_file in json_files:
                total_count += 1

                if structure_type == "simple_structure":
                    success = fix_simple_structure(json_file, collection_name)
                elif structure_type == "basic_with_fee":
                    success = fix_basic_with_fee_structure(json_file, collection_name)
                else:
                    print(f"   Unknown structure type: {structure_type}")
                    continue

                if success:
                    fixed_count += 1
                    print(f"   ✅ Fixed: {json_file.name}")
                else:
                    print(f"   ❌ Failed: {json_file.name}")

    print(f"   Results: {fixed_count}/{total_count} files fixed")
    return fixed_count, total_count

def main():
    """Main function to fix all collections that need fixing"""

    # Collections to fix based on classification
    collections_to_fix = {
        "simple_structure": ["quy_trinh_cap_ho_tich_cap_xa"],
        "basic_with_fee": [
            "quy_trinh_pbgdpl_htpldn",
            "quy_trinh_quan_tai_vien",
            "quy_trinh_thua_phat_lai",
            "quy_trinh_trong_tai_thuong_mai",
            "quy_trinh_tu_van_phap_luat"
        ]
    }

    collections_base = Path("d:/Personal/LegalRAG_Fixed/backend/data/storage/collections")

    print("🚀 STARTING BATCH JSON STRUCTURE FIX")
    print("=" * 60)

    total_fixed = 0
    total_processed = 0

    # Fix simple structure collections first
    print("\n📝 FIXING SIMPLE STRUCTURE COLLECTIONS:")
    print("-" * 50)

    for collection_name in collections_to_fix["simple_structure"]:
        collection_path = collections_base / collection_name
        if collection_path.exists():
            fixed, processed = fix_collection(collection_path, "simple_structure")
            total_fixed += fixed
            total_processed += processed
        else:
            print(f"   Collection not found: {collection_name}")

    # Fix basic_with_fee structure collections
    print("\n💰 FIXING BASIC WITH FEE COLLECTIONS:")
    print("-" * 50)

    for collection_name in collections_to_fix["basic_with_fee"]:
        collection_path = collections_base / collection_name
        if collection_path.exists():
            fixed, processed = fix_collection(collection_path, "basic_with_fee")
            total_fixed += fixed
            total_processed += processed
        else:
            print(f"   Collection not found: {collection_name}")

    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {total_processed}")
    print(f"Total files fixed: {total_fixed}")
    print(f"Success rate: {(total_fixed/total_processed*100):.1f}%" if total_processed > 0 else "0%")

    if total_fixed == total_processed:
        print("\n🎉 All files successfully converted to full_metadata format!")
        print("✅ Collections are now standardized with quy_trinh_cong_chung structure")
    else:
        print(f"\n⚠️  {total_processed - total_fixed} files failed to convert")

if __name__ == "__main__":
    main()
