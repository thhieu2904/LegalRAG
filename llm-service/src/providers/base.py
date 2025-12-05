"""
Base LLM Provider - Abstract Interface

Định nghĩa interface chung cho tất cả LLM providers.
Mỗi provider phải implement các methods này.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response format chuẩn từ LLM providers"""
    success: bool
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    provider: str
    model: str
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class cho LLM providers.
    
    Tất cả providers (Local, Gemini, OpenAI...) phải implement interface này
    để đảm bảo tính nhất quán trong API responses.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Tên provider (e.g., 'local', 'gemini')"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Tên model đang sử dụng"""
        pass
    
    @property
    @abstractmethod
    def is_ready(self) -> bool:
        """Kiểm tra provider đã sẵn sàng chưa"""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Khởi tạo provider (load model, setup client...).
        Được gọi khi startup service.
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        Cleanup khi shutdown service.
        Giải phóng resources (unload model, close connections...).
        """
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop: Optional[list] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text từ prompt.
        
        Args:
            prompt: Prompt đã được format sẵn
            max_tokens: Số token tối đa sinh ra
            temperature: Độ sáng tạo (0-2)
            top_p: Nucleus sampling threshold
            top_k: Top-K sampling
            stop: Danh sách stop sequences
            **kwargs: Các parameters khác tùy provider
            
        Returns:
            LLMResponse với text, token counts, và metadata
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Kiểm tra sức khỏe của provider.
        
        Returns:
            Dict với status, provider info, và chi tiết khác
        """
        pass
    
    def _create_error_response(self, error: str) -> LLMResponse:
        """Helper để tạo error response"""
        return LLMResponse(
            success=False,
            text="",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            finish_reason="error",
            provider=self.provider_name,
            model=self.model_name,
            error=error
        )
