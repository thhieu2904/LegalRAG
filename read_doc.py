import win32com.client
import os
import json
import sys

def read_word_document(file_path):
    """Read Word document content using COM objects with proper error handling"""
    word_app = None
    doc = None

    try:
        # Create Word application
        word_app = win32com.client.Dispatch("Word.Application")
        word_app.Visible = False

        # Open document
        doc = word_app.Documents.Open(file_path)

        # Read content
        content = doc.Content.Text

        return content

    except Exception as e:
        print(f"Error reading document: {e}")
        return None

    finally:
        # Clean up
        try:
            if doc:
                doc.Close(SaveChanges=False)
        except:
            pass

        try:
            if word_app:
                word_app.Quit()
        except:
            pass

def main():
    if len(sys.argv) != 2:
        print("Usage: python read_doc.py <doc_file_path>")
        return

    doc_path = sys.argv[1]

    if not os.path.exists(doc_path):
        print(f"File not found: {doc_path}")
        return

    print(f"Reading document: {doc_path}")
    content = read_word_document(doc_path)

    if content:
        print(f"Successfully read {len(content)} characters")
        print("Content preview (first 500 chars):")
        print(content[:500])
        print("...")

        # Save to a temp file for processing
        temp_file = "temp_doc_content.txt"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Content saved to: {temp_file}")
    else:
        print("Failed to read document")

if __name__ == "__main__":
    main()
