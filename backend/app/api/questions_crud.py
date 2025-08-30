"""
Questions CRUD API - Đơn giản để quản lý questions
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

router = APIRouter(prefix="/questions", tags=["Questions CRUD"])

class QuestionData(BaseModel):
    main_question: str
    question_variants: List[str]

@router.get("/stats")
async def get_questions_stats():
    """Thống kê questions"""
    try:
        base_path = Path("backend/data/storage/collections")
        stats = {
            'total_docs': 0,
            'with_good_questions': 0,
            'with_basic_questions': 0,
            'collections': {}
        }

        for collection_dir in base_path.iterdir():
            if not collection_dir.is_dir():
                continue

            collection_name = collection_dir.name
            stats['collections'][collection_name] = {'total': 0, 'good': 0, 'basic': 0}

            docs_path = collection_dir / "documents"
            if not docs_path.exists():
                continue

            for doc_dir in docs_path.iterdir():
                if not doc_dir.is_dir() or not doc_dir.name.startswith('DOC_'):
                    continue

                stats['total_docs'] += 1
                stats['collections'][collection_name]['total'] += 1

                questions_file = doc_dir / "questions.json"
                if questions_file.exists():
                    try:
                        with open(questions_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        variants = data.get('question_variants', [])
                        if len(variants) > 5:
                            stats['with_good_questions'] += 1
                            stats['collections'][collection_name]['good'] += 1
                        else:
                            stats['with_basic_questions'] += 1
                            stats['collections'][collection_name]['basic'] += 1
                    except:
                        pass

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {e}")

@router.get("/collections")
async def get_collections():
    """List collections"""
    try:
        base_path = Path("backend/data/storage/collections")
        collections = []

        for collection_dir in base_path.iterdir():
            if not collection_dir.is_dir():
                continue

            collection_name = collection_dir.name
            docs_path = collection_dir / "documents"

            doc_count = 0
            if docs_path.exists():
                doc_count = len([d for d in docs_path.iterdir() if d.is_dir() and d.name.startswith('DOC_')])

            collections.append({
                "name": collection_name,
                "display_name": collection_name.replace("_", " ").title(),
                "document_count": doc_count
            })

        return {"collections": collections}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collections: {e}")

@router.get("/collections/{collection_name}/documents")
async def get_documents(collection_name: str):
    """List documents in collection"""
    try:
        docs_path = Path(f"backend/data/storage/collections/{collection_name}/documents")
        documents = []

        if not docs_path.exists():
            return {"documents": []}

        for doc_dir in docs_path.iterdir():
            if not doc_dir.is_dir() or not doc_dir.name.startswith('DOC_'):
                continue

            questions_file = doc_dir / "questions.json"
            has_questions = questions_file.exists()

            question_count = 0
            main_question = ""

            if has_questions:
                try:
                    with open(questions_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    main_question = data.get('main_question', '')
                    variants = data.get('question_variants', [])
                    question_count = 1 + len(variants)
                except:
                    pass

            documents.append({
                "name": doc_dir.name,
                "main_question": main_question[:50] + "..." if len(main_question) > 50 else main_question,
                "question_count": question_count,
                "has_questions": has_questions
            })

        return {"documents": documents}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting documents: {e}")

@router.get("/collections/{collection_name}/documents/{document_name}")
async def get_questions(collection_name: str, document_name: str):
    """Get questions for document"""
    try:
        questions_file = Path(f"backend/data/storage/collections/{collection_name}/documents/{document_name}/questions.json")

        if not questions_file.exists():
            return {"main_question": "", "question_variants": []}

        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "main_question": data.get('main_question', ''),
            "question_variants": data.get('question_variants', [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting questions: {e}")

@router.put("/collections/{collection_name}/documents/{document_name}")
async def update_questions(
    collection_name: str,
    document_name: str,
    question_data: QuestionData
):
    """Update questions"""
    try:
        questions_file = Path(f"backend/data/storage/collections/{collection_name}/documents/{document_name}/questions.json")

        questions_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "main_question": question_data.main_question,
            "question_variants": question_data.question_variants
        }

        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {"message": "Updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating: {e}")

@router.post("/collections/{collection_name}/documents/{document_name}/enrich")
async def enrich_questions(
    collection_name: str,
    document_name: str,
    additional_variants: List[str] = Body(...)
):
    """Add more variants"""
    try:
        questions_file = Path(f"backend/data/storage/collections/{collection_name}/documents/{document_name}/questions.json")

        if not questions_file.exists():
            raise HTTPException(status_code=404, detail="Questions file not found")

        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        existing_variants = data.get('question_variants', [])

        # Add new variants (avoid duplicates)
        for variant in additional_variants:
            if variant.strip() and variant not in existing_variants:
                existing_variants.append(variant.strip())

        data['question_variants'] = existing_variants

        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {
            "message": f"Added {len(additional_variants)} variants",
            "total_variants": len(existing_variants)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enriching: {e}")

@router.delete("/collections/{collection_name}/documents/{document_name}/variants")
async def delete_variants(
    collection_name: str,
    document_name: str,
    variants_to_delete: List[str] = Body(...)
):
    """Delete variants"""
    try:
        questions_file = Path(f"backend/data/storage/collections/{collection_name}/documents/{document_name}/questions.json")

        if not questions_file.exists():
            raise HTTPException(status_code=404, detail="Questions file not found")

        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        existing_variants = data.get('question_variants', [])
        updated_variants = [v for v in existing_variants if v not in variants_to_delete]

        data['question_variants'] = updated_variants

        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {
            "message": f"Deleted {len(variants_to_delete)} variants",
            "remaining_variants": len(updated_variants)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting: {e}")
