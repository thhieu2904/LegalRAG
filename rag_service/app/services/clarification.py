#!/usr/bin/env python3
"""
Smart Clarification Service for LegalRAG V2
===========================================

5-Layer Clarification System for 13 Collections:
- High confidence (≥0.80): Auto route - no clarification needed
- Medium-High confidence (0.65-0.79): Confirm with best questions
- Medium confidence (0.50-0.64): Multiple choice from top matches
- Low confidence (0.30-0.49): Category-based suggestions
- Insufficient context (<0.30): Context gathering

Author: LegalRAG Team
"""

from typing import Dict, List, Any, Optional, Tuple, Union, cast
import logging
import os
import json
from dataclasses import dataclass

from app.utils.collection_utils import CollectionManager
from app.utils.clarification_config import ClarificationConfig
from app.models.schemas import (
    ClarificationOption, StandardClarificationResponse,
    ClarificationActionResponse, ProceedWithQuestionResponse, 
    CollectionOverviewResponse, ManualInputResponse, ClarificationErrorResponse
)

logger = logging.getLogger(__name__)

@dataclass
class ClarificationLevel:
    """Define clarification levels"""
    min_confidence: float
    max_confidence: float
    strategy: str
    message_template: str

class ClarificationService:
    """
    🎯 ENHANCED CLARIFICATION SERVICE with Embedding Intelligence
    - 5-layer confidence system cho nhiều collections
    - Similarity ranking for better question suggestions  
    - Scale-ready, clean architecture
    - Dựa trên schema chuẩn hóa và cấu hình ngoài
    - Tự động đọc collections từ data/storage
    """
    
    def __init__(self, embedding_model=None, config_path: Optional[str] = None, storage_path: Optional[str] = None):
        """
        Khởi tạo ClarificationService với các tùy chọn cấu hình
        
        Args:
            embedding_model: Model để embedding câu hỏi và tính similarity
            config_path: Đường dẫn đến file cấu hình (json), nếu không có sẽ dùng default
            storage_path: Đường dẫn đến thư mục storage, mặc định là "data/storage"
        """
        # Store embedding model for similarity calculations
        self.embedding_model = embedding_model
        
        # Load config từ file cấu hình hoặc default
        self.config = ClarificationConfig(config_path)
        
        # Khởi tạo Collection Manager để lấy thông tin collections
        self.collection_manager = CollectionManager(storage_path if storage_path else "data/storage/collections")
        
        # Try to import sklearn for similarity calculations
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            self.similarity_available = True
            self.cosine_similarity = cosine_similarity
            self.np = np
        except ImportError:
            self.similarity_available = False
            logger.warning("⚠️  sklearn not available - using fallback ranking")
        
        # 5-Layer clarification system - load từ config
        self.clarification_levels = {}
        # Load từ config ngoài
        levels_config = self.config.get_clarification_levels()
        for level_name, level_data in levels_config.items():
            self.clarification_levels[level_name] = ClarificationLevel(
                min_confidence=level_data.get("min_confidence", 0.0),
                max_confidence=level_data.get("max_confidence", 1.0),
                strategy=level_data.get("strategy", "fallback"),
                message_template=level_data.get("message_template", "No message template provided")
            )
        
        # 🎯 NO HARDCORE MAPPINGS - Use router results directly!

        # Load collections từ storage
        self.collections = self.collection_manager.get_all_collections()
        logger.info(f"✅ Loaded {len(self.collections)} collections dynamically from storage")
    
    def generate_clarification(
        self, 
        confidence: float,
        routing_result: Dict[str, Any],
        query: str,
        session_id: Optional[str] = None
    ) -> Union[StandardClarificationResponse, Dict[str, Any]]:
        """
        Tạo clarification thông minh dựa trên confidence level
        Trả về StandardClarificationResponse hoặc dict tương thích
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
                result = self._generate_auto_route_response(confidence, routing_result, level_config)
            elif level_config.strategy == 'confirm_with_best_questions':
                result = self._generate_confirmation_clarification(confidence, routing_result, level_config)
            elif level_config.strategy == 'multiple_choices':
                result = self._generate_multiple_choice_clarification(confidence, routing_result, level_config)
            elif level_config.strategy == 'category_suggestions':
                result = self._generate_category_clarification(confidence, routing_result, level_config)
            elif level_config.strategy == 'context_gathering':
                result = self._generate_context_gathering_clarification(confidence, routing_result, level_config)
            else:
                # Fallback
                result = self._generate_fallback_clarification(confidence, routing_result)
            
            # Nếu là StandardClarificationResponse, set session_id
            if isinstance(result, StandardClarificationResponse) and session_id:
                result.session_id = session_id
            # Nếu là dict, set session_id theo cách cũ
            elif isinstance(result, dict) and session_id:
                result['session_id'] = session_id
            
            return result
                
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
    ) -> StandardClarificationResponse:
        """
        HIGH CONFIDENCE (≥0.80): Auto route without clarification
        Sử dụng schema chuẩn hóa
        """
        target_collection = routing_result.get('target_collection')
        message = level_config.message_template.format(confidence=confidence)
        
        # Lấy document và procedure từ routing_result nếu có
        best_match = routing_result.get('best_match', {})
        document = best_match.get('document', None)
        procedure = best_match.get('question', None)
        
        # Sử dụng StandardClarificationResponse cho output chuẩn hóa
        return StandardClarificationResponse(
            type="auto_route",
            confidence_level="high_confidence",
            confidence=float(confidence),
            target_collection=target_collection,
            document=document,
            procedure=procedure,
            message=message,
            options=[],  # Không có options vì auto route
            style="auto_route",
            manual_input_placeholder=None,
            routing_context=routing_result,
            strategy=level_config.strategy,
            session_id=None,  # Session ID sẽ được set ở hàm generate_clarification
            additional_help=None,
            requires_user_input=False,
            show_manual_input=False
        )
    
    def _generate_context_gathering_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> StandardClarificationResponse:
        """
        INSUFFICIENT CONTEXT (0.00-0.29): Thu thập thêm context
        """
        message = level_config.message_template
        target_collection = routing_result.get('target_collection')
        
        # Lấy options từ config thay vì hardcode
        option_configs = self.config.get_context_gathering_options()
        options = []
        
        # Chuyển đổi từ config sang ClarificationOption
        clarification_options = []
        for opt_config in option_configs:
            clarification_options.append(ClarificationOption(
                id=opt_config.get("id", ""),
                title=opt_config.get("title", ""),
                description=opt_config.get("description"),
                action=opt_config.get("action", ""),
                collection=None,
                document=None,
                procedure=None,
                question_text=None,
                confidence_percent=None,
                source_file=None,
                context_type=opt_config.get("context_type"),
                category=None
            ))
        
        # Sử dụng schema chuẩn hóa
        return StandardClarificationResponse(
            type="context_gathering_needed",
            confidence_level="insufficient_context",
            confidence=float(confidence),
            message=message,
            target_collection=target_collection,
            document=None,
            procedure=None,
            options=clarification_options,
            requires_user_input=True,
            show_manual_input=True,
            manual_input_placeholder="Mô tả chi tiết tình huống của bạn...",
            style="context_gathering",
            routing_context=routing_result,
            strategy=level_config.strategy,
            session_id=None,
            additional_help="Bạn có thể cung cấp thêm thông tin về tình huống của mình để chúng tôi hỗ trợ tốt hơn."
        )

    def _generate_confirmation_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> StandardClarificationResponse:
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
            # 🔧 FIX: Simple fallback without hardcore mapping
            source_procedure = target_collection or 'thủ tục này'
        
        message = level_config.message_template.format(
            procedure=source_procedure,
            confidence=confidence
        )
        
        # MEDIUM-HIGH: Hiển thị câu hỏi trong document để chọn
        # Lấy document từ best_match 
        target_document = best_match.get('document', '')
        
        # Tạo danh sách options sử dụng schema mới
        clarification_options = []
        
        # Option 1: Xác nhận lựa chọn
        clarification_options.append(ClarificationOption(
            id='yes',
            title=f"Đúng, tôi muốn hỏi về {source_procedure}",
            description=f"Hiển thị câu hỏi về {source_procedure}",
            action='show_document_questions',
            collection=target_collection,
            document=target_document,
            procedure=source_procedure,
            confidence_percent=round(confidence * 100, 1),
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Option 2: Tương tự nhưng không chính xác
        clarification_options.append(ClarificationOption(
            id='similar',
            title="Tương tự, nhưng không hoàn toàn chính xác",
            description=f"Câu hỏi gốc: {best_question[:80]}..." if best_question else "Hãy giúp tôi tìm thủ tục phù hợp hơn",
            action='show_document_questions',
            collection=target_collection,
            document=target_document,
            procedure=source_procedure,
            confidence_percent=round(confidence * 100, 1),
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Option 3: Từ chối và chọn thủ tục khác
        clarification_options.append(ClarificationOption(
            id='no',
            title="Không, tôi muốn hỏi về thủ tục khác",
            description="Hãy cho tôi thêm lựa chọn khác",
            action='show_categories',
            collection=None,
            document=None,
            procedure=None,
            confidence_percent=0,
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Sử dụng schema chuẩn hóa
        return StandardClarificationResponse(
            type="clarification_needed",
            confidence_level="medium_high_confidence",
            confidence=float(confidence),
            message=message,
            target_collection=target_collection,
            document=target_document,
            procedure=source_procedure,
            options=clarification_options,
            requires_user_input=False,
            show_manual_input=False,
            manual_input_placeholder=None,
            style="confirmation",
            routing_context=routing_result,
            strategy=level_config.strategy,
            session_id=None,
            additional_help=None
        )
    
    def _generate_multiple_choice_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> StandardClarificationResponse:
        """
        MEDIUM CONFIDENCE (0.5-0.69): Multiple choices từ top matches
        """
        # Lấy top matches từ routing result và sort theo confidence
        all_scores = routing_result.get('all_scores', {})
        target_collection = routing_result.get('target_collection')
        
        # 🔧 DEBUG: Log để xem all_scores structure
        logger.info(f"🔍 DEBUG _generate_multiple_choice_clarification:")
        logger.info(f"  - all_scores keys: {list(all_scores.keys()) if all_scores else 'EMPTY'}")
        logger.info(f"  - all_scores values: {list(all_scores.values()) if all_scores else 'EMPTY'}")
        
        # 🎯 SIMPLE SORT: Chỉ cần sort theo score, không hardcode
        top_matches = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:5]  # Top 5 thay vì 3
        logger.info(f"  - top_matches: {top_matches}")
        
        message = level_config.message_template
        
        # Tạo danh sách options sử dụng schema mới
        clarification_options = []
        
        # Thêm các lựa chọn từ top matches
        for i, (collection, score) in enumerate(top_matches, 1):
            score_float = float(score) if score is not None else 0.0
            
            # 🎯 USE ROUTER DATA: Simple title from collection name
            collection_title = collection.replace('quy_trinh_', '').replace('_', ' ').title()
            collection_description = f"Thủ tục trong lĩnh vực {collection_title.lower()}"
            
            clarification_options.append(ClarificationOption(
                id=str(i),
                title=collection_title,
                description=collection_description,
                action='proceed_with_collection',
                collection=collection,
                document=None,
                procedure=None,
                confidence_percent=round(score_float * 100, 1),
                question_text=None,
                source_file=None,
                context_type=None,
                category=None
            ))
        
        # Add "none of the above" option
        clarification_options.append(ClarificationOption(
            id='other',
            title="Không có thủ tục nào phù hợp",
            description="Tôi muốn hỏi về thủ tục khác",
            action='manual_input',
            collection=None,
            document=None,
            procedure=None,
            confidence_percent=0,
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Sử dụng schema chuẩn hóa
        return StandardClarificationResponse(
            type="clarification_needed",
            confidence_level="medium_confidence",
            confidence=float(confidence),
            message=message,
            target_collection=target_collection,
            document=None,
            procedure=None,
            options=clarification_options,
            requires_user_input=False,
            show_manual_input=False,
            manual_input_placeholder=None,
            style="multiple_choice",
            routing_context=routing_result,
            strategy=level_config.strategy,
            session_id=None,
            additional_help=None
        )
    
    def _generate_category_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any], 
        level_config: ClarificationLevel
    ) -> StandardClarificationResponse:
        """
        LOW CONFIDENCE (0.30-0.49): Category-based suggestions
        🎯 USE ROUTER DATA: Get collections from router instead of hardcode
        """
        message = level_config.message_template
        target_collection = routing_result.get('target_collection')
        
        # 🎯 GET COLLECTIONS FROM ROUTER: Use router's all_scores if available
        all_scores = routing_result.get('all_scores', {})
        
        # Tạo danh sách options sử dụng schema mới
        clarification_options = []
        
        if all_scores:
            # Use top collections from router
            top_collections = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (collection, score) in enumerate(top_collections, 1):
                collection_title = collection.replace('quy_trinh_', '').replace('_', ' ').title()
                score_float = float(score) if score is not None else 0.0
                
                clarification_options.append(ClarificationOption(
                    id=str(i),
                    title=collection_title,
                    description=f"Thủ tục trong lĩnh vực {collection_title.lower()}",
                    action='proceed_with_collection',
                    collection=collection,
                    document=None,
                    procedure=None,
                    confidence_percent=round(score_float * 100, 1),
                    question_text=None,
                    source_file=None,
                    context_type=None,
                    category=collection
                ))
        else:
            # Fallback: basic options
            clarification_options.append(ClarificationOption(
                id='1',
                title='Hộ tịch',
                description='Thủ tục về khai sinh, kết hôn, khai tử',
                action='proceed_with_collection',
                collection='quy_trinh_cap_ho_tich_cap_xa',
                document=None,
                procedure=None,
                confidence_percent=0,
                question_text=None,
                source_file=None,
                context_type=None,
                category='ho_tich'
            ))
            
            clarification_options.append(ClarificationOption(
                id='2',
                title='Chứng thực',
                description='Thủ tục chứng thực giấy tờ, hợp đồng',
                action='proceed_with_collection',
                collection='quy_trinh_chung_thuc',
                document=None,
                procedure=None,
                confidence_percent=0,
                question_text=None,
                source_file=None,
                context_type=None,
                category='chung_thuc'
            ))
        
        # Add manual input option
        clarification_options.append(ClarificationOption(
            id='manual',
            title="Tôi muốn mô tả rõ hơn",
            description="Để tôi diễn đạt lại câu hỏi một cách chi tiết hơn",
            action='manual_input',
            collection='',  # Empty string thay vì None
            document=None,
            procedure=None,
            confidence_percent=0,
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Sử dụng schema chuẩn hóa
        return StandardClarificationResponse(
            type="clarification_needed",
            confidence_level="low_confidence",
            confidence=float(confidence),
            message=message,
            target_collection=target_collection,
            document=None,
            procedure=None,
            options=clarification_options,
            requires_user_input=True,
            show_manual_input=True,
            manual_input_placeholder="Mô tả chi tiết tình huống của bạn...",
            style="category_based",
            routing_context=routing_result,
            strategy=level_config.strategy,
            session_id=None,
            additional_help="Bạn có thể mô tả cụ thể hơn về tình huống hoặc giấy tờ bạn cần làm"
        )
    
    def _generate_fallback_clarification(
        self, 
        confidence: float, 
        routing_result: Dict[str, Any]
    ) -> StandardClarificationResponse:
        """Fallback clarification khi có lỗi"""
        message = "Xin lỗi, tôi cần thêm thông tin để hiểu rõ câu hỏi của bạn."
        target_collection = routing_result.get('target_collection')
        
        # Tạo options sử dụng schema chuẩn hóa
        clarification_options = []
        
        clarification_options.append(ClarificationOption(
            id='retry',
            title="Hãy diễn đạt lại câu hỏi",
            description="Tôi sẽ cố gắng hiểu rõ hơn",
            action='manual_input',
            collection=None,
            document=None,
            procedure=None,
            confidence_percent=0,
            question_text=None,
            source_file=None,
            context_type=None,
            category=None
        ))
        
        # Sử dụng schema chuẩn hóa
        return StandardClarificationResponse(
            type="clarification_needed",
            confidence_level="fallback",
            confidence=float(confidence),
            message=message,
            target_collection=target_collection,
            document=None,
            procedure=None,
            options=clarification_options,
            requires_user_input=True,
            show_manual_input=True,
            manual_input_placeholder="Vui lòng mô tả chi tiết hơn về câu hỏi của bạn...",
            style="fallback",
            routing_context=routing_result,
            strategy="fallback",
            session_id=None,
            additional_help="Bạn có thể cung cấp thêm thông tin hoặc diễn đạt lại câu hỏi một cách chi tiết hơn."
        )
    
    def handle_user_selection(
        self, 
        selected_option: Dict[str, Any], 
        session_id: str,
        smart_router = None
    ) -> Union[Dict[str, Any], StandardClarificationResponse]:
        """
        🎯 CENTRALIZED USER SELECTION HANDLING
        Handle all user selections for clarification flow
        """
        import time
        start_time = time.time()
        
        try:
            action = selected_option.get('action')
            collection = selected_option.get('collection')
            
            if action == 'show_document_questions':
                result = self._handle_show_document_questions(selected_option, session_id, smart_router)
            elif action == 'proceed_with_question':
                result = self._handle_proceed_with_question(selected_option, session_id)
            elif action == 'proceed_with_collection':
                result = self._handle_proceed_with_collection(selected_option, session_id, smart_router)
            elif action == 'show_categories':
                result = self._handle_show_categories(selected_option, session_id)
            elif action == 'manual_input':
                result = self._handle_manual_input(selected_option, session_id)
            else:
                result = self._handle_unknown_action(selected_option, session_id)
            
            # Add processing_time to result
            if isinstance(result, dict):
                result["processing_time"] = time.time() - start_time
                
            return result
                
        except Exception as e:
            logger.error(f"❌ Error handling user selection: {e}")
            error_result = self._generate_error_response(str(e), session_id)
            if isinstance(error_result, dict):
                error_result["processing_time"] = time.time() - start_time
            return error_result
    
    def _handle_show_document_questions(
        self, 
        selected_option: Dict[str, Any], 
        session_id: str,
        smart_router = None
    ) -> Dict[str, Any]:
        """Handle show_document_questions action - MOVED FROM RAG ENGINE"""
        try:
            collection = selected_option.get('collection')
            document = selected_option.get('document', '')
            procedure = selected_option.get('procedure', '')
            
            logger.info(f"🎯 ClarificationService: Showing questions for '{procedure}' in document '{document}'")
            
            if not smart_router:
                return self._generate_error_response("Smart router not available", session_id)
            
            # Get questions from specific document
            if document:
                document_filename = f"{document}"
                matching_questions = smart_router.get_questions_from_specific_document(collection, document_filename)
                logger.info(f"🚀 Retrieved {len(matching_questions)} questions from document {document_filename}")
            else:
                # Fallback: Get procedure-related questions
                matching_questions = smart_router.get_procedure_questions_limited(
                    collection_name=collection,
                    procedure=procedure,
                    limit=20
                )
                logger.info(f"🚀 Retrieved {len(matching_questions)} procedure-related questions")
            
            if not matching_questions:
                logger.warning(f"⚠️ No questions found for procedure '{procedure}' in document '{document}'")
                # Fallback to collection questions
                collection_questions = smart_router.get_example_questions_for_collection(collection)
                matching_questions = collection_questions[:10]
                logger.info(f"🔄 Fallback: Loaded {len(matching_questions)} questions")
            
            # Create standardized question options
            options = []
            for i, q in enumerate(matching_questions[:8]):  # Top 8 questions
                question_text = q.get('text', str(q)) if isinstance(q, dict) else str(q)
                options.append({
                    "id": str(i + 1),
                    "title": question_text,
                    "description": f"Câu hỏi về {procedure}",
                    "action": "proceed_with_question",
                    "collection": collection,
                    "document": document,
                    "procedure": procedure,
                    "question_text": question_text,
                    "source_file": q.get('source', '') if isinstance(q, dict) else '',
                    "category": q.get('category', 'general') if isinstance(q, dict) else 'general'
                })
            
            # Add manual input option
            options.append({
                "id": str(len(options) + 1),
                "title": "Câu hỏi khác...",
                "description": f"Tôi muốn hỏi về vấn đề khác trong {procedure}",
                "action": "manual_input",
                "collection": collection,
                "document": document,
                "procedure": procedure
            })
            
            # Return standardized response
            return {
                "type": "clarification_needed",
                "confidence": None,  # No confidence at this stage
                "answer": f"Đây là các câu hỏi về '{procedure}'. Hãy chọn câu hỏi phù hợp:",
                "clarification": {
                    "message": f"Đây là các câu hỏi về '{procedure}'. Hãy chọn câu hỏi phù hợp:",
                    "options": options,
                    "show_manual_input": True,
                    "manual_input_placeholder": f"Hoặc nhập câu hỏi cụ thể về {procedure}...",
                    "context": "document_questions",
                    "style": "document_questions",
                    "metadata": {
                        "collection": collection,
                        "document": document,
                        "procedure": procedure,
                        "stage": "document_questions"
                    }
                },
                "session_id": session_id,
                "routing_info": None,  # No routing info at this stage
                "target_collection": collection
            }
            
        except Exception as e:
            logger.error(f"❌ Error showing document questions: {e}")
            return self._generate_error_response(str(e), session_id)
    
    def _handle_proceed_with_question(self, selected_option: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle proceed_with_question action - STANDARDIZED RESPONSE"""
        return {
            "type": "proceed_with_question",
            "final_query": selected_option.get('question_text', ''),
            "collection": selected_option.get('collection'),
            "document": selected_option.get('document'),
            "procedure": selected_option.get('procedure'),
            "session_id": session_id,
            "message": "Proceeding with selected question for RAG processing"
        }
    
    def _handle_proceed_with_collection(self, selected_option: Dict[str, Any], session_id: str, smart_router = None) -> Dict[str, Any]:
        """Handle proceed_with_collection action"""
        collection = selected_option.get('collection')
        
        # Get collection overview or top documents
        if smart_router:
            collection_questions = smart_router.get_example_questions_for_collection(collection)[:10]
        else:
            collection_questions = []
        
        return {
            "type": "collection_overview", 
            "collection": collection,
            "questions": collection_questions,
            "session_id": session_id,
            "message": f"Showing overview for collection: {collection}"
        }
    
    def _handle_show_categories(self, selected_option: Dict[str, Any], session_id: str) -> StandardClarificationResponse:
        """Handle show_categories action"""
        # Tạo một đối tượng routing_result trống và thêm session_id
        routing_result = {"session_id": session_id}
        
        response = self._generate_category_clarification(
            confidence=0.0,
            routing_result=routing_result,
            level_config=self.clarification_levels['low_confidence']
        )
        return response
    
    def _handle_manual_input(self, selected_option: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle manual_input action"""
        return {
            "type": "manual_input_request",
            "message": "Please provide your specific question",
            "collection": selected_option.get('collection'),
            "document": selected_option.get('document'),
            "procedure": selected_option.get('procedure'),
            "session_id": session_id
        }
    
    def _handle_unknown_action(self, selected_option: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle unknown actions"""
        return self._generate_error_response(f"Unknown action: {selected_option.get('action')}", session_id)
    
    def _generate_error_response(self, error_message: str, session_id: str) -> Dict[str, Any]:
        """Generate standardized error response"""
        return {
            "type": "error",
            "error": error_message,
            "session_id": session_id,
            "message": "An error occurred during clarification processing"
        }
    
    def get_related_procedures(self, collection: str, procedure: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Lấy các thủ tục liên quan trong cùng collection
        (Có thể integrate với smart_router để lấy similar procedures)
        """
        # Placeholder - sẽ integrate với smart_router
        return []
    
    # 🔥 NEW: EMBEDDING SIMILARITY METHODS
    def get_similarity_ranked_questions(
        self, 
        query: str, 
        collection: str, 
        document: Optional[str] = None,
        limit: int = 5,
        smart_router = None
    ) -> List[Dict[str, Any]]:
        """
        🔥 ENHANCED: Get questions ranked by embedding similarity
        """
        try:
            if not self.similarity_available or not self.embedding_model:
                # Fallback to simple retrieval if no embedding model
                return self._get_fallback_questions(collection, document, limit, smart_router)
            
            # Get questions from router
            if document and smart_router:
                questions = smart_router.get_questions_from_specific_document(collection, document)
            elif smart_router:
                questions = smart_router.get_example_questions_for_collection(collection)
            else:
                return []
            
            if not questions:
                return []
            
            # 🔧 EMBEDDING SIMILARITY CALCULATION
            query_embedding = self.embedding_model.encode([query])
            
            # Extract question texts and compute embeddings
            question_texts = []
            question_data = []
            
            for q in questions:
                if isinstance(q, dict):
                    text = q.get('text', '')
                    question_texts.append(text)
                    question_data.append(q)
                else:
                    text = str(q)
                    question_texts.append(text)
                    question_data.append({'text': text})
            
            if not question_texts:
                return []
            
            # Compute similarities
            question_embeddings = self.embedding_model.encode(question_texts)
            similarities = self.cosine_similarity(query_embedding, question_embeddings)[0]
            
            # Combine with similarity scores and sort
            ranked_questions = []
            for i, (question, similarity) in enumerate(zip(question_data, similarities)):
                question_copy = question.copy() if isinstance(question, dict) else {'text': str(question)}
                similarity_score = float(similarity)
                # Lưu trữ score dưới dạng string để tránh lỗi typing
                question_copy['similarity_score'] = str(similarity_score)
                question_copy['similarity_percent'] = str(round(similarity_score * 100, 1))
                ranked_questions.append(question_copy)
            
            # Sort by similarity descending - chuyển về float khi so sánh
            ranked_questions.sort(key=lambda x: float(x['similarity_score']), reverse=True)
            
            logger.info(f"🔥 Similarity ranking: {len(ranked_questions)} questions ranked for query")
            
            return ranked_questions[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error in similarity ranking: {e}")
            return self._get_fallback_questions(collection, document, limit, smart_router)
    
    def _get_fallback_questions(
        self, 
        collection: str, 
        document: Optional[str] = None,
        limit: int = 5,
        smart_router = None
    ) -> List[Dict[str, Any]]:
        """Fallback question retrieval without similarity"""
        try:
            if document and smart_router:
                questions = smart_router.get_questions_from_specific_document(collection, document)
            elif smart_router:
                questions = smart_router.get_example_questions_for_collection(collection)
            else:
                return []
            
            # Convert to standard format
            standardized = []
            for q in questions[:limit]:
                if isinstance(q, dict):
                    standardized.append(q)
                else:
                    standardized.append({'text': str(q), 'similarity_percent': 0})
            
            return standardized
            
        except Exception as e:
            logger.error(f"❌ Error in fallback questions: {e}")
            return []
    
    def calculate_query_collection_relevance(self, query: str, collection: str) -> float:
        """
        🔧 ENHANCED: Calculate relevance between query and collection
        Simple keyword-based approach for now, can be enhanced with embeddings
        """
        try:
            # Basic keyword matching
            query_lower = query.lower()
            collection_lower = collection.lower().replace('quy_trinh_', '').replace('_', ' ')
            
            # Count keyword matches
            collection_words = collection_lower.split()
            matches = sum(1 for word in collection_words if word in query_lower)
            
            # Calculate relevance
            if len(collection_words) == 0:
                return 0.0
            
            relevance = matches / len(collection_words)
            
            # Bonus for exact phrase match
            if collection_lower in query_lower:
                relevance += 0.3
            
            return min(1.0, relevance)
            
        except Exception as e:
            logger.error(f"❌ Error calculating relevance: {e}")
            return 0.0
