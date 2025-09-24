#!/usr/bin/env python3
"""
Smart Clarification Service for LegalRAG V2
===========================================

5-Layer Clarification System for 13 Collections:
- High confidence (≥0.80): Auto route - no clarification needed
- Medium-High confidence (0.65-0.79): Confirm with best questions
- Medium confidence (0.50-0.64): Multiple choice from top matches
- Low confidence (0.30-0.49): Category-based suggestions
- Insufficient context (<0.30): Context gathering

Author: LegalRAG Team
"""

from typing import Dict, List, Any, Optional, Tuple, Union, cast
import logging
import os
import json
import pickle
from dataclasses import dataclass

from app.utils.collection_utils import CollectionManager
from app.utils.clarification_config import ClarificationConfig
from app.models.schemas import (
    ClarificationOption, StandardClarificationResponse,
    ClarificationActionResponse, ProceedWithQuestionResponse, 
    CollectionOverviewResponse, ManualInputResponse, ClarificationErrorResponse
)

logger = logging.getLogger(__name__)

class ClarifyCache:
    """
    Cache manager for clarify embeddings
    Loads and manages pre-computed document embeddings for confidence calculation
    """
    
    def __init__(self, cache_path: str = "data/cache/clarify_embeddings.pkl"):
        """
        Initialize clarify cache
        
        Args:
            cache_path: Path to clarify embeddings cache file
        """
        self.cache_path = cache_path
        self.cache_data = None
        self.similarity_available = False
        
        # Try to import required modules for similarity calculation
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            self.cosine_similarity = cosine_similarity
            self.np = np
            self.similarity_available = True
        except ImportError:
            logger.warning("⚠️ sklearn/numpy not available for similarity calculation")
        
        # Load cache on initialization
        self._load_cache()
    
    def _load_cache(self) -> bool:
        """Load clarify cache from pickle file"""
        try:
            if not os.path.exists(self.cache_path):
                logger.warning(f"⚠️ Clarify cache not found: {self.cache_path}")
                return False
            
            with open(self.cache_path, 'rb') as f:
                cache_with_metadata = pickle.load(f)
            
            self.cache_data = cache_with_metadata.get('data', {})
            cache_metadata = cache_with_metadata.get('metadata', {})
            
            total_docs = sum(len(docs) for docs in self.cache_data.values())
            logger.info(f"✅ Loaded clarify cache: {len(self.cache_data)} collections, {total_docs} documents")
            logger.info(f"🔧 Cache type: {cache_metadata.get('cache_type', 'unknown')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading clarify cache: {e}")
            return False
    
    def get_documents_for_collection(self, collection: str) -> List[Dict[str, Any]]:
        """Get all documents for a collection with their cached data"""
        if not self.cache_data or collection not in self.cache_data:
            logger.warning(f"⚠️ Collection '{collection}' not found in clarify cache")
            return []
        
        documents = []
        for doc_id, doc_data in self.cache_data[collection].items():
            documents.append({
                'document_id': doc_id,
                'title': doc_data.get('title', 'Untitled'),
                'has_form': doc_data.get('has_form', False),
                'metadata': doc_data.get('metadata', {}),
                'embedding': doc_data.get('embedding'),
                'fused_text': doc_data.get('fused_text', '')
            })
        
        return documents
    
    def calculate_similarity(self, query_embedding, document_embedding) -> float:
        """Calculate cosine similarity between query and document embeddings"""
        if not self.similarity_available or query_embedding is None or document_embedding is None:
            return 0.5  # Fallback confidence
        
        try:
            # Reshape embeddings for sklearn
            query_emb = self.np.array(query_embedding).reshape(1, -1)
            doc_emb = self.np.array(document_embedding).reshape(1, -1)
            
            similarity = self.cosine_similarity(query_emb, doc_emb)[0][0]
            
            # Convert to confidence score (0-1 range)
            confidence = (similarity + 1) / 2  # Convert from [-1,1] to [0,1]
            return max(0.0, min(1.0, confidence))  # Clamp to [0,1]
            
        except Exception as e:
            logger.error(f"❌ Error calculating similarity: {e}")
            return 0.5  # Fallback confidence
    
    def is_available(self) -> bool:
        """Check if cache is loaded and available"""
        return self.cache_data is not None and len(self.cache_data) > 0

@dataclass
class ClarificationLevel:
    """Define clarification levels"""
    min_confidence: float
    max_confidence: float
    strategy: str
    message_template: str

