#!/usr/bin/env python3
"""
LegalRAG Chunk Creator
======================
Extract text from PDFs and DOC files, split into chunks, and create embeddings.

Usage:
    python create_chunks.py [--batch-size 10]
"""

import os
import sys
import uuid
import json
import logging
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import argparse

# Third-party imports
try:
    import psycopg2
    from psycopg2.extras import execute_values
    import requests
    from tqdm import tqdm
    import fitz  # PyMuPDF for PDF text extraction
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install psycopg2-binary requests tqdm pymupdf")
    sys.exit(1)

# ============================================
# Configuration
# ============================================

# Database
DB_HOST = os.getenv("DB_HOST", "legalrag-postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "legalrag")
DB_USER = os.getenv("DB_USER", "legalrag")
DB_PASSWORD = os.getenv("DB_PASSWORD", "legalrag123")

# Embedding service
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://legalrag-embedding:8011")

# Chunk settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))  # characters
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))  # characters
MIN_CHUNK_SIZE = 100  # minimum characters for a valid chunk

# Paths
PDF_DIR = Path("/app/output")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================
# Text Processing
# ============================================

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text content from PDF file."""
    try:
        doc = fitz.open(str(pdf_path))
        text_parts = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                text_parts.append(text)
        
        doc.close()
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return ""


def extract_text_from_doc(doc_path: Path) -> str:
    """Extract text content from DOC file using antiword or catdoc."""
    try:
        # Try antiword first
        try:
            result = subprocess.run(
                ["antiword", str(doc_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        except FileNotFoundError:
            pass
        
        # Try catdoc as fallback
        try:
            result = subprocess.run(
                ["catdoc", str(doc_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        except FileNotFoundError:
            pass
        
        logger.error(f"No DOC reader available (antiword/catdoc) for {doc_path}")
        return ""
    except Exception as e:
        logger.error(f"Error extracting text from {doc_path}: {e}")
        return ""


def extract_text_from_file(file_path: Path) -> str:
    """Extract text from PDF or DOC file."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in [".doc", ".docx"]:
        return extract_text_from_doc(file_path)
    else:
        logger.warning(f"Unsupported file type: {suffix}")
        return ""


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\t+', ' ', text)
    
    # Remove page numbers and headers/footers patterns
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    
    # Normalize Vietnamese text
    text = text.strip()
    
    return text


