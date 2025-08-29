import win32com.client
import os

def read_word_to_txt(doc_path, txt_path):
    """Read Word document and save to text file"""
    try:
        # Initialize Word application
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False

        # Open document
        doc = word.Documents.Open(doc_path)

        # Get all text
        content = doc.Content.Text

        # Close document
        doc.Close()
        word.Quit()

        # Save to text file
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Successfully saved content to: {txt_path}")
        print(f"Content length: {len(content)} characters")

        return True

    except Exception as e:
        print(f"❌ Error reading {doc_path}: {e}")
        return False

def main():
    """Main function"""
    input_dir = r"d:\Personal\LegalRAG_Fixed"
    output_dir = r"d:\Personal\LegalRAG_Fixed"

    # Process temp_doc_001.doc
    doc_path = os.path.join(input_dir, "temp_doc_001.doc")
    txt_path = os.path.join(output_dir, "temp_doc_001_content.txt")

    if os.path.exists(doc_path):
        print(f"Reading Word document: {doc_path}")
        success = read_word_to_txt(doc_path, txt_path)
        if success:
            print("🎉 Word to text conversion completed!")
        else:
            print("❌ Failed to convert Word to text!")
    else:
        print(f"File not found: {doc_path}")

if __name__ == "__main__":
    main()
