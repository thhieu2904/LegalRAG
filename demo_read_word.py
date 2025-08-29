import os
import win32com.client
import json

def demo_read_word_file():
    """Demo cách đọc file Word để user thấy rõ"""

    doc_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents\DOC_001\01. Đăng ký khai sinh.doc"

    print("=== DEMO ĐỌC FILE WORD ===")
    print(f"📄 File: {os.path.basename(doc_path)}")
    print(f"📂 Path: {doc_path}")
    print()

    if not os.path.exists(doc_path):
        print(f"❌ Không tìm thấy file: {doc_path}")
        return

    try:
        print("🔄 Đang mở Word Application...")
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False

        print("📖 Đang đọc file Word...")
        doc = word.Documents.Open(doc_path)

        print("📝 Đang trích xuất nội dung...")
        content = doc.Content.Text

        print("🔒 Đang đóng file...")
        doc.Close()
        word.Quit()

        print("✅ Đã đọc thành công!")
        print(f"📊 Độ dài nội dung: {len(content)} ký tự")
        print()

        # Hiển thị một phần nội dung đầu tiên
        print("📋 NỘI DUNG ĐẦU TIÊN (200 ký tự):")
        print("-" * 50)
        print(content[:200])
        print("-" * 50)
        print()

        # Hiển thị một phần nội dung giữa
        print("📋 NỘI DUNG GIỮA FILE (từ 1000-1200 ký tự):")
        print("-" * 50)
        if len(content) > 1200:
            print(content[1000:1200])
        else:
            print("File quá ngắn")
        print("-" * 50)
        print()

        # Hiển thị một phần nội dung cuối
        print("📋 NỘI DUNG CUỐI FILE (200 ký tự cuối):")
        print("-" * 50)
        print(content[-200:])
        print("-" * 50)
        print()

        # Lưu nội dung thô vào file để user kiểm tra
        raw_content_path = r"d:\Personal\LegalRAG_Fixed\raw_content_demo.txt"
        with open(raw_content_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"💾 Đã lưu nội dung thô vào: {raw_content_path}")
        print("📝 Bạn có thể mở file này để kiểm tra nội dung gốc từ Word")

    except Exception as e:
        print(f"❌ Lỗi khi đọc file: {e}")
        print("💡 Nguyên nhân có thể:")
        print("   - File Word bị hỏng")
        print("   - Microsoft Word không được cài đặt")
        print("   - Quyền truy cập file bị hạn chế")

if __name__ == "__main__":
    demo_read_word_file()
