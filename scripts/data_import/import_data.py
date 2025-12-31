#!/usr/bin/env python3
"""
LegalRAG Data Import Script
===========================
Converts .doc files to PDF and imports them into the system.

Features:
- Batch convert .doc → .pdf using LibreOffice
- Upload PDFs to MinIO storage
- Create collections and documents in PostgreSQL
- Generate text chunks for vector search

Usage:
    python import_data.py [--dry-run] [--skip-convert]
"""

import os
import sys
import json
import uuid
import subprocess
import logging
import re
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse

# Third-party imports
try:
    import psycopg2
    from psycopg2.extras import execute_values
    from minio import Minio
    from minio.error import S3Error
    from tqdm import tqdm
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install psycopg2-binary minio tqdm")
    sys.exit(1)


# ============================================
# Helper Functions
# ============================================

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for MinIO storage.
    - Convert Vietnamese characters to ASCII
    - Remove special characters
    - Replace spaces with underscores
    - Limit length
    """
    # Vietnamese character mapping (including Đ/đ which NFD doesn't handle)
    vietnamese_map = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'À': 'A', 'Á': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
        'Ă': 'A', 'Ằ': 'A', 'Ắ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A',
        'Â': 'A', 'Ầ': 'A', 'Ấ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',
        'đ': 'd', 'Đ': 'D',  # Important: Đ is NOT handled by NFD!
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'È': 'E', 'É': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
        'Ê': 'E', 'Ề': 'E', 'Ế': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'Ì': 'I', 'Í': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'Ò': 'O', 'Ó': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
        'Ô': 'O', 'Ồ': 'O', 'Ố': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O',
        'Ơ': 'O', 'Ờ': 'O', 'Ớ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'Ù': 'U', 'Ú': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
        'Ư': 'U', 'Ừ': 'U', 'Ứ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'Ỳ': 'Y', 'Ý': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y',
    }
    
    # First, replace Vietnamese characters directly
    result = []
    for char in filename:
        if char in vietnamese_map:
            result.append(vietnamese_map[char])
        else:
            result.append(char)
    filename = ''.join(result)
    
    # Normalize unicode and remove any remaining diacritics
    filename = unicodedata.normalize('NFD', filename)
    filename = ''.join(c for c in filename if not unicodedata.combining(c))
    
    # Replace problematic characters (keep alphanumeric, spaces, hyphens, dots)
    filename = re.sub(r'[^\w\s\-\.]', '', filename, flags=re.ASCII)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Limit length (keep extension)
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    return name + ext


# ============================================
# Configuration
# ============================================

# Database settings
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "legalrag-postgres"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "legalrag"),
    "user": os.getenv("POSTGRES_USER", "legalrag"),
    "password": os.getenv("POSTGRES_PASSWORD", "legalrag123"),
}

# MinIO settings
MINIO_CONFIG = {
    "endpoint": os.getenv("MINIO_ENDPOINT", "legalrag-minio:9000"),
    "access_key": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    "secret_key": os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
    "secure": os.getenv("MINIO_SECURE", "false").lower() == "true",
    "bucket": os.getenv("MINIO_BUCKET", "legal-documents"),
}

# Paths
INPUT_DIR = Path(os.getenv("INPUT_DIR", "/app/input"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/output"))
MAPPING_FILE = Path(os.getenv("MAPPING_FILE", "/app/collections_mapping.json"))
LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))

# ============================================
# Logging Setup
# ============================================

LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ============================================
# Document Converter
# ============================================

class DocumentConverter:
    """Converts Word documents to PDF using LibreOffice."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_to_pdf(self, input_path: Path) -> Optional[Path]:
        """
        Convert a .doc/.docx file to PDF.
        
        Args:
            input_path: Path to the input Word document
            
        Returns:
            Path to the output PDF, or None if conversion failed
        """
        # Check if PDF already exists (skip conversion)
        pdf_name = input_path.stem + ".pdf"
        pdf_path = self.output_dir / pdf_name
        
        if pdf_path.exists():
            logger.info(f"⏭️ Skipped (exists): {pdf_name}")
            return pdf_path
        
        # Create temp copy with ASCII filename for LibreOffice
        import shutil
        import hashlib
        import signal
        temp_name = hashlib.md5(str(input_path).encode()).hexdigest() + ".doc"
        temp_path = self.output_dir / temp_name
        temp_pdf = self.output_dir / (temp_name.replace('.doc', '.pdf'))
        
        process = None
        try:
            # Copy to temp location
            shutil.copy2(input_path, temp_path)
            
            # Run LibreOffice in headless mode with Popen for better timeout handling
            cmd = [
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(self.output_dir),
                str(temp_path),
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,  # Create new process group for killpg
            )
            
            try:
                stdout, stderr = process.communicate(timeout=30)  # 30 seconds timeout
            except subprocess.TimeoutExpired:
                # Kill the entire process group
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except:
                    process.kill()
                process.wait()
                logger.warning(f"⏰ Timeout for {input_path.name} (>30s) - skipping")
                # Clean up
                if temp_path.exists():
                    temp_path.unlink()
                if temp_pdf.exists():
                    temp_pdf.unlink()
                return None
            
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            
            if process.returncode != 0:
                logger.error(f"Conversion failed for {input_path.name}: {stderr}")
                if temp_pdf.exists():
                    temp_pdf.unlink()
                return None
            
            # Rename temp PDF to proper name
            if temp_pdf.exists():
                shutil.move(str(temp_pdf), str(pdf_path))
                logger.info(f"✅ Converted: {input_path.name} → {pdf_name}")
                return pdf_path
            else:
                logger.error(f"PDF not found after conversion: {pdf_path}")
                return None

        except Exception as e:
            logger.error(f"❌ Error for {input_path.name}: {e}")
            # Clean up
            if process:
                try:
                    process.kill()
                except:
                    pass
            if temp_path.exists():
                temp_path.unlink()
            if temp_pdf.exists():
                temp_pdf.unlink()
            return None

    def batch_convert(self, input_files: List[Path]) -> Dict[Path, Path]:
        """
        Convert multiple files to PDF.
        
        Returns:
            Dict mapping input paths to output PDF paths
        """
        results = {}
        
        logger.info(f"📄 Converting {len(input_files)} documents to PDF...")
        
        for input_path in tqdm(input_files, desc="Converting"):
            pdf_path = self.convert_to_pdf(input_path)
            if pdf_path:
                results[input_path] = pdf_path
        
        success_count = len(results)
        fail_count = len(input_files) - success_count
        
        logger.info(f"📊 Conversion complete: {success_count} success, {fail_count} failed")
        
        return results


