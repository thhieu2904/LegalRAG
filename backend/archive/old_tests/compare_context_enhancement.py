#!/usr/bin/env python3
"""
So sánh context enhancement giữa tài liệu cơ bản và tài liệu đặc biệt
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.services.json_document_processor import JSONDocumentProcessor

def compare_documents():
    processor = JSONDocumentProcessor()
    
    # So sánh 2 tài liệu
    basic_doc = "data/documents/quy_trinh_cap_ho_tich_cap_xa/ho_tich_cap_xa_moi_nhat/01. Đăng ký khai sinh.json"
    special_doc = "data/documents/quy_trinh_cap_ho_tich_cap_xa/ho_tich_cap_xa_moi_nhat/30. Đăng ký khai sinh lưu động.json"
    
    print("=" * 100)
    print("SO SÁNH CONTEXT ENHANCEMENT: TÀI LIỆU CƠ BẢN VS ĐẶC BIỆT")
    print("=" * 100)
    
    for doc_path, doc_type in [(basic_doc, "CƠ BẢN"), (special_doc, "ĐẶC BIỆT")]:
        print(f"\n📄 TÀILIỆU {doc_type}: {Path(doc_path).name}")
        print("-" * 80)
        
        if not Path(doc_path).exists():
            print(f"❌ File không tồn tại: {doc_path}")
            continue
        
        result = processor.process_document(doc_path)
        if "error" in result:
            print(f"❌ Lỗi: {result['error']}")
            continue
        
        chunks = result["chunks"]
        print(f"✅ Số chunks: {len(chunks)}")
        print(f"✅ Collection: {result['collection']}")
        
        # Hiển thị chunk đầu tiên để so sánh
        if chunks:
            chunk = chunks[0]
            print(f"\n🔍 CHUNK ĐẦU TIÊN (Length: {len(chunk['content'])} chars):")
            print("=" * 60)
            # Chỉ hiển thị 300 ký tự đầu để so sánh
            preview = chunk['content'][:400] + "..." if len(chunk['content']) > 400 else chunk['content']
            print(preview)
            print("=" * 60)
        
        print()

if __name__ == "__main__":
    compare_documents()
