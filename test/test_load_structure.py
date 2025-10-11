import sys
sys.path.insert(0, '/app')

from tools.cache import load_new_structure

data = load_new_structure()
print(f"Collections: {len(data)}")
if data:
    print(f"First collection: {data[0]['collection_id']}")
    print(f"Documents in first collection: {len(data[0]['documents'])}")
    if data[0]['documents']:
        print(f"First doc ID: {data[0]['documents'][0]['doc_id']}")
