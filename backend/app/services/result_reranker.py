import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import CrossEncoder
import numpy as np
from ..core.config import settings

logger = logging.getLogger(__name__)

class RerankerService:
    """Service quản lý Vietnamese Reranker model để chấm lại độ liên quan"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.reranker_model_name
        self.model = None
        
        # Config đã setup environment rồi, không cần _setup_cache nữa
        self._load_model()
    
    def _load_model(self):
        """Load model từ cache local hoặc download nếu cần - GPU for optimal performance"""
        try:
            logger.info(f"Loading reranker model: {self.model_name}")
            
            # Thử load từ local cache trước - sử dụng GPU
            local_model_path = self._get_local_model_path()
            if local_model_path and local_model_path.exists():
                logger.info(f"Found local model at: {local_model_path}")
                try:
                    self.model = CrossEncoder(str(local_model_path), device='cuda:0')
                    logger.info("Reranker model loaded successfully from local cache on GPU")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load from local cache on GPU: {e}")
            
            # Fallback: load từ HuggingFace (sẽ download nếu cần) - sử dụng GPU
            logger.info("Loading from HuggingFace (may download) on GPU")
            self.model = CrossEncoder(self.model_name, device='cuda:0')
            logger.info("Reranker model loaded successfully from HuggingFace on GPU")
            
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            self.model = None
            raise
    
    def _get_local_model_path(self):
        """Tìm đường dẫn local model nếu có"""
        try:
            # Sử dụng config path
            cache_hub_path = settings.hf_cache_path / "hub"
            model_dir = cache_hub_path / "models--AITeamVN--Vietnamese_Reranker"
            
            if model_dir.exists():
                # Tìm snapshot directory
                snapshots_dir = model_dir / "snapshots"
                if snapshots_dir.exists():
                    # Lấy snapshot mới nhất
                    snapshot_dirs = [d for d in snapshots_dir.iterdir() if d.is_dir()]
                    if snapshot_dirs:
                        latest_snapshot = max(snapshot_dirs, key=lambda x: x.stat().st_mtime)
                        logger.info(f"Found local snapshot: {latest_snapshot}")
                        return latest_snapshot
            
            return None
        except Exception as e:
            logger.warning(f"Error finding local model path: {e}")
            return None
    
    def rerank_documents(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        top_k: Optional[int] = None,
        router_confidence: Optional[float] = None,
        router_confidence_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank danh sách documents dựa trên độ liên quan với query
        
        Args:
            query: Câu hỏi cần tìm
            documents: Danh sách documents cần rerank
            top_k: Số lượng documents tốt nhất cần trả về (nếu None thì trả về tất cả)
            router_confidence: Confidence score từ router (0.0-1.0)
            router_confidence_level: Level từ router ('low', 'medium', 'high')
        
        Returns:
            Danh sách documents đã được sắp xếp lại theo độ liên quan
        """
        if not self.model:
            logger.warning("Reranker model not loaded, returning original order")
            return documents[:top_k] if top_k else documents
        
        if not documents:
            return []
        
        # 🛡️ ROUTER TRUST MODE: Khi router có HIGH confidence, tin tưởng router hơn
        trust_router = (router_confidence_level == 'high' and router_confidence and router_confidence >= 0.85)
        if trust_router:
            logger.info(f"🛡️ ROUTER TRUST MODE: Router confidence {router_confidence:.3f} (HIGH) - Minimal rerank interference")
        
        try:
            # 🔍 DEBUG: Log query được truyền vào reranker
            logger.info(f"🔍 RERANK QUERY: '{query}' ({len(query)} chars)")
            
            # Chuẩn bị pairs (query, document_content) cho reranker
            pairs = []
            for i, doc in enumerate(documents):
                # 🔍 DEBUG: Log document content để phân tích
                content = doc['content']
                
                # 🎯 INTELLIGENT CONTENT EXTRACTION for Vietnamese Reranker
                # Thay vì truncate random, hãy extract phần liên quan nhất
                query_keywords = self._extract_query_keywords(query)
                relevant_content = self._extract_relevant_content(content, query_keywords, max_length=800)
                
                if len(relevant_content) != len(content):
                    logger.info(f"🔧 OPTIMIZED DOC[{i}] from {len(content)} to {len(relevant_content)} chars (focused content)")
                
                # Clean content: loại bỏ markdown symbols và ký tự đặc biệt
                cleaned_content = relevant_content.replace("**", "").replace("*", "").replace("#", "")
                cleaned_content = " ".join(cleaned_content.split())  # Normalize whitespace
                
                if len(cleaned_content) > 200:
                    logger.info(f"🔍 RERANK DOC[{i}] sample: '{cleaned_content[:200]}...' (total: {len(cleaned_content)} chars)")
                else:
                    logger.info(f"🔍 RERANK DOC[{i}] full: '{cleaned_content}' ({len(cleaned_content)} chars)")
                
                pairs.append((query, cleaned_content))
            
            # Tính rerank scores
            logger.info(f"Reranking {len(documents)} documents")
            scores = self.model.predict(pairs)
            
            # Gán điểm rerank vào mỗi document
            reranked_docs = []
            for doc, score in zip(documents, scores):
                doc_copy = doc.copy()
                doc_copy['rerank_score'] = float(score)
                reranked_docs.append(doc_copy)
            
            # Sắp xếp theo rerank score giảm dần
            reranked_docs.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            # Log thông tin về top document
            if reranked_docs:
                top_doc = reranked_docs[0]
                logger.info(f"Top document after reranking: score={top_doc['rerank_score']:.4f}, "
                          f"similarity={top_doc.get('similarity', 'N/A')}")
                
                # 🛡️ ROUTER TRUST MODE: Không trigger conservative strategy khi router HIGH confidence
                if trust_router:
                    logger.info(f"🛡️ TRUSTING ROUTER: Accepting rerank results without conservative override (router: {router_confidence:.3f})")
                elif top_doc['rerank_score'] < 0.2:
                    logger.warning(f"⚠️  LOW RERANK SCORE ({top_doc['rerank_score']:.4f}) - Conservative strategy may be triggered")
            
            # Trả về top_k documents nếu được chỉ định
            if top_k:
                return reranked_docs[:top_k]
            
            return reranked_docs
            
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Fallback về sắp xếp theo similarity score ban đầu
            return sorted(documents, key=lambda x: x.get('similarity', 0), reverse=True)[:top_k] if top_k else documents
    
    def _extract_query_keywords(self, query: str) -> List[str]:
        """Extract key terms từ query để tìm nội dung liên quan"""
        # Loại bỏ stop words tiếng Việt và giữ các từ khóa quan trọng
        stop_words = {'có', 'là', 'của', 'được', 'này', 'cho', 'từ', 'với', 'và', 'trong', 'khi', 'để', 'thì', 'như', 'về', 'theo', 'trên', 'dưới', 'bên', 'giữa', 'ngoài', 'sau', 'trước'}
        
        # Tách từ và loại bỏ stop words
        words = query.lower().split()
        keywords = []
        
        for word in words:
            # Clean word (loại bỏ dấu câu)
            clean_word = word.strip('.,!?":;()[]{}')
            if len(clean_word) > 2 and clean_word not in stop_words:
                keywords.append(clean_word)
                
        # Add specialized legal terms
        legal_terms = {
            'phí': ['phí', 'lệ phí', 'tiền', 'chi phí', 'miễn phí'],
            'giấy': ['giấy tờ', 'hồ sơ', 'tài liệu', 'chứng từ'],
            'thủ tục': ['thủ tục', 'quy trình', 'trình tự'],
            'đăng ký': ['đăng ký', 'khai báo', 'nộp đơn']
        }
        
        # Mở rộng keywords với legal terms
        expanded_keywords = keywords.copy()
        for keyword in keywords:
            for category, terms in legal_terms.items():
                if keyword in terms:
                    expanded_keywords.extend([t for t in terms if t not in expanded_keywords])
        
        logger.info(f"🔑 Query keywords: {expanded_keywords}")
        return expanded_keywords
    
    def _extract_relevant_content(self, content: str, keywords: List[str], max_length: int = 800) -> str:
        """Extract những phần của content có chứa keywords quan trọng"""
        if len(content) <= max_length:
            return content
        
        content_lower = content.lower()
        
        # Tìm các câu chứa keywords
        sentences = content.split('.')
        relevant_sentences = []
        score_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_lower = sentence.lower()
            score = 0
            
            # Tính score dựa trên số keywords matching
            for keyword in keywords:
                if keyword in sentence_lower:
                    score += len(keyword)  # Từ dài hơn có weight cao hơn
            
            if score > 0:
                score_sentences.append((sentence, score))
        
        # Sắp xếp theo score giảm dần
        score_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Lấy các câu có score cao nhất cho đến khi đạt max_length
        selected_sentences = []
        current_length = 0
        
        for sentence, score in score_sentences:
            if current_length + len(sentence) <= max_length:
                selected_sentences.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        if selected_sentences:
            relevant_content = '. '.join(selected_sentences)
            logger.info(f"📄 Extracted {len(selected_sentences)} relevant sentences from {len(sentences)} total")
            return relevant_content
        else:
            # Fallback: lấy phần đầu
            logger.info("⚠️  No keyword matches found, using content start")
            return content[:max_length] + "..."
            return sorted(documents, key=lambda x: x.get('similarity', 0), reverse=True)[:top_k] if top_k else documents
    
    def get_best_document(self, query: str, documents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Tìm document có độ liên quan cao nhất với query
        
        Args:
            query: Câu hỏi cần tìm
            documents: Danh sách documents cần đánh giá
        
        Returns:
            Document có điểm rerank cao nhất
        """
        reranked = self.rerank_documents(query, documents, top_k=1)
        return reranked[0] if reranked else None
    
    def is_loaded(self) -> bool:
        """Kiểm tra xem model đã được load chưa"""
        return self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Lấy thông tin về model"""
        return {
            'model_name': self.model_name,
            'is_loaded': self.is_loaded(),
            'model_type': 'CrossEncoder' if self.model else None
        }
