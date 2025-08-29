#!/usr/bin/env python3
"""
Script to classify collections by JSON structure type
"""

import os
import json
from pathlib import Path

def classify_json_structure(json_file_path):
    """Classify JSON structure type"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check for metadata section
        if "metadata" in data:
            return "full_metadata"  # Like quy_trinh_cong_chung

        # Check for basic structure with fee_structure
        elif "fee_structure" in data and "content_chunks" in data:
            return "basic_with_fee"  # Like quy_trinh_thua_phat_lai

        # Check for simple structure
        elif "content_chunks" in data and "title" in data:
            return "simple_structure"  # Like quy_trinh_cap_ho_tich_cap_xa

        else:
            return "unknown"

    except Exception as e:
        return f"error: {str(e)}"

def analyze_collection(collection_path):
    """Analyze a single collection"""
    collection_name = Path(collection_path).name
    documents_path = Path(collection_path) / "documents"

    if not documents_path.exists():
        return {
            "collection": collection_name,
            "status": "No documents folder",
            "structure_types": {},
            "sample_files": []
        }

    structure_counts = {}
    sample_files = {}
    total_files = 0

    # Analyze first JSON file from each DOC folder
    for doc_folder in sorted(documents_path.glob("DOC_*")):
        if doc_folder.is_dir():
            json_files = list(doc_folder.glob("*.json"))
            # Skip backup files
            json_files = [f for f in json_files if not f.name.endswith(".backup_simple") and not f.name.endswith(".backup_final")]

            if json_files:
                json_file = json_files[0]  # Take first JSON file
                structure_type = classify_json_structure(json_file)
                total_files += 1

                if structure_type not in structure_counts:
                    structure_counts[structure_type] = 0
                    sample_files[structure_type] = json_file.name

                structure_counts[structure_type] += 1

    return {
        "collection": collection_name,
        "status": "analyzed",
        "total_files": total_files,
        "structure_types": structure_counts,
        "sample_files": sample_files
    }

def main():
    """Main analysis function"""
    collections_base = Path("d:/Personal/LegalRAG_Fixed/backend/data/storage/collections")

    if not collections_base.exists():
        print("Collections path not found")
        return

    print("🔍 CLASSIFYING COLLECTIONS BY JSON STRUCTURE")
    print("=" * 60)

    all_results = []

    # Skip quy_trinh_cong_chung as we know it's the reference
    collections_to_analyze = [
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

    # Classify all collections
    for collection_name in collections_to_analyze:
        collection_path = collections_base / collection_name
        if collection_path.exists():
            result = analyze_collection(collection_path)
            all_results.append(result)

            print(f"\n📁 {result['collection']}")
            print(f"   Files analyzed: {result['total_files']}")

            for structure_type, count in result['structure_types'].items():
                sample = result['sample_files'].get(structure_type, 'N/A')
                print(f"   {structure_type}: {count} files (sample: {sample})")

    # Generate summary
    print("\n" + "=" * 60)
    print("📊 CLASSIFICATION SUMMARY")
    print("=" * 60)

    structure_summary = {}
    for result in all_results:
        for structure_type, count in result['structure_types'].items():
            if structure_type not in structure_summary:
                structure_summary[structure_type] = []
            structure_summary[structure_type].append({
                "collection": result['collection'],
                "count": count
            })

    print("\n🔧 COLLECTIONS NEEDING FIXES:")
    print("-" * 40)

    needs_fixing = []
    for structure_type, collections in structure_summary.items():
        if structure_type != "full_metadata":
            print(f"\n{structure_type.upper()}:")
            for item in collections:
                print(f"   - {item['collection']}: {item['count']} files")
                needs_fixing.append(item['collection'])

    print("\n✅ COLLECTIONS ALREADY GOOD:")
    print("-" * 40)

    already_good = []
    if "full_metadata" in structure_summary:
        for item in structure_summary["full_metadata"]:
            print(f"   - {item['collection']}: {item['count']} files")
            already_good.append(item['collection'])

    print("\n📋 ACTION PLAN:")
    print("-" * 40)
    print(f"Collections to fix: {len(needs_fixing)}")
    print(f"Collections already good: {len(already_good)}")
    print(f"Total collections: {len(collections_to_analyze)}")

    if needs_fixing:
        print("\n⚠️  Need to standardize to 'full_metadata' format:")
        for collection in needs_fixing:
            print(f"   - {collection}")

    # Save detailed results
    report_file = collections_base / "structure_classification_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    main()
