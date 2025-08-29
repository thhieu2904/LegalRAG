import win32com.client
import json
import os
import re
from datetime import datetime

def read_word_document(doc_path):
    """Read Word document and return cleaned content"""
    try:
        # Initialize Word application
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False

        # Open document
        doc = word.Documents.Open(doc_path)

        # Get all text
        raw_text = doc.Content.Text

        # Close document
        doc.Close()
        word.Quit()

        return raw_text

    except Exception as e:
        print(f"Error reading {doc_path}: {e}")
        return None

def clean_word_content(raw_text):
    """Clean the raw text from Word document"""
    if not raw_text:
        return ""

    # Remove control characters but keep newlines and tabs
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', raw_text)

    # Clean up excessive whitespace but preserve paragraph structure
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r' {2,}', ' ', cleaned)

    return cleaned.strip()

def extract_title_from_content(content):
    """Extract title from document content"""
    lines = content.split('\n')

    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if 'QUY TRÌNH' in line.upper() and len(line) > 10:
            # Clean up the title
            title = re.sub(r'[^\w\sÀ-ỹ]', '', line)
            return title.strip()

    return "Quy trình hành chính"

def create_simple_json(content, filename, title):
    """Create simple JSON with full content"""
    # Create basic metadata
    json_data = {
        "title": title,
        "description": f"Quy trình {title.lower()} tại UBND cấp xã",
        "procedure_code": f"QT {filename.split()[0]}/CX-HT",
        "processing_time": "Theo quy định pháp luật",
        "full_content": content,
        "metadata": {
            "source_file": filename,
            "processing_date": datetime.now().isoformat(),
            "content_length": len(content),
            "extraction_method": "full_content"
        }
    }

    return json_data

def process_single_file(doc_path, output_dir):
    """Process a single Word document"""
    try:
        filename = os.path.basename(doc_path)
        base_name = os.path.splitext(filename)[0]

        print(f"Processing: {filename}")

        # Read document
        raw_content = read_word_document(doc_path)
        if raw_content is None:
            print(f"Failed to read {filename}")
            return False

        print(f"Raw content length: {len(raw_content)} characters")

        # Clean content
        cleaned_content = clean_word_content(raw_content)
        print(f"Cleaned content length: {len(cleaned_content)} characters")

        # Extract title
        title = extract_title_from_content(cleaned_content)
        print(f"Extracted title: {title}")

        # Create JSON
        json_data = create_simple_json(cleaned_content, base_name, title)

        # Create output directory
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
    input_dir = r"d:\Personal\LegalRAG_Fixed"
    output_dir = r"d:\Personal\LegalRAG_Fixed\processed_simple"

    # Process temp_doc_001.doc as test
    doc_path = os.path.join(input_dir, "temp_doc_001.doc")

    if os.path.exists(doc_path):
        success = process_single_file(doc_path, output_dir)
        if success:
            print("\n✅ Processing completed successfully!")
            print("JSON file created with full document content.")
        else:
            print("\n❌ Processing failed!")
    else:
        print(f"File not found: {doc_path}")

if __name__ == "__main__":
    main()
