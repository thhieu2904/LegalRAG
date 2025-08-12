"""
Smart Query Router Service
Định tuyến câu hỏi đến đúng collection dựa trên semantic similarity
"""

import logging
import numpy as np
import json
import glob
from typing import Dict, List, Tuple, Optional, Any
from sentence_transformers import SentenceTransformer
import os
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class SmartQueryRouter:
    """Router thông minh định tuyến câu hỏi đến collection phù hợp nhất"""
    
    def __init__(self, embedding_model: SentenceTransformer):
        self.embedding_model = embedding_model
        
        # Example questions database - Loaded từ router_examples
        self.example_questions_db = {}
        self.example_vectors = {}
        
        # Collection mappings
        self.collection_mappings = {
            'ho_tich_cap_xa': 'Hộ tịch cấp xã',
            'chung_thuc': 'Chứng thực', 
            'nuoi_con_nuoi': 'Nuôi con nuôi'
        }
        
        # Thresholds - Performance optimized
        self.similarity_threshold = 0.4  # Tăng từ 0.3 để chỉ route query có confidence cao (Performance Optimization)
        self.high_confidence_threshold = 0.6  # Tăng từ 0.5 để đảm bảo quality routing (Performance Optimization)
        
        # Load example questions database và tạo vectors
        self._load_example_questions_database()
        self._initialize_example_vectors()
        
        logger.info(f"✅ Smart Query Router initialized with example questions from {len(self.example_questions_db)} procedure types")
    
    def _load_example_questions_database(self):
        """Load tất cả example questions từ router_examples directory"""
        try:
            router_examples_path = "data/router_examples"
            
            # Load index file để biết structure
            index_path = os.path.join(router_examples_path, "index.json")
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    logger.info(f"📚 Loaded router examples index with {len(index_data.get('collection_mappings', {}))} collections")
            
            # Tìm tất cả JSON files trong router_examples
            pattern = os.path.join(router_examples_path, "**", "*.json")
            example_files = glob.glob(pattern, recursive=True)
            
            # Filter ra index file
            example_files = [f for f in example_files if not f.endswith('index.json')]
            
            logger.info(f"🔍 Found {len(example_files)} example question files")
            
            for file_path in example_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Extract metadata
                    metadata = data.get('metadata', {})
                    collection_mapping = metadata.get('collection_mapping')
                    procedure_title = metadata.get('title', 'Unknown')
                    
                    if not collection_mapping:
                        logger.warning(f"⚠️ No collection_mapping in {file_path}")
                        continue
                    
                    # Extract example questions  
                    example_questions = data.get('example_questions', [])
                    
                    if collection_mapping not in self.example_questions_db:
                        self.example_questions_db[collection_mapping] = []
                    
                    # Add all questions và variants
                    for q_data in example_questions:
                        main_question = q_data.get('question', '')
                        variants = q_data.get('question_variants', [])
                        keywords = q_data.get('semantic_keywords', [])
                        
                        # Add main question
                        if main_question:
                            self.example_questions_db[collection_mapping].append({
                                'text': main_question,
                                'procedure': procedure_title,
                                'keywords': keywords,
                                'source_file': file_path
                            })
                        
                        # Add variants
                        for variant in variants:
                            if variant:
                                self.example_questions_db[collection_mapping].append({
                                    'text': variant,
                                    'procedure': procedure_title,
                                    'keywords': keywords,
                                    'source_file': file_path
                                })
                    
                    logger.info(f"📝 Loaded {len(example_questions)} questions from {procedure_title}")
                    
                except Exception as e:
                    logger.error(f"❌ Error loading {file_path}: {e}")
                    
            # Summary
            total_questions = sum(len(questions) for questions in self.example_questions_db.values())
            logger.info(f"✅ Loaded {total_questions} example questions across {len(self.example_questions_db)} collections")
            
            for collection, questions in self.example_questions_db.items():
                logger.info(f"  - {collection}: {len(questions)} questions")
                
        except Exception as e:
            logger.error(f"❌ Error loading example questions database: {e}")
            # Fallback to empty database
            self.example_questions_db = {}
    
    def _initialize_example_vectors(self):
        """Tạo vectors cho tất cả example questions"""
        try:
            self.example_vectors = {}
            
            for collection_name, questions in self.example_questions_db.items():
                if not questions:
                    continue
                    
                logger.info(f"🎯 Creating vectors for {collection_name} ({len(questions)} questions)")
                
                # Extract all question texts
                question_texts = [q['text'] for q in questions]
                
                # Create embeddings cho tất cả questions của collection này
                vectors = self.embedding_model.encode(question_texts)
                
                # Store vectors với metadata
                self.example_vectors[collection_name] = {
                    'vectors': vectors,
                    'questions': questions
                }
                
                logger.info(f"✅ Created {len(vectors)} vectors for {collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Error creating example vectors: {e}")
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
                'matched_procedure': str | None
            }
        """
        try:
            # Tạo vector cho query
            query_vector = self.embedding_model.encode([query])[0]
            
            # Tính similarity với tất cả example questions
            collection_scores = {}
            best_matches = {}
            
            for collection_name, vector_data in self.example_vectors.items():
                vectors = vector_data['vectors']
                questions = vector_data['questions']
                
                # Tính cosine similarity với tất cả examples trong collection này
                similarities = cosine_similarity(
                    query_vector.reshape(1, -1), 
                    vectors
                )[0]
                
                # Lấy best match trong collection này
                best_idx = np.argmax(similarities)
                best_score = similarities[best_idx]
                best_question = questions[best_idx]
                
                collection_scores[collection_name] = float(best_score)
                best_matches[collection_name] = {
                    'score': float(best_score),
                    'example': best_question['text'],
                    'procedure': best_question['procedure']
                }
            
            if not collection_scores:
                logger.warning("❌ No example questions loaded - routing impossible")
                return {
                    'status': 'no_match',
                    'target_collection': None,
                    'confidence': 0.0,
                    'all_scores': {},
                    'display_name': None,
                    'clarification_needed': True,
                    'matched_example': None,
                    'matched_procedure': None
                }
            
            # Tìm collection có similarity cao nhất
            best_collection = max(collection_scores.keys(), key=lambda k: collection_scores[k])
            best_score = collection_scores[best_collection]
            best_match = best_matches[best_collection]
            
            logger.info(f"🎯 Query: '{query[:50]}...' -> Best match: {best_collection} ({best_score:.3f})")
            logger.info(f"📝 Matched example: '{best_match['example'][:60]}...' from {best_match['procedure']}")
            
            # Quyết định routing
            if best_score >= self.high_confidence_threshold:
                # Tự tin cao - route ngay
                return {
                    'status': 'routed',
                    'target_collection': best_collection,
                    'confidence': best_score,
                    'all_scores': collection_scores,
                    'display_name': self.collection_mappings.get(best_collection, best_collection),
                    'clarification_needed': False,
                    'matched_example': best_match['example'],
                    'matched_procedure': best_match['procedure']
                }
            
            elif best_score >= self.similarity_threshold:
                # Tự tin vừa phải - route nhưng ghi nhận
                return {
                    'status': 'routed',
                    'target_collection': best_collection,
                    'confidence': best_score,
                    'all_scores': collection_scores,
                    'display_name': self.collection_mappings.get(best_collection, best_collection),
                    'clarification_needed': False,
                    'matched_example': best_match['example'],
                    'matched_procedure': best_match['procedure']
                }
            
            else:
                # Similarity thấp - cần clarification
                return {
                    'status': 'ambiguous',
                    'target_collection': None,
                    'confidence': best_score,
                    'all_scores': collection_scores,
                    'display_name': None,
                    'clarification_needed': True,
                    'matched_example': best_match['example'],
                    'matched_procedure': best_match['procedure']
                }
                
        except Exception as e:
            logger.error(f"❌ Error in query routing: {e}")
            return {
                'status': 'error',
                'target_collection': None,
                'confidence': 0.0,
                'all_scores': {},
                'display_name': None,
                'clarification_needed': True,
                'matched_example': None,
                'matched_procedure': None,
                'error': str(e)
            }
    
    def get_clarification_options(self) -> List[Dict[str, str]]:
        """Trả về danh sách các collection cho user chọn khi câu hỏi mơ hồ"""
        return [
            {
                'collection': collection_name,
                'display_name': info['display_name'],
                'description': info['description']
            }
            for collection_name, info in self.collection_descriptions.items()
        ]
    
    def force_route_to_collection(self, collection_name: str) -> Dict[str, Any]:
        """Force route đến một collection cụ thể (khi user chọn từ clarification)"""
        if collection_name in self.collection_descriptions:
            return {
                'status': 'routed',
                'target_collection': collection_name,
                'confidence': 1.0,
                'all_scores': {collection_name: 1.0},
                'display_name': self.collection_descriptions[collection_name]['display_name'],
                'clarification_needed': False,
                'forced': True
            }
        else:
            return {
                'status': 'error',
                'target_collection': None,
                'confidence': 0.0,
                'all_scores': {},
                'display_name': None,
                'clarification_needed': True,
                'error': f"Collection '{collection_name}' not found"
            }
    
    def add_collection(self, collection_name: str, description: str, keywords: str, display_name: str):
        """Thêm collection mới vào router (dynamic expansion)"""
        try:
            # Thêm vào descriptions
            self.collection_descriptions[collection_name] = {
                'description': description,
                'keywords': keywords,
                'display_name': display_name
            }
            
            # Tạo vector
            combined_text = f"{description} {keywords}"
            vector = self.embedding_model.encode([combined_text])
            self.collection_vectors[collection_name] = vector[0]
            
            logger.info(f"✅ Added new collection: {display_name}")
            
        except Exception as e:
            logger.error(f"❌ Error adding collection: {e}")
            raise
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Thống kê về router"""
        return {
            'total_collections': len(self.collection_descriptions),
            'collections': list(self.collection_descriptions.keys()),
            'similarity_threshold': self.similarity_threshold,
            'high_confidence_threshold': self.high_confidence_threshold,
            'vector_dimensions': len(list(self.collection_vectors.values())[0]) if self.collection_vectors else 0
        }


