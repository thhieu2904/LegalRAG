import json
import os
import glob

def verify_all_collections():
    base_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections"
    
    # Get all collection directories
    collections = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "documents")):
            collections.append(item)
    
    print(f"Found {len(collections)} collections to verify:")
    for collection in collections:
        print(f"  - {collection}")
    print()
    
    total_files_complete = 0
    total_files_checked = 0
    collection_results = {}
    
    for collection_name in sorted(collections):
        collection_path = os.path.join(base_path, collection_name, "documents")
        
        # Get all main JSON files (not questions.json)
        json_files = []
        for doc_folder in glob.glob(os.path.join(collection_path, "DOC_*")):
            for json_file in glob.glob(os.path.join(doc_folder, "*.json")):
                if not json_file.endswith("questions.json"):
                    json_files.append(json_file)
        
        print(f"Checking {collection_name} ({len(json_files)} files)...")
        
        complete_files = 0
        incomplete_files = 0
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                is_complete = True
                
                # Check content_chunks structure
                if 'content_chunks' not in data:
                    is_complete = False
                else:
                    for chunk in data['content_chunks']:
                        # Check chunk_id is numeric
                        if 'chunk_id' not in chunk or not isinstance(chunk['chunk_id'], int):
                            is_complete = False
                            break
                        
                        # Check required fields
                        required_fields = ['section_title', 'content', 'source_reference', 'keywords']
                        for field in required_fields:
                            if field not in chunk:
                                is_complete = False
                                break
                        
                        # Check keywords is array
                        if 'keywords' in chunk and not isinstance(chunk['keywords'], list):
                            is_complete = False
                            break
                        
                        if not is_complete:
                            break
                
                # Check metadata structure (both formats)
                if is_complete:
                    if 'metadata' not in data and 'title' not in data:
                        is_complete = False
                    elif 'metadata' in data and 'title' not in data['metadata'] and 'title' not in data:
                        is_complete = False
                
                # Check fee_structure exists
                if is_complete and 'fee_structure' not in data:
                    is_complete = False
                
                if is_complete:
                    complete_files += 1
                else:
                    incomplete_files += 1
                
            except Exception as e:
                incomplete_files += 1
                print(f"    ❗ Error reading {os.path.basename(file_path)}: {e}")
        
        success_rate = (complete_files / len(json_files)) * 100 if json_files else 0
        status = "✅ COMPLETE" if complete_files == len(json_files) else f"❌ {complete_files}/{len(json_files)}"
        
        print(f"  {status} ({success_rate:.1f}%)")
        
        collection_results[collection_name] = {
            'complete': complete_files,
            'total': len(json_files),
            'success_rate': success_rate
        }
        
        total_files_complete += complete_files
        total_files_checked += len(json_files)
    
    print(f"\n{'='*60}")
    print(f"OVERALL SUMMARY:")
    print(f"{'='*60}")
    
    complete_collections = []
    partial_collections = []
    
    for collection_name, result in collection_results.items():
        if result['success_rate'] == 100.0:
            complete_collections.append(f"{collection_name} ({result['total']} files)")
        else:
            partial_collections.append(f"{collection_name} ({result['complete']}/{result['total']} files)")
    
    if complete_collections:
        print(f"\n✅ COMPLETE COLLECTIONS ({len(complete_collections)}):")
        for collection in complete_collections:
            print(f"  - {collection}")
    
    if partial_collections:
        print(f"\n❌ INCOMPLETE COLLECTIONS ({len(partial_collections)}):")
        for collection in partial_collections:
            print(f"  - {collection}")
    
    overall_success_rate = (total_files_complete / total_files_checked) * 100 if total_files_checked > 0 else 0
    print(f"\n🎯 TOTAL PROGRESS: {total_files_complete}/{total_files_checked} files complete ({overall_success_rate:.1f}%)")
    
    if overall_success_rate == 100.0:
        print(f"🎉 ALL COLLECTIONS ARE 100% COMPLETE! Ready for LegalRAG deployment.")
    else:
        remaining = total_files_checked - total_files_complete
        print(f"📝 {remaining} files remaining to reach 100% completion.")
    
    return collection_results

if __name__ == "__main__":
    results = verify_all_collections()
