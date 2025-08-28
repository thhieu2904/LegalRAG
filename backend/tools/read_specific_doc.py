#!/usr/bin/env python3
"""
Script đặc biệt để đọc file 02. ĐKKS có yếu tố nước ngoài.doc
"""

import olefile
import re

def read_specific_doc():
    doc_path = "d:/Personal/LegalRAG_Fixed/backend/data/storage/collections/quy_trinh_cap_ho_tich_cap_xa/documents/DOC_002/02. ĐKKS có yếu tố nước ngoài.doc"

    try:
        with olefile.OleFileIO(doc_path) as ole:
            # Liệt kê tất cả streams
            print("📁 Available streams:")
            for stream in ole.listdir():
                print(f"  - {stream}")

            # Thử đọc stream WordDocument
            if ole.exists('WordDocument'):
                data = ole.openstream('WordDocument').read()
                print(f"\n📄 WordDocument stream size: {len(data)} bytes")

                # Thử các encoding khác nhau
                encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
                for encoding in encodings:
                    try:
                        text = data.decode(encoding, errors='ignore')
                        # Làm sạch text
                        text = re.sub(r'[^\x20-\x7E\xA0-\xFF\u0100-\uFFFF]', ' ', text)
                        text = re.sub(r'\s+', ' ', text).strip()

                        print(f"\n🔤 Decoded with {encoding} ({len(text)} chars):")
                        print("=" * 80)
                        print(text[:2000])  # Hiển thị 2000 ký tự đầu
                        print("=" * 80)
                        if len(text) > 2000:
                            print(f"... ({len(text) - 2000} characters more)")
                        break
                    except Exception as e:
                        print(f"❌ Failed with {encoding}: {e}")

            # Thử đọc các stream khác
            for stream_name in ['Text', 'Body', 'Contents']:
                if ole.exists(stream_name):
                    print(f"\n📄 Trying stream: {stream_name}")
                    data = ole.openstream(stream_name).read()
                    try:
                        text = data.decode('utf-8', errors='ignore')
                        print(text[:500])
                    except:
                        print("❌ Could not decode")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    read_specific_doc()
