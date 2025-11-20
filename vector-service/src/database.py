"""
PostgreSQL pgvector Database Client
"""
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from typing import List, Dict, Any, Optional
import logging
import uuid
import json

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
                    embedding: List[float], section_title: Optional[str] = None,
                    source_reference: Optional[str] = None, token_count: Optional[int] = None,
                    metadata: Optional[dict] = None) -> str:
        """Insert single chunk with embedding (LegalRAG schema)"""
        try:
            vector_id = str(uuid.uuid4())
            
            query = """
            INSERT INTO chunks (id, document_id, chunk_index, content, section_title,
                              source_reference, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s::jsonb)
            """
            
            cursor = self.execute_query(
                query,
                (vector_id, document_id, chunk_index, content, section_title,
                 source_reference, embedding, json.dumps(metadata) if metadata else '{}')
            )
            
            logger.info(f"✅ Inserted chunk: {vector_id}")
            return vector_id
        
        except Exception as e:
            logger.error(f"❌ Insert failed: {e}")
            raise
    
    def insert_or_update_document(self, document_id: str, collection_id: str, 
                                  title: str, filename: str,
                                  file_path: Optional[str] = None,
                                  file_size: Optional[int] = None,
                                  metadata: Optional[dict] = None) -> bool:
        """Insert or update document record with full information"""
        try:
            query = """
            INSERT INTO documents (id, collection_id, title, filename, file_path, file_size, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (
                document_id, 
                collection_id, 
                title, 
                filename, 
                file_path, 
                file_size,
                json.dumps(metadata) if metadata else '{}'
            ))
            self.connection.commit()
            cursor.close()
            logger.info(f"✅ Document record created: {document_id} in collection {collection_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create document: {e}")
            self.connection.rollback()
            return False

    def insert_batch_chunks(self, document_info: dict, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Insert document + multiple chunks"""
        try:
            logger.info(f"📥 Received document + {len(chunks) if chunks else 0} chunks to insert")
            
            # STEP 1: Create document record FIRST (for FK constraint)
            if document_info:
                logger.info(f"📌 Creating document: {document_info.get('id')}")
                success = self.insert_or_update_document(
                    document_id=document_info.get('id'),
                    collection_id=document_info.get('collection_id'),
                    title=document_info.get('title'),
                    filename=document_info.get('filename'),
                    file_path=document_info.get('file_path'),
                    file_size=document_info.get('file_size'),
                    metadata=document_info.get('metadata')
                )
                
                if not success:
                    raise Exception("Failed to create document record")
            
            # STEP 2: Insert chunks
            inserted = 0
            failed = 0
            
            for chunk in chunks:
                try:
                    self.insert_chunk(
                        document_id=chunk["document_id"],
                        chunk_index=chunk["chunk_index"],
                        content=chunk["content"],
                        embedding=chunk["embedding"],
                        section_title=chunk.get("section_title"),
                        source_reference=chunk.get("source_reference"),
                        token_count=chunk.get("token_count"),
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
    
    def insert_batch_chunks_only(self, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Insert only chunks (AICenter Pattern)
        Document MUST already exist in documents table
        """
        try:
            logger.info(f"📥 Inserting {len(chunks)} chunks (document already exists)")
            
            inserted = 0
            failed = 0
            
            for chunk in chunks:
                try:
                    self.insert_chunk(
                        document_id=chunk["document_id"],
                        chunk_index=chunk["chunk_index"],
                        content=chunk["content"],
                        embedding=chunk["embedding"],
                        section_title=chunk.get("section_title"),
                        source_reference=chunk.get("source_reference"),
                        token_count=chunk.get("token_count"),
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
                section_title,
                source_reference,
                metadata,
                1 - (embedding <=> %s::vector) as similarity
            FROM chunks
            WHERE 1=1
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
        """Delete vectors (CASCADE delete when document deleted)"""
        try:
            if vector_ids:
                placeholders = ','.join(['%s'] * len(vector_ids))
                query = f"""
                DELETE FROM chunks 
                WHERE id IN ({placeholders})
                """
                cursor = self.execute_query(query, tuple(vector_ids))
            elif document_id:
                query = """
                DELETE FROM chunks 
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
            query1 = "SELECT COUNT(*) as count FROM chunks"
            cursor = self.execute_query(query1)
            total_vectors = cursor.fetchone()["count"]
            
            # Total documents
            query2 = "SELECT COUNT(DISTINCT document_id) as count FROM chunks"
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
