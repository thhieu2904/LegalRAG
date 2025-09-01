#!/usr/bin/env python3
"""
📊 QUESTIONS VALIDATION SCRIPT
===============================

Script đơn giản để quét và kiểm tra trạng thái câu hỏi trong tất cả collections.
Chỉ kiểm tra, KHÔNG tạo câu hỏi mới.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

def scan_questions_status() -> Tuple[Dict, Dict]:
    """Quét trạng thái câu hỏi trong tất cả collections"""

    base_path = Path("backend/data/storage/collections")

    if not base_path.exists():
        print("❌ Không tìm thấy thư mục collections!")
        return {}, {}

    stats = {
        'total_collections': 0,
        'total_documents': 0,
        'documents_with_questions': 0,
        'documents_with_good_questions': 0,  # >= 50 variants
        'documents_with_basic_questions': 0,  # 7-49 variants
        'documents_missing_questions': 0,
        'documents_empty_questions': 0
    }

    collections = {}

    print("🔍 Đang quét collections...")
    print("=" * 60)

    for collection_dir in sorted(base_path.iterdir()):
        if not collection_dir.is_dir():
            continue

        collection_name = collection_dir.name
        stats['total_collections'] += 1

        collections[collection_name] = {
            'total_docs': 0,
            'with_good_questions': 0,
            'with_basic_questions': 0,
            'missing_questions': 0,
            'empty_questions': 0,
            'details': []
        }

        docs_path = collection_dir / "documents"
        if not docs_path.exists():
            print(f"⚠️  {collection_name}: Không có thư mục documents")
            continue

        print(f"\n📂 {collection_name}:")

        for doc_dir in sorted(docs_path.iterdir()):
            if not doc_dir.is_dir() or not doc_dir.name.startswith('DOC_'):
                continue

            doc_name = doc_dir.name
            collections[collection_name]['total_docs'] += 1
            stats['total_documents'] += 1

            questions_file = doc_dir / "questions.json"

            if not questions_file.exists():
                collections[collection_name]['missing_questions'] += 1
                stats['documents_missing_questions'] += 1
                collections[collection_name]['details'].append(f"❌ {doc_name}: Thiếu file questions.json")
                continue

            try:
                with open(questions_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    collections[collection_name]['empty_questions'] += 1
                    stats['documents_empty_questions'] += 1
                    collections[collection_name]['details'].append(f"📄 {doc_name}: File questions.json rỗng")
                    continue

                data = json.loads(content)
                variants = data.get('question_variants', [])

                if not variants:
                    collections[collection_name]['empty_questions'] += 1
                    stats['documents_empty_questions'] += 1
                    collections[collection_name]['details'].append(f"📄 {doc_name}: Không có question_variants")
                elif len(variants) >= 50:
                    collections[collection_name]['with_good_questions'] += 1
                    stats['documents_with_good_questions'] += 1
                    stats['documents_with_questions'] += 1
                    collections[collection_name]['details'].append(f"✅ {doc_name}: {len(variants)} câu hỏi (tốt)")
                elif len(variants) >= 7:
                    collections[collection_name]['with_basic_questions'] += 1
                    stats['documents_with_questions'] += 1
                    collections[collection_name]['details'].append(f"⚠️  {doc_name}: {len(variants)} câu hỏi (cơ bản)")
                else:
                    collections[collection_name]['with_basic_questions'] += 1
                    stats['documents_with_questions'] += 1
                    collections[collection_name]['details'].append(f"⚠️  {doc_name}: {len(variants)} câu hỏi (quá ít)")

            except json.JSONDecodeError:
                collections[collection_name]['empty_questions'] += 1
                stats['documents_empty_questions'] += 1
                collections[collection_name]['details'].append(f"❌ {doc_name}: JSON không hợp lệ")
            except Exception as e:
                collections[collection_name]['empty_questions'] += 1
                stats['documents_empty_questions'] += 1
                collections[collection_name]['details'].append(f"❌ {doc_name}: Lỗi đọc file - {str(e)}")

        # Hiển thị tóm tắt cho collection
        total = collections[collection_name]['total_docs']
        good = collections[collection_name]['with_good_questions']
        basic = collections[collection_name]['with_basic_questions']
        missing = collections[collection_name]['missing_questions']
        empty = collections[collection_name]['empty_questions']

        if total > 0:
            print(f"   Tổng: {total} văn bản")
            print(f"   ✅ Tốt (>=50 câu): {good}")
            print(f"   ⚠️  Cơ bản (7-49 câu): {basic}")
            print(f"   ❌ Thiếu/rỗng: {missing + empty}")

            # Hiển thị chi tiết nếu có vấn đề
            if missing + empty > 0:
                print("   Chi tiết:")
                for detail in collections[collection_name]['details']:
                    if "❌" in detail or "⚠️" in detail:
                        print(f"      {detail}")

    return stats, collections

def print_summary_report(stats: Dict, collections: Dict):
    """In báo cáo tổng kết"""

    print("\n" + "=" * 60)
    print("📊 BÁO CÁO TỔNG KẾT")
    print("=" * 60)

    print(f"📂 Tổng số collections: {stats['total_collections']}")
    print(f"📄 Tổng số văn bản: {stats['total_documents']}")
    print()

    print("📈 Phân tích câu hỏi:")
    print(f"   ✅ Văn bản có câu hỏi tốt (>=50 câu): {stats['documents_with_good_questions']}")
    print(f"   ⚠️  Văn bản có câu hỏi cơ bản (7-49 câu): {stats['documents_with_basic_questions']}")
    print(f"   ❌ Văn bản thiếu/rỗng câu hỏi: {stats['documents_missing_questions'] + stats['documents_empty_questions']}")
    print()

    # Tính tỷ lệ
    if stats['total_documents'] > 0:
        good_rate = (stats['documents_with_good_questions'] / stats['total_documents']) * 100
        basic_rate = (stats['documents_with_questions'] / stats['total_documents']) * 100

        print(".1f")
        print(".1f")
        print(".1f")
    # Collections cần chú ý
    problematic_collections = []
    for name, data in collections.items():
        if data['missing_questions'] + data['empty_questions'] > 0:
            problematic_collections.append((name, data['missing_questions'] + data['empty_questions']))

    if problematic_collections:
        print("\n⚠️  Collections cần chú ý:")
        for name, issues in sorted(problematic_collections, key=lambda x: x[1], reverse=True):
            print(f"   • {name}: {issues} văn bản có vấn đề")

    print("\n" + "=" * 60)

def main():
    """Main function"""
    print("🔍 KIỂM TRA TRẠNG THÁI CÂU HỎI")
    print("Chỉ kiểm tra, KHÔNG tạo câu hỏi mới")
    print()

    stats, collections = scan_questions_status()
    print_summary_report(stats, collections)

    print("✅ Hoàn thành kiểm tra!")

if __name__ == "__main__":
    main()
