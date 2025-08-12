"""
Enhanced Smart Query Router Service
Định tuyến câu hỏi đến đúng collection dựa trên example questions database
"""

import logging
import numpy as np
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class EnhancedSmartQueryRouter:
    """Router thông minh sử dụng database example questions cho routing chính xác"""
    
    def __init__(self, embedding_model: SentenceTransformer):
        self.embedding_model = embedding_model
        self.base_path = "data/router_examples"
        
        # Load configuration
        self.config = self._load_config()
        
        # Example questions database
        self.example_questions = {}
        self.question_vectors = {}
        self.collection_mappings = {}
        
        # Thresholds
        self.similarity_threshold = 0.3
        self.high_confidence_threshold = 0.5
        
        # Initialize database
        self._load_example_questions()
        self._initialize_question_vectors()
        
        logger.info(f"✅ Enhanced Smart Query Router initialized with {len(self.collection_mappings)} collections")
    
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
                        
                        logger.info(f"📚 Loaded {len(questions)} procedures from {data['metadata']['title']}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error loading {full_path}: {e}")
                        continue
                
                self.example_questions[collection_name] = collection_questions
                self.collection_mappings[collection_name]['total_questions'] = len(collection_questions)
                
                logger.info(f"🎯 Collection '{collection_name}': {len(collection_questions)} example questions")
                
        except Exception as e:
            logger.error(f"❌ Error loading example questions: {e}")
            raise
    
    def _initialize_question_vectors(self):
        """Tính toán vectors cho tất cả example questions"""
        try:
            for collection_name, questions in self.example_questions.items():
                collection_vectors = []
                
                for question in questions:
                    # Combine question text with keywords for better representation
                    keywords_text = " ".join(question.get('keywords', []))
                    combined_text = f"{question['text']} {keywords_text}"
                    
                    # Create embedding
                    vector = self.embedding_model.encode([combined_text])[0]
                    collection_vectors.append(vector)
                
                if collection_vectors:
                    # Store vectors as numpy array for efficient similarity computation
                    self.question_vectors[collection_name] = np.array(collection_vectors)
                    logger.info(f"🎯 Vectorized {len(collection_vectors)} questions for {collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Error initializing question vectors: {e}")
            raise
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """
        Định tuyến câu hỏi đến collection phù hợp nhất dựa trên example questions
        
        Returns:
            {
                'status': 'routed' | 'ambiguous' | 'no_match',
                'target_collection': str | None,
                'confidence': float,
                'all_scores': Dict[str, float],
                'display_name': str | None,
                'clarification_needed': bool,
                'matched_example': str | None,
                'source_procedure': str | None
            }
        """
        try:
            # Create vector for query
            query_vector = self.embedding_model.encode([query])[0]
            
            # Find best matching example question across all collections
            best_collection = None
            best_score = 0.0
            best_example = None
            best_source = None
            collection_scores = {}
            
            for collection_name, questions in self.example_questions.items():
                if collection_name not in self.question_vectors:
                    continue
                
                # Calculate similarities with all questions in this collection
                question_vectors = self.question_vectors[collection_name]
                similarities = cosine_similarity(
                    query_vector.reshape(1, -1),
                    question_vectors
                )[0]
                
                # Get best match in this collection
                max_idx = np.argmax(similarities)
                max_similarity = similarities[max_idx]
                collection_scores[collection_name] = float(max_similarity)
                
                # Update global best
                if max_similarity > best_score:
                    best_score = max_similarity
                    best_collection = collection_name
                    best_example = questions[max_idx]['text']
                    best_source = questions[max_idx]['source']
            
            logger.info(f"🎯 Query: '{query[:50]}...' -> Best match: {best_collection} ({best_score:.3f})")
            if best_example:
                logger.info(f"📝 Matched example: '{best_example[:80]}...'")
            
            # Determine routing decision
            if best_score >= self.high_confidence_threshold:
                # High confidence - route immediately
                return {
                    'status': 'routed',
                    'target_collection': best_collection,
                    'confidence': best_score,
                    'all_scores': collection_scores,
                    'display_name': self.collection_mappings.get(best_collection, {}).get('display_name'),
                    'clarification_needed': False,
                    'matched_example': best_example,
                    'source_procedure': best_source
                }
            
            elif best_score >= self.similarity_threshold:
                # Medium confidence - route but note
                return {
                    'status': 'routed',
                    'target_collection': best_collection,
                    'confidence': best_score,
                    'all_scores': collection_scores,
                    'display_name': self.collection_mappings.get(best_collection, {}).get('display_name'),
                    'clarification_needed': False,
                    'matched_example': best_example,
                    'source_procedure': best_source
                }
            
            else:
                # Low similarity - needs clarification
                return {
                    'status': 'ambiguous',
                    'target_collection': None,
                    'confidence': best_score,
                    'all_scores': collection_scores,
                    'display_name': None,
                    'clarification_needed': True,
                    'matched_example': best_example,
                    'source_procedure': best_source
                }
                
        except Exception as e:
            logger.error(f"❌ Error in enhanced query routing: {e}")
            return {
                'status': 'no_match',
                'target_collection': None,
                'confidence': 0.0,
                'all_scores': {},
                'display_name': None,
                'clarification_needed': True,
                'matched_example': None,
                'source_procedure': None
            }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Trả về thông tin về tất cả collections"""
        return {
            'total_collections': len(self.collection_mappings),
            'collections': self.collection_mappings,
            'total_questions': sum(info['total_questions'] for info in self.collection_mappings.values())
        }
    
    def get_example_questions_for_collection(self, collection_name: str) -> List[Dict[str, Any]]:
        """Trả về tất cả example questions cho một collection"""
        return self.example_questions.get(collection_name, [])

class RouterBasedAmbiguousQueryService:
    """Service xử lý câu hỏi mơ hồ dựa trên router results"""
    
    def __init__(self, router: EnhancedSmartQueryRouter):
        self.router = router
        self.clarification_templates = {
            'ambiguous': [
                "Câu hỏi của bạn có thể liên quan đến nhiều lĩnh vực. Bạn có thể cung cấp thêm thông tin cụ thể không?",
                "Để hỗ trợ bạn tốt hơn, bạn có thể nói rõ hơn về vấn đề bạn quan tâm?",
                "Câu hỏi của bạn khá chung. Bạn có thể chỉ rõ bạn muốn tìm hiểu về thủ tục nào cụ thể?"
            ],
            'no_match': [
                "Xin lỗi, tôi không tìm thấy thông tin phù hợp với câu hỏi của bạn trong cơ sở dữ liệu hiện tại.",
                "Câu hỏi này có vẻ nằm ngoài phạm vi hỗ trợ của tôi. Bạn có thể hỏi về các thủ tục hành chính khác không?",
                "Tôi không có thông tin về vấn đề này. Bạn có thể tham khảo trực tiếp tại cơ quan có thẩm quyền."
            ]
        }
        
        logger.info("✅ Router-based Ambiguous Query Service initialized")
    
    def is_ambiguous(self, query: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Kiểm tra query có ambiguous không dựa trên router results
        
        Returns:
            (is_ambiguous, routing_result)
        """
        try:
            routing_result = self.router.route_query(query)
            
            is_ambiguous = routing_result['status'] in ['ambiguous', 'no_match']
            
            if is_ambiguous:
                logger.info(f"🤔 Ambiguous query detected: {query[:50]}... (confidence: {routing_result['confidence']:.3f})")
            
            return is_ambiguous, routing_result
            
        except Exception as e:
            logger.error(f"❌ Error checking ambiguous query: {e}")
            return True, {'status': 'error', 'confidence': 0.0}
    
    def generate_clarification_response(self, routing_result: Dict[str, Any]) -> str:
        """Generate clarification response dựa trên routing result"""
        try:
            status = routing_result.get('status', 'no_match')
            
            if status == 'ambiguous':
                # Có match nhưng confidence thấp
                templates = self.clarification_templates['ambiguous']
                base_response = templates[0]
                
                # Suggest top collections
                all_scores = routing_result.get('all_scores', {})
                if all_scores:
                    top_collections = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:2]
                    suggestions = []
                    for collection, score in top_collections:
                        display_name = self.router.collection_mappings.get(collection, {}).get('display_name', collection)
                        suggestions.append(display_name)
                    
                    if suggestions:
                        base_response += f" Các lĩnh vực có thể liên quan: {', '.join(suggestions)}."
                
                return base_response
            
            else:  # no_match
                return self.clarification_templates['no_match'][0]
                
        except Exception as e:
            logger.error(f"❌ Error generating clarification response: {e}")
            return "Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi của bạn."
