import win32com.client
import json
import os
import re
from datetime import datetime

def extract_structured_content(doc_path):
    """Extract structured content from Word document"""
    try:
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False

        doc = word.Documents.Open(doc_path)

        content_info = {
            'title': '',
            'purpose': '',
            'scope': '',
            'documents': '',
            'definitions': '',
            'procedure_content': '',
            'forms': '',
            'retention': ''
        }

        # Extract title from first few paragraphs
        for i in range(min(5, doc.Paragraphs.Count)):
            para_text = doc.Paragraphs[i].Range.Text.strip()
            if 'QUY TRÌNH' in para_text.upper() and len(para_text) > 10:
                content_info['title'] = clean_paragraph_text(para_text)
                break

        # Extract sections by searching for keywords
        full_text = doc.Content.Text

        # Find purpose section
        purpose_match = re.search(r'MỤC ĐÍCH(.*?)(?=PHẠM VI|TÀI LIỆU|$)', full_text, re.DOTALL | re.IGNORECASE)
        if purpose_match:
            content_info['purpose'] = clean_paragraph_text(purpose_match.group(1))

        # Find scope section
        scope_match = re.search(r'PHẠM VI(.*?)(?=TÀI LIỆU|ĐỊNH NGHĨA|$)', full_text, re.DOTALL | re.IGNORECASE)
        if scope_match:
            content_info['scope'] = clean_paragraph_text(scope_match.group(1))

        # Find documents section
        docs_match = re.search(r'TÀI LIỆU VIỆN DẪN(.*?)(?=ĐỊNH NGHĨA|NỘI DUNG|$)', full_text, re.DOTALL | re.IGNORECASE)
        if docs_match:
            content_info['documents'] = clean_paragraph_text(docs_match.group(1))

        # Find definitions section
        defs_match = re.search(r'ĐỊNH NGHĨA.*?(.*?)(?=NỘI DUNG|BIỂU MẪU|$)', full_text, re.DOTALL | re.IGNORECASE)
        if defs_match:
            content_info['definitions'] = clean_paragraph_text(defs_match.group(1))

        # Find procedure content
        proc_match = re.search(r'NỘI DUNG QUY TRÌNH(.*?)(?=BIỂU MẪU|HỒ SƠ|$)', full_text, re.DOTALL | re.IGNORECASE)
        if proc_match:
            content_info['procedure_content'] = clean_paragraph_text(proc_match.group(1))

        # Find forms section
        forms_match = re.search(r'BIỂU MẪU(.*?)(?=HỒ SƠ|$)', full_text, re.DOTALL | re.IGNORECASE)
        if forms_match:
            content_info['forms'] = clean_paragraph_text(forms_match.group(1))

        # Find retention section
        ret_match = re.search(r'HỒ SƠ.*?(.*?)$', full_text, re.DOTALL | re.IGNORECASE)
        if ret_match:
            content_info['retention'] = clean_paragraph_text(ret_match.group(1))

        doc.Close()
        word.Quit()

        return content_info

    except Exception as e:
        print(f"Error extracting content: {e}")
        return None

def clean_paragraph_text(text):
    """Clean paragraph text from Word"""
    if not text:
        return ""

    # Remove control characters
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)

    # Clean up whitespace
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\t+', ' ', text)
    text = re.sub(r' +', ' ', text)

    return text.strip()

def create_chunks_from_structured_content(content_info, filename):
    """Create chunks from structured content"""
    chunks = []
    chunk_id = 1

    # Define chunk mappings
    chunk_definitions = [
        {
            'title': 'Mục đích và phạm vi',
            'content': content_info['purpose'] + '\n\n' + content_info['scope'],
            'keywords': ['mục đích', 'phạm vi', 'áp dụng']
        },
        {
            'title': 'Tài liệu viện dẫn và định nghĩa',
            'content': content_info['documents'] + '\n\n' + content_info['definitions'],
            'keywords': ['tài liệu', 'viện dẫn', 'định nghĩa', 'viết tắt']
        },
        {
            'title': 'Nội dung quy trình',
            'content': content_info['procedure_content'],
            'keywords': ['quy trình', 'thủ tục', 'trình tự', 'hồ sơ', 'thời hạn']
        },
        {
            'title': 'Biểu mẫu và lưu trữ',
            'content': content_info['forms'] + '\n\n' + content_info['retention'],
            'keywords': ['biểu mẫu', 'hồ sơ', 'lưu trữ', 'sổ sách']
        }
    ]

    for chunk_def in chunk_definitions:
        if chunk_def['content'].strip():  # Only create chunk if there's content
            chunks.append({
                "chunk_id": chunk_id,
                "section_title": f"Phần {chunk_id}: {chunk_def['title']}",
                "content": chunk_def['content'].strip(),
                "source_reference": f"{filename} - Chunk {chunk_id}",
                "keywords": chunk_def['keywords']
            })
            chunk_id += 1

    return chunks

def process_document_with_structure(doc_path, output_dir):
    """Process document using structured extraction"""
    try:
        filename = os.path.basename(doc_path)
        base_name = os.path.splitext(filename)[0]

        print(f"Processing: {filename}")

        # Extract structured content
        content_info = extract_structured_content(doc_path)
        if not content_info:
            print("Failed to extract structured content")
            return False

        # Create chunks
        chunks = create_chunks_from_structured_content(content_info, base_name)

        print(f"Created {len(chunks)} chunks")

        # Create JSON structure
        json_data = {
            "title": content_info['title'] or base_name,
            "description": f"Quy trình {base_name.lower()} tại UBND cấp xã",
            "procedure_code": f"QT {base_name.split()[0]}/CX-HT",
            "processing_time": "Theo quy định pháp luật",
            "content_chunks": chunks,
            "metadata": {
                "source_file": filename,
                "processing_date": datetime.now().isoformat(),
                "extraction_method": "structured",
                "chunk_count": len(chunks)
            }
        }

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Save to JSON
        output_file = os.path.join(output_dir, f"{base_name}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"Saved to: {output_file}")
        return True

    except Exception as e:
        print(f"Error processing {doc_path}: {e}")
        return False

def main():
    """Main processing function"""
    input_dir = r"d:\Personal\LegalRAG_Fixed"
    output_dir = r"d:\Personal\LegalRAG_Fixed\processed_content_structured"

    doc_path = os.path.join(input_dir, "temp_doc_001.doc")

    if os.path.exists(doc_path):
        success = process_document_with_structure(doc_path, output_dir)
        if success:
            print("Processing completed successfully!")
        else:
            print("Processing failed!")
    else:
        print(f"File not found: {doc_path}")

if __name__ == "__main__":
    main()
