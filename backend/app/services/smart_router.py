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
        
        # Thresholds - CỰC CAO để tránh route nhầm, chuyển logic xuống clarification
        self.high_confidence_threshold = 0.85  # CỰC CAO - chỉ route khi RẤT RẤT chắc chắn
        self.min_confidence_threshold = 0.50   # Dưới threshold này = hỏi lại user
        
        logger.info(f"🎯 Router thresholds - Min: {self.min_confidence_threshold}, High: {self.high_confidence_threshold}")
        logger.info("💡 STRATEGY: Threshold CỰC CAO, nếu không chắc chắn thì hỏi lại user")
        
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
        """Load configuration from router_examples_smart_v3 directory"""
        try:
            # New approach: Load from individual router files - Updated to V3
            router_smart_path = os.path.join(self.base_path.replace("router_examples", "router_examples_smart_v3"))
            
            if not os.path.exists(router_smart_path):
                logger.warning(f"Router examples directory not found: {router_smart_path}")
                return {}
            
            # Check for V3 summary file
            summary_file = os.path.join(router_smart_path, "llm_generation_summary_v3.json")
            if os.path.exists(summary_file):
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                logger.info(f"📋 Loaded router summary V3: {summary.get('statistics', {}).get('total_files_processed', 0)} files, {summary.get('statistics', {}).get('total_examples_generated', 0)} examples")
                
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
                logger.info("📁 Scanning router_examples_smart_v3 directory structure...")
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
            router_smart_path = os.path.join(self.base_path.replace("router_examples", "router_examples_smart_v3"))
            
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
            # Get router_examples_smart_v3 path
            router_smart_path = os.path.join(self.base_path.replace("router_examples", "router_examples_smart_v3"))
            
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
    
    def route_query(self, query: str, session: Optional[Any] = None) -> Dict[str, Any]:
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
            
            # � STATEFUL ROUTER LOGIC - Confidence Override
            original_confidence = best_score
            should_override = False
            override_collection = None
            
            if session and hasattr(session, 'should_override_confidence'):
                if session.should_override_confidence(best_score):
                    override_collection = session.last_successful_collection
                    should_override = True
                    # Boost confidence to medium level khi override
                    best_score = max(best_score, 0.75)
                    best_collection = override_collection
                    logger.info(f"🔥 CONFIDENCE OVERRIDE: {original_confidence:.3f} -> {best_score:.3f}")
                    logger.info(f"🔥 Override to collection: {override_collection} (from session state)")
                    
                    # Update display info for overridden case
                    if override_collection in self.collection_mappings:
                        display_name = self.collection_mappings[override_collection].get('display_name')
                    else:
                        display_name = override_collection
                elif original_confidence < self.min_confidence_threshold:
                    # Track consecutive low confidence
                    session.increment_low_confidence()
                    if session.consecutive_low_confidence_count >= 3:
                        # Too many failed attempts - clear state
                        logger.info("🧹 Clearing session state due to consecutive low confidence queries")
                        session.clear_routing_state()
            
            # �🐛 DEBUG: Final validation before returning
            if best_filters:
                final_title = best_filters.get('exact_title', ['Unknown'])
                logger.info(f"🔍 FINAL FILTERS CHECK - Exact title: {final_title}")
            
            # Determine routing decision - LOGIC MỚI với 3 mức tin cậy + Override
            if best_score >= self.high_confidence_threshold:
                # High confidence - route immediately với tin cậy cao
                confidence_level = 'high' if not should_override else 'override_high'
                logger.info(f"✅ HIGH CONFIDENCE routing: {best_score:.3f} >= {self.high_confidence_threshold}")
                return {
                    'status': 'routed',
                    'confidence_level': confidence_level,
                    'target_collection': best_collection,
                    'confidence': best_score,
                    'original_confidence': original_confidence if should_override else best_score,
                    'was_overridden': should_override,
                    'all_scores': collection_scores,
                    'display_name': self.collection_mappings.get(best_collection, {}).get('display_name'),
                    'clarification_needed': False,
                    'matched_example': best_example,
                    'source_procedure': best_source,
                    'inferred_filters': best_filters
                }
            
            elif best_score >= self.min_confidence_threshold:
                # Khả năng match có thể đúng nhưng chưa chắc chắn - ROUTE NHƯNG CAUTION
                confidence_level = 'low-medium' if not should_override else 'override_medium'
                logger.info(f"⚠️ LOW-MEDIUM CONFIDENCE routing: {best_score:.3f} >= {self.min_confidence_threshold}")
                return {
                    'status': 'routed',
                    'confidence_level': confidence_level, 
                    'target_collection': best_collection,
                    'confidence': best_score,
                    'original_confidence': original_confidence if should_override else best_score,
                    'was_overridden': should_override,
                    'all_scores': collection_scores,
                    'display_name': self.collection_mappings.get(best_collection, {}).get('display_name'),
                    'clarification_needed': False,  # Route nhưng sẽ có extra validation
                    'matched_example': best_example,
                    'source_procedure': best_source,
                    'inferred_filters': best_filters,
                    'warning': 'low_medium_confidence' if not should_override else 'overridden_routing'
                }
            
            else:
                # Below min threshold - cần clarification vì quá mơ hồ
                logger.warning(f"🤔 TOO AMBIGUOUS - cần clarification: {best_score:.3f} < {self.min_confidence_threshold}")
                return {
                    'status': 'clarification_needed',
                    'confidence_level': 'low',
                    'target_collection': best_collection,
                    'confidence': best_score,
                    'all_scores': collection_scores,
                    'display_name': self.collection_mappings.get(best_collection, {}).get('display_name'),
                    'clarification_needed': True,
                    'matched_example': best_example,
                    'source_procedure': best_source,
                    'inferred_filters': best_filters,
                    'suggested_topics': []
                }
            
            # Below min threshold - backup strategy hoặc clarification
            logger.warning(f"🚨 VERY LOW CONFIDENCE - kích hoạt backup strategy: {best_score:.3f} < {self.min_confidence_threshold}")
            return {
                'status': 'no_match',
                'confidence_level': 'very_low',
                'target_collection': None,
                'confidence': best_score,
                'all_scores': collection_scores,
                'display_name': None,
                'clarification_needed': True,
                'matched_example': best_example,
                'source_procedure': best_source,
                'inferred_filters': best_filters,
                'suggested_topics': [],
                'needs_vector_backup': True
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
    
    def _get_top_suggestions(self, collection_scores: Dict[str, float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Lấy top suggestions từ collection scores để hiển thị cho user"""
        try:
            # Sort collections by score
            sorted_collections = sorted(collection_scores.items(), key=lambda x: x[1], reverse=True)
            
            suggestions = []
            for collection_name, score in sorted_collections[:top_k]:
                if score > 0.2:  # Chỉ suggest nếu có ít nhất một chút liên quan
                    display_name = self.collection_mappings.get(collection_name, {}).get('display_name', collection_name)
                    
                    # Lấy example question từ collection này để làm gợi ý
                    example_questions = self.example_questions.get(collection_name, [])
                    sample_question = None
                    if example_questions:
                        # Lấy main question hoặc question có priority cao
                        main_questions = [q for q in example_questions if q.get('type') == 'main']
                        if main_questions:
                            sample_question = main_questions[0]['text']
                        else:
                            sample_question = example_questions[0]['text']
                    
                    suggestions.append({
                        'collection': collection_name,
                        'display_name': display_name,
                        'score': score,
                        'sample_question': sample_question
                    })
            
            return suggestions
            
        except Exception as e:
            logger.warning(f"Error getting top suggestions: {e}")
            return []
    
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
    
    def get_similar_procedures_for_collection(
        self, 
        collection_name: str, 
        reference_query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Tìm các thủ tục tương đồng trong collection dựa trên reference query
        Sử dụng embedding similarity để tìm procedures có liên quan cao nhất
        
        Args:
            collection_name: Tên collection cần tìm
            reference_query: Câu hỏi/procedure gốc để làm reference  
            top_k: Số lượng procedures trả về tối đa
            
        Returns:
            List các procedures tương đồng cao nhất, có thể ít hơn top_k nếu collection nhỏ
        """
        try:
            # Get all example questions for this collection
            collection_questions = self.example_questions.get(collection_name, [])
            
            if not collection_questions:
                logger.warning(f"No example questions found for collection: {collection_name}")
                return []
            
            # 🚀 OPTIMIZED: Get embedding for reference query with caching
            reference_cache_key = f"reference:{reference_query}"
            if reference_cache_key in self.question_vectors:
                reference_embedding = np.array(self.question_vectors[reference_cache_key]).reshape(1, -1)
                logger.info(f"📦 Using cached embedding for reference query")
            else:
                reference_embedding = self.embedding_model.encode([reference_query])
                # Cache the reference embedding for future use
                self.question_vectors[reference_cache_key] = reference_embedding[0].tolist()
                logger.info(f"🔄 Generated and cached embedding for reference query")
            
            # Calculate similarities with all questions in collection
            similarities = []
            
            # 🚀 DEBUG: Log cache structure để hiểu format
            if collection_name in self.question_vectors:
                cache_format = self.question_vectors[collection_name]
                if isinstance(cache_format, list):
                    logger.info(f"🔍 DEBUG: Cache format for {collection_name} is list with {len(cache_format)} items")
                elif isinstance(cache_format, dict):
                    logger.info(f"🔍 DEBUG: Cache format for {collection_name} is dict with keys: {list(cache_format.keys())[:3]}...")
                else:
                    logger.info(f"🔍 DEBUG: Cache format for {collection_name} is {type(cache_format)}")
                    
            for i, question in enumerate(collection_questions):
                question_text = question.get('text', question) if isinstance(question, dict) else question
                
                # 🚀 OPTIMIZED: Use pre-computed embedding from cache with correct format
                question_embedding = None
                
                # Try cache format: collection_name -> embeddings (numpy array or list)
                if collection_name in self.question_vectors:
                    collection_embeddings = self.question_vectors[collection_name]
                    
                    # Handle numpy array format (from cache)
                    if isinstance(collection_embeddings, np.ndarray):
                        if len(collection_embeddings.shape) == 2 and i < collection_embeddings.shape[0]:
                            question_embedding = collection_embeddings[i:i+1]  # Keep 2D shape
                            if i == 0:  # Log first match only to avoid spam
                                logger.info(f"📦 Using cached embedding (numpy format) for {collection_name}[{i}]")
                    
                    # Handle list format (fallback)
                    elif isinstance(collection_embeddings, list) and i < len(collection_embeddings):
                        embedding_data = collection_embeddings[i]
                        if embedding_data is not None:
                            question_embedding = np.array(embedding_data).reshape(1, -1)
                            if i == 0:  # Log first match only to avoid spam
                                logger.info(f"📦 Using cached embedding (list format) for {collection_name}[{i}]")
                
                # Try alternative cache format: "collection:question" key
                if question_embedding is None:
                    question_key = f"{collection_name}:{question_text}"
                    if question_key in self.question_vectors:
                        question_embedding = np.array(self.question_vectors[question_key]).reshape(1, -1)
                        if i == 0:  # Log first match only
                            logger.info(f"📦 Using cached embedding (key format) for {question_key[:50]}...")
                
                # Try embedded format: question dict with embedding
                if question_embedding is None and isinstance(question, dict) and 'embedding' in question:
                    question_embedding = np.array(question['embedding']).reshape(1, -1)
                    if i == 0:  # Log first match only
                        logger.info(f"📦 Using embedded embedding for {question_text[:50]}...")
                
                # Last resort: compute new embedding
                if question_embedding is None:
                    logger.warning(f"⚠️ Computing new embedding for: {question_text[:50]}...")
                    question_embedding = self.embedding_model.encode([question_text])
                    # Cache it for future use with both formats
                    question_key = f"{collection_name}:{question_text}"
                    self.question_vectors[question_key] = question_embedding[0].tolist()
                    
                    # Also update collection format if it exists
                    if collection_name not in self.question_vectors:
                        self.question_vectors[collection_name] = []
                    if isinstance(self.question_vectors[collection_name], list):
                        while len(self.question_vectors[collection_name]) <= i:
                            self.question_vectors[collection_name].append(None)
                        self.question_vectors[collection_name][i] = question_embedding[0].tolist()
                
                # Calculate cosine similarity
                similarity = cosine_similarity(reference_embedding, question_embedding)[0][0]
                
                similarities.append({
                    'question': question,
                    'similarity': float(similarity),
                    'text': question_text
                })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Return top results, ensuring we have diverse procedures
            results = []
            seen_sources = set()  # Track sources to avoid duplicate procedures from same document
            
            for item in similarities[:top_k * 2]:  # Get more to filter
                question = item['question']
                
                # Extract source info to avoid duplicates
                source = None
                if isinstance(question, dict):
                    source = question.get('source', question.get('file', ''))
                
                # Add if we haven't seen this source or if no source info available
                if not source or source not in seen_sources:
                    results.append({
                        'text': item['text'],
                        'similarity': item['similarity'],
                        'source': source or 'Unknown',
                        'category': question.get('category', 'general') if isinstance(question, dict) else 'general',
                        'collection': collection_name
                    })
                    
                    if source:
                        seen_sources.add(source)
                    
                    if len(results) >= top_k:
                        break
            
            logger.info(f"🎯 Found {len(results)} similar procedures in {collection_name} for reference: {reference_query[:50]}...")
            if results:
                logger.info(f"   Top similarity: {results[0]['similarity']:.3f} - {results[0]['text'][:60]}...")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error finding similar procedures for collection {collection_name}: {e}")
            # Fallback to first few questions from collection
            fallback_questions = self.get_example_questions_for_collection(collection_name)[:top_k]
            return [
                {
                    'text': q.get('text', q) if isinstance(q, dict) else q,
                    'similarity': 0.0,  # No similarity calculated
                    'source': q.get('source', 'Unknown') if isinstance(q, dict) else 'Unknown',
                    'category': q.get('category', 'general') if isinstance(q, dict) else 'general',
                    'collection': collection_name
                }
                for q in fallback_questions
            ]

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
        UPDATED: Sử dụng logic mới với multi-level confidence
        
        Returns:
            (is_ambiguous, routing_result)
        """
        try:
            routing_result = self.router.route_query(query)
            confidence_level = routing_result.get('confidence_level', 'low')
            
            # Ambiguous nếu confidence không phải high
            is_ambiguous = confidence_level in ['low', 'very_low']
            
            if is_ambiguous:
                logger.info(f"🤔 Ambiguous query detected: confidence_level={confidence_level}, score={routing_result['confidence']:.3f}")
            
            return is_ambiguous, routing_result
            
        except Exception as e:
            logger.error(f"❌ Error checking ambiguous query: {e}")
            return True, {'status': 'error', 'confidence': 0.0, 'confidence_level': 'very_low'}
    
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
