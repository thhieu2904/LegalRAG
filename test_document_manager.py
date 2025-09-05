"""
Test script để kiểm tra document manager trực tiếp
"""
import sys
sys.path.append(r"d:\Personal\LegalRAG_OCR\rag_service")

from app.services.document_manager import DocumentManagerService
from app.core.config import settings

def test_document_manager():
    print(f"Base dir: {settings.base_dir}")
    print(f"Storage dir: {settings.storage_dir}")
    
    doc_manager = DocumentManagerService()
    print(f"Storage root: {doc_manager.storage_root}")
    
    # Test list documents
    result = doc_manager.list_documents()
    print(f"Collections found: {len(result['collections'])}")
    for coll in result['collections']:
        print(f"  - {coll['collection_id']}: {coll['document_count']} documents")
    
    # Test specific document
    collection_id = "quy_trinh_cap_ho_tich_cap_xa"
    document_id = "DOC_001"
    
    doc_info = doc_manager.get_document_info(collection_id, document_id)
    print(f"\nDocument {collection_id}/{document_id}:")
    if doc_info:
        print(f"  Found: {doc_info['title']}")
        print(f"  Files: {list(doc_info.get('files', {}).keys())}")
    else:
        print("  Not found")
        
        # Try to find what's actually there
        collection_path = doc_manager.get_collection_path(collection_id)
        print(f"  Collection path: {collection_path}")
        print(f"  Collection exists: {collection_path.exists()}")
        
        if collection_path.exists():
            documents_path = collection_path / "documents"
            print(f"  Documents path: {documents_path}")
            print(f"  Documents exists: {documents_path.exists()}")
            
            if documents_path.exists():
                print(f"  Documents in folder: {list(documents_path.iterdir())}")

if __name__ == "__main__":
    test_document_manager()
