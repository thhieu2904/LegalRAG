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
from typing import Dict, List, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
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
        self.base_path = "data/storage/collections"  # New questions.json structure
        self.cache_file = "data/cache/router_embeddings.pkl"
        
        # Load configuration
        self.config = self._load_config()
        
        # Example questions database
        self.example_questions = {}
        self.question_vectors = {}
        self.collection_mappings = {}
        self.cached_embeddings = {}  # For pre-computed embeddings cache
        
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
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from new questions.json structure"""
        try:
            # Load from new structure: data/storage/collections/*/documents/*/questions.json
            collections_path = self.base_path  # "data/storage/collections"
            
            if not os.path.exists(collections_path):
                logger.warning(f"Collections directory not found: {collections_path}")
                return {}
            
            config = {
                'metadata': {
                    'version': '3.0',
                    'generator': 'questions_json_structure',
                    'structure': 'questions_plus_document'
                },
                'collection_mappings': {}
            }
            
            # Scan collections
            for collection_name in os.listdir(collections_path):
                collection_path = os.path.join(collections_path, collection_name)
                if not os.path.isdir(collection_path):
                    continue
                
                documents_path = os.path.join(collection_path, "documents")
                if not os.path.exists(documents_path):
                    continue
                
                # Count documents với questions.json
                doc_count = 0
                for doc_name in os.listdir(documents_path):
                    doc_path = os.path.join(documents_path, doc_name)
                    if os.path.isdir(doc_path):
                        questions_file = os.path.join(doc_path, "questions.json")
                        if os.path.exists(questions_file):
                            doc_count += 1
                
                if doc_count > 0:
                    config['collection_mappings'][collection_name] = {
                        'description': collection_name.replace('_', ' ').title(),
                        'file_count': doc_count,
                        'path': collection_path,
                        'documents_path': documents_path
                    }
            
            logger.info(f"📋 Loaded new structure: {len(config['collection_mappings'])} collections")
            return config
            
        except Exception as e:
            logger.error(f"❌ Error loading new structure config: {e}")
            return {}
    
    def _load_from_cache(self) -> bool:
        """Load router data from cache with embeddings support"""
        try:
            if not os.path.exists(self.cache_file):
                logger.info("📦 No cache file found")
                return False
            
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Check for NEW cache format with embeddings
            if isinstance(cache_data, dict) and 'embeddings' in cache_data:
                logger.info("🚀 Loading NEW cache format with pre-computed embeddings")
                
                # Load collections text data
                self.example_questions = cache_data.get('collections', {})
                
                # Load pre-computed embeddings
                self.cached_embeddings = cache_data.get('embeddings', {})
                
                # Build collection mappings from cache
                self.collection_mappings = {}
                for collection_name, docs in self.example_questions.items():
                    self.collection_mappings[collection_name] = {
                        'description': collection_name.replace('_', ' ').title(),
                        'file_count': len(docs),
                        'path': f"data/storage/collections/{collection_name}",
                        'documents_path': f"data/storage/collections/{collection_name}/documents"
                    }
                
                total_docs = sum(len(docs) for docs in self.example_questions.values())
                logger.info(f"📦 Loaded cache with EMBEDDINGS: {len(self.collection_mappings)} collections, {total_docs} documents")
                logger.info(f"🎯 Cached embeddings available for: {list(self.cached_embeddings.keys())}")
                return True
                
            elif isinstance(cache_data, dict) and 'metadata' in cache_data:
                # Old cache format without embeddings
                logger.warning("⚠️  OLD cache format without embeddings - will be slow")
                self.example_questions = cache_data.get('collections', {})
                self.cached_embeddings = {}  # No cached embeddings
                
                # Build collection mappings from cache
                self.collection_mappings = {}
                for collection_name, docs in self.example_questions.items():
                    self.collection_mappings[collection_name] = {
                        'description': collection_name.replace('_', ' ').title(),
                        'file_count': len(docs),
                        'path': f"data/storage/collections/{collection_name}",
                        'documents_path': f"data/storage/collections/{collection_name}/documents"
                    }
                
                logger.info(f"📦 Loaded cache: {len(self.collection_mappings)} collections, {sum(len(docs) for docs in self.example_questions.values())} documents")
                return True
            else:
                logger.warning("⚠️  Unknown cache format, will reload")
                return False
                
        except Exception as e:
            logger.error(f"❌ Cache loading error: {e}")
            return False
    
    def _load_example_questions(self):
        """Load example questions from questions.json files"""
        logger.info("🔄 Loading example questions from new structure...")
        
        self.example_questions = {}
        
        for collection_name, mapping in self.collection_mappings.items():
            collection_questions = {}
            documents_path = mapping['documents_path']
            
            if not os.path.exists(documents_path):
                continue
            
            for doc_name in os.listdir(documents_path):
                doc_path = os.path.join(documents_path, doc_name)
                questions_file = os.path.join(doc_path, "questions.json")
                
                if os.path.exists(questions_file):
                    try:
                        with open(questions_file, 'r', encoding='utf-8') as f:
                            questions_data = json.load(f)
                        
                        # Extract main question and variants
                        main_question = questions_data.get('main_question', '')
                        variants = questions_data.get('question_variants', [])
                        
                        collection_questions[doc_name] = {
                            'main_question': main_question,
                            'question_variants': variants
                        }
                    except Exception as e:
                        logger.error(f"❌ Error loading {questions_file}: {e}")
            
            if collection_questions:
                self.example_questions[collection_name] = collection_questions
        
        logger.info(f"✅ Loaded {len(self.example_questions)} collections with questions")
    
    def _initialize_question_vectors(self):
        """Initialize question vectors for similarity matching"""
        logger.info("🔄 Initializing question vectors...")
        
        self.question_vectors = {}
        
        for collection_name, documents in self.example_questions.items():
            collection_vectors = {}
            
            for doc_name, doc_data in documents.items():
                # Combine main question and variants
                all_questions = [doc_data['main_question']]
                all_questions.extend(doc_data['question_variants'])
                
                # Create embeddings (text-only for now)
                collection_vectors[doc_name] = {
                    'questions': all_questions,
                    'main_question': doc_data['main_question']
                }
            
            self.question_vectors[collection_name] = collection_vectors
        
        logger.info(f"✅ Initialized vectors for {len(self.question_vectors)} collections")
    
    def _save_to_cache(self):
        """Save router data to cache"""
        try:
            cache_data = {
                'metadata': {
                    'structure_version': '3.0',
                    'cache_type': 'questions_only',
                    'created_at': time.time(),
                    'collections_count': len(self.example_questions),
                    'total_documents': sum(len(docs) for docs in self.example_questions.values())
                },
                'collections': self.example_questions
            }
            
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.info(f"💾 Cache saved: {self.cache_file}")
            
        except Exception as e:
            logger.error(f"❌ Cache save error: {e}")
    
    def route_query(self, query: str, session=None) -> Dict[str, Any]:
        """Route query to appropriate collection using metadata and semantic matching"""
        try:
            # Use semantic routing based on document metadata and content
            return self._semantic_route_query(query, session)
            
        except Exception as e:
            logger.error(f"❌ Router error: {e}")
            return {
                'status': 'error',
                'confidence': 0.0,
                'target_collection': None,
                'confidence_level': 'none',
                'message': 'Lỗi hệ thống routing'
            }
    
    def _semantic_route_query(self, query: str, session=None) -> Dict[str, Any]:
        """Semantic routing using embedding similarity with cached embeddings"""
        try:
            # Get query embedding
            query_embedding = self.embedding_model.encode([query])
            
            collection_scores = {}
            all_similarities = []
            
            # Check if we have cached embeddings (FAST PATH)
            if hasattr(self, 'cached_embeddings') and self.cached_embeddings:
                logger.info("🚀 Using CACHED embeddings for fast similarity calculation")
                
                # Calculate similarity with cached embeddings
                for collection_name, collection_data in self.cached_embeddings.items():
                    collection_similarities = []
                    
                    for doc_name, doc_data in collection_data.items():
                        cached_embeddings = doc_data['embeddings']
                        questions = doc_data['questions']
                        
                        # Calculate cosine similarity with cached embeddings
                        from sklearn.metrics.pairwise import cosine_similarity
                        similarities = cosine_similarity(query_embedding, cached_embeddings)[0]
                        
                        # Get best similarity for this document
                        max_similarity = float(max(similarities))
                        best_question_idx = int(similarities.argmax())
                        best_question = questions[best_question_idx]
                        
                        collection_similarities.append({
                            'similarity': max_similarity,
                            'document': doc_name,
                            'best_question': best_question,
                            'question_type': 'main' if best_question_idx == 0 else 'variant'
                        })
                        
                        all_similarities.append({
                            'collection': collection_name,
                            'document': doc_name,
                            'similarity': max_similarity,
                            'question': best_question
                        })
                    
                    if collection_similarities:
                        # Get best document similarity for this collection
                        best_doc = max(collection_similarities, key=lambda x: x['similarity'])
                        collection_scores[collection_name] = {
                            'score': best_doc['similarity'],
                            'best_document': best_doc['document'],
                            'best_question': best_doc['best_question'],
                            'question_type': best_doc['question_type'],
                            'all_docs': collection_similarities
                        }
            
            else:
                # FALLBACK: Real-time embedding calculation (SLOW PATH)
                logger.warning("⚠️  No cached embeddings - using SLOW real-time calculation")
                
                # Calculate similarity with all cached questions
                for collection_name, documents in self.example_questions.items():
                    collection_similarities = []
                    
                    for doc_name, doc_data in documents.items():
                        # Get all questions for this document
                        main_question = doc_data.get('main_question', '')
                        variants = doc_data.get('question_variants', [])
                        all_questions = [main_question] + variants
                        
                        # Filter out empty questions
                        valid_questions = [q for q in all_questions if q.strip()]
                        
                        if valid_questions:
                            # Calculate embeddings for document questions (SLOW!)
                            question_embeddings = self.embedding_model.encode(valid_questions)
                            
                            # Calculate cosine similarity
                            from sklearn.metrics.pairwise import cosine_similarity
                            similarities = cosine_similarity(query_embedding, question_embeddings)[0]
                            
                            # Get best similarity for this document
                            max_similarity = float(max(similarities))
                            best_question_idx = int(similarities.argmax())
                            best_question = valid_questions[best_question_idx]
                            
                            collection_similarities.append({
                                'similarity': max_similarity,
                                'document': doc_name,
                                'best_question': best_question,
                                'question_type': 'main' if best_question_idx == 0 else 'variant'
                            })
                            
                            all_similarities.append({
                                'collection': collection_name,
                                'document': doc_name,
                                'similarity': max_similarity,
                                'question': best_question
                            })
                    
                    if collection_similarities:
                        # Get best document similarity for this collection
                        best_doc = max(collection_similarities, key=lambda x: x['similarity'])
                        collection_scores[collection_name] = {
                            'score': best_doc['similarity'],
                            'best_document': best_doc['document'],
                            'best_question': best_doc['best_question'],
                            'question_type': best_doc['question_type'],
                            'all_docs': collection_similarities
                        }
            
            # Find best collection
            if not collection_scores:
                return {
                    'status': 'ambiguous',
                    'confidence': 0.1,
                    'target_collection': None,
                    'confidence_level': 'low',
                    'message': 'Không tìm thấy câu hỏi tương tự'
                }
            
            best_collection = max(collection_scores.keys(), key=lambda k: collection_scores[k]['score'])
            best_score = collection_scores[best_collection]['score']
            best_match = collection_scores[best_collection]
            
            # DEBUG: Log top 3 documents for troubleshooting
            if collection_scores:
                sorted_docs = sorted([(k, v['score'], v['best_document']) for k, v in collection_scores.items()], 
                                   key=lambda x: x[1], reverse=True)
                logger.info(f"🏆 TOP DOCUMENT SCORES: {sorted_docs[:3]}")
                logger.info(f"🎯 WINNER: {best_match['best_document']} with {best_score:.4f}")
                logger.info(f"📝 WINNING QUESTION: {best_match['best_question']}")
            
            # Determine confidence level based on similarity score
            confidence_level = 'low'
            if best_score >= 0.85:  # Very high similarity
                confidence_level = 'high'
            elif best_score >= 0.75:  # Good similarity
                confidence_level = 'medium_high'
            elif best_score >= 0.65:  # Acceptable similarity
                confidence_level = 'medium'
            
            # Sort all similarities for clarification
            all_similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 🔥 SESSION CONFIDENCE OVERRIDE: Check if we should boost based on session context
            original_confidence = best_score
            original_confidence_level = confidence_level
            was_overridden = False
            
            if session and hasattr(session, 'should_override_confidence'):
                if session.should_override_confidence(best_score):
                    # Use session collection and boost confidence
                    target_collection = session.last_successful_collection
                    best_score = 0.85  # Override to high confidence 
                    confidence_level = 'override_high'
                    was_overridden = True
                    logger.info(f"🔥 SESSION OVERRIDE: {original_confidence:.3f} → {best_score:.3f} for collection {target_collection}")
                else:
                    target_collection = best_collection if best_score >= 0.65 else None
            else:
                target_collection = best_collection if best_score >= 0.65 else None
            
            return {
                'status': 'routed' if best_score >= 0.65 else 'ambiguous',
                'confidence': best_score,
                'target_collection': target_collection,
                'confidence_level': confidence_level,
                'original_confidence': original_confidence if was_overridden else None,
                'was_overridden': was_overridden,
                'all_scores': {k: v['score'] for k, v in collection_scores.items()},
                'best_match': {
                    'collection': best_collection,
                    'document': best_match['best_document'],
                    'question': best_match['best_question'],
                    'similarity_percent': round(best_score * 100, 1),
                    'question_type': best_match['question_type']
                },
                'top_similar_questions': all_similarities[:10],  # Top 10 for clarification
                'matching_details': [f"Best match: {best_match['best_question']} ({round(best_score * 100, 1)}%)"]
            }
            
        except Exception as e:
            logger.error(f"❌ Semantic routing error: {e}")
            # Simple fallback
            return {
                'status': 'ambiguous',
                'confidence': 0.3,
                'target_collection': None,
                'confidence_level': 'low',
                'message': f'Lỗi semantic routing: {e}'
            }
    
    def _get_document_metadata(self, collection_name: str, doc_name: str) -> Dict[str, Any]:
        """Get document metadata from JSON file"""
        try:
            collection_path = os.path.join(self.base_path, collection_name, "documents", doc_name)
            
            # Try to find the main document JSON (not questions.json)
            for file_name in os.listdir(collection_path):
                if file_name.endswith('.json') and file_name != 'questions.json':
                    file_path = os.path.join(collection_path, file_name)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        
                    # Extract metadata and keywords from content chunks
                    metadata = doc_data.get('metadata', {})
                    
                    # Aggregate keywords from all chunks
                    all_keywords = []
                    content_chunks = doc_data.get('content_chunks', [])
                    for chunk in content_chunks:
                        chunk_keywords = chunk.get('keywords', [])
                        all_keywords.extend(chunk_keywords)
                    
                    # Add keywords to metadata
                    if all_keywords:
                        metadata['keywords'] = list(set(all_keywords))  # Remove duplicates
                    
                    return metadata
            
            return {}
            
        except Exception as e:
            logger.warning(f"Could not load metadata for {collection_name}/{doc_name}: {e}")
            return {}
    
    def get_example_questions_for_collection(self, collection_name: str) -> List[Dict[str, Any]]:
        """Get example questions for a specific collection"""
        try:
            # Collection name mapping - frontend uses short names
            collection_mappings = {
                'ho_tich_cap_xa': 'quy_trinh_cap_ho_tich_cap_xa',
                'chung_thuc': 'quy_trinh_chung_thuc', 
                'nuoi_con_nuoi': 'quy_trinh_nuoi_con_nuoi'
            }
            
            # Map frontend collection name to actual collection name
            actual_collection = collection_mappings.get(collection_name, collection_name)
            
            if actual_collection not in self.example_questions:
                logger.warning(f"Collection not found: {actual_collection} (requested: {collection_name})")
                return []
            
            collection_docs = self.example_questions[actual_collection]
            questions_list = []
            
            for doc_name, doc_data in collection_docs.items():
                main_question = doc_data.get('main_question', '')
                variants = doc_data.get('question_variants', [])
                
                # Add main question
                if main_question:
                    questions_list.append({
                        'text': main_question,
                        'type': 'main',
                        'source': f"{actual_collection}/documents/{doc_name}/questions.json",
                        'document': doc_name
                    })
                
                # Add variants
                for variant in variants:
                    if variant.strip():
                        questions_list.append({
                            'text': variant,
                            'type': 'variant',
                            'source': f"{actual_collection}/documents/{doc_name}/questions.json",
                            'document': doc_name
                        })
            
            logger.info(f"Retrieved {len(questions_list)} questions for collection {actual_collection} (requested: {collection_name})")
            return questions_list
            
        except Exception as e:
            logger.error(f"Error getting questions for collection {collection_name}: {e}")
            return []
    
    def get_collections(self) -> List[Dict[str, Any]]:
        """Get list of available collections with proper structure"""
        try:
            # Frontend mapping - return short names for easier frontend handling
            name_mappings = {
                'quy_trinh_cap_ho_tich_cap_xa': 'ho_tich_cap_xa',
                'quy_trinh_chung_thuc': 'chung_thuc',
                'quy_trinh_nuoi_con_nuoi': 'nuoi_con_nuoi'
            }
            
            display_names = {
                'quy_trinh_cap_ho_tich_cap_xa': 'Hộ tịch cấp xã',
                'quy_trinh_chung_thuc': 'Chứng thực',
                'quy_trinh_nuoi_con_nuoi': 'Nuôi con nuôi'
            }
            
            collections = []
            
            # Iterate through collection_mappings (new structure)
            for collection_name, collection_info in self.collection_mappings.items():
                short_name = name_mappings.get(collection_name, collection_name)
                display_name = display_names.get(collection_name, collection_info.get('description', collection_name))
                
                collections.append({
                    'name': short_name,
                    'full_name': collection_name,
                    'title': display_name,
                    'description': f"Các thủ tục và quy trình về {display_name.lower() if display_name else 'unknown'}",
                    'file_count': collection_info.get('file_count', 0),
                    'path': collection_info.get('path', ''),
                    'documents_path': collection_info.get('documents_path', ''),
                    'question_count': len(self.example_questions.get(collection_name, []))
                })
            
            logger.info(f"📊 Returning {len(collections)} collections for frontend")
            return collections
            
        except Exception as e:
            logger.error(f"Error getting collections: {e}")
            return []

class RouterBasedQueryService:
    """Service for handling ambiguous queries using router"""
    
    def __init__(self, router: QueryRouter):
        self.router = router
        logger.info("✅ RouterBasedQueryService initialized")
    
    def handle_ambiguous_query(self, query: str, session=None):
        """Handle ambiguous query using router"""
        try:
            # Use router to find best match
            if hasattr(self.router, 'route_query'):
                return self.router.route_query(query, session)
            else:
                # Fallback basic response
                return {
                    'status': 'ambiguous',
                    'confidence': 0.3,
                    'target_collection': None,
                    'message': 'Query is ambiguous, please be more specific'
                }
        except Exception as e:
            logger.error(f"❌ RouterBasedQueryService error: {e}")
            return {
                'status': 'error',
                'confidence': 0.0,
                'target_collection': None,
                'message': f'Error processing query: {e}'
            }

    # _scan_individual_files method removed - no longer needed with questions.json structure