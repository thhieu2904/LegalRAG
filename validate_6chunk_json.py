#!/usr/bin/env python3
"""
JSON Validation Script for quy_trinh_cap_ho_tich_cap_xa collection
Validates that all JSON files have the correct 6-chunk structure
"""

import json
import os
import sys
from pathlib import Path

def validate_json_file(file_path):
    """Validate a single JSON file for 6-chunk structure"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        errors = []
        warnings = []

        # Check required top-level fields
        required_fields = ['metadata', 'fee_structure', 'form_logic', 'content_chunks']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Check metadata fields
        if 'metadata' in data:
            metadata = data['metadata']
            required_metadata = ['source', 'title', 'code', 'issuing_authority', 'effective_date',
                               'executing_agency', 'applicant_type', 'processing_time_text',
                               'fee_vnd', 'fee_text', 'has_form', 'legal_basis_references']
            for field in required_metadata:
                if field not in metadata:
                    errors.append(f"Missing metadata field: {field}")

        # Check content_chunks - must have exactly 6 chunks
        if 'content_chunks' in data:
            chunks = data['content_chunks']
            if len(chunks) != 6:
                errors.append(f"Expected 6 chunks, found {len(chunks)}")

            # Check each chunk has required fields
            for i, chunk in enumerate(chunks):
                required_chunk_fields = ['chunk_id', 'section_title', 'content', 'source_reference', 'keywords']
                for field in required_chunk_fields:
                    if field not in chunk:
                        errors.append(f"Chunk {i+1}: Missing field {field}")

                # Check chunk_id is sequential
                if chunk.get('chunk_id') != i + 1:
                    errors.append(f"Chunk {i+1}: chunk_id should be {i+1}, found {chunk.get('chunk_id')}")

        # Check fee_structure
        if 'fee_structure' in data:
            fee_structure = data['fee_structure']
            if 'base_fee' not in fee_structure:
                warnings.append("fee_structure missing base_fee field")

        # Check form_logic
        if 'form_logic' in data:
            form_logic = data['form_logic']
            if 'has_electronic_form' not in form_logic and 'has_paper_form' not in form_logic:
                warnings.append("form_logic missing form type indicators")

        return {
            'file': os.path.basename(file_path),
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    except json.JSONDecodeError as e:
        return {
            'file': os.path.basename(file_path),
            'valid': False,
            'errors': [f"Invalid JSON: {str(e)}"],
            'warnings': []
        }
    except Exception as e:
        return {
            'file': os.path.basename(file_path),
            'valid': False,
            'errors': [f"Error reading file: {str(e)}"],
            'warnings': []
        }

def main():
    """Main validation function"""
    collection_path = Path(r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents")

    if not collection_path.exists():
        print(f"Collection path not found: {collection_path}")
        return

    print("🔍 Validating JSON files in quy_trinh_cap_ho_tich_cap_xa collection...")
    print("=" * 80)

    results = []
    total_files = 0
    valid_files = 0

    # Find all DOC_xxx directories
    for doc_dir in sorted(collection_path.glob("DOC_*")):
        if doc_dir.is_dir():
            # Find JSON files in each DOC directory
            for json_file in doc_dir.glob("*.json"):
                if not json_file.name.endswith('.backup_final'):
                    total_files += 1
                    result = validate_json_file(json_file)
                    results.append(result)

                    if result['valid']:
                        valid_files += 1
                        print(f"✅ {result['file']}")
                        if result['warnings']:
                            for warning in result['warnings']:
                                print(f"   ⚠️  {warning}")
                    else:
                        print(f"❌ {result['file']}")
                        for error in result['errors']:
                            print(f"   🔴 {error}")

    print("\n" + "=" * 80)
    print(f"📊 SUMMARY:")
    print(f"   Total files: {total_files}")
    print(f"   Valid files: {valid_files}")
    print(f"   Invalid files: {total_files - valid_files}")
    print(f"   Success rate: {(valid_files/total_files)*100:.1f}%" if total_files > 0 else "   Success rate: N/A")
    # Show detailed errors for invalid files
    invalid_results = [r for r in results if not r['valid']]
    if invalid_results:
        print("\n🔴 INVALID FILES DETAILS:")
        for result in invalid_results:
            print(f"\n{result['file']}:")
            for error in result['errors']:
                print(f"   - {error}")

if __name__ == "__main__":
    main()
