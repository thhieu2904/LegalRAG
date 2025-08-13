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

class SmartClarificationService:
    """Service tạo clarification thông minh dựa trên confidence levels"""
    
    def __init__(self):
        self.clarification_levels = {
            'high_confidence': ClarificationLevel(
                min_confidence=0.70,
                max_confidence=0.84,
                strategy='confirm_with_suggestion',
                message_template="Tôi nghĩ bạn muốn hỏi về '{procedure}' (độ tin cậy: {confidence:.1%}). Đúng không?"
            ),
            'medium_confidence': ClarificationLevel(
                min_confidence=0.50,
                max_confidence=0.69,
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
        
        # Category mappings cho low confidence
        self.category_suggestions = {
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
            if level_config.strategy == 'confirm_with_suggestion':
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
        """Xác định clarification level dựa trên confidence"""
        # FIXED: Kiểm tra theo thứ tự từ cao xuống thấp để tránh overlap
        if confidence >= 0.70 and confidence <= 0.84:
            return 'high_confidence'
        elif confidence >= 0.50 and confidence < 0.70:
            return 'medium_confidence'
        elif confidence >= 0.00 and confidence < 0.50:
            return 'low_confidence'
        
        # Edge cases
        if confidence > 0.84:
            return 'high_confidence'
        else:
            return 'low_confidence'
    
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
                'action': 'proceed_with_routing',
                'collection': routing_result.get('target_collection'),
                'procedure': source_procedure
            },
            {
                'id': 'similar',
                'title': "Tương tự, nhưng không hoàn toàn chính xác",
                'description': f"Câu hỏi gốc: {best_match[:80]}..." if best_match else "Hãy giúp tôi tìm thủ tục phù hợp hơn",
                'action': 'show_related_options',
                'collection': routing_result.get('target_collection')
            },
            {
                'id': 'no',
                'title': "Không, tôi muốn hỏi về thủ tục khác",
                'description': "Hãy cho tôi thêm lựa chọn khác",
                'action': 'show_category_options',
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
                'action': 'explore_category',
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
