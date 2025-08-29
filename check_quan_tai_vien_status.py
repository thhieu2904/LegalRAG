import os
import json

collection_path = r'd:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_quan_tai_vien\documents'

print('=== QUY_TRINH_QUAN_TAI_VIEN COLLECTION STATUS ===')
print()

total_files = 0
completed_files = 0

for i in range(1, 9):
    doc_folder = f'DOC_{i:03d}'
    doc_path = os.path.join(collection_path, doc_folder)

    if os.path.exists(doc_path):
        total_files += 1

        # Find JSON file
        json_files = [f for f in os.listdir(doc_path) if f.endswith('.json') and not f.startswith('questions')]

        if json_files:
            json_file = json_files[0]
            json_path = os.path.join(doc_path, json_file)

            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check if properly structured
                if 'content_chunks' in data and len(data['content_chunks']) == 5:
                    completed_files += 1
                    title = data.get('title', 'Unknown')
                    print(f'✅ {doc_folder}: {title}')
                else:
                    print(f'❌ {doc_folder}: Incomplete structure')
            except:
                print(f'❌ {doc_folder}: JSON error')
        else:
            print(f'❌ {doc_folder}: No JSON file found')

print()
print(f'Progress: {completed_files}/{total_files} files completed')
status = "COMPLETE" if completed_files == total_files else "IN PROGRESS"
print(f'Collection Status: {status}')
