#!/usr/bin/env python3
"""
Clarification Config for LegalRAG
=================================

Config loader for clarification service

Author: LegalRAG Team
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "clarification_levels": {
        "high_confidence": {
            "min_confidence": 0.80,
            "max_confidence": 1.00,
            "strategy": "auto_route",
            "message_template": "Routing automatically with high confidence (confidence: {confidence:.1%})"
        },
        "medium_high_confidence": {
            "min_confidence": 0.65,
            "max_confidence": 0.79,
            "strategy": "confirm_with_best_questions", 
            "message_template": "Tôi nghĩ bạn muốn hỏi về '{procedure}' (độ tin cậy: {confidence:.1%}). Đúng không?"
        },
        "medium_confidence": {
            "min_confidence": 0.50,
            "max_confidence": 0.64,
            "strategy": "multiple_choices",
            "message_template": "Câu hỏi của bạn có thể liên quan đến các thủ tục sau. Bạn muốn hỏi về:"
        },
        "low_confidence": {
            "min_confidence": 0.30,
            "max_confidence": 0.49,
            "strategy": "category_suggestions",
            "message_template": "Tôi chưa hiểu rõ ý bạn. Bạn có thể cho biết bạn quan tâm đến lĩnh vực nào?"
        },
        "insufficient_context": {
            "min_confidence": 0.00,
            "max_confidence": 0.29,
            "strategy": "context_gathering",
            "message_template": "Tôi cần thêm thông tin để hiểu rõ câu hỏi của bạn. Bạn có thể:"
        }
    },
    "context_gathering_options": [
        {
            "id": "provide_more_details",
            "title": "Mô tả chi tiết hơn về tình huống",
            "description": "Ví dụ: Bạn đang làm thủ tục gì? Cần giấy tờ gì?",
            "action": "request_more_context",
            "context_type": "situation_description"
        },
        {
            "id": "select_document_type",
            "title": "Chọn loại giấy tờ bạn cần",
            "description": "Giấy khai sinh, chứng minh nhân dân, sổ hộ khẩu...",
            "action": "request_document_type",
            "context_type": "document_type"
        },
        {
            "id": "select_urgency",
            "title": "Mức độ khẩn cấp",
            "description": "Cần gấp trong ngày, tuần này, hay không gấp?",
            "action": "request_urgency",
            "context_type": "urgency_level"
        },
        {
            "id": "manual_description",
            "title": "Tôi muốn mô tả chi tiết",
            "description": "Hãy cho tôi nhập câu hỏi cụ thể hơn",
            "action": "manual_input",
            "context_type": "detailed_description"
        }
    ],
    "fallback_categories": [
        {
            "id": "1",
            "title": "Hộ tịch",
            "description": "Thủ tục về khai sinh, kết hôn, khai tử",
            "action": "proceed_with_collection",
            "collection": "quy_trinh_cap_ho_tich_cap_xa"
        },
        {
            "id": "2", 
            "title": "Chứng thực",
            "description": "Thủ tục chứng thực giấy tờ, hợp đồng",
            "action": "proceed_with_collection",
            "collection": "quy_trinh_chung_thuc"
        }
    ],
    "confirmation_options": {
        "yes": {
            "id": "yes",
            "title_template": "Đúng, tôi muốn hỏi về {procedure}",
            "description_template": "Hiển thị câu hỏi về {procedure}",
            "action": "show_document_questions"
        },
        "similar": {
            "id": "similar",
            "title": "Tương tự, nhưng không hoàn toàn chính xác",
            "description_template": "Câu hỏi gốc: {question_preview}...",
            "fallback_description": "Hãy giúp tôi tìm thủ tục phù hợp hơn",
            "action": "show_document_questions"
        },
        "no": {
            "id": "no",
            "title": "Không, tôi muốn hỏi về thủ tục khác",
            "description": "Hãy cho tôi thêm lựa chọn khác",
            "action": "show_categories"
        }
    },
    "manual_input_option": {
        "id": "manual",
        "title": "Tôi muốn mô tả rõ hơn",
        "description": "Để tôi diễn đạt lại câu hỏi một cách chi tiết hơn",
        "action": "manual_input"
    },
    "retry_option": {
        "id": "retry",
        "title": "Hãy diễn đạt lại câu hỏi",
        "description": "Tôi sẽ cố gắng hiểu rõ hơn", 
        "action": "manual_input"
    }
}

class ClarificationConfig:
    """
    Load và quản lý cấu hình cho Clarification Service
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Khởi tạo với file config (hoặc default nếu không có)
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load config từ file json hoặc dùng default
        """
        if not self.config_path or not os.path.exists(self.config_path):
            logger.info("🔧 Using default clarification config")
            return DEFAULT_CONFIG
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"✅ Loaded clarification config from {self.config_path}")
            return config
        except Exception as e:
            logger.warning(f"⚠️ Error loading config, using defaults: {str(e)}")
            return DEFAULT_CONFIG
    
    def get_clarification_levels(self) -> Dict[str, Dict[str, Any]]:
        """
        Lấy cấu hình các tầng clarification
        """
        return self.config.get("clarification_levels", DEFAULT_CONFIG["clarification_levels"])
    
    def get_context_gathering_options(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách option khi thu thập context
        """
        return self.config.get("context_gathering_options", DEFAULT_CONFIG["context_gathering_options"])
    
    def get_fallback_categories(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách category khi không có dữ liệu từ router
        """
        return self.config.get("fallback_categories", DEFAULT_CONFIG["fallback_categories"])
    
    def get_confirmation_options(self) -> Dict[str, Dict[str, Any]]:
        """
        Lấy các option xác nhận
        """
        return self.config.get("confirmation_options", DEFAULT_CONFIG["confirmation_options"])
    
    def get_manual_input_option(self) -> Dict[str, Any]:
        """
        Lấy option nhập thủ công
        """
        return self.config.get("manual_input_option", DEFAULT_CONFIG["manual_input_option"])
    
    def get_retry_option(self) -> Dict[str, Any]:
        """
        Lấy option retry
        """
        return self.config.get("retry_option", DEFAULT_CONFIG["retry_option"])