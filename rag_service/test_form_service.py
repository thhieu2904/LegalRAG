import logging
logging.basicConfig(level=logging.DEBUG)

from app.services.simple_form_detection import SimpleFormDetectionService

# Test với mock response
service = SimpleFormDetectionService()
mock_rag_response = {
    'answer': 'Test answer',
    'context_info': {
        'source_documents': [
            'D:\\Personal\\LegalRAG_OCR\\rag_service\\data\\storage\\collections\\quy_trinh_cap_ho_tich_cap_xa\\documents\\DOC_002\\02. ĐKKS có yếu tố nước ngoài.json'
        ],
        'source_collections': ['quy_trinh_cap_ho_tich_cap_xa']
    }
}

print('Testing enhance_rag_response_with_forms...')
enhanced = service.enhance_rag_response_with_forms(mock_rag_response)
print(f'Form attachments: {len(enhanced.get("form_attachments", []))}')
print(f'Form count: {enhanced.get("context_info", {}).get("form_count", 0)}')
print('Enhanced response keys:', list(enhanced.keys()))
if enhanced.get("form_attachments"):
    for form in enhanced["form_attachments"]:
        print(f'  - {form["document_title"]}: {form["form_filename"]}')
