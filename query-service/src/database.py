"""
PostgreSQL Database Helper
Fetch document metadata from main database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class DatabaseClient:
    """PostgreSQL client for document metadata and query logging"""
    
    # Keyword mappings for common follow-up question intents
    # Maps user intent → keywords to search in chunks
    KEYWORD_MAPPINGS = {
        "phí": ["phí", "lệ phí", "chi phí", "đồng", "miễn phí", "không thu", "vnđ"],
        "thời gian": ["thời gian", "ngày", "giờ", "bao lâu", "thời hạn", "trong ngày"],
        "hồ sơ": ["hồ sơ", "giấy tờ", "thành phần", "bản sao", "bản chính", "chứng minh"],
        "địa điểm": ["địa điểm", "ở đâu", "tại đâu", "địa chỉ", "nơi nộp", "trung tâm"],
        "đối tượng": ["đối tượng", "ai được", "điều kiện", "yêu cầu"],
    }
    
    def __init__(self, host: str, port: int, user: str, password: str, dbname: str):
        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "dbname": dbname
        }
        logger.info(f"📊 DatabaseClient initialized: {user}@{host}:{port}/{dbname}")
    
    def _get_connection(self):
        """Get a new database connection"""
        return psycopg2.connect(**self.config)
    
    def fetch_document_titles(self, doc_ids: List[str]) -> Dict[str, str]:
        """
        Batch fetch document titles
        
        Args:
            doc_ids: List of document UUIDs (as strings)
            
        Returns:
            Dict mapping document_id → title
        """
        if not doc_ids:
            return {}
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Cast text array to uuid array for PostgreSQL
            cursor.execute(
                "SELECT id, title FROM documents WHERE id = ANY(%s::uuid[])",
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

    # ============= KEYWORD SEARCH (Fallback for Semantic) =============
    
    def _extract_keywords_from_question(self, question: str) -> List[str]:
        """
        Extract relevant keywords from user question using intent mapping.
        
        Args:
            question: User's follow-up question
            
        Returns:
            List of keywords to search in chunks
        """
        q_lower = question.lower()
        keywords = []
        
        # Check each intent category
        for intent, kw_list in self.KEYWORD_MAPPINGS.items():
            # If question contains intent keyword, add all related keywords
            if intent in q_lower or any(kw in q_lower for kw in kw_list[:2]):
                keywords.extend(kw_list)
        
        # Fallback: extract any words > 2 chars as potential keywords
        if not keywords:
            words = q_lower.split()
            keywords = [w for w in words if len(w) > 2 and w not in ['là', 'có', 'của', 'cho', 'với', 'này', 'đó', 'gì', 'không']]
        
        return list(set(keywords))  # Remove duplicates
    
    def keyword_search_in_document(
        self, 
        document_id: str, 
        question: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search chunks by keyword within a specific document.
        This is a FALLBACK when semantic search fails.
        
        Args:
            document_id: UUID of the pinned document
            question: User's question (to extract keywords)
            limit: Max chunks to return
            
        Returns:
            List of chunk dicts with id, content, document_id
        """
        keywords = self._extract_keywords_from_question(question)
        
        if not keywords:
            logger.warning("⚠️ No keywords extracted from question")
            return []
        
        logger.info(f"🔍 Keyword search in doc {document_id[:8]}... with: {keywords}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build ILIKE conditions for each keyword
            conditions = []
            params = [document_id]
            
            for kw in keywords:
                conditions.append("content ILIKE %s")
                params.append(f"%{kw}%")
            
            # Search chunks containing ANY of the keywords
            where_clause = " OR ".join(conditions)
            
            cursor.execute(f"""
                SELECT id, content, document_id, metadata
                FROM chunks
                WHERE document_id = %s::uuid
                  AND ({where_clause})
                LIMIT %s
            """, params + [limit])
            
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convert to list of dicts
            chunks = []
            for row in results:
                chunks.append({
                    "id": str(row['id']),
                    "content": row['content'],
                    "document_id": str(row['document_id']),
                    "metadata": row.get('metadata', {}),
                    "similarity": 0.5,  # Fixed score for keyword match (will be reranked)
                    "match_type": "keyword"
                })
            
            logger.info(f"✅ Keyword search found {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Keyword search failed: {e}")
            return []

    # ============= SESSION MANAGEMENT =============
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data from database
        
        Returns:
            Session dict with context, or None if not found/expired
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT session_id, context, conversation_turns, 
                       created_at, last_accessed, expires_at
                FROM query_sessions
                WHERE session_id = %s
                  AND (expires_at IS NULL OR expires_at > NOW())
            """, (session_id,))
            
            row = cursor.fetchone()
            
            # Update last_accessed
            if row:
                cursor.execute("""
                    UPDATE query_sessions 
                    SET last_accessed = NOW()
                    WHERE session_id = %s
                """, (session_id,))
                conn.commit()
            
            cursor.close()
            conn.close()
            
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"❌ Get session failed: {e}")
            return None
    
    def save_session(
        self, 
        session_id: str, 
        context: Dict[str, Any],
        conversation_turns: int = 0
    ) -> bool:
        """
        Save or update session in database (UPSERT)
        
        Args:
            session_id: Unique session identifier
            context: Dict with pinned_document_id, pinned_document_title, etc.
            conversation_turns: Number of Q&A turns in this session
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Session expires after 30 minutes of inactivity
            expires_at = datetime.now() + timedelta(minutes=30)
            
            cursor.execute("""
                INSERT INTO query_sessions (session_id, context, conversation_turns, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE SET
                    context = EXCLUDED.context,
                    conversation_turns = EXCLUDED.conversation_turns,
                    last_accessed = NOW(),
                    expires_at = EXCLUDED.expires_at
            """, (session_id, json.dumps(context), conversation_turns, expires_at))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.debug(f"✅ Session saved: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Save session failed: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM query_sessions WHERE session_id = %s",
                (session_id,)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"❌ Delete session failed: {e}")
            return False

    # ============= QUERY LOGGING =============
    
    def _ensure_session_exists(self, session_id: str, conn) -> None:
        """
        Ensure a session exists in query_sessions table.
        Creates minimal session record if not exists (for FK constraint).
        """
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO query_sessions (session_id, context)
            VALUES (%s, %s)
            ON CONFLICT (session_id) DO NOTHING
        """, (session_id, json.dumps({})))
        cursor.close()
    
    def log_query(
        self,
        session_id: Optional[str],
        query_text: str,
        query_type: str = "initial",  # 'initial', 'follow_up', 'clarification', 'confirm'
        answer_text: Optional[str] = None,
        sources_used: Optional[List[Dict]] = None,
        confidence_score: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Log a query to the database for analytics
        
        Returns:
            Query log ID if successful, None otherwise
        """
        try:
            conn = self._get_connection()
            
            # Ensure session exists to satisfy FK constraint
            if session_id:
                self._ensure_session_exists(session_id, conn)
            
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO query_logs (
                    session_id, query_text, query_type, answer_text,
                    sources_used, confidence_score, processing_time_ms,
                    tokens_used, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                session_id,
                query_text,
                query_type,
                answer_text,
                json.dumps(sources_used or []),
                confidence_score,
                processing_time_ms,
                tokens_used,
                json.dumps(metadata or {})
            ))
            
            log_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.debug(f"📝 Query logged: {log_id}")
            return str(log_id)
            
        except Exception as e:
            logger.error(f"❌ Log query failed: {e}")
            return None
    
    def cleanup_expired_sessions(self) -> int:
        """
        Delete expired sessions (can be called periodically)
        
        Returns:
            Number of sessions deleted
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM query_sessions 
                WHERE expires_at < NOW()
            """)
            
            deleted = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted > 0:
                logger.info(f"🧹 Cleaned up {deleted} expired sessions")
            
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Cleanup sessions failed: {e}")
            return 0

    # ============= DOCUMENT & FORM QUERIES =============
    
    def fetch_document_info(self, doc_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch document info including file_path for download
        
        Args:
            doc_ids: List of document UUIDs
            
        Returns:
            Dict mapping document_id → {title, file_path, filename}
        """
        if not doc_ids:
            return {}
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                "SELECT id, title, file_path, filename FROM documents WHERE id = ANY(%s::uuid[])",
                (doc_ids,)
            )
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            info_map = {}
            for row in results:
                info_map[str(row['id'])] = {
                    'title': row['title'],
                    'file_path': row['file_path'],
                    'filename': row['filename']
                }
            
            logger.info(f"✅ Fetched info for {len(info_map)} documents")
            return info_map
            
        except Exception as e:
            logger.error(f"❌ Fetch document info failed: {e}")
            return {}
    
    def fetch_forms_by_document_ids(self, doc_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch forms associated with documents
        
        Args:
            doc_ids: List of document UUIDs
            
        Returns:
            Dict mapping document_id → list of forms [{id, form_name, template_path, description}]
        """
        if not doc_ids:
            return {}
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, document_id, form_name, template_path, description
                FROM forms
                WHERE document_id = ANY(%s::uuid[])
                ORDER BY form_name
            """, (doc_ids,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Group by document_id
            forms_map: Dict[str, List[Dict[str, Any]]] = {}
            for row in results:
                doc_id = str(row['document_id'])
                if doc_id not in forms_map:
                    forms_map[doc_id] = []
                forms_map[doc_id].append({
                    'id': str(row['id']),
                    'form_name': row['form_name'],
                    'template_path': row['template_path'],
                    'description': row['description']
                })
            
            total_forms = sum(len(forms) for forms in forms_map.values())
            logger.info(f"✅ Fetched {total_forms} forms for {len(forms_map)} documents")
            return forms_map
            
        except Exception as e:
            logger.error(f"❌ Fetch forms failed: {e}")
            return {}
