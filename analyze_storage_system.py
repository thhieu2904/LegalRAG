import os
import json
from collections import defaultdict

# Thu muc storage chinh
storage_dir = 'backend/data/storage/collections'

print('=== PHAN TICH TOAN HE THONG STORAGE ===')
print()

# Thong ke tong quan
total_collections = 0
total_doc_folders = 0
total_word_files = 0
total_json_files = 0
total_forms_word_files = 0

collection_stats = []

# Duyet qua tat ca collections
for collection_name in os.listdir(storage_dir):
    collection_path = os.path.join(storage_dir, collection_name)

    if not os.path.isdir(collection_path):
        continue

    total_collections += 1

    # Thong ke cho collection nay
    collection_word_files = 0
    collection_json_files = 0
    collection_forms_word_files = 0
    collection_doc_folders = 0

    documents_path = os.path.join(collection_path, 'documents')

    if os.path.exists(documents_path):
        # Dem DOC_xxx folders
        for item in os.listdir(documents_path):
            item_path = os.path.join(documents_path, item)
            if os.path.isdir(item_path) and item.startswith('DOC_'):
                collection_doc_folders += 1

                # Duyet cac file trong DOC_xxx
                for root, dirs, files in os.walk(item_path):
                    # Bo qua forms/
                    if 'forms' in root:
                        forms_word = [f for f in files if f.endswith(('.doc', '.docx'))]
                        collection_forms_word_files += len(forms_word)
                        total_forms_word_files += len(forms_word)
                        continue

                    # Dem file Word chinh
                    word_files = [f for f in files if f.endswith(('.doc', '.docx'))]
                    collection_word_files += len(word_files)
                    total_word_files += len(word_files)

                    # Dem file JSON chinh (bo qua questions.json)
                    json_files = [f for f in files if f.endswith('.json') and not f.endswith('questions.json')]
                    collection_json_files += len(json_files)
                    total_json_files += len(json_files)

    total_doc_folders += collection_doc_folders

    # Luu thong ke
    mapping_status = 'OK' if collection_word_files == collection_json_files else 'MISMATCH'
    collection_stats.append({
        'name': collection_name,
        'doc_folders': collection_doc_folders,
        'word_files': collection_word_files,
        'json_files': collection_json_files,
        'forms_word_files': collection_forms_word_files,
        'mapping_status': mapping_status
    })

print('📊 TONG QUAN HE THONG:')
print(f'   - Tong so collections: {total_collections}')
print(f'   - Tong so thu muc DOC_xxx: {total_doc_folders}')
print(f'   - Tong so file Word chinh: {total_word_files}')
print(f'   - Tong so file JSON chinh: {total_json_files}')
print(f'   - Tong so file Word trong forms/: {total_forms_word_files}')
print()

print('📋 CHI TIET TUNG COLLECTION:')
print('=' * 80)

for stat in collection_stats:
    status_icon = '✅' if stat['mapping_status'] == 'OK' else '❌'
    print(f'{status_icon} {stat["name"]}')
    print(f'   📁 DOC folders: {stat["doc_folders"]}')
    print(f'   📄 Word files: {stat["word_files"]}')
    print(f'   📋 JSON files: {stat["json_files"]}')
    print(f'   📝 Forms Word: {stat["forms_word_files"]}')

    if stat['mapping_status'] == 'MISMATCH':
        print(f'   ⚠️  MISMATCH: {stat["word_files"]} Word vs {stat["json_files"]} JSON')
    else:
        print(f'   ✅ Mapping OK: {stat["word_files"]}-{stat["json_files"]}')
    print()

# Tong ket
ok_collections = sum(1 for s in collection_stats if s['mapping_status'] == 'OK')
mismatch_collections = total_collections - ok_collections

print('🎯 TONG KET:')
print(f'   ✅ Collections OK: {ok_collections}/{total_collections}')
print(f'   ❌ Collections co van de: {mismatch_collections}/{total_collections}')

if mismatch_collections > 0:
    print()
    print('⚠️  CAC COLLECTIONS CAN KIEM TRA:')
    for stat in collection_stats:
        if stat['mapping_status'] == 'MISMATCH':
            print(f'   - {stat["name"]}: {stat["word_files"]} Word vs {stat["json_files"]} JSON')
