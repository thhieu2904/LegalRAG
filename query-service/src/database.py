"""
PostgreSQL Database Helper
Fetch document metadata from main database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DatabaseClient:
    """PostgreSQL client for document metadata"""
    
    def __init__(self, host: str, port: int, user: str, password: str, dbname: str):
        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "dbname": dbname
        }
        logger.info(f"📊 DatabaseClient initialized: {user}@{host}:{port}/{dbname}")
    
    def fetch_document_titles(self, doc_ids: List[str]) -> Dict[str, str]:
        """
        Batch fetch document titles
        
        Args:
            doc_ids: List of document UUIDs
            
        Returns:
            Dict mapping document_id → title
        """
        if not doc_ids:
            return {}
        
        try:
            conn = psycopg2.connect(**self.config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Use ANY for PostgreSQL array matching
            cursor.execute(
                "SELECT id, title FROM documents WHERE id = ANY(%s)",
                (doc_ids,)
            )
            
            results = cursor.fetchall()
            
            # Convert to dict
            title_map = {str(row['id']): row['title'] for row in results}
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Fetched {len(title_map)} document titles")
            return title_map
            
        except Exception as e:
            logger.error(f"❌ Database query failed: {e}")
            return {}
