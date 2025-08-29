import json
import os
import glob

def check_chunk_id_format():
    collection_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cong_chung\documents"
    
    files_to_fix = []
    files_correct = []
    
    # Get all main JSON files (not questions.json)
    json_files = []
    for doc_folder in glob.glob(os.path.join(collection_path, "DOC_*")):
        for json_file in glob.glob(os.path.join(doc_folder, "*.json")):
            if not json_file.endswith("questions.json"):
                json_files.append(json_file)
    
    print(f"Checking {len(json_files)} JSON files...")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            doc_name = os.path.basename(file_path)
            
            if 'content_chunks' in data:
                has_string_chunk_id = False
                for chunk in data['content_chunks']:
                    if 'chunk_id' in chunk:
                        if isinstance(chunk['chunk_id'], str):
                            has_string_chunk_id = True
                            break
                
                if has_string_chunk_id:
                    files_to_fix.append(file_path)
                    print(f"❌ {doc_name} - has string chunk_id")
                else:
                    files_correct.append(file_path)
                    print(f"✅ {doc_name} - has numeric chunk_id")
            
        except Exception as e:
            print(f"❗ Error checking {file_path}: {e}")
    
    print(f"\nSummary:")
    print(f"Files with correct numeric chunk_id: {len(files_correct)}")
    print(f"Files with incorrect string chunk_id: {len(files_to_fix)}")
    
    if files_to_fix:
        print(f"\nFiles needing fix:")
        for file_path in files_to_fix:
            doc_name = os.path.basename(file_path)
            print(f"  - {doc_name}")
    
    return files_to_fix

if __name__ == "__main__":
    files_to_fix = check_chunk_id_format()
