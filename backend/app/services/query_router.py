"""
Unified Query Router Service
Gộp 3 modes: Basic, Enhanced, và Cached routing strategies
"""

import logging
import os
import json
import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Unified Query Router với 3 modes:
    - basic: Keywords matching (nhanh, ít tài nguyên)
    - enhanced: Example questions database (chính xác cao)
    - cached: Pre-computed vectors (nhanh + chính xác)
    """
    
    def __init__(self, embedding_model: Optional[SentenceTransformer] = None, mode: str = "cached"):
        """
        Args:
            embedding_model: Model để encode queries 
            mode: "basic", "enhanced", hoặc "cached"
        """
        self.embedding_model = embedding_model
        self.mode = mode
        
        # Common settings
        self.similarity_threshold = 0.3
        self.high_confidence_threshold = 0.5
        
        # Data placeholders
        self.config = {}
        self.example_questions = {}
        self.question_vectors = {}
        self.collection_mappings = {}
        self.collections_config = {}
        
        # Initialize based on mode
        if mode == "basic":
            self._init_basic_mode()
        elif mode == "enhanced":
            self._init_enhanced_mode()
        elif mode == "cached":
            self._init_cached_mode()
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'basic', 'enhanced', or 'cached'")
        
        logger.info(f"✅ Query Router initialized in {mode} mode")
    
    def _init_basic_mode(self):
        """Initialize basic keywords-based routing"""
        self.collections_config = {
            'ho_tich_cap_xa': {
                'name': 'Hộ tịch cấp xã',
                'keywords': 'hộ tịch, cấp xã, khai sinh, kết hôn, khai tử, giám hộ, trích lục, bản sao, đăng ký lại, yếu tố nước ngoài, lưu động, tình trạng hôn nhân, giấy khai sinh, xác nhận hộ tịch, nhận cha mẹ con, cải chính, bổ sung, thay đổi thông tin, dân tộc, chấm dứt giám hộ, giám sát giám hộ',
                'sample_queries': [
                    'làm thế nào để đăng ký khai sinh',
                    'thủ tục kết hôn cần gì',
                    'cách cấp trích lục hộ tịch',
                    'đăng ký khai tử như thế nào',
                    'thủ tục giám hộ trẻ em'
                ]
            },
            
            'chung_thuc': {
                'name': 'Chứng thực',  
                'keywords': 'chứng thực, hợp đồng, giao dịch, di chúc, bản sao, chữ ký, di sản, sửa đổi, bổ sung, hủy bỏ, người dịch, tài sản, động sản, quyền sử dụng đất, nhà ở, từ chối nhận di sản, thỏa thuận phân chia, khai nhận di sản, cộng tác viên dịch thuật, sai sót trong hợp đồng',
                'sample_queries': [
                    'chứng thực hợp đồng mua bán',
                    'làm di chúc cần chứng thực gì',
                    'chứng thực bản sao giấy tờ',
                    'thủ tục chứng thực chữ ký',
                    'sửa lỗi trong hợp đồng đã chứng thực'
                ]
            },
            
            'nuoi_con_nuoi': {
                'name': 'Nuôi con nuôi',
                'keywords': 'nuôi con nuôi, đăng ký, STP, yếu tố nước ngoài, trẻ em, cơ sở nuôi dưỡng, cha dượng, mẹ kế, xác nhận, nhận con riêng, cô cậu dì chú bác ruột, nhận cháu làm con nuôi, người nước ngoài thường trú, công dân việt nam, đủ điều kiện',
                'sample_queries': [
                    'thủ tục nhận con nuôi trong nước',
                    'người nước ngoài nhận con nuôi việt nam',
                    'cha dượng nhận con riêng của vợ',
                    'cô ruột nhận cháu làm con nuôi'
                ]
            }
        }
    
    def _init_enhanced_mode(self):
        """Initialize enhanced mode với example questions database"""
        self.base_path = "data/router_examples"
        
        # Load configuration
        self.config = self._load_config()
        
        # Load example questions
        self._load_example_questions()
        self._initialize_question_vectors()
        
        logger.info(f"✅ Enhanced mode loaded with {len(self.collection_mappings)} collections")
    
    def _init_cached_mode(self):
        """Initialize cached mode với pre-computed vectors"""
        self.cache_path = "data/cache/router_cache.pkl"
        self._load_from_cache()
        
        logger.info(f"✅ Cached mode loaded with {len(self.collection_mappings)} collections")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from index.json"""
        try:
            config_path = os.path.join(self.base_path, "index.json")
            if not os.path.exists(config_path):
                logger.warning(f"Config file not found: {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.info(f"📋 Loaded router configuration v{config.get('metadata', {}).get('version', '1.0')}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return {}
    
    def _load_example_questions(self):
        """Load all example questions from JSON files"""
        try:
            collection_mappings = self.config.get('collection_mappings', {})
            
            for collection_name, mapping_info in collection_mappings.items():
                example_files = mapping_info.get('example_files', [])
                self.collection_mappings[collection_name] = {
                    'display_name': mapping_info.get('description', collection_name),
                    'total_questions': 0
                }
                
                collection_questions = []
                
                for file_path in example_files:
                    full_path = os.path.join(self.base_path, file_path)
                    if not os.path.exists(full_path):
                        logger.warning(f"Example file not found: {full_path}")
                        continue
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        questions = data.get('example_questions', [])
                        for question_data in questions:
                            # Main question
                            main_question = {
                                'text': question_data['question'],
                                'collection': collection_name,
                                'source': data['metadata']['title'],
                                'keywords': question_data.get('semantic_keywords', []),
                                'type': 'main'
                            }
                            collection_questions.append(main_question)
                            
                            # Question variants
                            variants = question_data.get('question_variants', [])
                            for variant in variants:
                                variant_question = {
                                    'text': variant,
                                    'collection': collection_name,
                                    'source': data['metadata']['title'],
                                    'keywords': question_data.get('semantic_keywords', []),
                                    'type': 'variant'
                                }
                                collection_questions.append(variant_question)
                    
                    except Exception as e:
                        logger.error(f"Error loading {full_path}: {e}")
                        continue
                
                self.example_questions[collection_name] = collection_questions
                self.collection_mappings[collection_name]['total_questions'] = len(collection_questions)
                
                logger.info(f"📚 Loaded {len(collection_questions)} questions for {collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Error loading example questions: {e}")
    
    def _initialize_question_vectors(self):
        """Initialize question vectors for enhanced mode"""
        if not self.embedding_model:
            logger.error("❌ No embedding model provided for enhanced mode")
            return
        
        try:
            for collection_name, questions in self.example_questions.items():
                if not questions:
                    continue
                
                question_texts = [q['text'] for q in questions]
                vectors = self.embedding_model.encode(question_texts, show_progress_bar=False)
                
                self.question_vectors[collection_name] = {
                    'vectors': vectors,
                    'questions': questions
                }
                
                logger.info(f"🔢 Created {len(vectors)} vectors for {collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Error creating question vectors: {e}")
    
    def _load_from_cache(self):
        """Load cached vectors and data"""
        try:
            if not os.path.exists(self.cache_path):
                logger.error(f"❌ Cache file not found: {self.cache_path}")
                logger.error("💡 Run 'python tools/3_generate_smart_router.py' to build cache first")
                raise FileNotFoundError(f"Router cache not found. Please run: python tools/3_generate_smart_router.py")
            
            logger.info(f"⚡ Loading router data from cache: {self.cache_path}")
            
            with open(self.cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Validate cache data
            required_keys = ['config', 'example_questions', 'question_vectors', 'collection_mappings', 'metadata']
            for key in required_keys:
                if key not in cache_data:
                    raise ValueError(f"Invalid cache: missing key '{key}'")
            
            # Load data
            self.config = cache_data['config']
            self.example_questions = cache_data['example_questions']
            self.question_vectors = cache_data['question_vectors']
            self.collection_mappings = cache_data['collection_mappings']
            
            # Log cache info
            metadata = cache_data['metadata']
            created_at = cache_data.get('created_at', 'unknown')
            
            logger.info(f"📊 Cache loaded successfully:")
            logger.info(f"   - Created: {created_at}")
            logger.info(f"   - Collections: {metadata['total_collections']}")
            logger.info(f"   - Questions: {metadata['total_questions']}")
            logger.info(f"   - Vector dimensions: {metadata['vector_dimensions']}")
            
        except Exception as e:
            logger.error(f"❌ Error loading from cache: {e}")
            logger.error("💡 Try running: python tools/3_generate_smart_router.py")
            raise
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """
        Main routing method - chooses strategy based on mode
        
        Returns:
            Dict chứa:
            - collection_name: Tên collection được chọn
            - confidence_score: Độ tin cậy (0-1)  
            - routing_strategy: Chiến lược routing đã sử dụng
            - metadata: Thông tin bổ sung
        """
        if self.mode == "basic":
            return self._route_basic(query)
        elif self.mode == "enhanced":
            return self._route_enhanced(query)
        elif self.mode == "cached":
            return self._route_cached(query)
        else:
            return self._fallback_route()
    
    def _route_basic(self, query: str) -> Dict[str, Any]:
        """Basic routing using keyword matching"""
        query_lower = query.lower()
        scores = {}
        
        for collection_id, config in self.collections_config.items():
            keywords = config['keywords'].lower().split(', ')
            score = sum(1 for keyword in keywords if keyword in query_lower)
            
            # Normalize score
            if keywords:
                scores[collection_id] = score / len(keywords)
            else:
                scores[collection_id] = 0
        
        if not scores:
            return self._fallback_route()
        
        best_collection = max(scores.items(), key=lambda x: x[1])
        
        return {
            'collection_name': best_collection[0],
            'confidence_score': best_collection[1],
            'routing_strategy': 'basic_keywords',
            'all_scores': scores,
            'metadata': {
                'collection_display_name': self.collections_config[best_collection[0]]['name'],
                'matched_keywords': self._get_matched_keywords(query, best_collection[0])
            }
        }
    
    def _route_enhanced(self, query: str) -> Dict[str, Any]:
        """Enhanced routing using example questions"""
        try:
            if not self.embedding_model or not self.question_vectors:
                logger.warning("Enhanced mode not properly initialized, falling back")
                return self._fallback_route()
            
            # Encode query
            query_vector = self.embedding_model.encode([query])[0]
            
            collection_scores = {}
            best_matches = {}
            
            for collection_name, vector_data in self.question_vectors.items():
                if not vector_data['vectors'].size:
                    continue
                
                # Calculate similarities
                similarities = cosine_similarity([query_vector], vector_data['vectors'])[0]
                best_idx = np.argmax(similarities)
                best_score = similarities[best_idx]
                
                collection_scores[collection_name] = best_score
                best_matches[collection_name] = {
                    'question': vector_data['questions'][best_idx],
                    'similarity': best_score
                }
            
            if not collection_scores:
                return self._fallback_route()
            
            best_collection = max(collection_scores.items(), key=lambda x: x[1])
            
            return {
                'collection_name': best_collection[0],
                'confidence_score': best_collection[1],
                'routing_strategy': 'enhanced_similarity',
                'all_scores': collection_scores,
                'matched_question': best_matches[best_collection[0]]['question']['text'],
                'metadata': {
                    'collection_display_name': self.collection_mappings[best_collection[0]]['display_name'],
                    'question_type': best_matches[best_collection[0]]['question']['type'],
                    'source_document': best_matches[best_collection[0]]['question']['source']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced routing: {e}")
            return self._fallback_route()
    
    def _route_cached(self, query: str) -> Dict[str, Any]:
        """Cached routing using pre-computed vectors"""
        try:
            if not self.embedding_model or not self.question_vectors:
                logger.error("Cached mode not properly loaded")
                return self._fallback_route()
            
            # Encode query
            query_vector = self.embedding_model.encode([query])[0]
            
            collection_scores = {}
            best_matches = {}
            
            for collection_name, vector_data in self.question_vectors.items():
                vectors = vector_data['vectors']
                questions = vector_data['questions']
                
                if len(vectors) == 0:
                    continue
                
                # Calculate similarities
                similarities = cosine_similarity([query_vector], vectors)[0]
                best_idx = np.argmax(similarities)
                best_score = similarities[best_idx]
                
                collection_scores[collection_name] = best_score
                best_matches[collection_name] = {
                    'question': questions[best_idx],
                    'similarity': best_score
                }
            
            if not collection_scores:
                return self._fallback_route()
            
            best_collection = max(collection_scores.items(), key=lambda x: x[1])
            
            return {
                'collection_name': best_collection[0],
                'confidence_score': best_collection[1],
                'routing_strategy': 'cached_similarity',
                'all_scores': collection_scores,
                'matched_question': best_matches[best_collection[0]]['question']['text'],
                'metadata': {
                    'collection_display_name': self.collection_mappings.get(best_collection[0], {}).get('display_name', best_collection[0]),
                    'question_type': best_matches[best_collection[0]]['question'].get('type', 'unknown'),
                    'source_document': best_matches[best_collection[0]]['question'].get('source', 'unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error in cached routing: {e}")
            return self._fallback_route()
    
    def _get_matched_keywords(self, query: str, collection_id: str) -> List[str]:
        """Get keywords that matched in basic mode"""
        query_lower = query.lower()
        keywords = self.collections_config[collection_id]['keywords'].lower().split(', ')
        return [kw for kw in keywords if kw in query_lower]
    
    def _fallback_route(self) -> Dict[str, Any]:
        """Fallback routing when other methods fail"""
        # Default to first available collection or a safe default
        if self.collections_config:
            default_collection = list(self.collections_config.keys())[0]
        elif self.collection_mappings:
            default_collection = list(self.collection_mappings.keys())[0]
        else:
            default_collection = "ho_tich_cap_xa"
        
        return {
            'collection_name': default_collection,
            'confidence_score': 0.1,
            'routing_strategy': 'fallback',
            'all_scores': {},
            'metadata': {
                'reason': 'fallback_used',
                'message': 'Không thể xác định collection phù hợp, sử dụng mặc định'
            }
        }
    
    def get_available_collections(self) -> Dict[str, str]:
        """Get list of available collections"""
        if self.mode == "basic":
            return {k: v['name'] for k, v in self.collections_config.items()}
        else:
            return {k: v.get('display_name', k) for k, v in self.collection_mappings.items()}
    
    def get_mode_info(self) -> Dict[str, Any]:
        """Get information about current mode"""
        if self.mode == "basic":
            total_collections = len(self.collections_config)
            total_keywords = sum(len(v['keywords'].split(', ')) for v in self.collections_config.values())
            return {
                'mode': self.mode,
                'total_collections': total_collections,
                'total_keywords': total_keywords,
                'features': ['keyword_matching', 'fast_startup']
            }
        elif self.mode in ["enhanced", "cached"]:
            total_collections = len(self.collection_mappings)
            total_questions = sum(v.get('total_questions', 0) for v in self.collection_mappings.values())
            return {
                'mode': self.mode,
                'total_collections': total_collections,
                'total_questions': total_questions,
                'features': ['similarity_matching', 'high_accuracy', 'example_based']
            }
        else:
            return {'mode': self.mode, 'status': 'unknown'}


# Legacy classes for backward compatibility
class EnhancedSmartQueryRouter(QueryRouter):
    """Backward compatibility wrapper"""
    def __init__(self, embedding_model: SentenceTransformer):
        super().__init__(embedding_model, mode="enhanced")


class CachedEnhancedSmartQueryRouter(QueryRouter):
    """Backward compatibility wrapper"""  
    def __init__(self, embedding_model: SentenceTransformer):
        super().__init__(embedding_model, mode="cached")


# Ambiguous Query Service (từ enhanced_smart_query_router.py)
class RouterBasedAmbiguousQueryService:
    """Service phát hiện và xử lý câu hỏi mơ hồ dựa trên router confidence"""
    
    def __init__(self, router: QueryRouter, llm_service):
        self.router = router
        self.llm_service = llm_service
        self.ambiguous_threshold = 0.3  # Threshold để xác định câu hỏi mơ hồ
        
    def detect_ambiguous_query(self, query: str) -> Dict[str, Any]:
        """
        Phát hiện câu hỏi mơ hồ dựa trên confidence score của router
        
        Returns:
            Dict chứa:
            - is_ambiguous: bool - có phải câu hỏi mơ hồ không
            - confidence: float - confidence score từ router
            - category: str - loại câu hỏi mơ hồ
            - suggested_collections: List[str] - các collection có thể liên quan
        """
        try:
            # Route query để lấy confidence score
            route_result = self.router.route_query(query)
            confidence = route_result.get('confidence_score', 0)
            
            # Xác định câu hỏi mơ hồ nếu confidence thấp
            is_ambiguous = confidence < self.ambiguous_threshold
            
            if is_ambiguous:
                # Lấy các collection có score cao
                all_scores = route_result.get('all_scores', {})
                sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
                
                # Lấy top collections có score gần nhau (chênh lệch < 0.1)
                top_score = sorted_scores[0][1] if sorted_scores else 0
                suggested_collections = [
                    coll for coll, score in sorted_scores 
                    if score >= top_score - 0.1 and score > 0
                ]
                
                # Xác định category dựa trên pattern
                category = self._categorize_ambiguous_query(query, suggested_collections)
                
                return {
                    'is_ambiguous': True,
                    'confidence': confidence,
                    'category': category,
                    'suggested_collections': suggested_collections[:3],  # Tối đa 3 suggestions
                    'route_result': route_result
                }
            
            return {
                'is_ambiguous': False,
                'confidence': confidence,
                'category': 'clear',
                'suggested_collections': [route_result.get('collection_name')],
                'route_result': route_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error detecting ambiguous query: {e}")
            return {
                'is_ambiguous': False,
                'confidence': 0.1,
                'category': 'error',
                'suggested_collections': [],
                'error': str(e)
            }
    
    def _categorize_ambiguous_query(self, query: str, suggested_collections: List[str]) -> str:
        """Phân loại câu hỏi mơ hồ"""
        query_lower = query.lower()
        
        # General queries
        general_patterns = ['làm thế nào', 'cần gì', 'như thế nào', 'có được không', 'thủ tục']
        if any(pattern in query_lower for pattern in general_patterns):
            return 'general_procedure'
        
        # Multiple domains
        if len(suggested_collections) > 1:
            return 'multiple_domains'
        
        # Vague terms
        vague_terms = ['giấy tờ', 'thủ tục', 'quy định', 'pháp luật']
        if any(term in query_lower for term in vague_terms):
            return 'vague_terminology'
        
        return 'unclear_intent'
