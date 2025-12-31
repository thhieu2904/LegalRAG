"""
Local Provider - Vistral 7B với llama-cpp-python

Provider cho local inference sử dụng Vistral 7B model.
Yêu cầu GPU với CUDA để đạt hiệu suất tốt.
"""

import os
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

from .base import BaseLLMProvider, LLMResponse
from ..config import settings

if TYPE_CHECKING:
    from llama_cpp import Llama

logger = logging.getLogger(__name__)


class LocalProvider(BaseLLMProvider):
    """
    Local LLM Provider sử dụng Vistral 7B với llama-cpp-python.
    
    Features:
    - GPU acceleration với CUDA
    - Context window 8192 tokens
    - Vietnamese language optimized
    """
    
    def __init__(self):
        self._llm: Optional["Llama"] = None
        self._model_name = settings.model_name
        self._is_ready = False
    
    @property
    def provider_name(self) -> str:
        return "local"
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready and self._llm is not None
    
    async def initialize(self) -> None:
        """Load Vistral 7B model với llama-cpp-python."""
        logger.info("=" * 60)
        logger.info("Initializing Local Provider (Vistral 7B)")
        logger.info("=" * 60)
        logger.info(f"Model: {settings.model_name}")
        logger.info(f"Model Path: {settings.model_path}")
        logger.info(f"Device: {settings.device}")
        logger.info(f"Context Window: {settings.n_ctx}")
        logger.info(f"GPU Layers: {settings.n_gpu_layers}")
        logger.info("=" * 60)
        
        try:
            from llama_cpp import Llama
            
            # Check if model file exists
            if not os.path.exists(settings.model_path):
                logger.error(f"Model file not found: {settings.model_path}")
                logger.info("Run download_model.py to download Vistral 7B model")
                raise FileNotFoundError(f"Model not found: {settings.model_path}")
            
            # Load Vistral 7B model
            logger.info("Loading Vistral 7B model (this may take a minute)...")
            self._llm = Llama(
                model_path=settings.model_path,
                n_ctx=settings.n_ctx,
                n_gpu_layers=settings.n_gpu_layers if settings.device == "cuda" else 0,
                n_threads=settings.n_threads,
                n_batch=settings.n_batch,
                use_mmap=settings.use_mmap,
                use_mlock=settings.use_mlock,
                verbose=settings.verbose
            )
            
            self._is_ready = True
            logger.info("✓ Vistral 7B model loaded successfully")
            logger.info(f"✓ Using device: {settings.device}")
            if settings.device == "cuda" and settings.n_gpu_layers == -1:
                logger.info("✓ All layers loaded on GPU")
            elif settings.device == "cuda":
                logger.info(f"✓ {settings.n_gpu_layers} layers on GPU")
                
        except ImportError as e:
            logger.error(f"✗ llama-cpp-python not installed: {e}")
            logger.error("Install with: pip install llama-cpp-python")
            raise
        except Exception as e:
            logger.error(f"✗ Failed to load model: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Unload model và giải phóng resources."""
        logger.info("Shutting down Local Provider")
        if self._llm:
            del self._llm
            self._llm = None
        self._is_ready = False
        logger.info("✓ Local Provider shutdown complete")
    
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
        """Generate text sử dụng Vistral 7B."""
        if not self.is_ready or self._llm is None:
            return self._create_error_response("Model not loaded")
        
        try:
            # Use defaults from settings if not provided
            max_tokens = max_tokens or settings.max_tokens
            temperature = temperature or settings.temperature
            top_p = top_p or settings.top_p
            top_k = top_k or settings.top_k
            repeat_penalty = kwargs.get("repeat_penalty") or settings.repeat_penalty
            
            # Ensure all numeric params are correct types (avoid string from env)
            max_tokens = int(max_tokens)
            temperature = float(temperature)
            top_p = float(top_p)
            top_k = int(top_k)
            repeat_penalty = float(repeat_penalty)
            
            # Generate với llama-cpp-python
            output = self._llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop or ["---", "## ", "Người dùng:", "CÂU HỎI"],
                echo=False
            )
            
            # Extract response data (type-safe access)
            choices = output.get("choices", [])  # type: ignore
            usage = output.get("usage", {})  # type: ignore
            
            generated_text = choices[0]["text"].strip() if choices else ""
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            finish_reason = choices[0].get("finish_reason", "stop") if choices else "stop"
            
            return LLMResponse(
                success=True,
                text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                finish_reason=str(finish_reason) if finish_reason else "stop",
                provider=self.provider_name,
                model=self.model_name
            )
            
        except Exception as e:
            logger.error(f"Local generation failed: {e}", exc_info=True)
            return self._create_error_response(str(e))
    
    async def health_check(self) -> Dict[str, Any]:
        """Kiểm tra sức khỏe của Local Provider."""
        return {
            "status": "healthy" if self.is_ready else "unhealthy",
            "provider": self.provider_name,
            "model": self.model_name,
            "model_loaded": self.is_ready,
            "device": settings.device,
            "n_ctx": settings.n_ctx,
            "n_gpu_layers": settings.n_gpu_layers
        }
