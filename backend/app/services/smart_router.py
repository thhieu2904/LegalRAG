"""
Enhanced Smart Query Router Service
Định tuyến câu hỏi đến đúng collection dựa trên example questions database
"""

import logging
import numpy as np
import json
import os
import pickle
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class EnhancedSmartQueryRouter:
    """Router thông minh sử dụng database example questions cho routing chính xác"""
    
    def __init__(self, embedding_model: SentenceTransformer):
        self.embedding_model = embedding_model
        self.base_path = "data/router_examples"
        self.cache_file = "data/cache/router_embeddings.pkl"
        
        # Load configuration
        self.config = self._load_config()
        
        # Example questions database
        self.example_questions = {}
        self.question_vectors = {}
        self.collection_mappings = {}
        
        # Thresholds
        self.similarity_threshold = 0.3
        self.high_confidence_threshold = 0.5
        
        # Initialize database - cache first, fallback to live loading
        if self._load_from_cache():
            logger.info("📦 Router loaded from cache (fast startup)")
        else:
            logger.info("🔄 Cache not available, loading from files (slow startup)...")
            self._load_example_questions()
            self._initialize_question_vectors()
            # Save cache for next time
            self._save_to_cache()
        
        logger.info(f"✅ Enhanced Smart Query Router initialized with {len(self.collection_mappings)} collections")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from router_examples_smart directory"""
        try:
            # New approach: Load from individual router files
            router_smart_path = os.path.join(self.base_path.replace("router_examples", "router_examples_smart"))
            
            if not os.path.exists(router_smart_path):
                logger.warning(f"Router examples directory not found: {router_smart_path}")
                return {}
            
            # Check for summary file
            summary_file = os.path.join(router_smart_path, "router_generation_summary.json")
            if os.path.exists(summary_file):
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                logger.info(f"📋 Loaded router summary: {summary.get('total_files_processed', 0)} files, {summary.get('total_examples', 0)} examples")
                
                # Build config from summary
                config = {
                    'metadata': {
                        'version': '2.0',
                        'generator': 'smart_router_individual',
                        'structure': 'individual_files'
                    },
                    'collection_mappings': {}
                }
                
                # Map collections from summary
                for collection_name, count in summary.get('collections', {}).items():
                    config['collection_mappings'][collection_name] = {
                        'description': collection_name.replace('_', ' ').title(),
                        'file_count': count,
                        'example_files': []  # Will be loaded dynamically
                    }
                
                return config
            
            # Fallback: scan directory structure
            else:
                logger.info("📁 Scanning router_examples_smart directory structure...")
                return self._scan_individual_files(router_smart_path)
            
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return {}
    
    def _scan_individual_files(self, router_smart_path: str) -> Dict[str, Any]:
        """Scan individual router files and build config"""
        try:
            from pathlib import Path
            
            config = {
                'metadata': {
                    'version': '2.0',
                    'generator': 'smart_router_individual_scan',
                    'structure': 'individual_files'
                },
                'collection_mappings': {}
            }
            
            # Scan for JSON files recursively
            router_path = Path(router_smart_path)
            json_files = list(router_path.rglob("*.json"))
            
            # Exclude summary files
            json_files = [f for f in json_files if not f.name.endswith('_summary.json')]
            
            # Group by collection (based on directory structure)
            collections = {}
            for json_file in json_files:
                # Try to determine collection from path
                relative_path = json_file.relative_to(router_path)
                parts = relative_path.parts
                
                if 'ho_tich' in str(relative_path).lower():
                    collection = 'ho_tich_cap_xa'
                elif 'chung_thuc' in str(relative_path).lower():
                    collection = 'chung_thuc'
                elif 'nuoi_con' in str(relative_path).lower():
                    collection = 'nuoi_con_nuoi'
                else:
                    collection = 'general'
                
                if collection not in collections:
                    collections[collection] = []
                collections[collection].append(str(relative_path))
            
            # Build collection mappings
            for collection_name, files in collections.items():
                config['collection_mappings'][collection_name] = {
                    'description': collection_name.replace('_', ' ').title(),
                    'file_count': len(files),
                    'example_files': files[:10]  # Limit for performance
                }
            
            logger.info(f"📁 Scanned {len(json_files)} individual router files in {len(collections)} collections")
            return config
            
        except Exception as e:
            logger.error(f"❌ Error scanning individual files: {e}")
            return {}
    
    def _load_from_cache(self) -> bool:
        """Load router data from cache if available"""
        try:
            if not os.path.exists(self.cache_file):
                logger.info("📦 No router cache found")
                return False
            
            # Check cache freshness - với tolerance 10 seconds để tránh race condition
            cache_time = os.path.getmtime(self.cache_file)
            router_smart_path = os.path.join(self.base_path.replace("router_examples", "router_examples_smart"))
            
            if os.path.exists(router_smart_path):
                from pathlib import Path
                router_files = list(Path(router_smart_path).rglob("*.json"))
                
                if router_files:
                    newest_router = max(f.stat().st_mtime for f in router_files)
                    # Thêm tolerance 10 giây để tránh cache bị invalidate không cần thiết
                    if cache_time < (newest_router - 10):
                        logger.info(f"🔄 Cache is older than router files (cache: {cache_time}, newest: {newest_router})")
                        return False
                    else:
                        logger.info(f"📦 Cache is fresh enough (tolerance: 10s)")
                else:
                    logger.info("📦 No router files found, using cache")
            
            # Load cache
            logger.info("📦 Loading router from cache...")
            start_time = time.time()
            
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Validate structure
            if not all(key in cache_data for key in ['metadata', 'questions', 'embeddings']):
                logger.warning("⚠️ Invalid cache structure")
                return False
            
            # Load data
            questions_data = cache_data['questions']
            embeddings_data = cache_data['embeddings']
            
            for collection_name, questions in questions_data.items():
                self.example_questions[collection_name] = questions
                self.question_vectors[collection_name] = embeddings_data[collection_name]
                
                self.collection_mappings[collection_name] = {
                    'display_name': collection_name.replace('_', ' ').title(),
                    'total_questions': len(questions)
                }
            
            load_time = time.time() - start_time
            total_questions = cache_data['metadata'].get('total_questions', 0)
            
            logger.info(f"📦 Cache loaded: {total_questions} questions in {load_time:.1f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading cache: {e}")
            return False

    def _save_to_cache(self):
        """Save router data to cache for faster startup next time"""
        try:
            # Ensure cache directory exists
            cache_dir = os.path.dirname(self.cache_file)
            os.makedirs(cache_dir, exist_ok=True)
            
            logger.info("💾 Saving router cache...")
            start_time = time.time()
            
            # Prepare cache data
            cache_data = {
                'metadata': {
                    'version': '1.0',
                    'created': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_questions': sum(len(questions) for questions in self.example_questions.values()),
                    'collections': {name: len(questions) for name, questions in self.example_questions.items()}
                },
                'questions': self.example_questions,
                'embeddings': self.question_vectors
            }
            
            # Save cache
            import pickle
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            save_time = time.time() - start_time
            total_questions = cache_data['metadata']['total_questions']
            file_size = os.path.getsize(self.cache_file) / (1024 * 1024)  # MB
            
            logger.info(f"💾 Cache saved: {total_questions} questions, {file_size:.1f}MB in {save_time:.1f}s")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to save cache: {e}")
            # Don't fail initialization just because of cache save failure
            pass
    
    def _load_example_questions(self):
        """Load all example questions from individual router JSON files"""
        try:
            # Get router_examples_smart path
            router_smart_path = os.path.join(self.base_path.replace("router_examples", "router_examples_smart"))
            
            if not os.path.exists(router_smart_path):
                logger.warning(f"Router examples directory not found: {router_smart_path}")
                return
            
            from pathlib import Path
            router_path = Path(router_smart_path)
            json_files = list(router_path.rglob("*.json"))
            
            # Exclude summary files
            json_files = [f for f in json_files if not f.name.endswith('_summary.json')]
            
            # Reset collections
            self.collection_mappings = {}
            collections_data = {}
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        router_data = json.load(f)
                    
                    # Get collection from metadata
                    collection_name = router_data.get('expected_collection', 'general')
                    
                    if collection_name not in collections_data:
                        collections_data[collection_name] = []
                        self.collection_mappings[collection_name] = {
                            'display_name': collection_name.replace('_', ' ').title(),
                            'total_questions': 0
                        }
                    
                    # Extract questions from individual router file
                    main_question = {
                        'text': router_data.get('main_question', ''),
                        'collection': collection_name,
                        'source': router_data.get('metadata', {}).get('title', ''),
                        'keywords': router_data.get('smart_filters', {}).get('title_keywords', []),
                        'type': 'main',
                        'filters': router_data.get('smart_filters', {}),
                        'priority_score': router_data.get('priority_score', 0.5)
                    }
                    collections_data[collection_name].append(main_question)
                    
                    # Add question variants
                    for variant in router_data.get('question_variants', []):
                        variant_question = {
                            'text': variant,
                            'collection': collection_name,
                            'source': router_data.get('metadata', {}).get('title', ''),
                            'keywords': router_data.get('smart_filters', {}).get('title_keywords', []),
                            'type': 'variant',
                            'filters': router_data.get('smart_filters', {}),
                            'priority_score': router_data.get('priority_score', 0.5) - 0.1
                        }
                        collections_data[collection_name].append(variant_question)
                
                except Exception as e:
                    logger.warning(f"⚠️ Error processing {json_file.name}: {e}")
                    continue
            
            # Store loaded questions and update counts
            total_questions = 0
            for collection_name, questions in collections_data.items():
                # Store questions by collection
                if collection_name not in self.example_questions:
                    self.example_questions[collection_name] = []
                self.example_questions[collection_name].extend(questions)
                self.collection_mappings[collection_name]['total_questions'] = len(questions)
                total_questions += len(questions)
            
            logger.info(f"📚 Loaded {total_questions} example questions from {len(json_files)} individual files")
            logger.info(f"📂 Collections: {list(collections_data.keys())}")
            
            # Build embeddings cache if needed
            if total_questions > 0:
                self._build_embeddings_cache()
            
        except Exception as e:
            logger.error(f"❌ Error loading example questions: {e}")
    
    def _build_embeddings_cache(self):
        """Build embeddings cache for loaded questions"""
        try:
            if not self.example_questions:
                logger.warning("No questions to build embeddings for")
                return
            
            logger.info("🔄 Building embeddings cache for router questions...")
            # This method can be implemented later if needed for caching
            logger.info("✅ Embeddings cache ready")
            
        except Exception as e:
            logger.error(f"❌ Error building embeddings cache: {e}")
    
    def _initialize_question_vectors(self):
        """Tính toán vectors cho tất cả example questions"""
        try:
            if not self.example_questions:
                logger.warning("No example questions to vectorize")
                return
            
            total_questions = sum(len(questions) for questions in self.example_questions.values())
            logger.info(f"🔢 Vectorizing {total_questions} example questions...")
            
            for collection_name, questions in self.example_questions.items():
                if not questions:
                    continue
                    
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
            best_filters = {}
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
                    best_filters = questions[max_idx].get('filters', {})
                    
                    # 🐛 DEBUG: Log the exact match info
                    logger.info(f"🔍 NEW BEST MATCH: score={max_similarity:.3f}, collection={collection_name}")
                    logger.info(f"🔍 Question text: '{best_example[:100]}...'")
                    logger.info(f"🔍 Source procedure: {best_source}")
                    if 'exact_title' in best_filters:
                        logger.info(f"🔍 Exact title from filters: {best_filters['exact_title']}")
            
            logger.info(f"🎯 Query: '{query[:50]}...' -> Best match: {best_collection} ({best_score:.3f})")
            if best_example:
                logger.info(f"📝 Matched example: '{best_example[:80]}...'")
            
            # 🐛 DEBUG: Final validation before returning
            if best_filters:
                final_title = best_filters.get('exact_title', ['Unknown'])
                logger.info(f"🔍 FINAL FILTERS CHECK - Exact title: {final_title}")
            
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
                    'source_procedure': best_source,
                    'inferred_filters': best_filters
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
                    'source_procedure': best_source,
                    'inferred_filters': best_filters
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
                    'source_procedure': best_source,
                    'inferred_filters': best_filters
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
                'source_procedure': None,
                'inferred_filters': {}
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
