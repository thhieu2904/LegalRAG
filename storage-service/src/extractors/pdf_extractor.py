"""
PDF Text Extractor
Extract text content from PDF files
"""
import PyPDF2
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF files"""
    
    @staticmethod
    def extract_text(pdf_data: bytes) -> str:
        """
        Extract text from PDF
        
        Args:
            pdf_data: PDF file content as bytes
        
        Returns:
            Extracted text
        """
        try:
            pdf_file = BytesIO(pdf_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.extract_text()
            
            logger.info(f"✅ Extracted {len(pdf_reader.pages)} pages from PDF")
            return text
        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {e}")
            raise
    
    @staticmethod
    def extract_metadata(pdf_data: bytes) -> dict:
        """Extract PDF metadata"""
        try:
            pdf_file = BytesIO(pdf_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            metadata = pdf_reader.metadata or {}
            return {
                "pages": len(pdf_reader.pages),
                "title": metadata.get("/Title", ""),
                "author": metadata.get("/Author", ""),
                "subject": metadata.get("/Subject", ""),
                "producer": metadata.get("/Producer", "")
            }
        except Exception as e:
            logger.error(f"❌ Metadata extraction failed: {e}")
            return {}