# ============================================
# MinIO Storage Handler
# ============================================

class StorageHandler:
    """Handles file uploads to MinIO."""

    def __init__(self, config: dict):
        self.client = Minio(
            endpoint=config["endpoint"],
            access_key=config["access_key"],
            secret_key=config["secret_key"],
            secure=config["secure"],
        )
        self.bucket = config["bucket"]
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(bucket_name=self.bucket):
                self.client.make_bucket(bucket_name=self.bucket)
                logger.info(f"📦 Created bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"MinIO bucket error: {e}")
            raise

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """
        Upload a file to MinIO.
        
        Args:
            local_path: Local file path
            remote_path: Remote path in bucket
            
        Returns:
            True if upload successful
        """
        try:
            self.client.fput_object(
                bucket_name=self.bucket,
                object_name=remote_path,
                file_path=str(local_path),
                content_type="application/pdf",
            )
            logger.debug(f"Uploaded: {remote_path}")
            return True
        except S3Error as e:
            logger.error(f"Upload failed for {local_path.name}: {e}")
            return False

    def clear_bucket(self):
        """Delete all objects in the bucket."""
        try:
            objects = self.client.list_objects(bucket_name=self.bucket, recursive=True)
            for obj in objects:
                self.client.remove_object(bucket_name=self.bucket, object_name=obj.object_name)
            logger.info(f"🗑️ Cleared bucket: {self.bucket}")
        except S3Error as e:
            logger.error(f"Failed to clear bucket: {e}")


# ============================================
# Database Handler
# ============================================

class DatabaseHandler:
    """Handles PostgreSQL database operations."""

    def __init__(self, config: dict):
        self.config = config
        self.conn = None

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**self.config)
            logger.info("🔌 Connected to PostgreSQL")
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("🔌 Disconnected from PostgreSQL")

    def cleanup_data(self):
        """Delete all existing data."""
        with self.conn.cursor() as cur:
            # Disable triggers for faster deletion
            cur.execute("ALTER TABLE chunks DISABLE TRIGGER ALL")
            cur.execute("ALTER TABLE documents DISABLE TRIGGER ALL")
            cur.execute("ALTER TABLE forms DISABLE TRIGGER ALL")

            # Truncate tables
            cur.execute("TRUNCATE TABLE system_metrics CASCADE")
            cur.execute("TRUNCATE TABLE admin_logs CASCADE")
            cur.execute("TRUNCATE TABLE query_logs CASCADE")
            cur.execute("TRUNCATE TABLE query_sessions CASCADE")
            cur.execute("TRUNCATE TABLE forms CASCADE")
            cur.execute("TRUNCATE TABLE chunks CASCADE")
            cur.execute("TRUNCATE TABLE documents CASCADE")
            cur.execute("TRUNCATE TABLE collections CASCADE")

            # Re-enable triggers
            cur.execute("ALTER TABLE chunks ENABLE TRIGGER ALL")
            cur.execute("ALTER TABLE documents ENABLE TRIGGER ALL")
            cur.execute("ALTER TABLE forms ENABLE TRIGGER ALL")

            self.conn.commit()
            logger.info("🗑️ Cleaned up all existing data")

    def create_collection(self, collection_data: dict) -> str:
        """
        Create a new collection.
        
        Returns:
            UUID of the created collection
        """
        collection_id = str(uuid.uuid4())
        
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO collections (id, name, display_name, description, icon, color)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    description = EXCLUDED.description,
                    icon = EXCLUDED.icon,
                    color = EXCLUDED.color
                RETURNING id
                """,
                (
                    collection_id,
                    collection_data["name"],
                    collection_data["display_name"],
                    collection_data["description"],
                    collection_data["icon"],
                    collection_data["color"],
                ),
            )
            result = cur.fetchone()
            self.conn.commit()
            
            return str(result[0])

    def create_document(
        self,
        collection_id: str,
        title: str,
        filename: str,
        file_path: str,
        file_size: int,
    ) -> str:
        """
        Create a new document.
        
        Returns:
            UUID of the created document
        """
        document_id = str(uuid.uuid4())
        
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (id, collection_id, title, filename, file_path, file_size)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (document_id, collection_id, title, filename, file_path, file_size),
            )
            result = cur.fetchone()
            self.conn.commit()
            
            return str(result[0])

    def get_stats(self) -> dict:
        """Get current database statistics."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    (SELECT COUNT(*) FROM collections) as collections,
                    (SELECT COUNT(*) FROM documents) as documents,
                    (SELECT COUNT(*) FROM chunks) as chunks,
                    (SELECT COUNT(*) FROM forms) as forms
                """
            )
            result = cur.fetchone()
            return {
                "collections": result[0],
                "documents": result[1],
                "chunks": result[2],
                "forms": result[3],
            }


# ============================================
# Main Import Logic
# ============================================

class DataImporter:
    """Main class for importing legal documents."""

    def __init__(self, dry_run: bool = False, skip_convert: bool = False):
        self.dry_run = dry_run
        self.skip_convert = skip_convert
        
        self.converter = DocumentConverter(OUTPUT_DIR)
        self.storage = None
        self.db = None
        
        # Load collection mapping
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            self.mapping = json.load(f)

    def setup(self):
        """Initialize connections."""
        if not self.dry_run:
            self.storage = StorageHandler(MINIO_CONFIG)
            self.db = DatabaseHandler(DB_CONFIG)
            self.db.connect()

    def cleanup(self):
        """Clean up connections."""
        if self.db:
            self.db.close()

    def scan_input_files(self) -> Dict[str, List[Path]]:
        """
        Scan input directory for Word documents.
        
        Returns:
            Dict mapping folder names to list of file paths
        """
        files_by_folder = {}
        
        for folder in INPUT_DIR.iterdir():
            if folder.is_dir():
                doc_files = list(folder.glob("*.doc")) + list(folder.glob("*.docx"))
                if doc_files:
                    files_by_folder[folder.name] = doc_files
                    logger.info(f"📁 {folder.name}: {len(doc_files)} files")
        
        total = sum(len(files) for files in files_by_folder.values())
        logger.info(f"📊 Total: {total} documents in {len(files_by_folder)} folders")
        
        return files_by_folder

    def get_collection_for_folder(self, folder_name: str) -> Optional[dict]:
        """Get collection mapping for a folder."""
        for collection in self.mapping["collections"]:
            if collection["folder_name"] == folder_name:
                return collection
        return None

    def run(self):
        """Execute the import process."""
        logger.info("=" * 60)
        logger.info("🚀 LegalRAG Data Import Started")
        logger.info("=" * 60)
        
        if self.dry_run:
            logger.info("⚠️ DRY RUN MODE - No changes will be made")
        
        try:
            self.setup()
            
            # Step 1: Scan input files
            files_by_folder = self.scan_input_files()
            
            if not files_by_folder:
                logger.error("No input files found!")
                return
            
            # Step 2: Clean up existing data
            if not self.dry_run:
                logger.info("\n📋 Step 1: Cleaning up existing data...")
                self.db.cleanup_data()
                self.storage.clear_bucket()
            
            # Step 3: Process each folder
            logger.info("\n📋 Step 2: Processing folders...")
            
            total_docs = 0
            
            for folder_name, doc_files in files_by_folder.items():
                collection_data = self.get_collection_for_folder(folder_name)
                
                if not collection_data:
                    logger.warning(f"⚠️ No mapping found for folder: {folder_name}")
                    continue
                
                logger.info(f"\n📂 Processing: {collection_data['display_name']}")
                
                # Create collection
                if not self.dry_run:
                    collection_id = self.db.create_collection(collection_data)
                    logger.info(f"   Created collection: {collection_id}")
                else:
                    collection_id = "dry-run-id"
                
                # Convert and upload documents
                if not self.skip_convert:
                    converted = self.converter.batch_convert(doc_files)
                else:
                    # Assume PDFs already exist
                    converted = {
                        doc: OUTPUT_DIR / (doc.stem + ".pdf")
                        for doc in doc_files
                        if (OUTPUT_DIR / (doc.stem + ".pdf")).exists()
                    }
                
                # Upload and create documents
                for original_path, pdf_path in converted.items():
                    if not pdf_path.exists():
                        continue
                    
                    # Generate title from filename (keep original for display)
                    title = original_path.stem.replace("_", " ").strip()
                    filename = pdf_path.name
                    file_size = pdf_path.stat().st_size
                    
                    # Sanitize filename for MinIO (avoid special characters)
                    safe_filename = sanitize_filename(filename)
                    
                    # Remote path in MinIO
                    remote_path = f"collections/{collection_data['name']}/{uuid.uuid4()}_{safe_filename}"
                    
                    if not self.dry_run:
                        # Upload to MinIO
                        if self.storage.upload_file(pdf_path, remote_path):
                            # Create document record
                            doc_id = self.db.create_document(
                                collection_id=collection_id,
                                title=title,
                                filename=filename,  # Keep original filename in DB
                                file_path=remote_path,
                                file_size=file_size,
                            )
                            total_docs += 1
                    else:
                        total_docs += 1
                        logger.debug(f"   [DRY RUN] Would import: {title}")
            
            # Step 4: Print summary
            logger.info("\n" + "=" * 60)
            logger.info("✅ Import Complete!")
            logger.info("=" * 60)
            
            if not self.dry_run:
                stats = self.db.get_stats()
                logger.info(f"📊 Final Statistics:")
                logger.info(f"   Collections: {stats['collections']}")
                logger.info(f"   Documents: {stats['documents']}")
                logger.info(f"   Chunks: {stats['chunks']} (pending embedding)")
            else:
                logger.info(f"📊 Would import: {total_docs} documents")
            
            logger.info(f"\n📝 Log saved to: {log_file}")

        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            raise
        finally:
            self.cleanup()


# ============================================
# Entry Point
# ============================================

def main():
    parser = argparse.ArgumentParser(description="LegalRAG Data Import Tool")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate import without making changes",
    )
    parser.add_argument(
        "--skip-convert",
        action="store_true",
        help="Skip PDF conversion (use existing PDFs)",
    )
    args = parser.parse_args()
    
    importer = DataImporter(
        dry_run=args.dry_run,
        skip_convert=args.skip_convert,
    )
    importer.run()


if __name__ == "__main__":
    main()