class ClarificationService:
    """
    🎯 ENHANCED CLARIFICATION SERVICE with Embedding Intelligence
    - 5-layer confidence system cho nhiều collections
    - Similarity ranking for better question suggestions  
    - Scale-ready, clean architecture
    - Dựa trên schema chuẩn hóa và cấu hình ngoài
    - Tự động đọc collections từ data/storage
    """
    
    def __init__(self, embedding_model=None, config_path: Optional[str] = None, storage_path: Optional[str] = None):
        """
        Khởi tạo ClarificationService với các tùy chọn cấu hình
        
        Args:
            embedding_model: Model để embedding câu hỏi và tính similarity
            config_path: Đường dẫn đến file cấu hình (json), nếu không có sẽ dùng default
            storage_path: Đường dẫn đến thư mục storage, mặc định là "data/storage"
        """
        # Store embedding model for similarity calculations
        self.embedding_model = embedding_model
        
        # Initialize ClarifyCache for real confidence calculation
        self.clarify_cache = ClarifyCache()
        
        # Load config từ file cấu hình hoặc default
        self.config = ClarificationConfig(config_path)
        
        # Khởi tạo Collection Manager để lấy thông tin collections
        self.collection_manager = CollectionManager(storage_path if storage_path else "data/storage/collections")
        
        # Try to import sklearn for similarity calculations
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            self.similarity_available = True
            self.cosine_similarity = cosine_similarity
            self.np = np
        except ImportError:
            self.similarity_available = False
            logger.warning("⚠️  sklearn not available - using fallback ranking")
        
        # 5-Layer clarification system - load từ config
        self.clarification_levels = {}
        # Load từ config ngoài
        levels_config = self.config.get_clarification_levels()
        for level_name, level_data in levels_config.items():
            self.clarification_levels[level_name] = ClarificationLevel(
                min_confidence=level_data.get("min_confidence", 0.0),
                max_confidence=level_data.get("max_confidence", 1.0),
                strategy=level_data.get("strategy", "fallback"),
                message_template=level_data.get("message_template", "No message template provided")
            )
        
        # 🎯 NO HARDCORE MAPPINGS - Use router results directly!

        # Load collections từ storage
        self.collections = self.collection_manager.get_all_collections()
        logger.info(f"✅ Loaded {len(self.collections)} collections dynamically from storage")
    
    # =====================================================================
    # INDEPENDENT CLARIFY DATA METHODS - NO EXTERNAL DEPENDENCIES
    # =====================================================================
    
    def _calculate_question_confidence_real_time(self, original_query: str, question_texts: List[str]) -> List[float]:
        """
        Calculate real confidence for questions using embedding similarity
        
        Args:
            original_query: Original user query
            question_texts: List of question texts to compare against
            
        Returns:
            List of confidence scores (0.0-1.0) for each question
        """
        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            if not self.embedding_model or not original_query.strip() or not question_texts:
                return [0.7 for _ in question_texts]  # Fallback
            
            # Encode original query
            query_embedding = self.embedding_model.encode([original_query.strip()])
            
            # Encode all questions
            question_embeddings = self.embedding_model.encode(question_texts)
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_embedding, question_embeddings)[0]
            
            # Convert similarities to confidence scores
            # Apply sigmoid-like transformation to spread scores better
            confidences = []
            for sim in similarities:
                # Transform similarity (-1 to 1) to confidence (0.5 to 0.95)
                # Use exponential scaling to reward high similarities
                confidence = 0.5 + (sim + 1.0) / 2.0 * 0.45  # Map to 0.5-0.95 range
                confidence = min(0.95, max(0.5, confidence))  # Clamp to range
                confidences.append(float(confidence))
            
            # Sort by confidence and apply small penalty for lower ranks
            sorted_indices = sorted(range(len(confidences)), key=lambda i: confidences[i], reverse=True)
            adjusted_confidences = [0.0] * len(confidences)
            
            for rank, idx in enumerate(sorted_indices):
                # Apply small ranking penalty (max 5% reduction)
                rank_penalty = rank * 0.01  # 1% per rank
                adjusted_confidences[idx] = max(0.5, confidences[idx] - rank_penalty)
            
            logger.info(f"🎯 Real confidence calculated: min={min(adjusted_confidences):.3f}, max={max(adjusted_confidences):.3f}, avg={np.mean(adjusted_confidences):.3f}")
            return adjusted_confidences
            
        except Exception as e:
            logger.error(f"Error calculating real question confidence: {e}")
            # Fallback to decreasing confidence
            return [max(0.5, 0.9 - (i * 0.05)) for i in range(len(question_texts))]
    
    
    def _normalize_document_metadata(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize document metadata to consistent format
        Only keep essential fields: id, title, source, has_form
        """
        return {
            "id": doc_data.get("id", ""),
            "title": doc_data.get("title", "Tài liệu không tên"),
            "source": doc_data.get("source", ""),
            "has_form": doc_data.get("has_form", False),
            "code": doc_data.get("code", ""),  # Keep code for additional context
        }
    
    def _calculate_real_confidence(self, user_query: str, collection: str) -> List[Dict[str, Any]]:
        """
        Calculate real confidence scores using embeddings similarity
        
        Args:
            user_query: The user's query
            collection: Target collection name
            
        Returns:
            List of documents with real confidence scores based on similarity
        """
        try:
            # Check if clarify cache is available
            if not self.clarify_cache.is_available():
                logger.warning("⚠️ Clarify cache not available, falling back to simple ranking")
                return self._get_documents_for_clarify(collection)
            
            # Get cached documents for the collection
            cached_docs = self.clarify_cache.get_documents_for_collection(collection)
            
            if not cached_docs:
                logger.warning(f"⚠️ No cached docs for collection '{collection}', using fallback")
                return self._get_documents_for_clarify(collection)
            
            # Generate query embedding if embedding model is available
            query_embedding = None
            if self.embedding_model:
                try:
                    query_embedding = self.embedding_model.encode([user_query])[0]
                except Exception as e:
                    logger.error(f"❌ Error generating query embedding: {e}")
            
            # Calculate confidence for each document
            documents_with_confidence = []
            
            for doc in cached_docs:
                doc_embedding = doc.get('embedding')
                
                # Calculate similarity-based confidence
                if query_embedding is not None and doc_embedding is not None:
                    confidence = self.clarify_cache.calculate_similarity(query_embedding, doc_embedding)
                else:
                    # Fallback to simple confidence based on order
                    confidence = 0.8 - (len(documents_with_confidence) * 0.1)
                    confidence = max(0.5, confidence)
                
                documents_with_confidence.append({
                    "document": doc['document_id'],
                    "title": doc['title'],
                    "has_form": doc['has_form'],
                    "code": doc.get('metadata', {}).get('code', ''),
                    "confidence": confidence
                })
            
            # Sort by confidence (highest first)
            documents_with_confidence.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Limit to top 6 documents
            limited_docs = documents_with_confidence[:6]
            
            logger.info(f"✅ Calculated real confidence for {len(limited_docs)} documents in '{collection}'")
            logger.debug(f"🎯 Top document confidence: {limited_docs[0]['confidence']:.3f}" if limited_docs else "No documents")
            
            return limited_docs
            
        except Exception as e:
            logger.error(f"❌ Error calculating real confidence: {e}")
            # Fallback to simple method
            return self._get_documents_for_clarify(collection)
    
    def _get_documents_for_clarify_with_real_confidence(self, collection: str, user_query: str = "") -> List[Dict[str, Any]]:
        """
        Get documents for clarify flow with real confidence calculation
        This method replaces the old _get_documents_for_clarify with embedding-based confidence
        
        Args:
            collection: Target collection name
            user_query: User's query for similarity calculation
            
        Returns:
            List of documents with real confidence scores
        """
        if user_query and user_query.strip():
            # Use real confidence calculation when query is available
            return self._calculate_real_confidence(user_query, collection)
        else:
            # Fallback to simple method when no query
            return self._get_documents_for_clarify(collection)
    
    def _get_documents_for_clarify(self, collection: str) -> List[Dict[str, Any]]:
        """
        Independent method to get documents for clarify flow
        Uses metadata.json for reliable document information
        """
        try:
            import os
            import json
            
            # Direct path to collection metadata
            metadata_file = f"data/storage/collections/{collection}/metadata.json"
            
            if not os.path.exists(metadata_file):
                logger.warning(f"Metadata file not found: {metadata_file}")
                return self._get_fallback_documents()
            
            # Read metadata.json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            documents = []
            for i, doc_data in enumerate(metadata.get('documents', [])[:6]):  # Limit to 6 documents
                # Normalize document metadata
                normalized_doc = self._normalize_document_metadata(doc_data)
                
                # Calculate simple confidence based on order
                confidence = 0.9 - (i * 0.1)  # First doc gets 0.9, second gets 0.8, etc.
                
                documents.append({
                    "document": normalized_doc["id"],
                    "title": normalized_doc["title"],
                    "has_form": normalized_doc["has_form"],
                    "code": normalized_doc["code"],
                    "confidence": max(0.5, confidence)  # Minimum 0.5
                })
            
            return documents if documents else self._get_fallback_documents()
            
        except Exception as e:
            logger.error(f"Error getting documents for clarify: {e}")
            return self._get_fallback_documents()
    
    def _get_questions_for_clarify(self, collection: str, document: str, original_query: str = "") -> List[Dict[str, Any]]:
        """
        Independent method to get questions for clarify flow
        Uses direct filesystem access, not router dependencies
        
        Args:
            collection: Collection name
            document: Document name  
            original_query: Original user query for similarity calculation
        """
        try:
            import os
            import json
            
            # Direct path to document questions
            questions_file = f"data/storage/collections/{collection}/documents/{document}/questions.json"
            
            if not os.path.exists(questions_file):
                logger.warning(f"Questions file not found: {questions_file}")
                return self._get_fallback_questions_simple()
            
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
            
            if not questions_data:
                return self._get_fallback_questions_simple()
            
            # Ensure questions_data is a list
            if isinstance(questions_data, dict):
                # If it's a dict with 'main_question' and 'question_variants'
                questions_list = []
                if 'main_question' in questions_data and questions_data['main_question']:
                    questions_list.append(questions_data['main_question'])
                if 'question_variants' in questions_data:
                    questions_list.extend(questions_data['question_variants'])
                questions_data = questions_list
            elif not isinstance(questions_data, list):
                questions_data = [questions_data]
            
            questions = []
            question_texts = []
            
            # Extract question texts for batch similarity calculation
            for i, q_data in enumerate(questions_data[:8]):  # Limit to 8 questions
                if isinstance(q_data, dict):
                    question_text = q_data.get('text', q_data.get('question', f'Câu hỏi {i+1}'))
                else:
                    question_text = str(q_data)
                question_texts.append(question_text)
            
            # Calculate real confidence using embedding similarity
            if original_query.strip() and self.embedding_model and question_texts:
                try:
                    confidences = self._calculate_question_confidence_real_time(original_query, question_texts)
                    logger.info(f"✅ Calculated real confidence for {len(question_texts)} questions using embedding similarity")
                except Exception as e:
                    logger.warning(f"Failed to calculate real confidence, using fallback: {e}")
                    confidences = [0.9 - (i * 0.05) for i in range(len(question_texts))]  # Fallback
            else:
                # Fallback: Simple confidence based on order in file
                confidences = [0.9 - (i * 0.05) for i in range(len(question_texts))]  # First question gets 0.9, decreasing by 0.05
                if original_query.strip():
                    logger.info(f"📝 Using fallback confidence (no embedding model available)")
                else:
                    logger.info(f"📝 Using fallback confidence (no original query)")
            
            # Build questions with calculated confidence
            for i, q_data in enumerate(questions_data[:8]):
                if isinstance(q_data, dict):
                    question_text = q_data.get('text', q_data.get('question', f'Câu hỏi {i+1}'))
                else:
                    question_text = str(q_data)
                
                confidence = max(0.5, confidences[i])  # Minimum 0.5
                
                questions.append({
                    "text": question_text,
                    "confidence": confidence,
                    "source": f"{collection}/documents/{document}/questions.json",
                    "category": "general"
                })
            
            return questions if questions else self._get_fallback_questions_simple()
            
        except Exception as e:
            logger.error(f"Error getting questions for clarify: {e}")
            return self._get_fallback_questions_simple()
    
    def _get_fallback_documents(self) -> List[Dict[str, Any]]:
        """Fallback documents when filesystem access fails"""
        return [
            {"document": "DOC_001", "title": "Tài liệu chính", "confidence": 0.9},
            {"document": "DOC_002", "title": "Tài liệu hướng dẫn", "confidence": 0.8},
            {"document": "DOC_003", "title": "Tài liệu bổ sung", "confidence": 0.7}
        ]
    
    def _get_fallback_questions_simple(self) -> List[Dict[str, Any]]:
        """Fallback questions when filesystem access fails"""
        return [
            {"text": "Thủ tục này thực hiện như thế nào?", "confidence": 0.9, "source": "fallback", "category": "general"},
            {"text": "Cần những giấy tờ gì?", "confidence": 0.8, "source": "fallback", "category": "general"},
            {"text": "Thời gian xử lý bao lâu?", "confidence": 0.7, "source": "fallback", "category": "general"},
            {"text": "Lệ phí bao nhiêu?", "confidence": 0.6, "source": "fallback", "category": "general"}
        ]
    
    def generate_clarification(
        self, 
        confidence: float,
        routing_result: Dict[str, Any],
        query: str,
        session_id: Optional[str] = None
    ) -> Union[StandardClarificationResponse, Dict[str, Any]]:
        """
        Tạo clarification thông minh dựa trên confidence level
        Trả về StandardClarificationResponse hoặc dict tương thích
        """
        try:
            # Convert numpy types to Python native types để tránh lỗi serialization
            confidence = float(confidence) if confidence is not None else 0.0
            
            # Xác định clarification level
            clarification_level = self._determine_clarification_level(confidence)
            level_config = self.clarification_levels[clarification_level]
            
            logger.info(f"🎯 Generating {clarification_level} clarification for confidence: {confidence:.3f}")
            
            # Generate theo strategy - 5-LAYER SYSTEM
            if level_config.strategy == 'auto_route':
                result = self._generate_auto_route_response(confidence, routing_result, level_config)
            elif level_config.strategy == 'confirm_with_best_questions':
                result = self._generate_confirmation_clarification(confidence, routing_result, level_config)
            elif level_config.strategy == 'multiple_choices':
                result = self._generate_multiple_choice_clarification(confidence, routing_result, level_config)
            elif level_config.strategy == 'category_suggestions':
                result = self._generate_category_clarification(confidence, routing_result, level_config)
            elif level_config.strategy == 'context_gathering':
                result = self._generate_context_gathering_clarification(confidence, routing_result, level_config)
            else:
                # Fallback
                result = self._generate_fallback_clarification(confidence, routing_result)
            
            # Nếu là StandardClarificationResponse, set session_id
            if isinstance(result, StandardClarificationResponse) and session_id:
                result.session_id = session_id
            # Nếu là dict, set session_id theo cách cũ
            elif isinstance(result, dict) and session_id:
                result['session_id'] = session_id
            
            return result
                
        except Exception as e:
            logger.error(f"Error generating smart clarification: {e}")
            return self._generate_fallback_clarification(float(confidence) if confidence is not None else 0.0, routing_result)
    
    def _determine_clarification_level(self, confidence: float) -> str:
        """Xác định clarification level dựa trên confidence - 5-LAYER SYSTEM"""
        # Kiểm tra theo thứ tự từ cao xuống thấp để tránh overlap
        if confidence >= 0.80:
            return 'high_confidence'
        elif confidence >= 0.65 and confidence < 0.80:
            return 'medium_high_confidence'
        elif confidence >= 0.50 and confidence < 0.65:
            return 'medium_confidence'
        elif confidence >= 0.30 and confidence < 0.50:
            return 'low_confidence'
        elif confidence >= 0.00 and confidence < 0.30:
            return 'insufficient_context'
        else:
            # Edge case - default to insufficient context
            return 'insufficient_context'
    
    def _generate_auto_route_response(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> StandardClarificationResponse:
        """
        HIGH CONFIDENCE (≥0.80): Auto route without clarification
        Sử dụng schema chuẩn hóa
        """
        target_collection = routing_result.get('target_collection')
        message = level_config.message_template.format(confidence=confidence)
        
        # Lấy document và procedure từ routing_result nếu có
        best_match = routing_result.get('best_match', {})
        document = best_match.get('document', None)
        procedure = best_match.get('question', None)
        
        # Sử dụng StandardClarificationResponse cho output chuẩn hóa
        return StandardClarificationResponse(
            type="auto_route",
            confidence_level="high_confidence",
            confidence=float(confidence),
            target_collection=target_collection,
            document=document,
            procedure=procedure,
            message=message,
            options=[],  # Không có options vì auto route
            style="auto_route",
            manual_input_placeholder=None,
            routing_context=routing_result,
            strategy=level_config.strategy,
            session_id=None,  # Session ID sẽ được set ở hàm generate_clarification
            additional_help=None,
            requires_user_input=False,
            show_manual_input=False
        )
    
    def _generate_context_gathering_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> StandardClarificationResponse:
        """
        INSUFFICIENT CONTEXT (0.00-0.29): Thu thập thêm context
        """
        message = level_config.message_template
        target_collection = routing_result.get('target_collection')
        
        # Lấy options từ config thay vì hardcode
        option_configs = self.config.get_context_gathering_options()
        options = []
        
        # Chuyển đổi từ config sang ClarificationOption
        clarification_options = []
        for opt_config in option_configs:
            clarification_options.append(ClarificationOption(
                id=opt_config.get("id", ""),
                title=opt_config.get("title", ""),
                description=opt_config.get("description"),
                action=opt_config.get("action", ""),
                collection=None,
                document=None,
                procedure=None,
                question_text=None,
                confidence_percent=None,
                source_file=None,
                context_type=opt_config.get("context_type"),
                category=None
            ))
        
        # Sử dụng schema chuẩn hóa
        return StandardClarificationResponse(
            type="context_gathering_needed",
            confidence_level="insufficient_context",
            confidence=float(confidence),
            message=message,
            target_collection=target_collection,
            document=None,
            procedure=None,
            options=clarification_options,
            requires_user_input=True,
            show_manual_input=True,
            manual_input_placeholder="Mô tả chi tiết tình huống của bạn...",
            style="context_gathering",
            routing_context=routing_result,
            strategy=level_config.strategy,
            session_id=None,
            additional_help="Bạn có thể cung cấp thêm thông tin về tình huống của mình để chúng tôi hỗ trợ tốt hơn."
        )

    def _generate_confirmation_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> StandardClarificationResponse:
        """
        🔥 SMART CONFIRMATION - MEDIUM-HIGH CONFIDENCE (0.65-0.79): 
        Find the best question and suggest proceeding directly instead of showing all questions
        """
        # Fix data mapping - sử dụng structure mới từ router
        best_match = routing_result.get('best_match', {})
        source_procedure = best_match.get('question', 'thủ tục này')
        best_question = best_match.get('question', '')
        target_collection = routing_result.get('target_collection')
        original_query = routing_result.get('query', '')
        
        # 🔧 DEBUG: Log target_collection value
        logger.info(f"🔍 DEBUG _generate_confirmation_clarification:")
        logger.info(f"  - routing_result keys: {list(routing_result.keys())}")
        logger.info(f"  - target_collection: {target_collection}")
        logger.info(f"  - best_match: {best_match}")
        logger.info(f"  - original_query: {original_query}")
        
        # Nếu không có best_match, thử fallback
        if not source_procedure or source_procedure == 'thủ tục này':
            # 🔧 FIX: Simple fallback without hardcore mapping
            source_procedure = target_collection or 'thủ tục này'
        
        # Lấy document từ best_match 
        target_document = best_match.get('document', '')
        
        # 🚀 SMART CONFIRMATION: Extract the suggested question from router or try to find one
        suggested_question = None
        suggested_question_confidence = confidence
        
        # First, try to get the suggested question from routing result (router may have already found it)
        if best_match and 'question' in best_match:
            suggested_question = best_match.get('question')
            logger.info(f"🎯 Using router's suggested question: '{suggested_question}'")
        
        # If no router suggestion, try to find the best question ourselves
        if not suggested_question and target_collection and target_document and original_query:
            try:
                best_questions = self._get_questions_for_clarify(
                    target_collection, 
                    target_document, 
                    original_query
                )[:1]  # Only get the top 1 question
                if best_questions:
                    best_question_data = best_questions[0]
                    suggested_question = best_question_data.get('text', '') if isinstance(best_question_data, dict) else str(best_question_data)
                    suggested_question_confidence = best_question_data.get('confidence', confidence) if isinstance(best_question_data, dict) else confidence
                    logger.info(f"✅ Found best question via _get_questions_for_clarify: '{suggested_question}'")
            except Exception as e:
                logger.warning(f"⚠️ Error getting best questions: {e}")
        
        # Tạo danh sách options sử dụng schema mới
        clarification_options = []
        
        # 🔥 REVISED LOGIC: If we have ANY suggested question (from router or search), offer to proceed
        if suggested_question and confidence > 0.65:  # Lower threshold to be more inclusive
            # Option 1: Proceed directly with the suggested question (SMART OPTION)
            proceed_option = ClarificationOption(
                id='proceed_direct',
                title=f'Đúng, tôi muốn hỏi về: "{suggested_question}"',
                description=f"Tiếp tục với câu hỏi được đề xuất (độ tin cậy {round(suggested_question_confidence * 100, 1)}%)",
                action='proceed_with_question',
                collection=target_collection,
                document=target_document,
                procedure=source_procedure,
                confidence_percent=round(suggested_question_confidence * 100, 1),
                question_text=suggested_question,
                source_file=None,
                context_type=None,
                category=None
            )
            # Add original_query as additional attribute
            if hasattr(proceed_option, '__dict__'):
                proceed_option.__dict__['original_query'] = original_query
            clarification_options.append(proceed_option)
            
            message = f"Tôi nghĩ bạn muốn hỏi về '{suggested_question}' (độ tin cậy: {round(confidence * 100, 1)}%). Đúng không?"
        else:
            # Fallback to old behavior if no suggested question found
            message = level_config.message_template.format(
                procedure=source_procedure,
                confidence=confidence
            )
        
        # Option 2: Show all questions in document (fallback option)
        clarification_options.append(ClarificationOption(
            id='show_all',
            title="Không chính xác, cho tôi xem các lựa chọn khác",
            description=f"Hiển thị tất cả câu hỏi về {source_procedure}",
            action='show_document_questions',
            collection=target_collection,
            document=target_document,
            procedure=source_procedure,
            confidence_percent=round(confidence * 100, 1),
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Option 3: Từ chối và chọn thủ tục khác
        clarification_options.append(ClarificationOption(
            id='no',
            title="Không, tôi muốn hỏi về thủ tục khác",
            description="Hãy cho tôi thêm lựa chọn khác",
            action='show_categories',
            collection=None,
            document=None,
            procedure=None,
            confidence_percent=0,
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Sử dụng schema chuẩn hóa
        return StandardClarificationResponse(
            type="clarification_needed",
            confidence_level="medium_high_confidence",
            confidence=float(confidence),
            message=message,
            target_collection=target_collection,
            document=target_document,
            procedure=source_procedure,
            options=clarification_options,
            requires_user_input=False,
            show_manual_input=False,
            manual_input_placeholder=None,
            style="confirmation",
            routing_context=routing_result,
            strategy=level_config.strategy,
            session_id=None,
            additional_help=None
        )
    
    def _generate_multiple_choice_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> StandardClarificationResponse:
        """
        MEDIUM CONFIDENCE (0.5-0.69): Multiple choices từ top matches
        """
        # Lấy top matches từ routing result và sort theo confidence
        all_scores = routing_result.get('all_scores', {})
        target_collection = routing_result.get('target_collection')
        
        # 🔧 DEBUG: Log để xem all_scores structure
        logger.info(f"🔍 DEBUG _generate_multiple_choice_clarification:")
        logger.info(f"  - all_scores keys: {list(all_scores.keys()) if all_scores else 'EMPTY'}")
        logger.info(f"  - all_scores values: {list(all_scores.values()) if all_scores else 'EMPTY'}")
        
        # 🎯 SIMPLE SORT: Chỉ cần sort theo score, không hardcode
        top_matches = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:5]  # Top 5 thay vì 3
        logger.info(f"  - top_matches: {top_matches}")
        
        message = level_config.message_template
        
        # Tạo danh sách options sử dụng schema mới
        clarification_options = []
        
        # Thêm các lựa chọn từ top matches
        for i, (collection, score) in enumerate(top_matches, 1):
            score_float = float(score) if score is not None else 0.0
            
            # 🎯 USE ROUTER DATA: Simple title from collection name
            collection_title = collection.replace('quy_trinh_', '').replace('_', ' ').title()
            collection_description = f"Thủ tục trong lĩnh vực {collection_title.lower()}"
            
            clarification_options.append(ClarificationOption(
                id=str(i),
                title=collection_title,
                description=collection_description,
                action='proceed_with_collection',
                collection=collection,
                document=None,
                procedure=None,
                confidence_percent=round(score_float * 100, 1),
                question_text=None,
                source_file=None,
                context_type=None,
                category=None
            ))
        
        # Add "none of the above" option
        clarification_options.append(ClarificationOption(
            id='other',
            title="Không có thủ tục nào phù hợp",
            description="Tôi muốn hỏi về thủ tục khác",
            action='manual_input',
            collection=None,
            document=None,
            procedure=None,
            confidence_percent=0,
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Sử dụng schema chuẩn hóa
        return StandardClarificationResponse(
            type="clarification_needed",
            confidence_level="medium_confidence",
            confidence=float(confidence),
            message=message,
            target_collection=target_collection,
            document=None,
            procedure=None,
            options=clarification_options,
            requires_user_input=False,
            show_manual_input=False,
            manual_input_placeholder=None,
            style="multiple_choice",
            routing_context=routing_result,
            strategy=level_config.strategy,
            session_id=None,
            additional_help=None
        )
    
    def _generate_category_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> StandardClarificationResponse:
        """
        LOW CONFIDENCE (0.30-0.49): Category-based suggestions
        🎯 USE ROUTER DATA: Get collections from router instead of hardcode
        """
        message = level_config.message_template
        target_collection = routing_result.get('target_collection')
        
        # 🎯 GET COLLECTIONS FROM ROUTER: Use router's all_scores if available
        all_scores = routing_result.get('all_scores', {})
        
        # Tạo danh sách options sử dụng schema mới
        clarification_options = []
        
        if all_scores:
            # Use top collections from router
            top_collections = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (collection, score) in enumerate(top_collections, 1):
                collection_title = collection.replace('quy_trinh_', '').replace('_', ' ').title()
                score_float = float(score) if score is not None else 0.0
                
                clarification_options.append(ClarificationOption(
                    id=str(i),
                    title=collection_title,
                    description=f"Thủ tục trong lĩnh vực {collection_title.lower()}",
                    action='proceed_with_collection',
                    collection=collection,
                    document=None,
                    procedure=None,
                    confidence_percent=round(score_float * 100, 1),
                    question_text=None,
                    source_file=None,
                    context_type=None,
                    category=collection
                ))
        else:
            # Fallback: basic options
            clarification_options.append(ClarificationOption(
                id='1',
                title='Hộ tịch',
                description='Thủ tục về khai sinh, kết hôn, khai tử',
                action='proceed_with_collection',
                collection='quy_trinh_cap_ho_tich_cap_xa',
                document=None,
                procedure=None,
                confidence_percent=0,
                question_text=None,
                source_file=None,
                context_type=None,
                category='ho_tich'
            ))
            
            clarification_options.append(ClarificationOption(
                id='2',
                title='Chứng thực',
                description='Thủ tục chứng thực giấy tờ, hợp đồng',
                action='proceed_with_collection',
                collection='quy_trinh_chung_thuc',
                document=None,
                procedure=None,
                confidence_percent=0,
                question_text=None,
                source_file=None,
                context_type=None,
                category='chung_thuc'
            ))
        
        # Add manual input option
        clarification_options.append(ClarificationOption(
            id='manual',
            title="Tôi muốn mô tả rõ hơn",
            description="Để tôi diễn đạt lại câu hỏi một cách chi tiết hơn",
            action='manual_input',
            collection='',  # Empty string thay vì None
            document=None,
            procedure=None,
            confidence_percent=0,
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Sử dụng schema chuẩn hóa
        return StandardClarificationResponse(
            type="clarification_needed",
            confidence_level="low_confidence",
            confidence=float(confidence),
            message=message,
            target_collection=target_collection,
            document=None,
            procedure=None,
            options=clarification_options,
            requires_user_input=True,
            show_manual_input=True,
            manual_input_placeholder="Mô tả chi tiết tình huống của bạn...",
            style="category_based",
            routing_context=routing_result,
            strategy=level_config.strategy,
            session_id=None,
            additional_help="Bạn có thể mô tả cụ thể hơn về tình huống hoặc giấy tờ bạn cần làm"
        )
    
    def _generate_fallback_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any]
    ) -> StandardClarificationResponse:
        """Fallback clarification khi có lỗi"""
        message = "Xin lỗi, tôi cần thêm thông tin để hiểu rõ câu hỏi của bạn."
        target_collection = routing_result.get('target_collection')
        
        # Tạo options sử dụng schema chuẩn hóa
        clarification_options = []
        
        clarification_options.append(ClarificationOption(
            id='retry',
            title="Hãy diễn đạt lại câu hỏi",
            description="Tôi sẽ cố gắng hiểu rõ hơn",
            action='manual_input',
            collection=None,
            document=None,
            procedure=None,
            confidence_percent=0,
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Sử dụng schema chuẩn hóa
        return StandardClarificationResponse(
            type="clarification_needed",
            confidence_level="fallback",
            confidence=float(confidence),
            message=message,
            target_collection=target_collection,
            document=None,
            procedure=None,
            options=clarification_options,
            requires_user_input=True,
            show_manual_input=True,
            manual_input_placeholder="Vui lòng mô tả chi tiết hơn về câu hỏi của bạn...",
            style="fallback",
            routing_context=routing_result,
            strategy="fallback",
            session_id=None,
            additional_help="Bạn có thể cung cấp thêm thông tin hoặc diễn đạt lại câu hỏi một cách chi tiết hơn."
        )
    
    def handle_user_selection(
        self, 
        selected_option: Dict[str, Any], 
        session_id: str,
        smart_router = None
    ) -> Union[Dict[str, Any], StandardClarificationResponse]:
        """
        🎯 CENTRALIZED USER SELECTION HANDLING
        Handle all user selections for clarification flow
        """
        import time
        start_time = time.time()
        
        try:
            action = selected_option.get('action')
            collection = selected_option.get('collection')
            
            if action == 'show_document_questions':
                result = self._handle_show_document_questions(selected_option, session_id, smart_router)
            elif action == 'proceed_with_question':
                result = self._handle_proceed_with_question(selected_option, session_id)
            elif action == 'proceed_with_collection':
                result = self._handle_proceed_with_collection(selected_option, session_id, smart_router)
            elif action == 'proceed_with_document':
                result = self._handle_proceed_with_document(selected_option, session_id, smart_router)
            elif action == 'show_categories':
                result = self._handle_show_categories(selected_option, session_id)
            elif action == 'manual_input':
                result = self._handle_manual_input(selected_option, session_id)
            else:
                result = self._handle_unknown_action(selected_option, session_id)
            
            # Add processing_time to result
            if isinstance(result, dict):
                result["processing_time"] = time.time() - start_time
                
            return result
                
        except Exception as e:
            logger.error(f"❌ Error handling user selection: {e}")
            error_result = self._generate_error_response(str(e), session_id)
            if isinstance(error_result, dict):
                error_result["processing_time"] = time.time() - start_time
            return error_result
    
    def _handle_show_document_questions(
        self, 
        selected_option: Dict[str, Any], 
        session_id: str,
        smart_router = None
    ) -> Dict[str, Any]:
        """Handle show_document_questions action - INDEPENDENT CLARIFY METHOD"""
        try:
            collection = selected_option.get('collection')
            document = selected_option.get('document', '')
            procedure = selected_option.get('procedure', '')
            original_query = selected_option.get('original_query', '')  # Get from selected_option
            
            logger.info(f"🎯 ClarificationService: Showing questions for '{procedure}' in document '{document}'")
            
            # Use independent clarify method with original_query for real confidence calculation
            if document:
                matching_questions = self._get_questions_for_clarify(collection or "", document or "", original_query)
                logger.info(f"🚀 Retrieved {len(matching_questions)} questions from document {document}")
            else:
                # If no specific document, fallback to questions method
                matching_questions = self._get_fallback_questions_simple()
                logger.info(f"🔄 Fallback: Using default questions")
            
            # Create standardized question options (already in correct clarify format)
            options = []
            for i, q in enumerate(matching_questions[:8]):  # Top 8 questions
                question_text = q.get('text', str(q)) if isinstance(q, dict) else str(q)
                confidence = q.get('confidence', 0.5) if isinstance(q, dict) else 0.5
                options.append({
                    "id": str(i + 1),
                    "title": question_text,
                    "description": f"Câu hỏi về {procedure}",
                    "action": "proceed_with_question",
                    "collection": collection,
                    "document": document,
                    "procedure": procedure,
                    "question_text": question_text,
                    "confidence_percent": round(confidence * 100, 1),  # 🔥 ADD CONFIDENCE PERCENT
                    "source_file": q.get('source', '') if isinstance(q, dict) else '',
                    "category": q.get('category', 'general') if isinstance(q, dict) else 'general'
                })
            
            # Add manual input option
            options.append({
                "id": str(len(options) + 1),
                "title": "Câu hỏi khác...",
                "description": f"Tôi muốn hỏi về vấn đề khác trong {procedure}",
                "action": "manual_input",
                "collection": collection,
                "document": document,
                "procedure": procedure
            })
            
            # Return standardized DIRECT response
            return {
                "type": "clarification_needed",
                "confidence": None,  # No confidence at this stage
                "message": f"Đây là các câu hỏi về '{procedure}'. Hãy chọn câu hỏi phù hợp:",
                "answer": f"Đây là các câu hỏi về '{procedure}'. Hãy chọn câu hỏi phù hợp:",
                "options": options,  # ← DIRECT ACCESS - No nesting!
                "show_manual_input": True,
                "manual_input_placeholder": f"Hoặc nhập câu hỏi cụ thể về {procedure}...",
                "style": "document_questions",
                "target_collection": collection,
                "document": document,
                "procedure": procedure,
                "session_id": session_id,
                "routing_info": {
                    "context": "document_questions",
                    "source": "document_questions_handler",
                    "stage": "document_questions"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error showing document questions: {e}")
            return self._generate_error_response(str(e), session_id)
    
    def _handle_proceed_with_question(self, selected_option: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle proceed_with_question action - STANDARDIZED RESPONSE FOR RAG PIPELINE"""
        question_text = selected_option.get('question_text', '')
        original_query = selected_option.get('original_query', '')
        
        logger.info(f"🚀 Smart Clarification: Proceeding directly with question: '{question_text[:100]}...'")
        
        return {
            "type": "proceed_with_question",
            "final_query": question_text,
            "original_query": original_query,  # Keep original query for context
            "collection": selected_option.get('collection'),
            "document": selected_option.get('document'),
            "procedure": selected_option.get('procedure'),
            "session_id": session_id,
            "confidence": selected_option.get('confidence_percent', 0) / 100,
            "message": f"✅ Smart Clarification: Proceeding with high-confidence question directly to RAG processing"
        }
    
    def _handle_proceed_with_collection(self, selected_option: Dict[str, Any], session_id: str, smart_router = None) -> Dict[str, Any]:
        """Handle proceed_with_collection action - STEP 2: RETURNS DOCUMENT LIST"""
        collection = selected_option.get('collection')
        original_query = selected_option.get('original_query', '')
        
        # Use new method with real confidence calculation when original_query is available
        if original_query and original_query.strip():
            documents_info = self._get_documents_for_clarify_with_real_confidence(collection or "", original_query)
            logger.info(f"🎯 Using real confidence calculation for collection '{collection}' with query: '{original_query[:50]}...'")
        else:
            # Fallback to simple method when no original query
            documents_info = self._get_documents_for_clarify(collection or "")
            logger.info(f"⚠️ Using fallback confidence for collection '{collection}' (no original query)")
        
        # Create options from documents (already in correct clarify format)
        options = []
        for i, doc_info in enumerate(documents_info[:6]):  # Limit to 6 documents
            document_id = doc_info.get('document', f'DOC_{i+1:03d}')
            document_title = doc_info.get('title', f'Tài liệu {i+1}')
            confidence = doc_info.get('confidence', 0.5)
            
            options.append({
                "id": str(i + 1),
                "title": document_title,
                "description": f"Tài liệu thuộc {collection} (độ phù hợp: {confidence*100:.1f}%)",
                "action": "proceed_with_document",
                "collection": collection,
                "document": document_id,
                "confidence_percent": round(confidence * 100, 1)
            })
        
        # Add manual input option for this collection
        options.append({
            "id": str(len(options) + 1),
            "title": "Không thấy tài liệu phù hợp",
            "description": f"Tôi muốn nhập câu hỏi trực tiếp về {collection}",
            "action": "manual_input",
            "collection": collection
        })
        
        # Return document selection step - DIRECT STRUCTURE
        return {
            "type": "clarification_needed",
            "confidence": None,
            "message": f"Hãy chọn tài liệu trong '{collection}' mà bạn quan tâm:",
            "answer": f"Hãy chọn tài liệu trong '{collection}' mà bạn quan tâm:",
            "options": options,  # ← DIRECT ACCESS - No nesting!
            "show_manual_input": True,
            "manual_input_placeholder": f"Hoặc nhập câu hỏi cụ thể về {collection}...",
            "style": "document_selection",
            "target_collection": collection,
            "session_id": session_id,
            "routing_info": {
                "context": "document_selection",
                "stage": "document_selection"
            }
        }
    
    def _handle_proceed_with_document(self, selected_option: Dict[str, Any], session_id: str, smart_router = None) -> Dict[str, Any]:
        """Handle proceed_with_document action - STEP 3: RETURNS QUESTION LIST"""
        collection = selected_option.get('collection')
        document = selected_option.get('document')
        original_query = selected_option.get('original_query', '')  # Get from selected_option
        
        # Use independent clarify method with original_query for real confidence calculation
        document_questions = self._get_questions_for_clarify(collection or "", document or "", original_query)
        
        # Create options from document questions (already in correct clarify format)
        options = []
        for i, q in enumerate(document_questions[:8]):  # Limit to 8 questions
            question_text = q.get('text', str(q)) if isinstance(q, dict) else str(q)
            confidence = q.get('confidence', 0.5)
            source_file = q.get('source', f'{collection}/documents/{document}/questions.json')
            
            options.append({
                "id": str(i + 1),
                "title": question_text,
                "description": f"Câu hỏi về {document} (độ phù hợp: {confidence*100:.1f}%)",
                "action": "proceed_with_question",
                "collection": collection,
                "document": document,
                "question_text": question_text,
                "confidence_percent": round(confidence * 100, 1),
                "source_file": source_file,
                "category": q.get('category', 'general') if isinstance(q, dict) else 'general'
            })
        
        # Add manual input option for this document
        options.append({
            "id": str(len(options) + 1),
            "title": "Câu hỏi khác...",
            "description": f"Tôi muốn hỏi về vấn đề khác trong {document}",
            "action": "manual_input",
            "collection": collection,
            "document": document
        })
        
        # Return question selection step - DIRECT STRUCTURE
        return {
            "type": "clarification_needed",
            "confidence": None,
            "message": f"Đây là các câu hỏi phổ biến về '{document}'. Hãy chọn câu hỏi phù hợp:",
            "answer": f"Đây là các câu hỏi phổ biến về '{document}'. Hãy chọn câu hỏi phù hợp:",
            "options": options,  # ← DIRECT ACCESS - No nesting!
            "show_manual_input": True,
            "manual_input_placeholder": f"Hoặc nhập câu hỏi cụ thể về {document}...",
            "style": "document_questions",
            "target_collection": collection,
            "document": document,
            "session_id": session_id,
            "routing_info": {
                "context": "document_questions",
                "stage": "document_questions"
            }
        }
    
    def _handle_show_categories(self, selected_option: Dict[str, Any], session_id: str) -> StandardClarificationResponse:
        """Handle show_categories action"""
        # Tạo một đối tượng routing_result trống và thêm session_id
        routing_result = {"session_id": session_id}
        
        response = self._generate_category_clarification(
            confidence=0.0,
            routing_result=routing_result,
            level_config=self.clarification_levels['low_confidence']
        )
        return response
    
    def _handle_manual_input(self, selected_option: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle manual_input action - PRESERVE SELECTED CONTEXT"""
        collection = selected_option.get('collection')
        document = selected_option.get('document') 
        procedure = selected_option.get('procedure')
        
        logger.info(f"🔥 Manual input request with preserved context: collection={collection}, document={document}, procedure={procedure}")
        
        return {
            "type": "manual_input_request",
            "message": "Please provide your specific question",
            "collection": collection,  # Preserve selected collection
            "document": document,      # Preserve selected document  
            "procedure": procedure,    # Preserve selected procedure
            "session_id": session_id,
            "context_preserved": True,  # Flag to indicate context preservation
            "force_routing": True,      # Flag to force router into this context
            "routing_info": {
                "context": "manual_input_with_context",
                "source": "manual_input_handler", 
                "stage": "manual_input",
                "force_collection": collection,
                "force_document": document
            }
        }
    
    def _handle_unknown_action(self, selected_option: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle unknown actions"""
        return self._generate_error_response(f"Unknown action: {selected_option.get('action')}", session_id)
    
    def _generate_error_response(self, error_message: str, session_id: str) -> Dict[str, Any]:
        """Generate standardized error response"""
        return {
            "type": "error",
            "error": error_message,
            "session_id": session_id,
            "message": "An error occurred during clarification processing"
        }
    
    def get_related_procedures(self, collection: str, procedure: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Lấy các thủ tục liên quan trong cùng collection
        (Có thể integrate với smart_router để lấy similar procedures)
        """
        # Placeholder - sẽ integrate với smart_router
        return []
    
    # 🔥 NEW: EMBEDDING SIMILARITY METHODS
    def get_similarity_ranked_questions(
        self, 
        query: str, 
        collection: str, 
        document: Optional[str] = None,
        limit: int = 5,
        smart_router = None
    ) -> List[Dict[str, Any]]:
        """
        🔥 ENHANCED: Get questions ranked by embedding similarity
        """
        try:
            if not self.similarity_available or not self.embedding_model:
                # Fallback to simple retrieval if no embedding model
                return self._get_fallback_questions(collection, document, limit, smart_router)
            
            # Get questions from router
            if document and smart_router:
                questions = smart_router.get_questions_from_specific_document(collection, document)
            elif smart_router:
                questions = smart_router.get_example_questions_for_collection(collection)
            else:
                return []
            
            if not questions:
                return []
            
            # 🔧 EMBEDDING SIMILARITY CALCULATION
            query_embedding = self.embedding_model.encode([query])
            
            # Extract question texts and compute embeddings
            question_texts = []
            question_data = []
            
            for q in questions:
                if isinstance(q, dict):
                    text = q.get('text', '')
                    question_texts.append(text)
                    question_data.append(q)
                else:
                    text = str(q)
                    question_texts.append(text)
                    question_data.append({'text': text})
            
            if not question_texts:
                return []
            
            # Compute similarities
            question_embeddings = self.embedding_model.encode(question_texts)
            similarities = self.cosine_similarity(query_embedding, question_embeddings)[0]
            
            # Combine with similarity scores and sort
            ranked_questions = []
            for i, (question, similarity) in enumerate(zip(question_data, similarities)):
                question_copy = question.copy() if isinstance(question, dict) else {'text': str(question)}
                similarity_score = float(similarity)
                # Lưu trữ score dưới dạng string để tránh lỗi typing
                question_copy['similarity_score'] = str(similarity_score)
                question_copy['similarity_percent'] = str(round(similarity_score * 100, 1))
                ranked_questions.append(question_copy)
            
            # Sort by similarity descending - chuyển về float khi so sánh
            ranked_questions.sort(key=lambda x: float(x['similarity_score']), reverse=True)
            
            logger.info(f"🔥 Similarity ranking: {len(ranked_questions)} questions ranked for query")
            
            return ranked_questions[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error in similarity ranking: {e}")
            return self._get_fallback_questions(collection, document, limit, smart_router)
    
    def _get_fallback_questions(
        self, 
        collection: str, 
        document: Optional[str] = None,
        limit: int = 5,
        smart_router = None
    ) -> List[Dict[str, Any]]:
        """Fallback question retrieval without similarity"""
        try:
            if document and smart_router:
                questions = smart_router.get_questions_from_specific_document(collection, document)
            elif smart_router:
                questions = smart_router.get_example_questions_for_collection(collection)
            else:
                return []
            
            # Convert to standard format
            standardized = []
            for q in questions[:limit]:
                if isinstance(q, dict):
                    standardized.append(q)
                else:
                    standardized.append({'text': str(q), 'similarity_percent': 0})
            
            return standardized
            
        except Exception as e:
            logger.error(f"❌ Error in fallback questions: {e}")
            return []
    
    def calculate_query_collection_relevance(self, query: str, collection: str) -> float:
        """
        🔧 ENHANCED: Calculate relevance between query and collection
        Simple keyword-based approach for now, can be enhanced with embeddings
        """
        try:
            # Basic keyword matching
            query_lower = query.lower()
            collection_lower = collection.lower().replace('quy_trinh_', '').replace('_', ' ')
            
            # Count keyword matches
            collection_words = collection_lower.split()
            matches = sum(1 for word in collection_words if word in query_lower)
            
            # Calculate relevance
            if len(collection_words) == 0:
                return 0.0
            
            relevance = matches / len(collection_words)
            
            # Bonus for exact phrase match
            if collection_lower in query_lower:
                relevance += 0.3
            
            return min(1.0, relevance)
            
        except Exception as e:
            logger.error(f"❌ Error calculating relevance: {e}")
            return 0.0

    def handle_clarification(
        self,
        session_id: str,
        selected_option: Dict[str, Any],
        original_query: str,
        smart_router=None
    ) -> Union[Dict[str, Any], StandardClarificationResponse]:
        """
        🎯 MAIN CLARIFICATION HANDLER - Moved from RagEngine for proper separation of concerns
        
        Handle all clarification logic independently from RAG processing.
        This method replaces the wrapper in RagEngine.
        
        Args:
            session_id: Current session ID
            selected_option: User's selected clarification option
            original_query: Original user query for similarity calculation
            smart_router: Optional router instance for advanced features
            
        Returns:
            Dict containing clarification response
        """
        import time
        start_time = time.time()
        
        try:
            # Extract action from selected option
            action = selected_option.get('action')
            logger.info(f"🎯 Processing clarification action: '{action}' for session {session_id}")
            
            # Add original query to selected_option for similarity calculation
            if original_query and original_query.strip():
                selected_option['original_query'] = original_query
                logger.info(f"🔍 Using original query for similarity: '{original_query[:50]}...'")
            
            # Delegate to existing user selection handler
            result = self.handle_user_selection(
                selected_option=selected_option,
                session_id=session_id,
                smart_router=smart_router
            )
            
            # Ensure processing time is included
            if isinstance(result, dict) and 'processing_time' not in result:
                result['processing_time'] = time.time() - start_time
            
            logger.info(f"✅ Clarification completed for action '{action}' in {time.time() - start_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error handling clarification: {e}")
            return {
                "type": "error",
                "error": f"Clarification processing failed: {str(e)}",
                "session_id": session_id,
                "processing_time": time.time() - start_time
            }
