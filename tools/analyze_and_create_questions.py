#!/usr/bin/env python3
"""
Script để kiểm tra và tạo questions cho documents chưa có
"""

import json
import os
from pathlib import Path

def analyze_questions_status():
    """Phân tích trạng thái questions trong collections"""

    base_path = Path("backend/data/storage/collections")
    stats = {
        'total_docs': 0,
        'with_questions': 0,
        'with_good_questions': 0,  # > 5 variants
        'empty_questions': 0,
        'missing_questions': 0
    }

    collections = {}

    for collection_dir in base_path.iterdir():
        if not collection_dir.is_dir():
            continue

        collection_name = collection_dir.name
        collections[collection_name] = {
            'total': 0,
            'with_questions': 0,
            'missing': []
        }

        docs_path = collection_dir / "documents"
        if not docs_path.exists():
            continue

        for doc_dir in docs_path.iterdir():
            if not doc_dir.is_dir() or not doc_dir.name.startswith('DOC_'):
                continue

            stats['total_docs'] += 1
            collections[collection_name]['total'] += 1

            questions_file = doc_dir / "questions.json"

            if not questions_file.exists():
                stats['missing_questions'] += 1
                collections[collection_name]['missing'].append(doc_dir.name)
                continue

            try:
                with open(questions_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    stats['empty_questions'] += 1
                    collections[collection_name]['missing'].append(doc_dir.name)
                    continue

                data = json.loads(content)
                variants = data.get('question_variants', [])

                if variants and len(variants) > 5:
                    stats['with_good_questions'] += 1
                else:
                    stats['with_questions'] += 1

                collections[collection_name]['with_questions'] += 1

            except json.JSONDecodeError:
                stats['empty_questions'] += 1
                collections[collection_name]['missing'].append(doc_dir.name)
            except Exception as e:
                print(f"Error reading {questions_file}: {e}")
                stats['empty_questions'] += 1
                collections[collection_name]['missing'].append(doc_dir.name)

    return stats, collections

def generate_basic_questions(doc_name, collection_name):
    """Tạo questions cơ bản dựa trên tên document"""

    # Mapping document names to procedures
    procedure_mapping = {
        'khai_sinh': 'đăng ký khai sinh',
        'ket_hon': 'đăng ký kết hôn',
        'ly_hon': 'đăng ký ly hôn',
        'nhan_con_nuoi': 'nhận con nuôi',
        'chứng_thực': 'chứng thực',
        'ho_tich': 'hộ tịch'
    }

    # Extract procedure type from collection/doc name
    procedure = ""
    for key, value in procedure_mapping.items():
        if key in collection_name.lower() or key in doc_name.lower():
            procedure = value
            break

    if not procedure:
        procedure = collection_name.replace('_', ' ')

    # Generate basic questions
    main_question = f"Thủ tục {procedure} được thực hiện như thế nào?"

    variants = [
        f"Tôi muốn {procedure} cần chuẩn bị gì?",
        f"Hồ sơ {procedure} gồm những gì?",
        f"{procedure} mất bao lâu?",
        f"Phí {procedure} là bao nhiêu?",
        f"Tôi cần nộp hồ sơ {procedure} ở đâu?",
        f"Điều kiện để {procedure} là gì?",
        f"Quy trình {procedure} gồm những bước nào?"
    ]

    return {
        "main_question": main_question,
        "question_variants": variants
    }

def create_missing_questions():
    """Tạo questions cho documents thiếu"""

    base_path = Path("backend/data/storage/collections")
    created_count = 0

    for collection_dir in base_path.iterdir():
        if not collection_dir.is_dir():
            continue

        collection_name = collection_dir.name
        docs_path = collection_dir / "documents"

        if not docs_path.exists():
            continue

        for doc_dir in docs_path.iterdir():
            if not doc_dir.is_dir() or not doc_dir.name.startswith('DOC_'):
                continue

            questions_file = doc_dir / "questions.json"

            # Skip if already exists and has content
            if questions_file.exists():
                try:
                    with open(questions_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if data.get('question_variants') and len(data['question_variants']) > 3:
                        continue  # Already has good questions
                except:
                    pass  # Will recreate

            # Generate and save questions
            questions_data = generate_basic_questions(doc_dir.name, collection_name)

            # Ensure directory exists
            questions_file.parent.mkdir(parents=True, exist_ok=True)

            with open(questions_file, 'w', encoding='utf-8') as f:
                json.dump(questions_data, f, ensure_ascii=False, indent=2)

            created_count += 1
            print(f"✅ Created questions for {collection_name}/{doc_dir.name}")

    return created_count

if __name__ == "__main__":
    print("🔍 Analyzing questions status...")

    stats, collections = analyze_questions_status()

    print("\n📊 STATS:")
    print(f"Total documents: {stats['total_docs']}")
    print(f"With good questions (>5 variants): {stats['with_good_questions']}")
    print(f"With basic questions: {stats['with_questions']}")
    print(f"Empty/missing: {stats['empty_questions'] + stats['missing_questions']}")

    print("\n📂 COLLECTIONS:")
    for name, data in collections.items():
        missing = len(data['missing'])
        if missing > 0:
            print(f"{name}: {data['total']} docs, {missing} missing questions")

    print("\n🚀 Creating missing questions...")
    created = create_missing_questions()
    print(f"✅ Created {created} question files")

    print("\n✨ Done! Now you have questions for all documents.")
    print("Next: Use the CRUD API to enrich them further.")
