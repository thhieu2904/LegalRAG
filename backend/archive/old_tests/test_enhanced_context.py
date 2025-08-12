#!/usr/bin/env python3
"""
Test script để kiểm tra việc tăng cường ngữ cảnh cho chunks
Hiển thị so sánh giữa chunk cũ và chunk mới với context được tăng cường
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.services.json_document_processor import JSONDocumentProcessor

def test_enhanced_context():
    """Test việc tăng cường ngữ cảnh cho chunks"""
    processor = JSONDocumentProcessor()
    
    # Test với một file JSON cụ thể
    test_file = Path("data/documents/quy_trinh_cap_ho_tich_cap_xa/ho_tich_cap_xa_moi_nhat/01. Đăng ký khai sinh.json")
    
    print("=" * 80)
    print("KIỂM TRA TĂNG CƯỜNG NGỮ CẢNH CHO CHUNKS")
    print("=" * 80)
    print(f"Đang test với file: {test_file}")
    print()
    
    if not test_file.exists():
        print(f"❌ File không tồn tại: {test_file}")
        return
    
    # Process document
    result = processor.process_document(str(test_file))
    
    if "error" in result:
        print(f"❌ Lỗi khi xử lý file: {result['error']}")
        return
    
    chunks = result["chunks"]
    print(f"✅ Đã xử lý thành công {len(chunks)} chunks")
    print()
    
    # Hiển thị 3 chunks đầu tiên để xem context enhancement
    for i, chunk in enumerate(chunks[:3]):
        print(f"--- CHUNK {i+1} ---")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Type: {chunk['type']}")
        print(f"Length: {len(chunk['content'])} ký tự")
        print()
        print("CONTENT:")
        print("-" * 40)
        print(chunk['content'])
        print("-" * 40)
        print()
        
        # Hiển thị metadata quan trọng
        source_info = chunk.get('source', {})
        print("SOURCE INFO:")
        print(f"  - Document title: {source_info.get('document_title', 'N/A')}")
        print(f"  - Section title: {source_info.get('section_title', 'N/A')}")
        print(f"  - Executing agency: {source_info.get('executing_agency', 'N/A')}")
        print()
        
        if i < 2:  # Không in separator cho chunk cuối
            print("=" * 80)
            print()
    
    # Thống kê tổng quan
    print("THỐNG KÊ TỔNG QUAN:")
    print(f"- Tổng số chunks: {len(chunks)}")
    print(f"- Tổng ký tự: {result['total_characters']}")
    print(f"- Collection: {result['collection']}")
    print()
    
    # Kiểm tra xem context có được thêm vào không
    enhanced_chunks = 0
    for chunk in chunks:
        if "Tiêu đề tài liệu:" in chunk['content']:
            enhanced_chunks += 1
    
    print(f"✅ Số chunks được tăng cường context: {enhanced_chunks}/{len(chunks)}")
    
    if enhanced_chunks > 0:
        percentage = (enhanced_chunks / len(chunks)) * 100
        print(f"✅ Tỉ lệ tăng cường: {percentage:.1f}%")
        print("🎉 Context enhancement hoạt động thành công!")
    else:
        print("❌ Context enhancement chưa hoạt động!")

if __name__ == "__main__":
    test_enhanced_context()
