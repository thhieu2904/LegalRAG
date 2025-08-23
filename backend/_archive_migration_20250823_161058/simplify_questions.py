import json
import os
import glob

def simplify_router_questions():
    """Đơn giản hóa các file router_questions.json"""
    
    pattern = "data/storage/collections/*/documents/*/router_questions.json"
    files = glob.glob(pattern)
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cấu trúc mới đơn giản
            simplified = {
                "metadata": {
                    "title": data.get("metadata", {}).get("title", ""),
                    "code": data.get("metadata", {}).get("code", ""),
                    "generated_at": data.get("metadata", {}).get("generated_at", "")
                },
                "main_question": data.get("main_question", ""),
                "question_variants": data.get("question_variants", [])
            }
            
            # Backup file cũ
            backup_path = file_path + ".backup"
            os.rename(file_path, backup_path)
            
            # Ghi file mới
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(simplified, f, ensure_ascii=False, indent=2)
                
            print(f"Simplified: {file_path}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    simplify_router_questions()
