import json
import os
import glob

def fix_chunk_id_format():
    collection_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cong_chung\documents"
    
    # Files that need fixing based on previous check
    files_needing_fix = [
        "7. Thay đổi nơi tập sự hành nghề công chứng từ tổ chức hành nghề công chứng này sang tổ chức hành nghề công chứng khác trong cùng một tỉnh, thành phố trực thuộc Trung ương.json",
        "8. Thay đổi nơi tập sự hành nghề công chứng từ tổ chức hành nghề công chứng tại tỉnh, thành phôd này sang tỉnh, thành phố khác .json",
        "9. Công nhận hoàn thành tập sự hành nghề công chứng.json",
        "10. Chấm dứt tập sự hành nghề công chứng.json",
        "11. Đăng ký tham dự kiểm tra kết quả tập sự hành nghề công chứng.json",
        "12. Cấp thẻ công chứng viên.json",
        "13. Cấp lại Thẻ công chứng viên.json",
        "14. Thu hồi Thẻ công chứng viên.json",
        "15. Thành lập Văn phòng công chứng.json"
    ]
    
    fixed_count = 0
    error_count = 0
    
    # Find and fix each file
    for doc_folder in glob.glob(os.path.join(collection_path, "DOC_*")):
        for json_file in glob.glob(os.path.join(doc_folder, "*.json")):
            if not json_file.endswith("questions.json"):
                file_name = os.path.basename(json_file)
                
                if file_name in files_needing_fix:
                    try:
                        print(f"Fixing: {file_name}")
                        
                        # Read current file
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Fix chunk_id format
                        if 'content_chunks' in data:
                            for i, chunk in enumerate(data['content_chunks']):
                                if 'chunk_id' in chunk and isinstance(chunk['chunk_id'], str):
                                    # Convert string chunk_id to numeric (1-based index)
                                    chunk['chunk_id'] = i + 1
                                    print(f"  - Converted chunk_id from '{chunk['chunk_id']}' to {i + 1}")
                        
                        # Write fixed file
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        
                        print(f"✅ Fixed: {file_name}")
                        fixed_count += 1
                        
                    except Exception as e:
                        print(f"❌ Error fixing {file_name}: {e}")
                        error_count += 1
    
    print(f"\nSummary:")
    print(f"Files successfully fixed: {fixed_count}")
    print(f"Files with errors: {error_count}")
    print(f"Total files that needed fixing: {len(files_needing_fix)}")

if __name__ == "__main__":
    fix_chunk_id_format()
