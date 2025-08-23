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
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Import PathConfig for new structure with multiple fallbacks
PathConfig = None
try:
    from ..core.path_config import PathConfig
except ImportError:
    try:
        from app.core.path_config import PathConfig
    except ImportError:
        try:
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from core.path_config import PathConfig
        except ImportError:
            pass
    
logger = logging.getLogger(__name__)

class QueryRouter:
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
        
        # Thresholds - UPDATED to match clarification levels
        self.high_confidence_threshold = 0.80      # >= 0.80: auto route
        self.medium_high_threshold = 0.65          # 0.65-0.79: questions in document  
        self.min_confidence_threshold = 0.50       # 0.50-0.64: multiple choices
        # < 0.50: category suggestions
        
        logger.info(f"🎯 Router thresholds - Min: {self.min_confidence_threshold}, Medium-High: {self.medium_high_threshold}, High: {self.high_confidence_threshold}")
        logger.info("💡 STRATEGY: 4-level clarification system")
        
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
    
    def _is_followup_question(self, query: str) -> bool:
        """Simple follow-up detection"""
        followup_words = ["ủa", "vậy", "thế", "còn", "khi nào", "bao nhiêu", "phí", "tiền", "chi phí", "lệ phí"]
        query_lower = query.lower()
        return any(word in query_lower for word in followup_words) or len(query.split()) <= 6
    
    def _route_followup(self, query: str, session) -> Dict[str, Any]:
        """Route follow-up questions to same collection"""
        return {
            'status': 'routed',
            'confidence_level': 'high_followup',
            'target_collection': session.last_successful_collection,
            'confidence': 0.85,
            'all_scores': {session.last_successful_collection: 0.85},
            'display_name': self.collection_mappings.get(session.last_successful_collection, {}).get('display_name'),
            'clarification_needed': False,
            'matched_example': f"Follow-up question in {session.last_successful_collection}",
            'source_procedure': "Context-aware routing",
            'inferred_filters': getattr(session, 'last_successful_filters', {}),
            'is_followup': True
        }
    
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
        """Load router data from cache if available - Updated for new structure"""
        try:
            if not os.path.exists(self.cache_file):
                logger.info("📦 No router cache found")
                return False
            
            # Check cache freshness against new structure
            cache_time = os.path.getmtime(self.cache_file)
            tolerance = 10  # seconds tolerance
            
            # Check against new structure router files
            try:
                if PathConfig:
                    path_config = PathConfig()
                    
                    # Get all router_questions.json files in new structure
                    router_files = path_config.get_all_router_files()
                    
                    if router_files:
                        # Find newest router file
                        newest_router_time = 0
                        for router_info in router_files:
                            router_path = router_info.get('router_path')
                            if router_path and os.path.exists(router_path):
                                file_time = os.path.getmtime(router_path)
                                newest_router_time = max(newest_router_time, file_time)
                        
                        # Check cache freshness with tolerance
                        if cache_time < (newest_router_time - tolerance):
                            logger.info(f"🔄 Cache outdated vs new structure (cache: {cache_time}, newest: {newest_router_time})")
                            return False
                        else:
                            logger.info(f"📦 Cache is fresh vs new structure (tolerance: {tolerance}s)")
                    else:
                        logger.info("📦 No router files found in new structure, checking old structure...")
                        
                        # Fallback: check old structure if new structure empty
                        router_smart_path = os.path.join(self.base_path.replace("router_examples", "router_examples_smart_v3"))
                        if os.path.exists(router_smart_path):
                            from pathlib import Path
                            old_router_files = list(Path(router_smart_path).rglob("*.json"))
                            
                            if old_router_files:
                                newest_router = max(f.stat().st_mtime for f in old_router_files)
                                if cache_time < (newest_router - tolerance):
                                    logger.info(f"🔄 Cache older than old structure files")
                                    return False
                else:
                    # PathConfig not available, use old structure check
                    logger.info("📦 PathConfig not available, using old structure check...")
                    router_smart_path = os.path.join(self.base_path.replace("router_examples", "router_examples_smart_v3"))
                    if os.path.exists(router_smart_path):
                        from pathlib import Path
                        old_router_files = list(Path(router_smart_path).rglob("*.json"))
                        
                        if old_router_files:
                            newest_router = max(f.stat().st_mtime for f in old_router_files)
                            if cache_time < (newest_router - tolerance):
                                logger.info(f"🔄 Cache older than old structure files")
                                return False
            
            except Exception as e:
                logger.warning(f"⚠️ Error checking cache freshness: {e}")
                # If freshness check fails, load from cache anyway (safer)
                logger.info("📦 Using cache despite freshness check failure")
            
            # Load cache
            logger.info("📦 Loading router from cache...")
            start_time = time.time()
            
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Validate cache structure
            if not all(key in cache_data for key in ['metadata', 'questions', 'embeddings']):
                logger.warning("⚠️ Invalid cache structure")
                return False
            
            # Check cache version compatibility
            cache_version = cache_data.get('metadata', {}).get('version', '0.0')
            if cache_version < '1.0':
                logger.info(f"🔄 Cache version {cache_version} too old, rebuilding...")
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
        """Load all example questions from new storage structure with CRUD support"""
        try:
            # Use PathConfig to access new structure
            if not PathConfig:
                logger.error("❌ PathConfig not available, cannot load from new structure")
                return
                
            path_config = PathConfig()
            
            # Get all collections from new structure
            collections = path_config.list_collections()
            if not collections:
                logger.warning("No collections found in new storage structure")
                return
            
            logger.info(f"📂 Loading router questions from {len(collections)} collections in new structure...")
            
            # Reset collections
            self.collection_mappings = {}
            collections_data = {}
            
            for collection_name in collections:
                try:
                    logger.info(f"📋 Processing collection: {collection_name}")
                    
                    if collection_name not in collections_data:
                        collections_data[collection_name] = []
                        self.collection_mappings[collection_name] = {
                            'display_name': collection_name.replace('_', ' ').title(),
                            'total_questions': 0
                        }
                    
                    # Get all documents in this collection
                    documents = path_config.list_documents(collection_name)
                    
                    for doc_info in documents:
                        doc_id = None  # Initialize doc_id
                        try:
                            # Extract doc_id from document info
                            doc_id = doc_info.get('doc_id') if isinstance(doc_info, dict) else doc_info
                            if not doc_id:
                                continue
                            
                            # Check if document has router questions
                            has_router = doc_info.get('has_router', False) if isinstance(doc_info, dict) else False
                            if not has_router:
                                continue
                            
                            # Try to load router questions for this document
                            router_questions_path = path_config.get_document_router(collection_name, doc_id)
                            
                            if os.path.exists(router_questions_path):
                                with open(router_questions_path, 'r', encoding='utf-8') as f:
                                    router_data = json.load(f)
                                
                                # Extract questions with CRUD support
                                questions = self._extract_questions_with_crud_support(router_data, collection_name)
                                collections_data[collection_name].extend(questions)
                                
                                logger.debug(f"✅ Loaded {len(questions)} questions from {doc_id}")
                            else:
                                # If no router_questions.json, create basic questions from document
                                doc_data = path_config.load_document_json(collection_name, doc_id)
                                if doc_data:
                                    basic_questions = self._create_basic_questions_from_document(doc_data, collection_name, doc_id)
                                    collections_data[collection_name].extend(basic_questions)
                                    logger.debug(f"✅ Created {len(basic_questions)} basic questions from {doc_id}")
                        
                        except Exception as e:
                            doc_id_str = doc_id if doc_id else "unknown"
                            logger.warning(f"⚠️ Error processing document {doc_id_str}: {e}")
                            continue
                
                except Exception as e:
                    logger.warning(f"⚠️ Error processing collection {collection_name}: {e}")
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
            
            logger.info(f"📚 Loaded {total_questions} example questions from {len(collections)} collections in new structure")
            logger.info(f"📂 Collections: {list(collections_data.keys())}")
            
            # Build embeddings cache if needed
            if total_questions > 0:
                self._build_embeddings_cache()
            
        except Exception as e:
            logger.error(f"❌ Error loading example questions from new structure: {e}")
    
    def _create_basic_questions_from_document(self, doc_data: Dict[str, Any], collection_name: str, doc_id: str) -> List[Dict[str, Any]]:
        """Create basic questions from document when no router_questions.json exists"""
        try:
            questions = []
            title = doc_data.get('metadata', {}).get('title', f'Document {doc_id}')
            
            # Create main question
            main_question = {
                'id': f'{doc_id}_main',
                'text': f'Thủ tục {title}',
                'collection': collection_name,
                'source': title,
                'keywords': [title.lower()],
                'type': 'main',
                'category': 'main_procedure',
                'priority_score': 1.0,
                'status': 'active'
            }
            questions.append(main_question)
            
            # Create variant questions based on content
            content = doc_data.get('content', '')
            if 'thủ tục' in content.lower():
                variant1 = {
                    'id': f'{doc_id}_variant_1',
                    'text': f'Làm thế nào để {title.lower()}?',
                    'collection': collection_name,
                    'source': title,
                    'keywords': ['thủ tục', 'làm thế nào'],
                    'type': 'variant',
                    'category': 'procedure_variant',
                    'priority_score': 0.8,
                    'status': 'active'
                }
                questions.append(variant1)
            
            if 'hồ sơ' in content.lower():
                variant2 = {
                    'id': f'{doc_id}_variant_2', 
                    'text': f'Cần chuẩn bị hồ sơ gì cho {title.lower()}?',
                    'collection': collection_name,
                    'source': title,
                    'keywords': ['hồ sơ', 'cần chuẩn bị'],
                    'type': 'variant',
                    'category': 'document_requirements',
                    'priority_score': 0.7,
                    'status': 'active'
                }
                questions.append(variant2)
            
            return questions
            
        except Exception as e:
            logger.error(f"❌ Error creating basic questions from document {doc_id}: {e}")
            return []
    
    def _extract_questions_with_crud_support(self, router_data: Dict[str, Any], collection_name: str) -> List[Dict[str, Any]]:
        """Extract questions with support for both old and new CRUD formats"""
        questions = []
        
        try:
            # 🔥 NEW FORMAT: CRUD-ready with individual question objects
            if "crud_config" in router_data and router_data.get("crud_config", {}).get("enable_crud", False):
                logger.info(f"📋 Loading CRUD format for {collection_name}")
                
                # Main question
                main_q = router_data.get("main_question", {})
                if main_q and main_q.get("text"):
                    questions.append({
                        'id': main_q.get('id', 'main_001'),
                        'text': main_q['text'],
                        'collection': collection_name,
                        'source': router_data.get('metadata', {}).get('document_title', ''),
                        'keywords': main_q.get('tags', []),
                        'type': 'main',
                        'filters': router_data.get('smart_filters', {}),
                        'priority_score': main_q.get('priority', 1.0),
                        'category': main_q.get('category', 'main_procedure'),
                        'status': main_q.get('status', 'active'),
                        'created_at': main_q.get('created_at'),
                        'updated_at': main_q.get('updated_at'),
                        'embedding_vector': main_q.get('embedding_vector')  # Pre-computed if available
                    })
                
                # Individual questions with IDs
                for question_obj in router_data.get("questions", []):
                    if question_obj.get('status') == 'active':  # Only load active questions
                        questions.append({
                            'id': question_obj.get('id', f'q_{len(questions):03d}'),
                            'text': question_obj['text'],
                            'collection': collection_name,
                            'source': router_data.get('metadata', {}).get('document_title', ''),
                            'keywords': question_obj.get('tags', []),
                            'type': 'variant',
                            'filters': router_data.get('smart_filters', {}),
                            'priority_score': question_obj.get('frequency_score', 0.5),
                            'category': question_obj.get('category', 'procedure_variant'),
                            'status': question_obj.get('status', 'active'),
                            'created_at': question_obj.get('created_at'),
                            'updated_at': question_obj.get('updated_at'),
                            'embedding_vector': question_obj.get('embedding_vector')  # Pre-computed if available
                        })
                
                logger.info(f"✅ Loaded {len(questions)} questions from CRUD format")
            
            # 🔄 LEGACY FORMAT: Backward compatibility
            else:
                logger.info(f"📋 Loading legacy format for {collection_name}")
                
                # Main question (legacy)
                main_question = {
                    'text': router_data.get('main_question', ''),
                    'collection': collection_name,
                    'source': router_data.get('metadata', {}).get('title', ''),
                    'keywords': router_data.get('smart_filters', {}).get('title_keywords', []),
                    'type': 'main',
                    'filters': router_data.get('smart_filters', {}),
                    'priority_score': router_data.get('priority_score', 0.5)
                }
                if main_question['text']:
                    questions.append(main_question)
                
                # Question variants (legacy)
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
                    questions.append(variant_question)
                
                logger.info(f"✅ Loaded {len(questions)} questions from legacy format")
            
            return questions
            
        except Exception as e:
            logger.error(f"❌ Error extracting questions from router data: {e}")
            return []
    
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
            
            # 🔥 STATEFUL ROUTER LOGIC - Confidence Override (ƯU TIÊN CAO NHẤT)
            original_confidence = best_score
            should_override = False
            override_collection = None
            
            if session and hasattr(session, 'should_override_confidence'):
                if session.should_override_confidence(best_score):
                    override_collection = session.last_successful_collection
                    override_filters = getattr(session, 'last_successful_filters', None)  # 🔥 NEW: Lấy filters từ session
                    should_override = True
                    # 🔧 FIX: Boost confidence to HIGH level để route trực tiếp (không trigger clarification)
                    best_score = max(best_score, 0.85)  # Changed from 0.75 to 0.85 để đảm bảo HIGH confidence
                    best_collection = override_collection
                    if override_filters:
                        best_filters = override_filters  # 🔥 NEW: Override filters
                        logger.info(f"🔥 OVERRIDE FILTERS: {override_filters}")
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
            
            # 🔗 FOLLOW-UP DETECTION (chỉ khi KHÔNG có override)
            # 🔍 DEBUG: Always log session state for debugging
            if session:
                logger.info(f"🔍 DEBUG Session state: last_successful_collection={getattr(session, 'last_successful_collection', 'MISSING')}, confidence={getattr(session, 'last_successful_confidence', 'MISSING')}")
            
            if not should_override and session and hasattr(session, 'last_successful_collection') and session.last_successful_collection:
                logger.info(f"🔗 Session has previous context: {session.last_successful_collection}")
                is_followup = self._is_followup_question(query)
                logger.info(f"🔗 Follow-up check: query='{query}' -> is_followup={is_followup}")
                if is_followup:
                    logger.info(f"🔗 FOLLOW-UP DETECTED: '{query[:50]}...' -> maintaining {session.last_successful_collection}")
                    return self._route_followup(query, session)
            elif not should_override:
                logger.info(f"🔗 No session context available: session={session is not None}, has_attr={hasattr(session, 'last_successful_collection') if session else False}, value={getattr(session, 'last_successful_collection', None) if session else None}")
            
            # �🐛 DEBUG: Final validation before returning
            if best_filters:
                final_title = best_filters.get('exact_title', ['Unknown'])
                logger.info(f"🔍 FINAL FILTERS CHECK - Exact title: {final_title}")
            
            # Determine routing decision - LOGIC MỚI với 4 mức tin cậy + Override
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
            
            elif best_score >= self.medium_high_threshold:
                # Medium-high confidence - cần clarification cho questions trong document
                confidence_level = 'medium-high' if not should_override else 'override_medium_high'
                logger.info(f"🔍 MEDIUM-HIGH CONFIDENCE: {best_score:.3f} >= {self.medium_high_threshold} - questions in document")
                return {
                    'status': 'clarification_needed',
                    'confidence_level': confidence_level,
                    'target_collection': best_collection,
                    'confidence': best_score,
                    'original_confidence': original_confidence if should_override else best_score,
                    'was_overridden': should_override,
                    'all_scores': collection_scores,
                    'display_name': self.collection_mappings.get(best_collection, {}).get('display_name'),
                    'clarification_needed': True,
                    'matched_example': best_example,
                    'source_procedure': best_source,
                    'inferred_filters': best_filters
                }
            
            elif best_score >= self.min_confidence_threshold:
                # Medium confidence - cần clarification cho document selection
                confidence_level = 'medium' if not should_override else 'override_medium'
                logger.info(f"⚠️ MEDIUM CONFIDENCE: {best_score:.3f} >= {self.min_confidence_threshold} - document selection")
                return {
                    'status': 'clarification_needed',
                    'confidence_level': confidence_level, 
                    'target_collection': best_collection,
                    'confidence': best_score,
                    'original_confidence': original_confidence if should_override else best_score,
                    'was_overridden': should_override,
                    'all_scores': collection_scores,
                    'display_name': self.collection_mappings.get(best_collection, {}).get('display_name'),
                    'clarification_needed': True,
                    'matched_example': best_example,
                    'source_procedure': best_source,
                    'inferred_filters': best_filters
                }
            
            else:
                # Below min threshold - cần clarification cho collection selection
                logger.warning(f"🤔 LOW CONFIDENCE - cần clarification: {best_score:.3f} < {self.min_confidence_threshold} - collection selection")
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
    
    # 🔥 NEW: CRUD Methods for Router Questions Management
    def add_question(self, collection_name: str, question_data: Dict[str, Any]) -> bool:
        """Add a new question to the router system with CRUD support"""
        try:
            from datetime import datetime
            
            # Validate required fields
            if not question_data.get('text'):
                logger.error("❌ Question text is required")
                return False
            
            # Generate ID if not provided
            if 'id' not in question_data:
                existing_ids = set()
                for questions in self.example_questions.get(collection_name, []):
                    if questions.get('id'):
                        existing_ids.add(questions['id'])
                
                # Generate unique ID
                counter = 1
                while f"q_{counter:03d}" in existing_ids:
                    counter += 1
                question_data['id'] = f"q_{counter:03d}"
            
            # Set defaults
            question_data.setdefault('collection', collection_name)
            question_data.setdefault('type', 'variant')
            question_data.setdefault('status', 'active')
            question_data.setdefault('priority_score', 0.5)
            question_data.setdefault('category', 'user_generated')
            question_data.setdefault('created_at', datetime.now().isoformat())
            question_data.setdefault('updated_at', datetime.now().isoformat())
            
            # Add to in-memory collection
            if collection_name not in self.example_questions:
                self.example_questions[collection_name] = []
            
            self.example_questions[collection_name].append(question_data)
            
            # Update collection mappings
            if collection_name not in self.collection_mappings:
                self.collection_mappings[collection_name] = {
                    'display_name': collection_name.replace('_', ' ').title(),
                    'total_questions': 0
                }
            self.collection_mappings[collection_name]['total_questions'] += 1
            
            # 🔥 Incremental vector update
            try:
                # Combine question text with keywords for vectorization
                keywords_text = " ".join(question_data.get('keywords', []))
                combined_text = f"{question_data['text']} {keywords_text}"
                
                # Generate embedding vector
                new_vector = self.embedding_model.encode([combined_text])[0]
                
                # Update question_vectors for this collection
                if collection_name in self.question_vectors:
                    # Append to existing vectors
                    current_vectors = self.question_vectors[collection_name]
                    self.question_vectors[collection_name] = np.vstack([current_vectors, new_vector])
                else:
                    # Create new vector array
                    self.question_vectors[collection_name] = np.array([new_vector])
                
                logger.info(f"✅ Added vector for new question: {question_data['id']}")
            except Exception as e:
                logger.warning(f"⚠️ Could not generate vector for new question: {e}")
            
            logger.info(f"✅ Added question {question_data['id']} to collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding question: {e}")
            return False
    
    def update_question(self, collection_name: str, question_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing question in the router system"""
        try:
            from datetime import datetime
            
            if collection_name not in self.example_questions:
                logger.error(f"❌ Collection {collection_name} not found")
                return False
            
            # Find question by ID
            question_index = None
            for i, question in enumerate(self.example_questions[collection_name]):
                if question.get('id') == question_id:
                    question_index = i
                    break
            
            if question_index is None:
                logger.error(f"❌ Question {question_id} not found in collection {collection_name}")
                return False
            
            # Apply updates
            original_question = self.example_questions[collection_name][question_index]
            for key, value in updates.items():
                if key != 'id':  # Don't allow ID changes
                    original_question[key] = value
            
            # Update timestamp
            original_question['updated_at'] = datetime.now().isoformat()
            
            # Update vector if text or keywords changed
            if ('text' in updates or 'keywords' in updates) and collection_name in self.question_vectors:
                try:
                    # Combine updated text with keywords
                    keywords_text = " ".join(original_question.get('keywords', []))
                    combined_text = f"{original_question['text']} {keywords_text}"
                    
                    # Generate new vector
                    new_vector = self.embedding_model.encode([combined_text])[0]
                    
                    # Update in question_vectors array
                    if question_index < len(self.question_vectors[collection_name]):
                        self.question_vectors[collection_name][question_index] = new_vector
                    
                    logger.info(f"✅ Updated vector for question: {question_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not update vector: {e}")
            
            logger.info(f"✅ Updated question {question_id} in collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating question: {e}")
            return False
    
    def delete_question(self, collection_name: str, question_id: str) -> bool:
        """Delete a question from the router system (soft delete)"""
        try:
            from datetime import datetime
            
            if collection_name not in self.example_questions:
                logger.error(f"❌ Collection {collection_name} not found")
                return False
            
            # Find and mark as deleted (soft delete)
            for question in self.example_questions[collection_name]:
                if question.get('id') == question_id:
                    question['status'] = 'deleted'
                    question['updated_at'] = datetime.now().isoformat()
                    
                    # Update collection count
                    if collection_name in self.collection_mappings:
                        self.collection_mappings[collection_name]['total_questions'] -= 1
                    
                    logger.info(f"✅ Soft deleted question {question_id} from collection {collection_name}")
                    return True
            
            logger.error(f"❌ Question {question_id} not found in collection {collection_name}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error deleting question: {e}")
            return False
    
    def get_questions_by_collection(self, collection_name: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """Get all questions in a collection with optional filtering"""
        try:
            if collection_name not in self.example_questions:
                return []
            
            questions = self.example_questions[collection_name]
            
            if not include_deleted:
                questions = [q for q in questions if q.get('status', 'active') != 'deleted']
            
            return questions
            
        except Exception as e:
            logger.error(f"❌ Error getting questions for collection {collection_name}: {e}")
            return []
    
    def search_questions(self, query: str, collection_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search questions by text similarity with optional collection filtering"""
        try:
            if not self.question_vectors:
                logger.warning("⚠️ No question vectors available for search")
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Get results from each collection
            all_results = []
            
            for coll_name, vectors in self.question_vectors.items():
                # Skip if collection filter is specified and doesn't match
                if collection_name is not None and coll_name != collection_name:
                    continue
                
                # Get questions for this collection (only active ones)
                questions = self.get_questions_by_collection(coll_name, include_deleted=False)
                
                if len(questions) == 0 or len(vectors) == 0:
                    continue
                
                # Calculate similarities using vectorized operations
                from sklearn.metrics.pairwise import cosine_similarity
                similarities = cosine_similarity(query_embedding, vectors)[0]
                
                # Create results with similarity scores
                for i, (question, similarity) in enumerate(zip(questions, similarities)):
                    if i < len(similarities):  # Safety check
                        all_results.append({
                            **question,
                            'similarity_score': float(similarity)
                        })
            
            # Sort by similarity and return top results
            all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error searching questions: {e}")
            return []
    
    def save_questions_to_file(self, collection_name: str) -> bool:
        """Save questions back to individual router_questions.json files in new structure"""
        try:
            import json
            from datetime import datetime
            
            if not PathConfig:
                logger.error("❌ PathConfig not available, cannot save to new structure")
                return False
                
            path_config = PathConfig()
            
            # Get questions for this collection
            questions = self.get_questions_by_collection(collection_name, include_deleted=True)
            if not questions:
                logger.warning(f"No questions found for collection {collection_name}")
                return False
            
            # Group questions by document (based on source or document ID)
            questions_by_doc = {}
            for question in questions:
                # Extract document ID from question ID or source
                doc_id = None
                if question.get('id'):
                    # Try to extract doc_id from question ID (format: DOC_XXX_main, DOC_XXX_variant_1)
                    parts = question['id'].split('_')
                    if len(parts) >= 2 and parts[0] == 'DOC':
                        doc_id = f"{parts[0]}_{parts[1]}"
                
                if not doc_id:
                    # Fallback: use 'general' as doc_id for questions without clear document association
                    doc_id = 'DOC_GENERAL'
                
                if doc_id not in questions_by_doc:
                    questions_by_doc[doc_id] = []
                questions_by_doc[doc_id].append(question)
            
            # Save questions to individual router_questions.json files
            saved_count = 0
            for doc_id, doc_questions in questions_by_doc.items():
                try:
                    # Get router file path for this document
                    router_file_path = path_config.get_document_router(collection_name, doc_id)
                    
                    # Ensure directory exists
                    router_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Separate main question and variants
                    main_questions = [q for q in doc_questions if q.get('type') == 'main']
                    variant_questions = [q for q in doc_questions if q.get('type') != 'main']
                    
                    # Create router data structure for this document
                    router_data = {
                        'metadata': {
                            'document_id': doc_id,
                            'collection': collection_name,
                            'last_updated': datetime.now().isoformat()
                        },
                        'crud_config': {
                            'enable_crud': True,
                            'version': '1.0',
                            'last_updated': datetime.now().isoformat()
                        },
                        'questions': []
                    }
                    
                    # Add main question if exists
                    if main_questions:
                        main_q = main_questions[0]
                        router_data['main_question'] = {
                            'id': main_q.get('id', 'main_001'),
                            'text': main_q['text'],
                            'tags': main_q.get('keywords', []),
                            'category': main_q.get('category', 'main_procedure'),
                            'priority': main_q.get('priority_score', 1.0),
                            'status': main_q.get('status', 'active'),
                            'created_at': main_q.get('created_at'),
                            'updated_at': main_q.get('updated_at')
                        }
                    
                    # Add variant questions
                    for question in variant_questions:
                        router_data['questions'].append({
                            'id': question.get('id', f'q_{len(router_data["questions"]):03d}'),
                            'text': question['text'],
                            'tags': question.get('keywords', []),
                            'category': question.get('category', 'procedure_variant'),
                            'frequency_score': question.get('priority_score', 0.5),
                            'status': question.get('status', 'active'),
                            'created_at': question.get('created_at'),
                            'updated_at': question.get('updated_at')
                        })
                    
                    # Save to file
                    with open(router_file_path, 'w', encoding='utf-8') as f:
                        json.dump(router_data, f, ensure_ascii=False, indent=2)
                    
                    saved_count += 1
                    logger.debug(f"✅ Saved {len(doc_questions)} questions to {router_file_path}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Error saving questions for document {doc_id}: {e}")
                    continue
            
            logger.info(f"✅ Saved questions to {saved_count} router files in collection {collection_name}")
            return saved_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error saving questions to new structure: {e}")
            return False
    
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
            
            # 🎯 ENHANCED: Boost exact/partial title matches to prioritize core procedures
            for item in similarities:
                question = item['question']
                question_text = item['text']
                
                # Extract document title if available
                if isinstance(question, dict):
                    doc_title = question.get('title', '')
                    source_file = question.get('source', '')
                    
                    # Extract title from source filename if no explicit title
                    if not doc_title and source_file:
                        filename = source_file.split('/')[-1].replace('.json', '').replace('.doc', '')
                        if '. ' in filename:
                            doc_title = filename.split('. ', 1)[1]  # Remove numbering like "01. "
                    
                    # 🔥 EXACT TITLE MATCH: Boost if reference query contains the exact document title
                    if doc_title:
                        # Clean both strings for comparison
                        clean_reference = reference_query.lower().strip()
                        clean_doc_title = doc_title.lower().strip()
                        
                        # Check for exact match or reference contains the document title
                        if clean_doc_title in clean_reference or clean_reference in clean_doc_title:
                            # 🚀 Special boost for core procedures (without "lưu động", "có yếu tố nước ngoài", etc.)
                            is_core_procedure = not any(special in clean_doc_title for special in [
                                'lưu động', 'có yếu tố nước ngoài', 'lại', 'kết hợp', 'chấm dứt'
                            ])
                            
                            if is_core_procedure:
                                # Major boost for core procedures with exact title match
                                item['similarity'] = min(1.0, item['similarity'] + 0.3)
                                logger.info(f"🎯 CORE TITLE MATCH: Boosted '{doc_title}' similarity to {item['similarity']:.3f}")
                            else:
                                # Minor boost for specialized procedures
                                item['similarity'] = min(1.0, item['similarity'] + 0.1)
                                logger.info(f"🎯 SPECIALIZED TITLE MATCH: Boosted '{doc_title}' similarity to {item['similarity']:.3f}")
            
            # Re-sort after boosting
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

class RouterBasedQueryService:
    """Service xử lý câu hỏi mơ hồ dựa trên router results"""
    
    def __init__(self, router: QueryRouter):
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
