#!/usr/bin/env python3
"""
JSON Validation Script for LegalRAG Documents
Tests if JSON files have complete 6-chunk structure and valid content
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import sys

class JSONValidator:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.results = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'errors': []
        }

    def validate_json_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate a single JSON file"""
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            errors.append(f"JSON parsing error: {str(e)}")
            return False, errors

        # Check metadata
        if 'metadata' not in data:
            errors.append("Missing 'metadata' section")
        else:
            metadata = data['metadata']
            required_metadata_fields = [
                'source', 'title', 'code', 'issuing_authority',
                'effective_date', 'executing_agency', 'applicant_type',
                'processing_time_text', 'fee_vnd', 'fee_text',
                'has_form', 'legal_basis_references'
            ]

            for field in required_metadata_fields:
                if field not in metadata:
                    errors.append(f"Missing metadata field: {field}")
                elif metadata[field] is None or metadata[field] == "":
                    errors.append(f"Empty metadata field: {field}")

        # Check fee_structure
        if 'fee_structure' not in data:
            errors.append("Missing 'fee_structure' section")
        else:
            fee_structure = data['fee_structure']
            if 'base_fee' not in fee_structure:
                errors.append("Missing 'base_fee' in fee_structure")

        # Check form_logic
        if 'form_logic' not in data:
            errors.append("Missing 'form_logic' section")
        else:
            form_logic = data['form_logic']
            if 'has_electronic_form' not in form_logic:
                errors.append("Missing 'has_electronic_form' in form_logic")
            if 'has_paper_form' not in form_logic:
                errors.append("Missing 'has_paper_form' in form_logic")

        # Check content_chunks - most important part
        if 'content_chunks' not in data:
            errors.append("Missing 'content_chunks' section")
        else:
            chunks = data['content_chunks']

            # Check if exactly 6 chunks
            if len(chunks) != 6:
                errors.append(f"Expected 6 content chunks, found {len(chunks)}")

            # Check each chunk
            for i, chunk in enumerate(chunks):
                chunk_num = i + 1

                # Check required fields
                required_chunk_fields = [
                    'chunk_id', 'section_title', 'content',
                    'source_reference', 'keywords'
                ]

                for field in required_chunk_fields:
                    if field not in chunk:
                        errors.append(f"Chunk {chunk_num}: Missing field '{field}'")
                    elif chunk[field] is None or chunk[field] == "":
                        errors.append(f"Chunk {chunk_num}: Empty field '{field}'")
                    elif field == 'content' and len(str(chunk[field]).strip()) < 10:
                        errors.append(f"Chunk {chunk_num}: Content too short (< 10 chars)")
                    elif field == 'keywords' and not isinstance(chunk[field], list):
                        errors.append(f"Chunk {chunk_num}: Keywords should be a list")
                    elif field == 'keywords' and len(chunk[field]) < 3:
                        errors.append(f"Chunk {chunk_num}: Too few keywords (< 3)")

                # Check chunk_id is correct
                if 'chunk_id' in chunk and chunk['chunk_id'] != chunk_num:
                    errors.append(f"Chunk {chunk_num}: chunk_id should be {chunk_num}, found {chunk['chunk_id']}")

        return len(errors) == 0, errors

    def scan_collections(self) -> Dict[str, Dict]:
        """Scan all collections and validate JSON files"""
        collections_path = self.base_path / "backend" / "data" / "storage" / "collections"

        if not collections_path.exists():
            print(f"Collections path not found: {collections_path}")
            return {}

        collection_results = {}

        for collection_dir in collections_path.iterdir():
            if not collection_dir.is_dir():
                continue

            collection_name = collection_dir.name
            print(f"\n🔍 Scanning collection: {collection_name}")

            documents_path = collection_dir / "documents"
            if not documents_path.exists():
                print(f"  No documents folder in {collection_name}")
                continue

            collection_results[collection_name] = {
                'total_files': 0,
                'valid_files': 0,
                'invalid_files': 0,
                'files': {}
            }

            # Scan all DOC_xxx folders
            for doc_dir in sorted(documents_path.iterdir()):
                if not doc_dir.is_dir() or not doc_dir.name.startswith('DOC_'):
                    continue

                # Find JSON files in this DOC folder
                json_files = list(doc_dir.glob('*.json'))
                json_files = [f for f in json_files if not f.name.endswith('.backup_final') and not f.name.endswith('.backup_simple')]

                for json_file in json_files:
                    collection_results[collection_name]['total_files'] += 1
                    self.results['total_files'] += 1

                    file_key = f"{doc_dir.name}/{json_file.name}"
                    is_valid, errors = self.validate_json_file(json_file)

                    collection_results[collection_name]['files'][file_key] = {
                        'valid': is_valid,
                        'errors': errors
                    }

                    if is_valid:
                        collection_results[collection_name]['valid_files'] += 1
                        self.results['valid_files'] += 1
                    else:
                        collection_results[collection_name]['invalid_files'] += 1
                        self.results['invalid_files'] += 1
                        self.results['errors'].extend([f"{file_key}: {error}" for error in errors])

        return collection_results

    def generate_report(self, collection_results: Dict[str, Dict]) -> str:
        """Generate a comprehensive report"""
        report = []
        report.append("=" * 80)
        report.append("LEGALRAG JSON VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated on: {os.popen('date').read().strip()}")
        report.append("")

        # Overall summary
        report.append("📊 OVERALL SUMMARY:")
        report.append(f"Total files scanned: {self.results['total_files']}")
        report.append(f"Valid files: {self.results['valid_files']}")
        report.append(f"Invalid files: {self.results['invalid_files']}")

        if self.results['total_files'] > 0:
            overall_rate = (self.results['valid_files'] / self.results['total_files']) * 100
            report.append(f"Overall validity rate: {overall_rate:.1f}%")
        else:
            report.append("Overall validity rate: N/A (no files found)")

        report.append("")

        # Collection breakdown
        report.append("📁 COLLECTION BREAKDOWN:")
        for collection_name, data in collection_results.items():
            if data['total_files'] > 0:
                validity_rate = (data['valid_files'] / data['total_files']) * 100
                report.append(f"  {collection_name}:")
                report.append(f"    Total: {data['total_files']}")
                report.append(f"    Valid: {data['valid_files']}")
                report.append(f"    Invalid: {data['invalid_files']}")
                report.append(f"    Validity rate: {validity_rate:.1f}%")
                report.append("")

        # Detailed errors
        if self.results['errors']:
            report.append("❌ DETAILED ERRORS:")
            for error in self.results['errors'][:50]:  # Show first 50 errors
                report.append(f"  • {error}")

            if len(self.results['errors']) > 50:
                report.append(f"  ... and {len(self.results['errors']) - 50} more errors")
            report.append("")

        # Files with issues
        invalid_files = []
        for collection_name, data in collection_results.items():
            for file_key, file_data in data['files'].items():
                if not file_data['valid']:
                    invalid_files.append(f"{collection_name}/{file_key}")

        if invalid_files:
            report.append("📋 FILES WITH ISSUES:")
            for file in invalid_files:
                report.append(f"  • {file}")
            report.append("")

        # Recommendations
        report.append("💡 RECOMMENDATIONS:")
        if self.results['invalid_files'] > 0:
            report.append("  • Review and fix the invalid files listed above")
            report.append("  • Ensure all JSON files have exactly 6 content chunks")
            report.append("  • Verify all required fields are present and not empty")
            report.append("  • Check that keywords are meaningful and relevant")
        else:
            report.append("  • All files are valid! Great job! 🎉")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

def main():
    """Main function"""
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir

    # If script is in a subdirectory, go up to find the project root
    if script_dir.name in ['scripts', 'tools', 'utils']:
        project_root = script_dir.parent

    print("🚀 Starting JSON validation...")
    print(f"Project root: {project_root}")

    validator = JSONValidator(str(project_root))
    collection_results = validator.scan_collections()

    report = validator.generate_report(collection_results)

    # Save report to file
    report_file = project_root / "json_validation_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print("\n" + report)
    print(f"\n📄 Report saved to: {report_file}")

    # Exit with error code if there are invalid files
    if validator.results['invalid_files'] > 0:
        print(f"\n❌ Found {validator.results['invalid_files']} invalid files")
        sys.exit(1)
    else:
        print("\n✅ All files are valid!")
        sys.exit(0)

if __name__ == "__main__":
    main()
