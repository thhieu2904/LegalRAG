import json
import os
import glob
from pathlib import Path

def safe_cleanup_router_questions():
    """An toàn loại bỏ các trường không sử dụng trong router_questions.json"""
    
    pattern = "data/storage/collections/*/documents/*/router_questions.json"
    files = glob.glob(pattern)
    
    # Backup directory
    backup_dir = "data/backup_router_questions"
    os.makedirs(backup_dir, exist_ok=True)
    
    processed = 0
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Backup original
            backup_name = file_path.replace("/", "_").replace("\\", "_") + ".backup"
            backup_path = os.path.join(backup_dir, backup_name)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Cấu trúc mới - GIỮ LẠI những gì CẦN THIẾT
            minimal_structure = {
                "metadata": {
                    "title": data.get("metadata", {}).get("title", ""),
                    "code": data.get("metadata", {}).get("code", ""),
                    "collection": data.get("metadata", {}).get("collection", ""),
                    "generated_at": data.get("metadata", {}).get("generated_at", "")
                },
                "main_question": data.get("main_question", ""),
                "question_variants": data.get("question_variants", [])
            }
            
            # GIỮ smart_filters nếu có vì Vector.py sử dụng
            if "smart_filters" in data and data["smart_filters"]:
                minimal_structure["smart_filters"] = data["smart_filters"]
            
            # Ghi file mới
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(minimal_structure, f, ensure_ascii=False, indent=2)
                
            processed += 1
            print(f"✅ Cleaned: {file_path}")
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    print(f"\n🎉 Successfully processed {processed} files")
    print(f"📦 Backups saved in: {backup_dir}")
    
    # Tính toán tiết kiệm dung lượng
    original_size = sum(os.path.getsize(os.path.join(backup_dir, f)) for f in os.listdir(backup_dir) if f.endswith('.backup'))
    new_size = sum(os.path.getsize(f) for f in glob.glob(pattern))
    saved = original_size - new_size
    
    print(f"💾 Space saved: {saved:,} bytes ({saved/1024:.1f} KB)")

if __name__ == "__main__":
    safe_cleanup_router_questions()
