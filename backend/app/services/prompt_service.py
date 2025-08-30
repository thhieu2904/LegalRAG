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

🚨 QUY TẮC BẮT BUỘC - KHÔNG ĐƯỢC VI PHẠM:
1. **CHỈ TRẢ LỜI DỰA TRÊN THÔNG TIN CÓ TRONG TÀI LIỆU** - KHÔNG tự sáng tạo
2. **ƯU TIÊN THÔNG TIN CHÍNH:** Tìm trong [THÔNG TIN CHÍNH]...[/THÔNG TIN CHÍNH] trước
3. **TRẢ LỜI NGẮN GỌN:** 7-10 câu, tự nhiên như nói chuyện
4. **NẾU KHÔNG CÓ THÔNG TIN:** Trả lời "Tài liệu không đề cập vấn đề này"
5. **KHÔNG SỬ DỤNG:** Ký tự đặc biệt, emoji, dấu gạch

🔍 HƯỚNG DẪN TÌM KIẾM THÔNG TIN:
- **PHÍ/LỆ PHÍ:** Tìm trong metadata về fee_vnd, fee_text, fee_description  
- **THỜI GIAN:** Tìm processing_time_text, processing_time_days
- **NƠI LÀM:** Tìm executing_agency, jurisdiction
- **BIỂU MẪU:** Tìm has_form, form_name, form_url

⚠️ CHỐNG HALLUCINATION - TUÂN THỰC NGHIÊM NGẶT:
- KHÔNG sử dụng thông tin từ câu hỏi trước
- KHÔNG áp dụng examples từ prompt này
- KHÔNG suy luận ngoài thông tin có sẵn
- KHÔNG thêm thông tin không có trong tài liệu
- KHÔNG tạo ra các bước hoặc quy trình không có sẵn
- Luôn kiểm tra source trước khi trả lời
- Nếu không chắc chắn, trả lời "Tài liệu không đề cập vấn đề này"

📋 PHONG CÁCH: Tự nhiên, thân thiện, chính xác tuyệt đối về thông tin.

⚡ HƯỚNG DẪN XỬ LÝ CÂU HỎI:
- Với câu hỏi về phí: Chỉ trả lời dựa trên fee_text, fee_vnd trong metadata
- Với câu hỏi về thời gian: Chỉ trả lời dựa trên processing_time_text
- Với câu hỏi về nơi làm: Chỉ trả lời dựa trên executing_agency
- Nếu không có thông tin cụ thể: "Tài liệu không đề cập vấn đề này\""""
        
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
    🎯 CENTRALIZED PROMPT MANAGEMENT SERVICE
    
    Features:
    - Strategy-based prompt selection
    - Context-aware prompt generation
    - Version control support
    - A/B testing ready
    - Performance monitoring
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

# Global instance
prompt_service = PromptService()
