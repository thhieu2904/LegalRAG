import json
import os
import re
from datetime import datetime

def read_and_clean_txt_file(file_path):
    """Read and clean the text file content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove special characters and control characters
    content = re.sub(r'[\x00-\x1F\x7F\x80-\x9F]', '', content)

    # Clean up excessive whitespace and empty lines
    lines = content.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line:  # Only keep non-empty lines
            cleaned_lines.append(line)

    # Join back with proper spacing
    content = '\n\n'.join(cleaned_lines)

    return content

def extract_title(content):
    """Extract title from content"""
    lines = content.split('\n')

    for line in lines[:20]:
        line = line.strip()
        if 'QUY TRÌNH' in line.upper() and len(line) > 10:
            # Get the next few lines for complete title
            title_parts = []
            for i, next_line in enumerate(lines[lines.index(line):lines.index(line)+5]):
                next_line = next_line.strip()
                if next_line and not next_line.startswith('Mã hiệu:') and not next_line.startswith('Lần ban hành:'):
                    title_parts.append(next_line)
                if len(title_parts) >= 3 or next_line.startswith('Mã hiệu:'):
                    break

            return ' '.join(title_parts).strip()

    return "Quy trình hành chính"

def extract_procedure_code(content):
    """Extract procedure code"""
    match = re.search(r'Mã hiệu:\s*([^\n]+)', content)
    if match:
        return match.group(1).strip()
    return ""

def create_clean_json(content, filename, title, procedure_code):
    """Create clean JSON from processed content"""

    # Create the JSON structure
    json_data = {
        "title": title,
        "description": f"Quy trình {title.lower()} tại UBND cấp xã",
        "procedure_code": procedure_code or f"QT {filename.split()[0]}/CX-HT",
        "processing_time": "Theo quy định pháp luật",
        "full_content": content,
        "metadata": {
            "source_file": filename,
            "processing_date": datetime.now().isoformat(),
            "content_length": len(content),
            "extraction_method": "txt_to_json",
            "content_type": "legal_procedure"
        }
    }

    return json_data

def process_txt_to_json(txt_path, output_dir):
    """Process text file to JSON"""
    try:
        filename = os.path.basename(txt_path)
        base_name = os.path.splitext(filename)[0]

        print(f"Processing: {filename}")

        # Read and clean content
        content = read_and_clean_txt_file(txt_path)
        print(f"Content length: {len(content)} characters")

        # Extract information
        title = extract_title(content)
        procedure_code = extract_procedure_code(content)

        print(f"Title: {title}")
        print(f"Procedure code: {procedure_code}")

        # Create JSON
        json_data = create_clean_json(content, base_name, title, procedure_code)

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Save to JSON file
        output_file = os.path.join(output_dir, f"{base_name}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved to: {output_file}")
        return True

    except Exception as e:
        print(f"❌ Error processing {txt_path}: {e}")
        return False

def main():
    """Main processing function"""
    input_dir = r"d:\Personal\LegalRAG_Fixed"
    output_dir = r"d:\Personal\LegalRAG_Fixed\processed_from_txt"

    # Process temp_doc_001_content.txt
    txt_path = os.path.join(input_dir, "temp_doc_001_content.txt")

    if os.path.exists(txt_path):
        success = process_txt_to_json(txt_path, output_dir)
        if success:
            print("\n🎉 Processing completed successfully!")
            print("JSON file created from text content.")
        else:
            print("\n❌ Processing failed!")
    else:
        print(f"File not found: {txt_path}")

if __name__ == "__main__":
    main()
