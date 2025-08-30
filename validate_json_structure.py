#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script validate JSON structure theo chuẩn mới
"""

import json
import os
from datetime import datetime

def validate_json_structure(json_path):
    """Validate JSON structure theo chuẩn mới"""

    if not os.path.exists(json_path):
        return False, f"File không tồn tại: {json_path}"

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        errors = []
        warnings = []

        # Validate metadata
        if 'metadata' not in data:
            errors.append("Thiếu trường 'metadata'")
        else:
            metadata = data['metadata']
            required_meta_fields = [
                'document_id', 'document_code', 'title', 'version',
                'issue_date', 'document_type', 'issuing_authority',
                'applicable_scope', 'purpose', 'keywords', 'references',
                'created_at', 'updated_at', 'status'
            ]

            for field in required_meta_fields:
                if field not in metadata:
                    errors.append(f"Metadata thiếu trường '{field}'")

            # Validate keywords and references
            if 'keywords' in metadata and not isinstance(metadata['keywords'], list):
                errors.append("Metadata.keywords phải là array")
            if 'references' in metadata and not isinstance(metadata['references'], list):
                errors.append("Metadata.references phải là array")

        # Validate fee_structure
        if 'fee_structure' not in data:
            errors.append("Thiếu trường 'fee_structure'")
        else:
            fee = data['fee_structure']
            required_fee_fields = ['base_fee', 'additional_fees', 'exemptions']

            for field in required_fee_fields:
                if field not in fee:
                    errors.append(f"Fee_structure thiếu trường '{field}'")

            # Validate additional_fees format
            if 'additional_fees' in fee and not isinstance(fee['additional_fees'], list):
                errors.append("Fee_structure.additional_fees phải là array")

        # Validate form_logic
        if 'form_logic' not in data:
            errors.append("Thiếu trường 'form_logic'")
        else:
            form = data['form_logic']
            required_form_fields = ['required_forms', 'optional_forms', 'form_requirements', 'submission_methods']

            for field in required_form_fields:
                if field not in form:
                    errors.append(f"Form_logic thiếu trường '{field}'")

        # Validate content_chunks
        if 'content_chunks' not in data:
            errors.append("Thiếu trường 'content_chunks'")
        else:
            chunks = data['content_chunks']
            if not isinstance(chunks, list):
                errors.append("Content_chunks phải là array")
            else:
                for i, chunk in enumerate(chunks):
                    required_chunk_fields = ['chunk_id', 'title', 'content', 'keywords', 'source_reference', 'chunk_type', 'importance_score']

                    for field in required_chunk_fields:
                        if field not in chunk:
                            errors.append(f"Chunk {i+1} thiếu trường '{field}'")

                    # Validate chunk_id format
                    if 'chunk_id' in chunk and not chunk['chunk_id'].startswith('chunk_'):
                        warnings.append(f"Chunk {i+1}: chunk_id nên bắt đầu bằng 'chunk_'")

                    # Validate importance_score
                    if 'importance_score' in chunk:
                        score = chunk['importance_score']
                        if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
                            errors.append(f"Chunk {i+1}: importance_score phải từ 0.0 đến 1.0")

                    # Validate chunk_type
                    valid_types = ['header', 'purpose_scope', 'references_definitions', 'procedure_details', 'forms_documents']
                    if 'chunk_type' in chunk and chunk['chunk_type'] not in valid_types:
                        warnings.append(f"Chunk {i+1}: chunk_type '{chunk['chunk_type']}' không chuẩn, nên dùng: {valid_types}")

        # Summary
        is_valid = len(errors) == 0
        summary = {
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'total_chunks': len(data.get('content_chunks', [])),
            'document_id': data.get('metadata', {}).get('document_id', 'Unknown')
        }

        return is_valid, summary

    except json.JSONDecodeError as e:
        return False, f"Lỗi parse JSON: {e}"
    except Exception as e:
        return False, f"Lỗi không xác định: {e}"

def main():
    """Main function"""
    print("🔍 JSON Structure Validator")
    print("=" * 50)

    # Test với file DOC_001 đã tạo
    test_file = "backend/data/storage/collections/quy_trinh_chung_thuc/documents/DOC_001/1_Cap_ban_sao_tu_so_goc.json"

    is_valid, result = validate_json_structure(test_file)

    if is_valid:
        print("✅ JSON structure hợp lệ!")
        print(f"📄 Document ID: {result['document_id']}")
        print(f"📊 Total chunks: {result['total_chunks']}")
        if result['warnings']:
            print(f"⚠️  Warnings: {len(result['warnings'])}")
            for warning in result['warnings']:
                print(f"   - {warning}")
    else:
        print("❌ JSON structure không hợp lệ!")
        if isinstance(result, dict):
            print(f"📄 Document ID: {result.get('document_id', 'Unknown')}")
            print(f"❌ Errors: {len(result['errors'])}")
            for error in result['errors']:
                print(f"   - {error}")
            if result.get('warnings'):
                print(f"⚠️  Warnings: {len(result['warnings'])}")
                for warning in result['warnings']:
                    print(f"   - {warning}")
        else:
            print(f"❌ Error: {result}")

if __name__ == "__main__":
    main()
