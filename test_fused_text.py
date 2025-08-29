import sys
import os
import json
from pathlib import Path

# Test fused text creation logic from the tool
def test_fused_text_creation():
    # Load sample document
    sample_path = Path('data/storage/collections/quy_trinh_cap_ho_tich_cap_xa/documents/DOC_029/29. Ghi vào Sổ hộ tịch việc hộ tịch khác của công dân Việt Nam đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài.json')

    if not sample_path.exists():
        print('❌ Sample file not found')
        return

    with open(sample_path, 'r', encoding='utf-8') as f:
        content = json.load(f)

    # Load questions
    questions_path = sample_path.parent / 'questions.json'
    questions_data = {}
    if questions_path.exists():
        with open(questions_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)

    print('📄 SAMPLE DOCUMENT ANALYSIS')
    print('=' * 50)
    print(f'File: {sample_path.name}')
    print(f'Has questions: {bool(questions_data)}')
    print()

    # Test fused text creation (same logic as tool)
    text_content = ''

    # Format 1: Direct content field
    if isinstance(content.get('content'), str):
        text_content = content['content']
    elif isinstance(content.get('content'), list):
        text_content = ' '.join(str(item) for item in content['content'])

    # Format 2: Content chunks (legal documents format)
    elif content.get('content_chunks'):
        chunks = []
        for chunk in content['content_chunks']:
            if isinstance(chunk, dict) and chunk.get('content'):
                chunks.append(chunk['content'])
        text_content = ' '.join(chunks)

    # Format 3: Summary or text fields
    elif content.get('summary'):
        text_content = content['summary']
    elif content.get('text'):
        text_content = content['text']

    print(f'Content length: {len(text_content)} chars')
    print(f'Content preview: {text_content[:200]}...')
    print()

    # CREATE FUSED TEXT (questions + metadata + content)
    fused_text = ''

    # Add questions first
    if questions_data.get('main_question'):
        fused_text = questions_data['main_question']
        if questions_data.get('question_variants'):
            fused_text += ' | ' + ' | '.join(questions_data['question_variants'])

    # Add metadata if available
    if content.get('metadata'):
        metadata_items = []
        for k, v in content['metadata'].items():
            if isinstance(v, (str, list)) and str(v).strip():
                if isinstance(v, list):
                    v = ' '.join(str(item) for item in v)
                metadata_items.append(f'{k}: {str(v)}')
        if metadata_items:
            metadata_str = ' | '.join(metadata_items)
            if fused_text:
                fused_text += ' | METADATA: ' + metadata_str
            else:
                fused_text = 'METADATA: ' + metadata_str

    # Add content last
    if fused_text:
        fused_text += ' | CONTENT: ' + text_content
    else:
        fused_text = text_content

    # Limit fused text length
    if len(fused_text) > 2000:
        fused_text = fused_text[:2000]

    print('🔗 FUSED TEXT CREATION:')
    print(f'Total fused length: {len(fused_text)} chars')
    print(f'Fused text preview: {fused_text[:300]}...')
    print()

    # Show components
    print('📋 COMPONENTS:')
    if questions_data.get('main_question'):
        print('✅ Main question:', questions_data['main_question'])
    if questions_data.get('question_variants'):
        print('✅ Variants:', len(questions_data['question_variants']), 'variants')
    if content.get('metadata'):
        print('✅ Metadata:', len(content['metadata']), 'fields')
    print('✅ Content:', len(text_content), 'chars')

    return fused_text

if __name__ == "__main__":
    test_fused_text_creation()
