#!/usr/bin/env python3
"""
Script to scan all collections and report missing files
"""

import os
import json
from pathlib import Path

def scan_collection_documents(collection_path):
    """Scan documents in a collection and return statistics"""
    collection_name = Path(collection_path).name
    documents_path = Path(collection_path) / "documents"

    if not documents_path.exists():
        return {
            "collection": collection_name,
            "status": "No documents folder",
            "doc_count": 0,
            "details": []
        }

    doc_folders = list(documents_path.glob("DOC_*"))
    doc_count = len(doc_folders)

    if doc_count == 0:
        return {
            "collection": collection_name,
            "status": "Empty documents folder",
            "doc_count": 0,
            "details": []
        }

    details = []
    total_json_files = 0
    total_doc_files = 0
    total_questions_files = 0
    total_forms_folders = 0

    for doc_folder in sorted(doc_folders):
        if doc_folder.is_dir():
            files = list(doc_folder.glob("*"))
            json_files = [f for f in files if f.suffix == ".json" and not f.name.endswith(".backup_simple") and not f.name.endswith(".backup_final")]
            doc_files = [f for f in files if f.suffix == ".doc"]
            questions_files = [f for f in files if f.name == "questions.json"]
            forms_folders = [f for f in files if f.is_dir() and f.name == "forms"]

            total_json_files += len(json_files)
            total_doc_files += len(doc_files)
            total_questions_files += len(questions_files)
            total_forms_folders += len(forms_folders)

            # Check for missing files
            missing = []
            if len(json_files) == 0:
                missing.append("JSON file")
            if len(doc_files) == 0:
                missing.append("DOC file")
            if len(questions_files) == 0:
                missing.append("questions.json")
            if len(forms_folders) == 0:
                missing.append("forms/ folder")

            if missing:
                details.append({
                    "doc_id": doc_folder.name,
                    "missing": missing
                })

    status = "Complete" if not details else f"Missing files in {len(details)} documents"

    return {
        "collection": collection_name,
        "status": status,
        "doc_count": doc_count,
        "total_json_files": total_json_files,
        "total_doc_files": total_doc_files,
        "total_questions_files": total_questions_files,
        "total_forms_folders": total_forms_folders,
        "details": details
    }

def generate_report():
    """Generate comprehensive report of all collections"""
    collections_base = Path("d:/Personal/LegalRAG_Fixed/backend/data/storage/collections")

    if not collections_base.exists():
        print(f"Collections path not found: {collections_base}")
        return

    print("🔍 SCANNING ALL COLLECTIONS FOR MISSING FILES")
    print("=" * 60)

    all_collections = []
    total_collections = 0
    collections_with_issues = 0
    total_documents = 0

    # Scan all collections
    for collection_path in sorted(collections_base.iterdir()):
        if collection_path.is_dir():
            total_collections += 1
            result = scan_collection_documents(collection_path)
            all_collections.append(result)

            total_documents += result["doc_count"]

            if result["details"]:
                collections_with_issues += 1

            # Print summary for this collection
            print(f"\n📁 {result['collection']}")
            print(f"   Status: {result['status']}")
            print(f"   Documents: {result['doc_count']}")

            if "total_json_files" in result:
                print(f"   JSON files: {result['total_json_files']}")
                print(f"   DOC files: {result['total_doc_files']}")
                print(f"   Questions files: {result['total_questions_files']}")
                print(f"   Forms folders: {result['total_forms_folders']}")

            if result["details"]:
                print("   ⚠️  Missing files in:")
                for detail in result["details"]:
                    print(f"      {detail['doc_id']}: {', '.join(detail['missing'])}")

    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 SUMMARY REPORT")
    print("=" * 60)
    print(f"Total Collections: {total_collections}")
    print(f"Collections with Issues: {collections_with_issues}")
    print(f"Total Documents: {total_documents}")

    if collections_with_issues > 0:
        print(f"\n⚠️  Collections needing attention:")
        for collection in all_collections:
            if collection["details"]:
                print(f"   - {collection['collection']}: {len(collection['details'])} documents with missing files")
    else:
        print("\n✅ All collections appear to be complete!")

    # Save detailed report to file
    report_file = collections_base / "collection_scan_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(all_collections, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    generate_report()
