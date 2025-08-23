#!/usr/bin/env python3
"""
Smart Clarification Service for LegalRAG
========================================

Tạo câu hỏi clarification thông minh dựa trên confidence levels:
- High confidence (0.7-0.84): Xác nhận với gợi ý cụ thể
- Medium confidence (0.5-0.69): Multiple choices từ top matches  
- Low confidence (0.0-0.49): Category-based suggestions

Author: LegalRAG Team
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClarificationLevel:
    """Định nghĩa các mức clarification"""
    min_confidence: float
    max_confidence: float
    strategy: str
    message_template: str

class ClarificationService:
    """Service tạo clarification thông minh dựa trên confidence levels"""
    
    def __init__(self):
        self.clarification_levels = {
            'high_confidence': ClarificationLevel(
                min_confidence=0.80,
                max_confidence=1.00,
                strategy='auto_route',
                message_template="Routing automatically to '{procedure}' (confidence: {confidence:.1%})"
            ),
            'medium_high_confidence': ClarificationLevel(
                min_confidence=0.65,
                max_confidence=0.79,
                strategy='questions_in_document', 
                message_template="Tôi nghĩ bạn muốn hỏi về '{procedure}'. Chọn câu hỏi cụ thể hoặc tự nhập:"
            ),
            'medium_confidence': ClarificationLevel(
                min_confidence=0.50,
                max_confidence=0.64,
                strategy='multiple_choices',
                message_template="Câu hỏi của bạn có thể liên quan đến các thủ tục sau. Bạn muốn hỏi về:"
            ),
            'low_confidence': ClarificationLevel(
                min_confidence=0.00,
                max_confidence=0.49,
                strategy='category_suggestions',
                message_template="Tôi chưa hiểu rõ ý bạn. Bạn có thể cho biết bạn quan tâm đến lĩnh vực nào?"
            )
        }
        
        # Category mappings cho low confidence - UPDATED FOR NEW STRUCTURE
        self.category_suggestions = {
            # Old structure compatibility
            'ho_tich_cap_xa': {
                'title': 'Hộ tịch cấp xã',
                'description': 'Khai sinh, kết hôn, khai tử, thay đổi hộ tịch',
                'examples': ['khai sinh con', 'đăng ký kết hôn', 'làm lại giấy khai sinh']
            },
            'chung_thuc': {
                'title': 'Chứng thực',
                'description': 'Chứng thực hợp đồng, chữ ký, bản sao giấy tờ',
                'examples': ['chứng thực hợp đồng mua bán', 'chứng thực chữ ký', 'chứng thực bản sao']
            },
            'nuoi_con_nuoi': {
                'title': 'Nuôi con nuôi',
                'description': 'Thủ tục nhận con nuôi, giám hộ',
                'examples': ['nhận con nuôi', 'thủ tục nuôi con nuôi', 'giám hộ trẻ em']
            },
            # New structure mappings
            'quy_trinh_cap_ho_tich_cap_xa': {
                'title': 'Hộ tịch cấp xã',
                'description': 'Khai sinh, kết hôn, khai tử, thay đổi hộ tịch',
                'examples': ['khai sinh con', 'đăng ký kết hôn', 'làm lại giấy khai sinh']
            },
            'quy_trinh_chung_thuc': {
                'title': 'Chứng thực',
                'description': 'Chứng thực hợp đồng, chữ ký, bản sao giấy tờ, di chúc',
                'examples': ['chứng thực hợp đồng mua bán', 'chứng thực di chúc', 'chứng thực bản sao']
            },
            'quy_trinh_nuoi_con_nuoi': {
                'title': 'Nuôi con nuôi',
                'description': 'Thủ tục nhận con nuôi, giám hộ',
                'examples': ['nhận con nuôi', 'thủ tục nuôi con nuôi', 'giám hộ trẻ em']
            }
        }
    
    def generate_clarification(
        self, 
        confidence: float,
        routing_result: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        Tạo clarification thông minh dựa trên confidence level
        """
        try:
            # Convert numpy types to Python native types để tránh lỗi serialization
            confidence = float(confidence) if confidence is not None else 0.0
            
            # Xác định clarification level
            clarification_level = self._determine_clarification_level(confidence)
            level_config = self.clarification_levels[clarification_level]
            
            logger.info(f"🎯 Generating {clarification_level} clarification for confidence: {confidence:.3f}")
            
            # Generate theo strategy
            if level_config.strategy == 'auto_route':
                return self._generate_auto_route_response(confidence, routing_result, level_config)
            
            elif level_config.strategy == 'questions_in_document':
                return self._generate_questions_in_document_clarification(confidence, routing_result, level_config)
            
            elif level_config.strategy == 'confirm_with_suggestion':
                return self._generate_confirmation_clarification(confidence, routing_result, level_config)
            
            elif level_config.strategy == 'multiple_choices':
                return self._generate_multiple_choice_clarification(confidence, routing_result, level_config)
            
            elif level_config.strategy == 'category_suggestions':
                return self._generate_category_clarification(confidence, routing_result, level_config)
            
            else:
                # Fallback
                return self._generate_fallback_clarification(confidence, routing_result)
                
        except Exception as e:
            logger.error(f"Error generating smart clarification: {e}")
            return self._generate_fallback_clarification(float(confidence) if confidence is not None else 0.0, routing_result)
    
    def _determine_clarification_level(self, confidence: float) -> str:
        """Xác định clarification level dựa trên confidence - UPDATED WITH 4 LEVELS"""
        # FIXED: Kiểm tra theo thứ tự từ cao xuống thấp để tránh overlap
        if confidence >= 0.80:
            return 'high_confidence'
        elif confidence >= 0.65 and confidence < 0.80:
            return 'medium_high_confidence'
        elif confidence >= 0.50 and confidence < 0.65:
            return 'medium_confidence'
        elif confidence >= 0.00 and confidence < 0.50:
            return 'low_confidence'
        
        # Edge cases
        else:
            return 'low_confidence'
    
    def _generate_auto_route_response(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> Dict[str, Any]:
        """
        HIGH CONFIDENCE (>0.80): Auto route without clarification
        """
        return {
            "type": "auto_route",
            "confidence_level": "high_confidence",
            "confidence": float(confidence),
            "routing_result": routing_result,
            "message": "Routing automatically with high confidence",
            "strategy": level_config.strategy
        }
    
    def _generate_questions_in_document_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> Dict[str, Any]:
        """
        MEDIUM-HIGH CONFIDENCE (0.65-0.79): Show questions within best matched document
        """
        source_procedure = routing_result.get('source_procedure', 'thủ tục này')
        target_collection = routing_result.get('target_collection')
        
        # Debug logging
        logger.info(f"🔍 MEDIUM-HIGH DEBUG: source_procedure={source_procedure}, target_collection={target_collection}")
        logger.info(f"🔍 MEDIUM-HIGH DEBUG: routing_result keys={list(routing_result.keys())}")
        
        # Handle case where source_procedure is None
        if source_procedure is None or source_procedure == 'thủ tục này':
            # Try to get display name from collection mappings
            display_name = routing_result.get('display_name')
            if display_name:
                source_procedure = display_name
            else:
                source_procedure = f"thủ tục trong {target_collection}" if target_collection else "thủ tục này"
        
        # Get similarity info from routing result
        best_match_info = routing_result.get('best_match', {})
        similarity_percent = best_match_info.get('similarity_percent', round(confidence * 100, 1))
        best_question = best_match_info.get('question', '')
        
        # Enhanced message with similarity info
        if best_question:
            message = f"Tôi nghĩ bạn muốn hỏi về '{source_procedure}'. Câu hỏi tương tự nhất ({similarity_percent}%): \"{best_question[:60]}...\"\n\nChọn câu hỏi cụ thể hoặc tự nhập:"
        else:
            message = level_config.message_template.format(
                procedure=source_procedure,
                confidence=confidence
            )
        
        # This will be handled by RAG engine to get questions from the specific document
        options = [
            {
                'id': 'show_questions',
                'title': f"Xem câu hỏi về {source_procedure}",
                'description': f"Hiển thị các câu hỏi thường gặp về {source_procedure}",
                'action': 'show_document_questions',  # New action for medium-high
                'collection': target_collection,
                'procedure': source_procedure,
                'document_title': source_procedure  # Pass procedure as document title
            },
            {
                'id': 'manual',
                'title': "Tôi muốn mô tả câu hỏi cụ thể",
                'description': "Để tôi diễn đạt lại câu hỏi một cách chi tiết hơn",
                'action': 'manual_input',
                'collection': target_collection
            }
        ]
        
        return {
            "type": "clarification_needed",
            "confidence_level": "medium_high_confidence",
            "confidence": float(confidence),
            "clarification": {
                "message": message,
                "options": options,
                "style": "questions_in_document"
            },
            "routing_context": routing_result,
            "strategy": level_config.strategy
        }

    def _generate_confirmation_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> Dict[str, Any]:
        """
        HIGH CONFIDENCE (0.7-0.84): Xác nhận với gợi ý cụ thể
        """
        source_procedure = routing_result.get('source_procedure', 'thủ tục này')
        best_match = routing_result.get('matched_example', '')
        
        message = level_config.message_template.format(
            procedure=source_procedure,
            confidence=confidence
        )
        
        options = [
            {
                'id': 'yes',
                'title': f"Đúng, tôi muốn hỏi về {source_procedure}",
                'description': f"Tiến hành tìm kiếm thông tin về {source_procedure}",
                'action': 'proceed_with_collection',  # 🔧 CHANGE: Unified action name
                'collection': routing_result.get('target_collection'),
                'procedure': source_procedure
            },
            {
                'id': 'similar',
                'title': "Tương tự, nhưng không hoàn toàn chính xác",
                'description': f"Câu hỏi gốc: {best_match[:80]}..." if best_match else "Hãy giúp tôi tìm thủ tục phù hợp hơn",
                'action': 'proceed_with_collection',  # 🔧 CHANGE: Use same action, let collection decide
                'collection': routing_result.get('target_collection')
            },
            {
                'id': 'no',
                'title': "Không, tôi muốn hỏi về thủ tục khác",
                'description': "Hãy cho tôi thêm lựa chọn khác",
                'action': 'manual_input',  # 🔧 CHANGE: Ask for manual input
                'collection': None
            }
        ]
        
        return {
            "type": "clarification_needed",
            "confidence_level": "high_confidence",
            "confidence": float(confidence),
            "clarification": {
                "message": message,
                "options": options,
                "style": "confirmation"
            },
            "routing_context": routing_result,
            "strategy": level_config.strategy
        }
    
    def _generate_multiple_choice_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> Dict[str, Any]:
        """
        MEDIUM CONFIDENCE (0.5-0.69): Multiple choices từ top matches
        """
        # Lấy top matches từ routing result (cần implement trong smart_router)
        all_scores = routing_result.get('all_scores', {})
        top_matches = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        message = level_config.message_template
        
        options = []
        for i, (collection, score) in enumerate(top_matches, 1):
            collection_display = self.category_suggestions.get(collection, {})
            
            # Convert numpy types to Python native types
            score_float = float(score) if score is not None else 0.0
            
            option = {
                'id': str(i),
                'title': collection_display.get('title', collection),
                'description': collection_display.get('description', ''),
                'confidence': f"{score_float:.1%}",
                'examples': collection_display.get('examples', [])[:2],
                'action': 'proceed_with_collection',
                'collection': collection
            }
            options.append(option)
        
        # Add "none of the above" option
        options.append({
            'id': 'other',
            'title': "Không có thủ tục nào phù hợp",
            'description': "Tôi muốn hỏi về thủ tục khác",
            'action': 'manual_input',
            'collection': None
        })
        
        return {
            "type": "clarification_needed",
            "confidence_level": "medium_confidence",
            "confidence": float(confidence),
            "clarification": {
                "message": message,
                "options": options,
                "style": "multiple_choice"
            },
            "routing_context": routing_result,
            "strategy": level_config.strategy
        }
    
    def _generate_category_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> Dict[str, Any]:
        """
        LOW CONFIDENCE (0.0-0.49): Category-based suggestions
        """
        message = level_config.message_template
        
        options = []
        for i, (collection_id, category_info) in enumerate(self.category_suggestions.items(), 1):
            option = {
                'id': str(i),
                'title': category_info['title'],
                'description': category_info['description'],
                'examples': category_info['examples'],
                'action': 'proceed_with_collection',  # 🔧 CHANGE: Match handler expectation
                'collection': collection_id
            }
            options.append(option)
        
        # Add manual input option
        options.append({
            'id': 'manual',
            'title': "Tôi muốn mô tả rõ hơn",
            'description': "Để tôi diễn đạt lại câu hỏi một cách chi tiết hơn",
            'action': 'manual_input',
            'collection': None
        })
        
        return {
            "type": "clarification_needed",
            "confidence_level": "low_confidence",
            "confidence": float(confidence),
            "clarification": {
                "message": message,
                "options": options,
                "style": "category_based",
                "additional_help": "Bạn có thể mô tả cụ thể hơn về tình huống hoặc giấy tờ bạn cần làm"
            },
            "routing_context": routing_result,
            "strategy": level_config.strategy
        }
    
    def _generate_fallback_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback clarification khi có lỗi"""
        return {
            "type": "clarification_needed",
            "confidence_level": "fallback",
            "confidence": float(confidence),
            "clarification": {
                "message": "Xin lỗi, tôi cần thêm thông tin để hiểu rõ câu hỏi của bạn.",
                "options": [
                    {
                        'id': 'retry',
                        'title': "Hãy diễn đạt lại câu hỏi",
                        'description': "Tôi sẽ cố gắng hiểu rõ hơn",
                        'action': 'manual_input'
                    }
                ],
                "style": "fallback"
            },
            "routing_context": routing_result,
            "strategy": "fallback"
        }
    
    def get_related_procedures(self, collection: str, procedure: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Lấy các thủ tục liên quan trong cùng collection
        (Có thể integrate với smart_router để lấy similar procedures)
        """
        # Placeholder - sẽ integrate với smart_router
        return []