class RouterBasedAmbiguousQueryService:
    """
    Service mới thay thế AmbiguousQueryService cũ
    Sử dụng Router để xác định câu hỏi mơ hồ
    """
    
    def __init__(self, router: SmartQueryRouter, llm_service):
        self.router = router
        self.llm_service = llm_service
        
        logger.info("✅ Router-based Ambiguous Query Service initialized")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Xử lý query với router-based approach
        
        Returns format tương thích với code cũ:
        {
            'is_ambiguous': bool,
            'category': str | None, 
            'confidence': float,
            'clarification': Dict | None,
            'target_collection': str | None
        }
        """
        routing_result = self.router.route_query(query)
        
        if routing_result['status'] == 'routed':
            # Không mơ hồ - đã route thành công
            return {
                'is_ambiguous': False,
                'category': routing_result['target_collection'],
                'confidence': routing_result['confidence'],
                'clarification': None,
                'target_collection': routing_result['target_collection'],
                'routing_result': routing_result
            }
        
        elif routing_result['status'] == 'ambiguous':
            # Mơ hồ - cần clarification
            clarification_options = self.router.get_clarification_options()
            
            clarification = {
                'template': 'Vấn đề của bạn thuộc lĩnh vực nào sau đây?',
                'options': [opt['display_name'] for opt in clarification_options],
                'collection_mapping': {
                    opt['display_name']: opt['collection'] 
                    for opt in clarification_options
                }
            }
            
            return {
                'is_ambiguous': True,
                'category': 'multi_domain',
                'confidence': routing_result['confidence'],
                'clarification': clarification,
                'target_collection': None,
                'routing_result': routing_result
            }
        
        else:
            # Error case
            return {
                'is_ambiguous': True,
                'category': 'unknown',
                'confidence': 0.0,
                'clarification': {
                    'template': 'Xin lỗi, có lỗi trong việc xử lý câu hỏi. Vui lòng thử lại.',
                    'options': []
                },
                'target_collection': None,
                'routing_result': routing_result
            }
    
    def generate_clarifying_questions(self, query: str, category: str) -> List[str]:
        """Tạo câu hỏi làm rõ dựa trên routing results"""
        clarification_options = self.router.get_clarification_options()
        
        questions = [
            f"Bạn có muốn tìm hiểu về {opt['display_name'].lower()} không?"
            for opt in clarification_options
        ]
        
        return questions[:3]  # Giới hạn 3 câu hỏi
