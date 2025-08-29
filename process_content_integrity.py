import win32com.client
import json
import os
import re
from datetime import datetime

def clean_text(text):
    """Clean Vietnamese text from Word documents"""
    if not text:
        return ""

    # Remove special characters and control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # Fix broken lines where single letters are separated
    # Pattern: letter\n\nletter or letter\nletter
    lines = text.split('\n')
    cleaned_lines = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            if buffer:
                cleaned_lines.append(buffer)
                buffer = ""
            continue

        # If line is a single character or very short, accumulate it
        if len(line) <= 3 and line.isalpha():
            buffer += line
        else:
            if buffer:
                # Check if buffer + line makes sense
                combined = buffer + line
                if len(combined) > 10:  # Likely a real word/phrase
                    cleaned_lines.append(combined)
                else:
                    cleaned_lines.append(buffer)
                    cleaned_lines.append(line)
                buffer = ""
            else:
                cleaned_lines.append(line)

    # Add remaining buffer
    if buffer:
        cleaned_lines.append(buffer)

    # Join lines back
    text = '\n'.join(cleaned_lines)

    # Clean up multiple spaces
    text = re.sub(r' +', ' ', text)

    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

def extract_content_from_word(doc_path):
    """Extract content from Word document with proper cleaning"""
    try:
        # Initialize Word application
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False

        # Open document
        doc = word.Documents.Open(doc_path)

        # Get all text
        full_text = doc.Content.Text

        # Clean the text
        cleaned_text = clean_text(full_text)

        # Close document
        doc.Close()
        word.Quit()

        return cleaned_text

    except Exception as e:
        print(f"Error reading {doc_path}: {e}")
        return ""

def create_logical_chunks(content, title):
    """Create logical chunks based on content structure, not fixed count"""
    chunks = []

    # Split content into sections based on common legal document patterns
    # Look for main sections in Vietnamese legal documents
    section_patterns = [
        r'(?=MỤC \d+\.?\s*[A-ZÀ-Ỹ])',  # MỤC 1. TÊN MỤC
        r'(?=PHẠM VI\s*$)',  # PHẠM VI
        r'(?=TÀI LIỆU VIỆN DẪN\s*$)',  # TÀI LIỆU VIỆN DẪN
        r'(?=ĐỊNH NGHĨA.*TẮT\s*$)',  # ĐỊNH NGHĨA/VIẾT TẮT
        r'(?=NỘI DUNG.*QUY TRÌNH\s*$)',  # NỘI DUNG QUY TRÌNH
        r'(?=BIỂU MẪU\s*$)',  # BIỂU MẪU
        r'(?=HỒ SƠ.*LƯU\s*$)',  # HỒ SƠ CẦN LƯU
        r'(?=Thành phần.*hồ sơ\s*:)',  # Thành phần hồ sơ
        r'(?=Thời hạn.*giải quyết\s*:)',  # Thời hạn giải quyết
        r'(?=Cơ quan.*thẩm quyền\s*:)',  # Cơ quan có thẩm quyền
        r'(?=Lệ phí.*\(nếu có\)\s*:)',  # Lệ phí
        r'(?=Kết quả.*thủ tục\s*:)',  # Kết quả
    ]

    # Combine patterns
    combined_pattern = '|'.join(section_patterns)
    sections = re.split(combined_pattern, content)

    chunk_id = 1
    current_content = ""
    current_title = ""

    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        # Check if this looks like a section header
        if is_section_header(section):
            # Save previous chunk if exists
            if current_content:
                section_title = extract_section_title(current_title, chunk_id)
                chunks.append({
                    "chunk_id": chunk_id,
                    "section_title": section_title,
                    "content": current_content.strip(),
                    "source_reference": f"{title} - Chunk {chunk_id}",
                    "keywords": extract_keywords(current_content)
                })
                chunk_id += 1

            current_title = section
            current_content = section
        else:
            # Accumulate content
            if current_content:
                current_content += "\n\n" + section
            else:
                current_content = section

    # Add the last chunk
    if current_content:
        section_title = extract_section_title(current_title, chunk_id)
        chunks.append({
            "chunk_id": chunk_id,
            "section_title": section_title,
            "content": current_content.strip(),
            "source_reference": f"{title} - Chunk {chunk_id}",
            "keywords": extract_keywords(current_content)
        })

    return chunks

