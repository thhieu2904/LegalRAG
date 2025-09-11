#!/usr/bin/env python3
"""
Smart Clarification Service for LegalRAG
========================================

5-Layer Clarification System:
- High confidence (≥0.80): Auto route - no clarification needed
- Medium-High confidence (0.65-0.79): Confirm with best questions
- Medium confidence (0.50-0.64): Multiple choice options
- Low confidence (0.30-0.49): Category-based suggestions
- Insufficient context (<0.30): Context gathering

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
                message_template="Routing automatically with high confidence (confidence: {confidence:.1%})"
            ),
            'medium_high_confidence': ClarificationLevel(
                min_confidence=0.65,
                max_confidence=0.79,
                strategy='confirm_with_best_questions', 
                message_template="Tôi nghĩ bạn muốn hỏi về '{procedure}' (độ tin cậy: {confidence:.1%}). Đúng không?"
            ),
            'medium_confidence': ClarificationLevel(
                min_confidence=0.50,
                max_confidence=0.64,
                strategy='multiple_choices',
                message_template="Câu hỏi của bạn có thể liên quan đến các thủ tục sau. Bạn muốn hỏi về:"
            ),
            'low_confidence': ClarificationLevel(
                min_confidence=0.30,
                max_confidence=0.49,
                strategy='category_suggestions',
                message_template="Tôi chưa hiểu rõ ý bạn. Bạn có thể cho biết bạn quan tâm đến lĩnh vực nào?"
            ),
            'insufficient_context': ClarificationLevel(
                min_confidence=0.00,
                max_confidence=0.29,
                strategy='context_gathering',
                message_template="Tôi cần thêm thông tin để hiểu rõ câu hỏi của bạn. Bạn có thể:"
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
            
            # Generate theo strategy - 5-LAYER SYSTEM
            if level_config.strategy == 'auto_route':
                return self._generate_auto_route_response(confidence, routing_result, level_config)
            
            elif level_config.strategy == 'confirm_with_best_questions':
                return self._generate_confirmation_clarification(confidence, routing_result, level_config)
            
            elif level_config.strategy == 'multiple_choices':
                return self._generate_multiple_choice_clarification(confidence, routing_result, level_config)
            
            elif level_config.strategy == 'category_suggestions':
                return self._generate_category_clarification(confidence, routing_result, level_config)
            
            elif level_config.strategy == 'context_gathering':
                return self._generate_context_gathering_clarification(confidence, routing_result, level_config)
            
            else:
                # Fallback
                return self._generate_fallback_clarification(confidence, routing_result)
                
        except Exception as e:
            logger.error(f"Error generating smart clarification: {e}")
            return self._generate_fallback_clarification(float(confidence) if confidence is not None else 0.0, routing_result)
    
    def _determine_clarification_level(self, confidence: float) -> str:
        """Xác định clarification level dựa trên confidence - 5-LAYER SYSTEM"""
        # Kiểm tra theo thứ tự từ cao xuống thấp để tránh overlap
        if confidence >= 0.80:
            return 'high_confidence'
        elif confidence >= 0.65 and confidence < 0.80:
            return 'medium_high_confidence'
        elif confidence >= 0.50 and confidence < 0.65:
            return 'medium_confidence'
        elif confidence >= 0.30 and confidence < 0.50:
            return 'low_confidence'
        elif confidence >= 0.00 and confidence < 0.30:
            return 'insufficient_context'
        else:
            # Edge case - default to insufficient context
            return 'insufficient_context'
    
    def _generate_auto_route_response(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> Dict[str, Any]:
        """
        HIGH CONFIDENCE (≥0.80): Auto route without clarification
        """
        return {
            "type": "auto_route",
            "confidence_level": "high_confidence",
            "confidence": float(confidence),
            "target_collection": routing_result.get('target_collection'),
            "message": level_config.message_template.format(confidence=confidence),
            "routing_context": routing_result,
            "strategy": level_config.strategy
        }
    
    def _generate_context_gathering_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> Dict[str, Any]:
        """
        INSUFFICIENT CONTEXT (0.00-0.29): Thu thập thêm context
        """
        message = level_config.message_template
        
        options = [
            {
                'id': 'provide_more_details',
                'title': "Mô tả chi tiết hơn về tình huống",
                'description': "Ví dụ: Bạn đang làm thủ tục gì? Cần giấy tờ gì?",
                'action': 'request_more_context',
                'context_type': 'situation_description'
            },
            {
                'id': 'select_document_type',
                'title': "Chọn loại giấy tờ bạn cần",
                'description': "Giấy khai sinh, chứng minh nhân dân, sổ hộ khẩu...",
                'action': 'request_document_type',
                'context_type': 'document_type'
            },
            {
                'id': 'select_urgency',
                'title': "Mức độ khẩn cấp",
                'description': "Cần gấp trong ngày, tuần này, hay không gấp?",
                'action': 'request_urgency',
                'context_type': 'urgency_level'
            },
            {
                'id': 'manual_description',
                'title': "Tôi muốn mô tả chi tiết",
                'description': "Hãy cho tôi nhập câu hỏi cụ thể hơn",
                'action': 'manual_input',
                'context_type': 'detailed_description'
            }
        ]
        
        return {
            "type": "context_gathering_needed",
            "confidence_level": "insufficient_context",
            "confidence": float(confidence),
            "target_collection": routing_result.get('target_collection'),  # 🔧 Fix: Add target_collection to top level
            "clarification": {
                "message": message,
                "options": options,
                "style": "context_gathering",
                "requires_user_input": True,
                "additional_help": "Bạn có thể mô tả cụ thể hơn về tình huống hoặc giấy tờ bạn cần làm"
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
        MEDIUM-HIGH CONFIDENCE (0.65-0.79): Xác nhận với câu hỏi gần nhất
        """
        # Fix data mapping - sử dụng structure mới từ router
        best_match = routing_result.get('best_match', {})
        source_procedure = best_match.get('question', 'thủ tục này')
        best_question = best_match.get('question', '')
        target_collection = routing_result.get('target_collection')
        
        # 🔧 DEBUG: Log target_collection value
        logger.info(f"🔍 DEBUG _generate_confirmation_clarification:")
        logger.info(f"  - routing_result keys: {list(routing_result.keys())}")
        logger.info(f"  - target_collection: {target_collection}")
        logger.info(f"  - best_match: {best_match}")
        
        # Nếu không có best_match, thử fallback
        if not source_procedure or source_procedure == 'thủ tục này':
            # Try to get collection display name
            collection_display = self.category_suggestions.get(target_collection or '', {})
            source_procedure = collection_display.get('title', target_collection or 'thủ tục này')
        
        message = level_config.message_template.format(
            procedure=source_procedure,
            confidence=confidence
        )
        
        # MEDIUM-HIGH: Hiển thị câu hỏi trong document để chọn
        # Lấy document từ best_match 
        target_document = best_match.get('document', '')
        
        options = [
            {
                'id': 'yes',
                'title': f"Đúng, tôi muốn hỏi về {source_procedure}",
                'description': f"Hiển thị câu hỏi về {source_procedure}",
                'action': 'show_document_questions', 
                'collection': target_collection,
                'document': target_document,
                'procedure': source_procedure
            },
            {
                'id': 'similar',
                'title': "Tương tự, nhưng không hoàn toàn chính xác",
                'description': f"Câu hỏi gốc: {best_question[:80]}..." if best_question else "Hãy giúp tôi tìm thủ tục phù hợp hơn",
                'action': 'show_document_questions',
                'collection': target_collection,
                'document': target_document,
                'procedure': source_procedure
            },
            {
                'id': 'no',
                'title': "Không, tôi muốn hỏi về thủ tục khác",
                'description': "Hãy cho tôi thêm lựa chọn khác",
                'action': 'show_categories',
                'collection': None
            }
        ]
        
        return {
            "type": "clarification_needed",
            "confidence_level": "medium_high_confidence",
            "confidence": float(confidence),
            "target_collection": routing_result.get('target_collection'),  # 🔧 Fix: Add target_collection to top level
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
            "target_collection": routing_result.get('target_collection'),  # 🔧 Fix: Add target_collection to top level
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
        LOW CONFIDENCE (0.30-0.49): Category-based suggestions
        """
        message = level_config.message_template
        
        options = []
        # Chỉ hiển thị 3 collections chính (bỏ qua duplicates)
        main_collections = {
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
        
        for i, (collection_id, category_info) in enumerate(main_collections.items(), 1):
            option = {
                'id': str(i),
                'title': category_info['title'],
                'description': category_info['description'],
                'examples': category_info['examples'],
                'action': 'proceed_with_collection',
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
            "target_collection": routing_result.get('target_collection'),  # 🔧 Fix: Add target_collection to top level
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
            "target_collection": routing_result.get('target_collection'),  # 🔧 Fix: Add target_collection to top level
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
