"""
Enhanced Router Service - Phase 1: Signal Optimization
Tối ưu hóa tín hiệu để giảm nhiễu và cải thiện độ chính xác
"""

import logging
import numpy as np
import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class EnhancedQueryRouter:
    """Enhanced Router với signal optimization để giảm nhiễu và cải thiện accuracy"""
    
    def __init__(self, base_router):
        """Initialize enhanced router wrapper"""
        self.base_router = base_router
        self.embedding_model = base_router.embedding_model
        
        # Weighted scoring configuration
        self.similarity_weights = {
            'title_weight': 0.6,        # Title matching là quan trọng nhất
            'main_question_weight': 0.4, # Main question weight
            'variant_weight': 0.25,     # Variants weight thấp hơn
            'metadata_penalty': 0.1     # Penalty cho metadata noise
        }
        
        # Critical metadata fields only (reduce noise)
        self.important_metadata_fields = {
            'title',                    # Quan trọng nhất
            'code',                     # Document code
            'requirements_conditions',  # Requirements
            'fee_vnd'                   # Cost info
        }
        
        logger.info("🎯 Enhanced Router initialized with signal optimization")
        logger.info(f"📊 Similarity weights: {self.similarity_weights}")
    
    def route_query_enhanced(self, query: str, session=None) -> Dict[str, Any]:
        """Enhanced routing với weighted similarity calculation"""
        try:
            # Get query embedding
            query_embedding = self.embedding_model.encode([query])
            
            collection_scores = {}
            all_similarities = []
            
            # Use optimized similarity calculation
            if hasattr(self.base_router, 'cached_embeddings') and self.base_router.cached_embeddings:
                logger.info("🚀 Using ENHANCED similarity calculation with GPU optimization")
                
                for collection_name, collection_data in self.base_router.cached_embeddings.items():
                    collection_similarities = []
                    
                    for doc_name, doc_data in collection_data.items():
                        # Calculate enhanced similarity score
                        enhanced_score = self._calculate_enhanced_similarity(
                            query, query_embedding, doc_name, doc_data, collection_name
                        )
                        
                        collection_similarities.append({
                            'similarity': enhanced_score['total_score'],
                            'document': doc_name,
                            'best_question': enhanced_score['best_question'],
                            'question_type': enhanced_score['question_type'],
                            'score_breakdown': enhanced_score['breakdown']
                        })
                        
                        all_similarities.append({
                            'collection': collection_name,
                            'document': doc_name,
                            'similarity': enhanced_score['total_score'],
                            'question': enhanced_score['best_question'],
                            'breakdown': enhanced_score['breakdown']
                        })
                    
                    if collection_similarities:
                        # Get best document for this collection
                        best_doc = max(collection_similarities, key=lambda x: x['similarity'])
                        collection_scores[collection_name] = {
                            'score': best_doc['similarity'],
                            'best_document': best_doc['document'],
                            'best_question': best_doc['best_question'],
                            'question_type': best_doc['question_type'],
                            'score_breakdown': best_doc['score_breakdown'],
                            'all_docs': collection_similarities
                        }
            
            else:
                # Fallback to base router
                logger.warning("⚠️ No cached embeddings, falling back to base router")
                return self.base_router._semantic_route_query(query, session)
            
            # Find best collection with enhanced logic
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
            
            # Enhanced confidence level calculation
            confidence_level = self._determine_enhanced_confidence_level(best_score, best_match)
            
            # Log detailed results for debugging
            sorted_docs = sorted([(k, v['score'], v['best_document']) for k, v in collection_scores.items()], 
                               key=lambda x: x[1], reverse=True)
            logger.info(f"🏆 ENHANCED TOP SCORES: {sorted_docs[:3]}")
            logger.info(f"🎯 ENHANCED WINNER: {best_match['best_document']} with {best_score:.4f}")
            logger.info(f"📝 WINNING QUESTION: {best_match['best_question']}")
            logger.info(f"📊 SCORE BREAKDOWN: {best_match['score_breakdown']}")
            
            # Apply session override logic if needed
            target_collection = best_collection if best_score >= 0.65 else None
            
            return {
                'status': 'routed' if best_score >= 0.65 else 'ambiguous',
                'confidence': best_score,
                'target_collection': target_collection,
                'confidence_level': confidence_level,
                'all_scores': {k: v['score'] for k, v in collection_scores.items()},
                'best_match': {
                    'collection': best_collection,
                    'document': best_match['best_document'],
                    'question': best_match['best_question'],
                    'similarity_percent': round(best_score * 100, 1),
                    'question_type': best_match['question_type'],
                    'score_breakdown': best_match['score_breakdown']
                },
                'top_similar_questions': all_similarities[:10],
                'enhancement_applied': True,
                'routing_method': 'enhanced_weighted_similarity'
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced routing error: {e}")
            # Fallback to base router
            return self.base_router._semantic_route_query(query, session)
    
    def _calculate_enhanced_similarity(
        self, 
        query: str,
        query_embedding: np.ndarray, 
        doc_name: str,
        doc_data: Dict,
        collection_name: str
    ) -> Dict[str, Any]:
        """Calculate enhanced similarity với weighted components"""
        
        # Get document metadata với noise reduction
        doc_metadata = self._get_filtered_metadata(collection_name, doc_name)
        
        # Component scores
        scores = {}
        
        # 1. Title similarity (highest weight)
        title_score = 0.0
        if doc_metadata and 'title' in doc_metadata:
            title_embedding = self.embedding_model.encode([doc_metadata['title']])[0]
            title_similarity = cosine_similarity([query_embedding[0]], [title_embedding])[0][0]
            title_score = float(title_similarity)
            scores['title'] = title_score
        
        # 2. Questions similarity (from cached embeddings)
        embeddings = doc_data['embeddings']
        questions = doc_data['questions']
        
        similarities = cosine_similarity(query_embedding, embeddings)[0]
        max_similarity = float(max(similarities))
        best_question_idx = int(similarities.argmax())
        best_question = questions[best_question_idx]
        question_type = 'main' if best_question_idx == 0 else 'variant'
        
        # Apply question type weighting
        if question_type == 'main':
            question_score = max_similarity * self.similarity_weights['main_question_weight']
        else:
            question_score = max_similarity * self.similarity_weights['variant_weight']
        
        scores['question'] = max_similarity
        scores['question_weighted'] = question_score
        
        # 3. Intent-based penalties and boosts
        intent_adjustment = self._calculate_intent_adjustment(query, doc_metadata, best_question)
        scores['intent_adjustment'] = intent_adjustment
        
        # 4. Calculate weighted total score
        if title_score > 0:
            # If we have title, use title + question weighted
            total_score = (
                title_score * self.similarity_weights['title_weight'] +
                question_score +
                intent_adjustment
            )
        else:
            # No title, rely more on question
            total_score = question_score * 1.2 + intent_adjustment
        
        # Clamp score to [0, 1]
        total_score = max(0.0, min(1.0, total_score))
        
        return {
            'total_score': total_score,
            'best_question': best_question,
            'question_type': question_type,
            'breakdown': {
                'title_score': title_score,
                'question_score': max_similarity,
                'question_weighted': question_score,
                'intent_adjustment': intent_adjustment,
                'final_weighted': total_score
            }
        }
    
    def _get_filtered_metadata(self, collection_name: str, doc_name: str) -> Dict[str, Any]:
        """Get metadata với noise filtering - chỉ giữ các fields quan trọng"""
        try:
            # Get full metadata from base router
            full_metadata = self.base_router._get_document_metadata(collection_name, doc_name)
            
            if not full_metadata:
                return {}
            
            # Filter to keep only important fields
            filtered_metadata = {}
            for field in self.important_metadata_fields:
                if field in full_metadata:
                    filtered_metadata[field] = full_metadata[field]
            
            return filtered_metadata
            
        except Exception as e:
            logger.warning(f"⚠️ Error getting filtered metadata for {collection_name}/{doc_name}: {e}")
            return {}
    
    def _calculate_intent_adjustment(
        self, 
        query: str, 
        doc_metadata: Dict, 
        best_question: str
    ) -> float:
        """Calculate intent-based adjustment để phân biệt similar documents"""
        
        adjustment = 0.0
        query_lower = query.lower()
        title_lower = doc_metadata.get('title', '').lower() if doc_metadata else ''
        question_lower = best_question.lower()
        
        # Intent signals detection
        combination_signals = [
            'nhận cha', 'nhận mẹ', 'nhận con', 'kết hợp', 'cùng lúc', 
            '2 trong 1', 'đăng ký nhận', 'cam đoan', 'giám định'
        ]
        
        simple_signals = [
            'chỉ cần', 'đơn thuần', 'bình thường', 'thôi', 'không cần nhận'
        ]
        
        # Count intent signals in query
        combination_count = sum(1 for signal in combination_signals if signal in query_lower)
        simple_count = sum(1 for signal in simple_signals if signal in query_lower)
        
        # Check document type
        is_combination_doc = any(signal in title_lower for signal in ['kết hợp', 'nhận cha', 'nhận mẹ'])
        
        # Apply intent-based adjustments
        if combination_count > 0:
            # User có intent về combination
            if is_combination_doc:
                adjustment += 0.15  # Boost combination docs
            else:
                adjustment -= 0.05  # Slight penalty for simple docs
        
        elif simple_count > 0:
            # User có intent về simple procedure
            if not is_combination_doc:
                adjustment += 0.1   # Boost simple docs
            else:
                adjustment -= 0.15  # Strong penalty for combination docs
        
        else:
            # No explicit intent signals - rely on other factors
            # Check for implicit signals
            has_father_foreign = any(phrase in query_lower for phrase in ['cha nước ngoài', 'cha là người nước ngoài'])
            has_birth_request = any(phrase in query_lower for phrase in ['làm giấy khai sinh', 'đăng ký khai sinh'])
            
            if has_father_foreign and has_birth_request and not combination_count:
                # Implicit simple birth registration intent
                if not is_combination_doc:
                    adjustment += 0.08  # Favor simple docs
                else:
                    adjustment -= 0.12  # Penalty for combination docs
        
        # Keyword matching boost
        query_words = set(query_lower.split())
        title_words = set(title_lower.split()) if title_lower else set()
        
        # Exact keyword matches
        exact_matches = len(query_words.intersection(title_words))
        if exact_matches > 0:
            adjustment += min(0.05, exact_matches * 0.02)
        
        return adjustment
    
    def _determine_enhanced_confidence_level(self, score: float, best_match: Dict) -> str:
        """Determine confidence level với enhanced logic"""
        
        # Get score breakdown for more nuanced confidence
        breakdown = best_match.get('score_breakdown', {})
        title_score = breakdown.get('title_score', 0)
        intent_adjustment = breakdown.get('intent_adjustment', 0)
        
        # Enhanced confidence thresholds
        if score >= 0.85:
            return 'very_high_confidence'
        elif score >= 0.75:
            # Check if we have strong title match
            if title_score > 0.7:
                return 'high_confidence'
            else:
                return 'medium_high_confidence'
        elif score >= 0.65:
            # Check intent alignment
            if intent_adjustment > 0:
                return 'medium_high_confidence'
            else:
                return 'medium_confidence'
        elif score >= 0.5:
            return 'medium_confidence'
        else:
            return 'low_confidence'
    
    def route_query(self, query: str, session=None) -> Dict[str, Any]:
        """Main routing method - wrapper cho enhanced routing"""
        return self.route_query_enhanced(query, session)
