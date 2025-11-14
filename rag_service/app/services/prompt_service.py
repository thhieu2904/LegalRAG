"""
🎯 CENTRALIZED PROMPT SERVICE
Quản lý tất cả prompts trong hệ thống với kiến trúc modular và extensible

Design Principles:
1. Single Responsibility: Chỉ quản lý prompts
2. Strategy Pattern: Different prompt strategies cho different contexts
3. Template Pattern: Reusable prompt templates
4. Version Control: Prompt versioning support
5. A/B Testing Ready: Easy prompt experimentation
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class PromptType(Enum):
    """Types of prompts in the system"""
    LEGAL_RAG = "legal_rag"
    ANTI_HALLUCINATION = "anti_hallucination"
    CLARIFICATION = "clarification"
    FALLBACK = "fallback"

class ContextType(Enum):
    """Context types for different scenarios"""
    HIGH_CONFIDENCE = "high_confidence"
    MEDIUM_CONFIDENCE = "medium_confidence"
    LOW_CONFIDENCE = "low_confidence"
    MANUAL_INPUT = "manual_input"
    FOLLOW_UP = "follow_up"

@dataclass
class PromptTemplate:
    """Template for prompt construction"""
    name: str
    type: PromptType
    context: ContextType
    template: str
    version: str = "1.0"
    description: str = ""
    
class BasePromptStrategy(ABC):
    """Base class for prompt strategies"""
    
    @abstractmethod
    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get prompt based on context"""
        pass
    
    @abstractmethod
    def get_template(self) -> PromptTemplate:
        """Get prompt template"""
        pass

class LegalRAGPromptStrategy(BasePromptStrategy):
    """Strategy for Legal RAG prompts"""
    
    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get legal RAG prompt with anti-hallucination features"""
        
        base_prompt = """Bạn là trợ lý AI chuyên về pháp luật Việt Nam.

QUY TẮC:
1. CHỈ trả lời dựa trên thông tin có trong tài liệu được cung cấp
2. KHÔNG tự sáng tạo thông tin không có trong tài liệu  
3. Trả lời ngắn gọn 7-10 câu, tự nhiên như nói chuyện
4. Nếu không có thông tin: "Tài liệu không đề cập vấn đề này"
5. KHÔNG sử dụng emoji, ký tự đặc biệt
6. KHÔNG đặt câu hỏi ngược lại cho người dùng
7. KHÔNG tự suy luận thông tin ngoài tài liệu

HƯỚNG DẪN TÌM THÔNG TIN:
- Phí/lệ phí: Tìm fee_vnd, fee_text trong metadata
- Thời gian: Tìm processing_time_text, processing_time_days  
- Nơi làm: Tìm executing_agency, jurisdiction
- Biểu mẫu: Tìm has_form, form_name, form_url

CHỐNG HALLUCINATION:
- KHÔNG sử dụng thông tin từ câu hỏi trước nếu không liên quan
- KHÔNG suy luận ngoài thông tin có sẵn
- KHÔNG thêm thông tin không có trong tài liệu
- KHÔNG tạo ra câu hỏi gợi ý cho người dùng
- Nếu không chắc chắn: "Tài liệu không đề cập vấn đề này\""""
        
        # Context-specific modifications
        confidence_level = context.get('confidence_level', 'medium')
        
        if confidence_level == 'high':
            base_prompt += "\n\n🎯 HIGH CONFIDENCE: Bạn có thể trả lời trực tiếp với thông tin rõ ràng."
        elif confidence_level == 'low':
            base_prompt += "\n\n⚠️ LOW CONFIDENCE: Hãy đặc biệt cẩn trọng về độ chính xác."
            
        return base_prompt
    
    def get_template(self) -> PromptTemplate:
        return PromptTemplate(
            name="legal_rag_main",
            type=PromptType.LEGAL_RAG,
            context=ContextType.HIGH_CONFIDENCE,
            template=self.get_prompt({}),
            version="2.0",
            description="Main legal RAG prompt with anti-hallucination features"
        )

class FallbackPromptStrategy(BasePromptStrategy):
    """Strategy for fallback prompts"""
    
    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Get simple fallback prompt"""
        return """Bạn là trợ lý AI chuyên về pháp luật Việt Nam.

🚨 QUY TẮC CƠ BẢN:
1. CHỈ trả lời dựa trên thông tin CÓ TRONG tài liệu được cung cấp
2. KHÔNG tự sáng tạo thông tin không có trong tài liệu
3. Trả lời NGẮN GỌN, CHÍNH XÁC và TRỰC TIẾP
4. Nếu không có thông tin: "Tài liệu không đề cập vấn đề này"

