import json
import os
import glob

def verify_collection_complete(collection_name):
    collection_path = rf"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\{collection_name}\documents"
    
    if not os.path.exists(collection_path):
        print(f"❌ Collection {collection_name} not found")
        return False
    
    # Get all main JSON files (not questions.json)
    json_files = []
    for doc_folder in glob.glob(os.path.join(collection_path, "DOC_*")):
        for json_file in glob.glob(os.path.join(doc_folder, "*.json")):
            if not json_file.endswith("questions.json"):
                json_files.append(json_file)
    
    print(f"Checking {collection_name} collection ({len(json_files)} files)...")
    
    complete_files = 0
    incomplete_files = 0
    error_files = 0
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            doc_name = os.path.basename(file_path)
            is_complete = True
            missing_items = []
            
            # Check content_chunks structure
            if 'content_chunks' not in data:
                is_complete = False
                missing_items.append("content_chunks")
            else:
                for i, chunk in enumerate(data['content_chunks']):
                    chunk_issues = []
                    
                    # Check chunk_id is numeric
                    if 'chunk_id' not in chunk:
                        chunk_issues.append("chunk_id missing")
                    elif not isinstance(chunk['chunk_id'], int):
                        chunk_issues.append(f"chunk_id is {type(chunk['chunk_id'])}, should be int")
                    
                    # Check required fields
                    required_fields = ['section_title', 'content', 'source_reference', 'keywords']
                    for field in required_fields:
                        if field not in chunk:
                            chunk_issues.append(f"{field} missing")
                    
                    # Check keywords is array
                    if 'keywords' in chunk and not isinstance(chunk['keywords'], list):
                        chunk_issues.append("keywords should be array")
                    
                    if chunk_issues:
                        is_complete = False
                        missing_items.append(f"chunk_{i+1}: {', '.join(chunk_issues)}")
            
            # Check metadata structure
            if 'metadata' not in data:
                is_complete = False
                missing_items.append("metadata section")
            else:
                # Check both old format (direct fields) and new format (metadata object)
                metadata = data.get('metadata', {})
                required_metadata = ['title']  # Key required field
                
                # Check if it's old format (direct fields) or new format (metadata object)
                if 'title' in data:  # Old format
                    check_fields = ['title', 'description', 'legal_basis', 'procedure_code', 'processing_time', 'application_method']
                    for field in check_fields:
                        if field not in data:
                            is_complete = False
                            missing_items.append(f"{field}")
                elif 'title' in metadata:  # New format
                    check_fields = ['title']  # Just check key field for new format
                    for field in check_fields:
                        if field not in metadata:
                            is_complete = False
                            missing_items.append(f"metadata.{field}")
                else:  # Missing title in both formats
                    is_complete = False
                    missing_items.append("title (in metadata or root)")
            
            # Check fee_structure exists
            if 'fee_structure' not in data:
                is_complete = False
                missing_items.append("fee_structure")
            
            if is_complete:
                complete_files += 1
                print(f"  ✅ {doc_name}")
            else:
                incomplete_files += 1
                print(f"  ❌ {doc_name} - Missing: {', '.join(missing_items[:3])}{'...' if len(missing_items) > 3 else ''}")
            
        except Exception as e:
            error_files += 1
            print(f"  ❗ Error reading {os.path.basename(file_path)}: {e}")
    
    success_rate = (complete_files / len(json_files)) * 100 if json_files else 0
    print(f"\n{collection_name} Summary:")
    print(f"✅ Complete: {complete_files}/{len(json_files)} files ({success_rate:.1f}%)")
    print(f"❌ Incomplete: {incomplete_files} files")
    print(f"❗ Errors: {error_files} files")
    
    return complete_files == len(json_files) and error_files == 0

if __name__ == "__main__":
    # Check the quy_trinh_cong_chung collection that we just fixed
    result = verify_collection_complete("quy_trinh_cong_chung")
    print(f"\nquy_trinh_cong_chung collection is {'✅ COMPLETE' if result else '❌ INCOMPLETE'}")
