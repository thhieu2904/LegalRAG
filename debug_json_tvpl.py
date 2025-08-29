import os
import json

def debug_json_writing():
    """Debug JSON writing issues"""

    base_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_tu_van_phap_luat\documents\DOC_001"
    json_path = os.path.join(base_path, "1 Đăng ký hoạt động của Trung tâm tư vấn pháp luật.json")

    print(f"Checking file: {json_path}")
    print(f"File exists: {os.path.exists(json_path)}")

    if os.path.exists(json_path):
        # Check current content
        with open(json_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        print(f"Current content length: {len(current_content)}")
        print(f"Current content: {current_content[:200]}...")

        # Try to write new content
        test_data = {
            "title": "Test Title",
            "description": "Test Description",
            "content_chunks": [{"chunk_id": 1, "content": "Test content"}]
        }

        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            print("✅ Successfully wrote test data")

            # Verify
            with open(json_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            print(f"New content length: {len(new_content)}")
            print(f"New content preview: {new_content[:200]}...")

        except Exception as e:
            print(f"❌ Error writing file: {e}")

if __name__ == "__main__":
    debug_json_writing()