def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> List[Dict]:
    """
    Split text into overlapping chunks.
    
    Returns:
        List of dicts with 'content' and 'chunk_index'
    """
    if not text or len(text) < MIN_CHUNK_SIZE:
        return []
    
    chunks = []
    
    # Try to split by paragraphs first
    paragraphs = text.split('\n\n')
    
    current_chunk = ""
    chunk_index = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding this paragraph exceeds chunk size
        if len(current_chunk) + len(para) + 2 > chunk_size:
            if current_chunk and len(current_chunk) >= MIN_CHUNK_SIZE:
                chunks.append({
                    "content": current_chunk.strip(),
                    "chunk_index": chunk_index
                })
                chunk_index += 1
                
                # Start new chunk with overlap
                words = current_chunk.split()
                overlap_words = words[-overlap // 5:] if len(words) > overlap // 5 else []
                current_chunk = " ".join(overlap_words) + "\n\n" + para
            else:
                current_chunk = para
        else:
            current_chunk = (current_chunk + "\n\n" + para).strip()
    
    # Don't forget the last chunk
    if current_chunk and len(current_chunk) >= MIN_CHUNK_SIZE:
        chunks.append({
            "content": current_chunk.strip(),
            "chunk_index": chunk_index
        })
    
    # If no chunks were created (text too short or no paragraphs), create one chunk
    if not chunks and len(text) >= MIN_CHUNK_SIZE:
        chunks.append({
            "content": text.strip(),
            "chunk_index": 0
        })
    
    return chunks


# ============================================
# Embedding Service
# ============================================

class EmbeddingClient:
    """Client for embedding service."""
    
    def __init__(self, base_url: str = EMBEDDING_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """Check if embedding service is healthy."""
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Embedding service health check failed: {e}")
            return False
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        if not texts:
            return []
        
        try:
            # Use /embed-batch endpoint for multiple texts
            resp = self.session.post(
                f"{self.base_url}/embed-batch",
                json={"texts": texts},
                timeout=120  # Longer timeout for batch processing
            )
            resp.raise_for_status()
            
            data = resp.json()
            return data.get("embeddings", [])
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            return []


# ============================================
# Database Operations
# ============================================

class ChunkManager:
    """Manage chunk operations in database."""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info("🔌 Connected to PostgreSQL")
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("🔌 Disconnected from PostgreSQL")
    
    def get_documents_without_chunks(self) -> List[Dict]:
        """Get documents that don't have chunks yet."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT d.id, d.title, d.filename, d.file_path, c.name as collection_name
                FROM documents d
                JOIN collections c ON d.collection_id = c.id
                WHERE d.chunk_count = 0 OR d.chunk_count IS NULL
                ORDER BY c.name, d.title
            """)
            
            columns = ['id', 'title', 'filename', 'file_path', 'collection_name']
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def insert_chunks(self, document_id: str, chunks: List[Dict]) -> int:
        """
        Insert chunks with embeddings into database.
        
        Args:
            document_id: UUID of the document
            chunks: List of dicts with 'content', 'chunk_index', 'embedding'
        
        Returns:
            Number of chunks inserted
        """
        if not chunks:
            return 0
        
        with self.conn.cursor() as cur:
            # Prepare data for batch insert
            values = []
            for chunk in chunks:
                embedding = chunk.get('embedding')
                if embedding:
                    # Convert to PostgreSQL vector format
                    embedding_str = f"[{','.join(map(str, embedding))}]"
                else:
                    embedding_str = None
                
                values.append((
                    str(uuid.uuid4()),
                    document_id,
                    chunk['chunk_index'],
                    chunk['content'],
                    chunk.get('section_title'),
                    chunk.get('source_reference'),
                    embedding_str,
                    json.dumps(chunk.get('metadata', {}))
                ))
            
            # Batch insert
            execute_values(
                cur,
                """
                INSERT INTO chunks (id, document_id, chunk_index, content, section_title, source_reference, embedding, metadata)
                VALUES %s
                ON CONFLICT (document_id, chunk_index) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
                """,
                values,
                template="(%s, %s, %s, %s, %s, %s, %s::vector, %s::jsonb)"
            )
            
            self.conn.commit()
            return len(values)
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM documents) as documents,
                    (SELECT COUNT(*) FROM documents WHERE chunk_count > 0) as docs_with_chunks,
                    (SELECT COUNT(*) FROM chunks) as total_chunks,
                    (SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL) as chunks_with_embeddings
            """)
            row = cur.fetchone()
            return {
                "documents": row[0],
                "docs_with_chunks": row[1],
                "total_chunks": row[2],
                "chunks_with_embeddings": row[3]
            }


# ============================================
# Main Processing
# ============================================

def find_file_for_document(doc: Dict, file_dir: Path) -> Optional[Path]:
    """Find the PDF or DOC file for a document."""
    filename = doc['filename']
    
    # Try exact filename match first
    exact_path = file_dir / filename
    if exact_path.exists():
        return exact_path
    
    # Try with .pdf extension (for converted files)
    if filename.endswith('.doc'):
        pdf_name = filename[:-4] + '.pdf'
    elif filename.endswith('.docx'):
        pdf_name = filename[:-5] + '.pdf'
    else:
        pdf_name = filename if filename.endswith('.pdf') else filename + '.pdf'
    
    pdf_path = file_dir / pdf_name
    if pdf_path.exists():
        return pdf_path
    
    # Try file_path if available
    if doc.get('file_path'):
        file_path = Path(doc['file_path'])
        if file_path.exists():
            return file_path
    
    # Try searching by title in PDF files
    title = doc['title']
    for pdf_file in file_dir.glob("*.pdf"):
        if title in pdf_file.stem:
            return pdf_file
    
    # Try searching by title in DOC files
    for doc_file in file_dir.glob("*.doc"):
        if title in doc_file.stem:
            return doc_file
    
    return None


def process_document(
    doc: Dict,
    pdf_dir: Path,
    embedding_client: EmbeddingClient,
    chunk_manager: ChunkManager,
    batch_size: int = 10
) -> Tuple[int, int]:
    """
    Process a single document: extract text, create chunks, embed, save.
    
    Returns:
        (chunks_created, embeddings_created)
    """
    file_path = find_file_for_document(doc, pdf_dir)
    
    if not file_path:
        logger.warning(f"⚠️ File not found for: {doc['title']}")
        return 0, 0
    
    # Extract text (supports PDF and DOC)
    text = extract_text_from_file(file_path)
    if not text:
        logger.warning(f"⚠️ No text extracted from: {file_path.name}")
        return 0, 0
    
    # Clean text
    text = clean_text(text)
    
    # Split into chunks
    chunks = split_into_chunks(text)
    if not chunks:
        logger.warning(f"⚠️ No chunks created for: {doc['title']}")
        return 0, 0
    
    # Get embeddings in batches
    embeddings_created = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c['content'] for c in batch]
        
        embeddings = embedding_client.get_embeddings(texts)
        
        if embeddings and len(embeddings) == len(batch):
            for j, emb in enumerate(embeddings):
                batch[j]['embedding'] = emb
                embeddings_created += 1
    
    # Add metadata
    for chunk in chunks:
        chunk['metadata'] = {
            'source_file': doc['filename'],
            'collection': doc['collection_name'],
            'char_count': len(chunk['content'])
        }
    
    # Save to database
    chunks_saved = chunk_manager.insert_chunks(doc['id'], chunks)
    
    return chunks_saved, embeddings_created


def main():
    parser = argparse.ArgumentParser(description="Create chunks and embeddings for documents")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for embedding")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of documents to process (0=all)")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🚀 LegalRAG Chunk Creator Started")
    logger.info("=" * 60)
    
    # Initialize clients
    embedding_client = EmbeddingClient()
    if not embedding_client.health_check():
        logger.error("❌ Embedding service is not available!")
        sys.exit(1)
    logger.info("✅ Embedding service is healthy")
    
    chunk_manager = ChunkManager()
    
    try:
        # Get initial stats
        stats = chunk_manager.get_stats()
        logger.info(f"📊 Initial stats: {stats}")
        
        # Get documents without chunks
        documents = chunk_manager.get_documents_without_chunks()
        if args.limit > 0:
            documents = documents[:args.limit]
        
        logger.info(f"📄 Found {len(documents)} documents to process")
        
        if not documents:
            logger.info("✅ All documents already have chunks!")
            return
        
        # Process each document
        total_chunks = 0
        total_embeddings = 0
        failed = 0
        
        for doc in tqdm(documents, desc="Processing documents"):
            try:
                chunks, embeddings = process_document(
                    doc,
                    PDF_DIR,
                    embedding_client,
                    chunk_manager,
                    args.batch_size
                )
                total_chunks += chunks
                total_embeddings += embeddings
                
                if chunks > 0:
                    logger.info(f"✅ {doc['title']}: {chunks} chunks, {embeddings} embeddings")
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing {doc['title']}: {e}")
                failed += 1
        
        # Final stats
        logger.info("=" * 60)
        logger.info("✅ Processing Complete!")
        logger.info("=" * 60)
        
        final_stats = chunk_manager.get_stats()
        logger.info(f"📊 Final stats:")
        logger.info(f"   Documents with chunks: {final_stats['docs_with_chunks']}/{final_stats['documents']}")
        logger.info(f"   Total chunks: {final_stats['total_chunks']}")
        logger.info(f"   Chunks with embeddings: {final_stats['chunks_with_embeddings']}")
        logger.info(f"   Failed documents: {failed}")
        
    finally:
        chunk_manager.close()


if __name__ == "__main__":
    main()
