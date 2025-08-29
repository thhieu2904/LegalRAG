import os
import json
from pathlib import Path

collections_path = Path('d:/Personal/LegalRAG_Fixed/backend/data/storage/collections')
issues = []

for collection_dir in collections_path.iterdir():
    if collection_dir.is_dir():
        collection_name = collection_dir.name
        json_files = list(collection_dir.rglob('*.json'))

        if not json_files:
            issues.append({
                'collection': collection_name,
                'issue': 'No JSON files found',
                'severity': 'Critical'
            })
            continue

        # Check for validation issues
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check for required fields
                if 'metadata' not in data:
                    issues.append({
                        'collection': collection_name,
                        'file': json_file.name,
                        'issue': 'Missing metadata section',
                        'severity': 'High'
                    })

                if 'content_chunks' not in data:
                    issues.append({
                        'collection': collection_name,
                        'file': json_file.name,
                        'issue': 'Missing content_chunks section',
                        'severity': 'High'
                    })
                elif len(data.get('content_chunks', [])) != 6:
                    chunk_count = len(data.get('content_chunks', []))
                    issues.append({
                        'collection': collection_name,
                        'file': json_file.name,
                        'issue': f'Incorrect number of chunks: {chunk_count} (expected 6)',
                        'severity': 'Medium'
                    })

            except json.JSONDecodeError as e:
                issues.append({
                    'collection': collection_name,
                    'file': json_file.name,
                    'issue': f'Invalid JSON: {str(e)}',
                    'severity': 'Critical'
                })
            except Exception as e:
                issues.append({
                    'collection': collection_name,
                    'file': json_file.name,
                    'issue': f'Error reading file: {str(e)}',
                    'severity': 'High'
                })

# Group issues by collection
collection_issues = {}
for issue in issues:
    collection = issue['collection']
    if collection not in collection_issues:
        collection_issues[collection] = []
    collection_issues[collection].append(issue)

# Print summary
print('=== COLLECTION VALIDATION REPORT ===')
print(f'Total collections checked: {len([d for d in collections_path.iterdir() if d.is_dir()])}')
print(f'Collections with issues: {len(collection_issues)}')
print()

for collection, issues_list in collection_issues.items():
    print(f'📁 {collection}:')
    severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    for issue in issues_list:
        severity_counts[issue['severity']] += 1

    for severity, count in severity_counts.items():
        if count > 0:
            print(f'  {severity}: {count} issues')

    # Show first few issues as examples
    print('  Sample issues:')
    for i, issue in enumerate(issues_list[:3]):
        file_name = issue.get('file', 'N/A')
        print(f'    - {file_name}: {issue["issue"]}')
    if len(issues_list) > 3:
        print(f'    ... and {len(issues_list) - 3} more issues')
    print()