def is_section_header(text):
    """Check if text looks like a section header"""
    text_upper = text.upper()

    # Common section headers in Vietnamese legal documents
    headers = [
        'MỤC', 'PHẠM VI', 'TÀI LIỆU VIỆN DẪN', 'ĐỊNH NGHĨA', 'VIẾT TẮT',
        'NỘI DUNG', 'QUY TRÌNH', 'BIỂU MẪU', 'HỒ SƠ', 'THÀNH PHẦN',
        'THỜI HẠN', 'CƠ QUAN', 'LỆ PHÍ', 'KẾT QUẢ'
    ]

    return any(header in text_upper for header in headers) and len(text) < 200

def extract_section_title(content, chunk_id):
    """Extract section title from content"""
    lines = content.split('\n')[:3]  # Check first few lines

    for line in lines:
        line = line.strip()
        if line and len(line) < 100:  # Reasonable title length
            # Check if it looks like a title
            if re.match(r'^(MỤC|PHẦN|CHƯƠNG|\d+\.|\([A-Z]\))', line.upper()):
                return f"Phần {chunk_id}: {line}"
            elif any(keyword in line.upper() for keyword in ['HỒ SƠ', 'TRÌNH TỰ', 'CƠ QUAN', 'LỆ PHÍ', 'KẾT QUẢ']):
                return f"Phần {chunk_id}: {line}"

    return f"Phần {chunk_id}: Nội dung chính"

def extract_keywords(content):
    """Extract relevant keywords from content"""
    keywords = []

    # Common legal keywords
    legal_terms = [
        'hồ sơ', 'giấy tờ', 'tờ khai', 'biểu mẫu', 'trình tự', 'các bước',
        'thủ tục', 'cơ quan', 'UBND', 'ủy ban nhân dân', 'lệ phí', 'phí',
        'kết quả', 'giấy chứng nhận', 'thời hạn', 'thời gian'
    ]

    content_lower = content.lower()
    for term in legal_terms:
        if term in content_lower:
            keywords.append(term)

    return keywords[:10]  # Limit to 10 keywords

def process_single_document(doc_path, output_dir):
    """Process a single Word document"""
    try:
        # Extract filename without extension
        filename = os.path.basename(doc_path)
        base_name = os.path.splitext(filename)[0]

        print(f"Processing: {filename}")

        # Extract content
        content = extract_content_from_word(doc_path)
        if not content:
            print(f"Failed to extract content from {filename}")
            return False

        print(f"Extracted {len(content)} characters")

        # Create logical chunks
        chunks = create_logical_chunks(content, base_name)

        print(f"Created {len(chunks)} chunks")

        # Create JSON structure
        json_data = {
            "title": base_name,
            "description": f"Quy trình {base_name.lower()} tại UBND cấp xã",
            "procedure_code": f"QT {base_name.split()[0]}/CX-HT",
            "processing_time": "Theo quy định pháp luật",
            "content_chunks": chunks,
            "metadata": {
                "source_file": filename,
                "processing_date": datetime.now().isoformat(),
                "total_characters": len(content),
                "chunk_count": len(chunks)
            }
        }

        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)

        # Save to JSON file
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
    # Input and output directories
    input_dir = r"d:\Personal\LegalRAG_Fixed"
    output_dir = r"d:\Personal\LegalRAG_Fixed\processed_content"

    # Process temp_doc_001.doc as test
    doc_path = os.path.join(input_dir, "temp_doc_001.doc")

    if os.path.exists(doc_path):
        success = process_single_document(doc_path, output_dir)
        if success:
            print("Processing completed successfully!")
        else:
            print("Processing failed!")
    else:
        print(f"File not found: {doc_path}")

if __name__ == "__main__":
    main()
