"""
PostgreSQL pgvector Database Client
"""
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from typing import List, Dict, Any, Optional
import logging
import uuid

logger = logging.getLogger(__name__)


class VectorDatabase:
    """PostgreSQL pgvector database client"""
    
    def __init__(self, host: str, port: int, user: str, password: str, dbname: str):
        """Initialize database connection"""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = dbname
        self.connection = None
    
    def connect(self):
        """Connect to database"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.dbname
            )
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("✅ Disconnected from PostgreSQL")
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute query and return cursor"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            self.connection.commit()
            return cursor
        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Query failed: {e}")
            raise
    
    def insert_chunk(self, document_id: str, chunk_index: int, content: str, 
                    embedding: List[float], metadata: Optional[dict] = None) -> str:
        """Insert single chunk with embedding"""
        try:
            vector_id = str(uuid.uuid4())
            
            query = """
            INSERT INTO chunks (id, document_id, chunk_index, content, embedding, chunk_metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor = self.execute_query(
                query,
                (vector_id, document_id, chunk_index, content, embedding, metadata or {})
            )
            
            logger.info(f"✅ Inserted chunk: {vector_id}")
            return vector_id
        
        except Exception as e:
            logger.error(f"❌ Insert failed: {e}")
            raise
    
    def insert_batch_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Insert multiple chunks"""
        try:
            inserted = 0
            failed = 0
            
            for chunk in chunks:
                try:
                    self.insert_chunk(
                        document_id=chunk["document_id"],
                        chunk_index=chunk["chunk_index"],
                        content=chunk["content"],
                        embedding=chunk["embedding"],
                        metadata=chunk.get("metadata")
                    )
                    inserted += 1
                except Exception as e:
                    logger.warning(f"⚠️  Failed to insert chunk: {e}")
                    failed += 1
            
            logger.info(f"✅ Batch insert: {inserted} succeeded, {failed} failed")
            return {
                "inserted": inserted,
                "failed": failed,
                "total": len(chunks)
            }
        
        except Exception as e:
            logger.error(f"❌ Batch insert failed: {e}")
            raise
    
    def search_similar(self, embedding: List[float], top_k: int = 10, 
                      threshold: float = 0.7, document_ids: Optional[List[str]] = None) -> List[Dict]:
        """Search similar chunks"""
        try:
            # Convert list to pgvector format
            embedding_str = str(embedding)
            
            # Build query
            query = """
            SELECT 
                id as vector_id,
                document_id,
                chunk_index,
                content,
                1 - (embedding <=> %s::vector) as similarity
            FROM chunks
            WHERE is_deleted = false
            """
            
            params = [embedding_str]
            
            # Optional filter by document_ids
            if document_ids:
                placeholders = ','.join(['%s'] * len(document_ids))
                query += f" AND document_id IN ({placeholders})"
                params.extend(document_ids)
            
            query += f"""
            AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """
            
            params.extend([embedding_str, threshold, embedding_str, top_k])
            
            cursor = self.execute_query(query, tuple(params))
            results = cursor.fetchall()
            
            logger.info(f"✅ Search found {len(results)} similar chunks")
            return [dict(row) for row in results]
        
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise
    
    def delete_vectors(self, vector_ids: Optional[List[str]] = None, 
                      document_id: Optional[str] = None) -> int:
        """Soft delete vectors"""
        try:
            if vector_ids:
                placeholders = ','.join(['%s'] * len(vector_ids))
                query = f"""
                UPDATE chunks 
                SET is_deleted = true 
                WHERE id IN ({placeholders})
                """
                cursor = self.execute_query(query, tuple(vector_ids))
            elif document_id:
                query = """
                UPDATE chunks 
                SET is_deleted = true 
                WHERE document_id = %s
                """
                cursor = self.execute_query(query, (document_id,))
            else:
                raise ValueError("Either vector_ids or document_id required")
            
            deleted = cursor.rowcount
            logger.info(f"✅ Deleted {deleted} vectors")
            return deleted
        
        except Exception as e:
            logger.error(f"❌ Delete failed: {e}")
            raise
    
    def count_vectors(self) -> Dict[str, int]:
        """Get vector count"""
        try:
            # Total vectors
            query1 = "SELECT COUNT(*) as count FROM chunks WHERE is_deleted = false"
            cursor = self.execute_query(query1)
            total_vectors = cursor.fetchone()["count"]
            
            # Total documents
            query2 = "SELECT COUNT(DISTINCT document_id) as count FROM chunks WHERE is_deleted = false"
            cursor = self.execute_query(query2)
            total_documents = cursor.fetchone()["count"]
            
            return {
                "total_vectors": total_vectors,
                "total_documents": total_documents
            }
        
        except Exception as e:
            logger.error(f"❌ Count failed: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check database health"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except:
            return False