📝 Lưu ý: System prompt chi tiết sẽ được cung cấp bởi RAG engine."""
    
    def get_template(self) -> PromptTemplate:
        return PromptTemplate(
            name="fallback_basic",
            type=PromptType.FALLBACK,
            context=ContextType.LOW_CONFIDENCE,
            template=self.get_prompt({}),
            version="1.0",
            description="Basic fallback prompt for error scenarios"
        )

class PromptService:
    """
    🎯 CENTRALIZED PROMPT MANAGEMENT SERVICE - SINGLE SOURCE OF TRUTH
    
    This service is the ONLY place where prompts are created and formatted.
    It eliminates multi-layer prompt formatting and prompt bleeding issues.
    
    Key Principles:
    - Single Responsibility: Only handles prompt creation and formatting
    - Complete Prompt Generation: Creates ready-to-use prompts for LLM
    - No Multi-layer Formatting: Eliminates confusion and prompt bleeding
    - Strategy Pattern: Different strategies for different contexts
    - Performance Optimized: Direct path to LLM without intermediate processing
    
    Usage:
        # ✅ RECOMMENDED (Single layer):
        complete_prompt = prompt_service.get_complete_rag_prompt(
            query=user_query,
            context=retrieved_context,
            confidence_level="medium",
            chat_history=chat_history
        )
        response = llm_service.generate_response_direct(complete_prompt)
        
        # ❌ DEPRECATED (Multi-layer):  
        system_prompt = prompt_service.get_legal_rag_prompt()
        response = llm_service.generate_response(query, context, system_prompt)
    """
    
    def __init__(self):
        self.strategies: Dict[PromptType, BasePromptStrategy] = {}
        self.metrics = {
            'prompts_served': 0,
            'strategy_usage': {},
            'average_prompt_length': 0
        }
        
        # Initialize strategies
        self._initialize_strategies()
        logger.info("✅ PromptService initialized with all strategies")
    
    def _initialize_strategies(self):
        """Initialize all prompt strategies"""
        self.strategies[PromptType.LEGAL_RAG] = LegalRAGPromptStrategy()
        self.strategies[PromptType.FALLBACK] = FallbackPromptStrategy()
        
        logger.info(f"🎯 Initialized {len(self.strategies)} prompt strategies")
    
    def get_prompt(
        self, 
        prompt_type: PromptType = PromptType.LEGAL_RAG,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get prompt based on type and context
        
        Args:
            prompt_type: Type of prompt needed
            context: Context information for prompt customization
            
        Returns:
            Optimized prompt string
        """
        if context is None:
            context = {}
            
        # Get strategy
        strategy = self.strategies.get(prompt_type)
        if not strategy:
            logger.warning(f"⚠️ No strategy found for {prompt_type}, using fallback")
            strategy = self.strategies[PromptType.FALLBACK]
        
        # Generate prompt
        prompt = strategy.get_prompt(context)
        
        # Update metrics
        self._update_metrics(prompt_type, prompt)
        
        logger.debug(f"📝 Generated {prompt_type.value} prompt ({len(prompt)} chars)")
        return prompt
    
    def get_legal_rag_prompt(self, confidence_level: str = "medium") -> str:
        """Convenience method for legal RAG prompts"""
        return self.get_prompt(
            prompt_type=PromptType.LEGAL_RAG,
            context={'confidence_level': confidence_level}
        )
    
    def get_complete_rag_prompt(
        self,
        query: str,
        context: str = "",
        confidence_level: str = "medium",
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        🎯 COMPLETE PROMPT GENERATION - Ready for LLM
        
        Creates complete prompt that includes:
        - System rules
        - Context information  
        - Chat history (if any)
        - User query
        - Proper PhoGPT format
        
        This eliminates the need for multi-layer prompt formatting
        
        Args:
            query: User's question
            context: Retrieved context from vector DB
            confidence_level: Confidence level for response
            chat_history: Previous conversation turns
            
        Returns:
            Complete prompt ready to send directly to LLM (no further formatting needed)
        """
        # Get base system prompt (simplified)
        system_prompt = self.get_prompt(
            prompt_type=PromptType.LEGAL_RAG,
            context={'confidence_level': confidence_level}
        )
        
        # Build complete instruction
        instruction_parts = []
        
        # 1. System rules
        instruction_parts.append(system_prompt)
        
        # 2. Chat history (if any) - Only take 2 most recent turns (1 user + 1 assistant)
        if chat_history:
            # Only take the last 2 turns (user + assistant)
            recent_history = chat_history[-2:] if len(chat_history) > 2 else chat_history

            # Build conversation context with both user and assistant messages
            conversation_parts = []
            for turn in recent_history:
                role = turn.get("role")
                content = turn.get("content") 
                if role == "user" and content:
                    conversation_parts.append(f"Người dùng: {content}")
                elif role == "assistant" and content:
                    conversation_parts.append(f"Trợ lý: {content}")

            # Add conversation context if any
            if conversation_parts:
                instruction_parts.append(f"Ngữ cảnh cuộc trò chuyện trước:\n" + "\n".join(conversation_parts))
        
        # 3. Context from vector DB with nucleus emphasis
        if context.strip():
            if "📋 THÔNG TIN CHÍNH CẦN TRẢ LỜI:" in context:
                instruction_parts.append(
                    "HƯỚNG DẪN TRẢ LỜI:\n"
                    "- Dựa chủ yếu vào phần '📋 THÔNG TIN CHÍNH CẦN TRẢ LỜI'\n"
                    "- Phần '📚 Thông tin bổ sung' chỉ tham khảo khi cần thiết\n"
                    "- Trả lời ngắn gọn, không lặp lại thông tin đã nêu\n"
                )
            instruction_parts.append(f"Ngữ cảnh tài liệu:\n{context}")
            
        # 4. Confidence adjustment (moved before query)
        if confidence_level == 'low':
            instruction_parts.append("Lưu ý: Hãy đặc biệt cẩn trọng về độ chính xác.")
            
        # Combine all instruction parts (WITHOUT the actual query)
        full_instruction = "\n\n".join(instruction_parts)
        
        # Apply official PhoGPT format with query SEPARATE from instructions
        return f"### Câu hỏi: {full_instruction}\n\nCâu hỏi: {query}\n\n### Trả lời:"
    
    def get_fallback_prompt(self) -> str:
        """Convenience method for fallback prompts"""
        return self.get_prompt(prompt_type=PromptType.FALLBACK)
    
    def register_strategy(self, prompt_type: PromptType, strategy: BasePromptStrategy):
        """Register new prompt strategy"""
        self.strategies[prompt_type] = strategy
        logger.info(f"✅ Registered new strategy for {prompt_type.value}")
    
    def get_all_templates(self) -> List[PromptTemplate]:
        """Get all available prompt templates"""
        return [strategy.get_template() for strategy in self.strategies.values()]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get prompt service metrics"""
        return {
            **self.metrics,
            'available_strategies': list(self.strategies.keys()),
            'total_strategies': len(self.strategies)
        }
    
    def _update_metrics(self, prompt_type: PromptType, prompt: str):
        """Update usage metrics"""
        self.metrics['prompts_served'] += 1
        
        if prompt_type.value not in self.metrics['strategy_usage']:
            self.metrics['strategy_usage'][prompt_type.value] = 0
        self.metrics['strategy_usage'][prompt_type.value] += 1
        
        # Update average prompt length
        current_avg = self.metrics['average_prompt_length']
        total_served = self.metrics['prompts_served']
        new_avg = ((current_avg * (total_served - 1)) + len(prompt)) / total_served
        self.metrics['average_prompt_length'] = round(new_avg, 2)

    def test_complete_prompt_generation(self):
        """
        🧪 TEST METHOD: Test complete prompt generation
        
        This method demonstrates how the new single-layer prompt generation works
        and can be used for debugging prompt bleeding issues.
        """
        # Test data
        test_query = "đăng ký kết hôn cần giấy tờ gì"
        test_context = """
        11. ĐĂNG KÝ KẾT HÔN

        THỦ TỤC HÀNH CHÍNH: Đăng ký kết hôn

        HỒ SƠ BAO GỒM:
        1. Tờ khai đăng ký kết hôn theo mẫu
        2. Căn cước công dân/Hộ chiếu của hai bên
        3. Giấy tờ chứng minh về cư trú (nếu cần)

        PHÍ: Miễn lệ phí đăng ký kết hôn. Phí cấp bản sao trích lục: 8.000 đồng

        ĐỘ TUỔI: Nam từ đủ 20 tuổi, nữ từ đủ 18 tuổi
        """
        
        test_chat_history = [
            {"role": "user", "content": "cần đóng phí gì không"},
            {"role": "assistant", "content": "Miễn lệ phí đăng ký kết hôn. Chỉ đóng phí cấp bản sao trích lục 8.000 đồng."}
        ]
        
        # Generate complete prompt using new method
        complete_prompt = self.get_complete_rag_prompt(
            query=test_query,
            context=test_context,
            confidence_level="medium", 
            chat_history=test_chat_history
        )
        
        print("="*80)
        print("🧪 COMPLETE PROMPT TEST")
        print("="*80)
        print("📊 Prompt Length:", len(complete_prompt), "chars")
        print("📊 Estimated Tokens:", len(complete_prompt) // 3)
        print("="*80)
        print("📝 GENERATED PROMPT:")
        print("="*80)
        print(complete_prompt)
        print("="*80)
        
        # Verify no multi-layer formatting
        if complete_prompt.count("### Câu hỏi:") == 1 and complete_prompt.count("### Trả lời:") == 1:
            print("✅ Single-layer formatting verified!")
        else:
            print("❌ Multi-layer formatting detected!")
            
        return complete_prompt

# Global instance
prompt_service = PromptService()
