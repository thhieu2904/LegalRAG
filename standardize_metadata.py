import os
import json
from pathlib import Path

def convert_to_standard_metadata(json_file_path):
    """Convert JSON file to standard metadata format"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if already has metadata section
        if 'metadata' in data:
            print(f"✓ {json_file_path.name} - Already has metadata")
            return True

        # Create new structure with metadata
        new_data = {}

        # Extract metadata from existing fields
        metadata = {}

        # Required fields
        metadata['source'] = f"data/documents/{json_file_path.parent.parent.parent.name}/{json_file_path.parent.name}/{json_file_path.stem}.doc"
        metadata['title'] = data.get('title', '')
        metadata['code'] = data.get('procedure_code', '')
        metadata['issuing_authority'] = 'Sở Tư pháp'  # Default, can be updated based on content
        metadata['effective_date'] = '2025-08-27'  # Default current date
        metadata['executing_agency'] = 'Sở Tư pháp cấp tỉnh'  # Default, can be updated
        metadata['applicant_type'] = ['Cá nhân', 'Tổ chức']  # Default
        metadata['processing_time_text'] = data.get('processing_time', '')
        metadata['fee_vnd'] = None  # Will be extracted from fee_structure
        metadata['fee_text'] = ''  # Will be extracted from fee_structure
        metadata['has_form'] = True  # Default
        metadata['requirements_conditions'] = ''  # Can be extracted from content
        metadata['legal_basis_references'] = []

        # Extract legal basis
        legal_basis = data.get('legal_basis', '')
        if legal_basis:
            if isinstance(legal_basis, list):
                # If it's already a list, use it directly
                metadata['legal_basis_references'] = legal_basis
            else:
                # Split by comma and clean up
                refs = [ref.strip() for ref in legal_basis.split(',')]
                metadata['legal_basis_references'] = refs

        # Extract fee information
        fee_structure = data.get('fee_structure', {})
        if isinstance(fee_structure, dict) and 'main_fee' in fee_structure:
            main_fee = fee_structure.get('main_fee', {})
            if main_fee:
                direct_fee = main_fee.get('direct', '0đ')
                if direct_fee != '0đ':
                    # Extract number from fee string
                    import re
                    fee_match = re.search(r'(\d+(?:\.\d+)*)', direct_fee.replace(',', ''))
                    if fee_match:
                        metadata['fee_vnd'] = int(float(fee_match.group(1).replace('.', '')))
                    metadata['fee_text'] = f"{direct_fee} (theo quy định)"
        elif isinstance(fee_structure, dict):
            # Handle case where fee_structure has direct/online keys
            direct_fee = fee_structure.get('direct', '0đ')
            if direct_fee != '0đ':
                import re
                fee_match = re.search(r'(\d+(?:\.\d+)*)', str(direct_fee).replace(',', ''))
                if fee_match:
                    metadata['fee_vnd'] = int(float(fee_match.group(1).replace('.', '')))
                metadata['fee_text'] = f"{direct_fee} (theo quy định)"

        new_data['metadata'] = metadata

        # Keep fee_structure as is
        if 'fee_structure' in data:
            new_data['fee_structure'] = data['fee_structure']

        # Keep content_chunks as is
        if 'content_chunks' in data:
            new_data['content_chunks'] = data['content_chunks']

        # Add form_logic if missing
        if 'form_logic' not in new_data:
            new_data['form_logic'] = {
                'has_electronic_form': True,
                'electronic_form_description': 'Mẫu điện tử tương tác (được sử dụng khi nộp hồ sơ theo hình thức trực tuyến)',
                'has_paper_form': True,
                'paper_form_description': 'Mẫu giấy theo quy định (được sử dụng khi nộp hồ sơ theo hình thức trực tiếp)'
            }

        # Write back to file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

        print(f"✓ {json_file_path.name} - Converted to standard metadata format")
        return True

    except Exception as e:
        print(f"✗ {json_file_path.name} - Error: {str(e)}")
        return False

def process_collection(collection_path):
    """Process all JSON files in a collection"""
    print(f"\n📁 Processing collection: {collection_path.name}")

    json_files = list(collection_path.rglob('*.json'))
    json_files = [f for f in json_files if not f.name.endswith('questions.json') and not f.name.endswith('metadata.json')]

    success_count = 0
    total_count = len(json_files)

    for json_file in json_files:
        if convert_to_standard_metadata(json_file):
            success_count += 1

    print(f"✅ {collection_path.name}: {success_count}/{total_count} files converted successfully")

    return success_count, total_count

def main():
    collections_path = Path('d:/Personal/LegalRAG_Fixed/backend/data/storage/collections')

    total_success = 0
    total_files = 0

    print("🚀 STARTING METADATA STANDARDIZATION PROCESS")
    print("=" * 60)

    for collection_dir in collections_path.iterdir():
        if collection_dir.is_dir():
            success, total = process_collection(collection_dir)
            total_success += success
            total_files += total

    print("\n" + "=" * 60)
    print("📊 FINAL REPORT")
    print(f"Total files processed: {total_files}")
    print(f"Successfully converted: {total_success}")
    print(f"Success rate: {(total_success/total_files*100):.1f}%" if total_files > 0 else "0%")

if __name__ == "__main__":
    main()
