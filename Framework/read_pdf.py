from pypdf import PdfReader
import sys

def extract_text(pdf_path, output_path):
    try:
        reader = PdfReader(pdf_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, page in enumerate(reader.pages):
                f.write(f"--- Page {i+1} ---\n")
                text = page.extract_text()
                if text:
                    f.write(text)
                f.write("\n\n")
        print(f"Successfully extracted text to {output_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_text("Major Project Report D5 Draft Ver 5.pdf", "report_content.txt")
