#!/usr/bin/env python3
"""
🔍 ULTIMATE STORAGE SYSTEM ANALYZER
==================================

Script phân tích ULTIMATE với validation tuyệt đối
- Logging chi tiết từng bước
- Validation từng collection
- Error handling toàn diện
- Double-check tất cả kết quả
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('storage_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateStorageAnalyzer:
    """Ultimate analyzer with absolute accuracy"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.storage_path = self.base_path / "backend" / "data" / "storage" / "collections"

        # Validation counters
        self.validation_checks = {
            'collections_found': 0,
            'collections_validated': 0,
            'doc_folders_found': 0,
            'word_files_found': 0,
            'json_files_found': 0,
            'forms_word_found': 0,
            'mapping_errors': 0
        }

        logger.info("🚀 ULTIMATE STORAGE ANALYZER INITIALIZED")
        logger.info(f"📁 Storage path: {self.storage_path}")

    def validate_storage_exists(self) -> bool:
        """Validate storage directory exists"""
        if not self.storage_path.exists():
            logger.error(f"❌ Storage path does not exist: {self.storage_path}")
            return False

        if not self.storage_path.is_dir():
            logger.error(f"❌ Storage path is not a directory: {self.storage_path}")
            return False

        logger.info("✅ Storage directory validated")
        return True

    def discover_collections(self) -> List[str]:
        """Discover all collections with validation"""
        logger.info("🔍 Discovering collections...")

        collections = []
        try:
            for item in self.storage_path.iterdir():
                if item.is_dir():
                    # Double-check it's a valid collection
                    metadata_file = item / "metadata.json"
                    documents_dir = item / "documents"

                    if metadata_file.exists() and documents_dir.exists():
                        collections.append(item.name)
                        logger.info(f"✅ Valid collection found: {item.name}")
                    else:
                        logger.warning(f"⚠️  Invalid collection structure: {item.name}")
                        if not metadata_file.exists():
                            logger.warning(f"   - Missing metadata.json")
                        if not documents_dir.exists():
                            logger.warning(f"   - Missing documents/ directory")

            collections.sort()  # Sort for consistency
            self.validation_checks['collections_found'] = len(collections)
            logger.info(f"📊 Found {len(collections)} valid collections")

        except Exception as e:
            logger.error(f"❌ Error discovering collections: {e}")
            return []

        return collections

    def analyze_collection(self, collection_name: str) -> Dict:
        """Analyze single collection with detailed validation"""
        logger.info(f"🔬 Analyzing collection: {collection_name}")

        collection_path = self.storage_path / collection_name
        documents_path = collection_path / "documents"

        result = {
            'name': collection_name,
            'doc_folders': 0,
            'word_files': 0,
            'json_files': 0,
            'forms_word_files': 0,
            'mapping_status': 'UNKNOWN',
            'errors': [],
            'details': []
        }

        try:
            # Validate documents directory
            if not documents_path.exists():
                result['errors'].append("Documents directory missing")
                return result

            # Scan DOC_xxx folders
            doc_folders = []
            for item in documents_path.iterdir():
                if item.is_dir() and item.name.startswith('DOC_'):
                    doc_folders.append(item)
                    self.validation_checks['doc_folders_found'] += 1

            result['doc_folders'] = len(doc_folders)
            logger.info(f"   📁 Found {len(doc_folders)} DOC folders")

            # Analyze each DOC folder
            for doc_folder in sorted(doc_folders):
                doc_analysis = self.analyze_doc_folder(doc_folder)
                result['word_files'] += doc_analysis['word_files']
                result['json_files'] += doc_analysis['json_files']
                result['forms_word_files'] += doc_analysis['forms_word_files']
                result['details'].append(doc_analysis)

                if doc_analysis['errors']:
                    result['errors'].extend(doc_analysis['errors'])

            # Determine mapping status
            if result['word_files'] == result['json_files']:
                result['mapping_status'] = 'PERFECT'
            else:
                result['mapping_status'] = 'MISMATCH'
                self.validation_checks['mapping_errors'] += 1

            logger.info(f"   ✅ {collection_name}: {result['doc_folders']} DOC, {result['word_files']} Word, {result['json_files']} JSON")

        except Exception as e:
            logger.error(f"❌ Error analyzing collection {collection_name}: {e}")
            result['errors'].append(str(e))

        return result

    def analyze_doc_folder(self, doc_folder: Path) -> Dict:
        """Analyze single DOC folder"""
        result = {
            'folder_name': doc_folder.name,
            'word_files': 0,
            'json_files': 0,
            'forms_word_files': 0,
            'errors': []
        }

        try:
            # Count files in main directory (exclude forms/)
            main_word_files = []
            main_json_files = []

            for file_path in doc_folder.iterdir():
                if file_path.is_file():
                    if file_path.name.endswith(('.doc', '.docx')):
                        main_word_files.append(file_path.name)
                        self.validation_checks['word_files_found'] += 1
                    elif file_path.name.endswith('.json') and not file_path.name.endswith('questions.json'):
                        main_json_files.append(file_path.name)
                        self.validation_checks['json_files_found'] += 1

            result['word_files'] = len(main_word_files)
            result['json_files'] = len(main_json_files)

            # Count files in forms/ directory
            forms_dir = doc_folder / "forms"
            if forms_dir.exists():
                forms_word_files = []
                for file_path in forms_dir.rglob("*"):
                    if file_path.is_file() and file_path.name.endswith(('.doc', '.docx')):
                        forms_word_files.append(file_path.name)
                        self.validation_checks['forms_word_found'] += 1

                result['forms_word_files'] = len(forms_word_files)

            # Validation
            if len(main_word_files) != len(main_json_files):
                result['errors'].append(f"Word-JSON mismatch: {len(main_word_files)} vs {len(main_json_files)}")

            if len(main_word_files) > 1:
                result['errors'].append(f"Multiple Word files in main directory: {main_word_files}")

            if len(main_json_files) > 1:
                result['errors'].append(f"Multiple JSON files in main directory: {main_json_files}")

        except Exception as e:
            result['errors'].append(f"Analysis error: {str(e)}")

        return result

    def run_complete_analysis(self) -> Dict:
        """Run complete analysis with validation"""
        logger.info("🎯 STARTING COMPLETE ANALYSIS")
        start_time = datetime.now()

        # Step 1: Validate storage
        if not self.validate_storage_exists():
            return {'error': 'Storage validation failed'}

        # Step 2: Discover collections
        collections = self.discover_collections()
        if not collections:
            return {'error': 'No collections found'}

        # Step 3: Analyze each collection
        collection_results = []
        for collection_name in collections:
            result = self.analyze_collection(collection_name)
            collection_results.append(result)
            self.validation_checks['collections_validated'] += 1

        # Step 4: Generate summary
        summary = self.generate_summary(collection_results)

        # Step 5: Final validation
        validation_result = self.final_validation(summary)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"🎉 ANALYSIS COMPLETE in {duration:.2f} seconds")

        return {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'summary': summary,
            'collections': collection_results,
            'validation': validation_result,
            'checks': self.validation_checks
        }

    def generate_summary(self, collection_results: List[Dict]) -> Dict:
        """Generate comprehensive summary"""
        summary = {
            'total_collections': len(collection_results),
            'total_doc_folders': sum(r['doc_folders'] for r in collection_results),
            'total_word_files': sum(r['word_files'] for r in collection_results),
            'total_json_files': sum(r['json_files'] for r in collection_results),
            'total_forms_word_files': sum(r['forms_word_files'] for r in collection_results),
            'perfect_collections': sum(1 for r in collection_results if r['mapping_status'] == 'PERFECT'),
            'problematic_collections': sum(1 for r in collection_results if r['mapping_status'] != 'PERFECT'),
            'total_errors': sum(len(r['errors']) for r in collection_results)
        }

        return summary

    def final_validation(self, summary: Dict) -> Dict:
        """Final validation of results"""
        validation = {
            'status': 'PASSED',
            'checks': [],
            'warnings': [],
            'errors': []
        }

        # Check 1: Word-JSON mapping
        if summary['total_word_files'] == summary['total_json_files']:
            validation['checks'].append("✅ Word-JSON mapping perfect")
        else:
            validation['status'] = 'FAILED'
            validation['errors'].append(f"❌ Word-JSON mismatch: {summary['total_word_files']} vs {summary['total_json_files']}")

        # Check 2: All collections perfect
        if summary['problematic_collections'] == 0:
            validation['checks'].append("✅ All collections have perfect mapping")
        else:
            validation['warnings'].append(f"⚠️  {summary['problematic_collections']} collections have issues")

        # Check 3: No errors
        if summary['total_errors'] == 0:
            validation['checks'].append("✅ No analysis errors")
        else:
            validation['warnings'].append(f"⚠️  {summary['total_errors']} analysis errors found")

        # Check 4: Reasonable numbers
        if summary['total_collections'] >= 10 and summary['total_doc_folders'] >= 100:
            validation['checks'].append("✅ Reasonable collection and document counts")
        else:
            validation['warnings'].append("⚠️  Unusual collection/document counts")

        logger.info(f"🔍 Final validation: {validation['status']}")

        return validation

    def print_results(self, results: Dict):
        """Print formatted results"""
        print("\n" + "="*80)
        print("🎯 ULTIMATE STORAGE ANALYSIS RESULTS")
        print("="*80)

        if 'error' in results:
            print(f"❌ ERROR: {results['error']}")
            return

        summary = results['summary']
        validation = results['validation']

        # Summary section
        print("📊 SUMMARY:")
        print(f"   📚 Collections: {summary['total_collections']}")
        print(f"   📁 DOC Folders: {summary['total_doc_folders']}")
        print(f"   📄 Word Files: {summary['total_word_files']}")
        print(f"   📋 JSON Files: {summary['total_json_files']}")
        print(f"   📝 Forms Word: {summary['total_forms_word_files']}")
        print()

        # Validation section
        print("🔍 VALIDATION:")
        for check in validation['checks']:
            print(f"   {check}")
        for warning in validation['warnings']:
            print(f"   {warning}")
        for error in validation['errors']:
            print(f"   {error}")
        print()

        # Collections section
        print("📋 COLLECTIONS DETAIL:")
        print("-" * 80)

        for collection in results['collections']:
            status_icon = "✅" if collection['mapping_status'] == 'PERFECT' else "❌"
            print(f"{status_icon} {collection['name']}")
            print(f"   📁 DOC: {collection['doc_folders']}")
            print(f"   📄 Word: {collection['word_files']}")
            print(f"   📋 JSON: {collection['json_files']}")
            print(f"   📝 Forms: {collection['forms_word_files']}")

            if collection['errors']:
                print(f"   ⚠️  Errors: {len(collection['errors'])}")
                for error in collection['errors'][:3]:  # Show first 3 errors
                    print(f"      - {error}")
            else:
                print("   ✅ No errors")
            print()

        # Final status
        if validation['status'] == 'PASSED':
            print("🎉 ALL CHECKS PASSED - SYSTEM IS PERFECT!")
        else:
            print("⚠️  SOME ISSUES FOUND - REVIEW ABOVE")

        print(f"\n⏱️  Analysis completed in {results['duration_seconds']:.2f} seconds")
        print(f"📅 Timestamp: {results['timestamp']}")

def main():
    """Main function"""
    analyzer = UltimateStorageAnalyzer()

    try:
        results = analyzer.run_complete_analysis()
        analyzer.print_results(results)

        # Save results to file
        with open('storage_analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info("💾 Results saved to storage_analysis_results.json")

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        print(f"\n❌ ANALYSIS FAILED: {e}")

if __name__ == "__main__":
    main()
