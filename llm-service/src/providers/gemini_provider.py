"""
Gemini Provider - Google Gemini API

Provider sử dụng Google Gemini API cho text generation.
Không yêu cầu GPU, chỉ cần API key.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, TYPE_CHECKING

from .base import BaseLLMProvider, LLMResponse
from ..config import settings

if TYPE_CHECKING:
    import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Gemini API Provider.
    
    Features:
    - Không cần GPU
    - Retry logic với exponential backoff
    - Safety settings cho legal domain
    """
    
    def __init__(self):
        self._model: Any = None
        self._model_name = settings.gemini_model
        self._is_ready = False
        self._genai: Any = None
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready and self._model is not None
    
    async def initialize(self) -> None:
        """Setup Gemini client và verify API key."""
        logger.info("=" * 60)
        logger.info("Initializing Gemini Provider")
        logger.info("=" * 60)
        logger.info(f"Model: {settings.gemini_model}")
        logger.info(f"Temperature: {settings.gemini_temperature}")
        logger.info(f"Max Output Tokens: {settings.gemini_max_output_tokens}")
        logger.info("=" * 60)
        
        try:
            import google.generativeai as genai
            self._genai = genai
            
            # Check API key
            if not settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY is required when using Gemini provider")
            
            # Configure API
            genai.configure(api_key=settings.gemini_api_key)
            
            # Initialize model
            self._model = genai.GenerativeModel(settings.gemini_model)
            
            # Verify API với simple request
            logger.info("Verifying Gemini API connection...")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._model.generate_content("Xin chào")
            )
            
            self._is_ready = True
            logger.info("✓ Gemini API connected successfully")
            logger.info(f"✓ Model: {settings.gemini_model}")
            
        except ImportError as e:
            logger.error(f"✗ google-generativeai not installed: {e}")
            logger.error("Install with: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"✗ Failed to initialize Gemini: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Cleanup Gemini resources."""
        logger.info("Shutting down Gemini Provider")
        self._model = None
        self._is_ready = False
        logger.info("✓ Gemini Provider shutdown complete")
    
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
        """Generate text sử dụng Gemini API."""
        if not self.is_ready or self._genai is None:
            return self._create_error_response("Gemini client not initialized")
        
        try:
            # Use defaults from settings if not provided
            max_tokens = max_tokens or settings.gemini_max_output_tokens
            temperature = temperature or settings.gemini_temperature
            top_p = top_p or settings.gemini_top_p
            top_k = top_k or settings.gemini_top_k
            
            # Generation config
            generation_config = self._genai.types.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_output_tokens=max_tokens
            )
            
            # Safety settings - giảm block cho legal domain
            safety_settings = [
                {
                    "category": self._genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": self._genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": self._genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": self._genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
            
            # Call API with retry
            response = await self._call_with_retry(
                prompt, 
                generation_config, 
                safety_settings
            )
            
            # Extract response
            generated_text = response.text
            
            # Estimate tokens (Gemini không trả về chính xác)
            prompt_tokens = len(prompt.split())
            completion_tokens = len(generated_text.split())
            
            finish_reason = "stop"
            if response.candidates:
                finish_reason = str(response.candidates[0].finish_reason)
            
            return LLMResponse(
                success=True,
                text=generated_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                finish_reason=finish_reason,
                provider=self.provider_name,
                model=self.model_name
            )
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}", exc_info=True)
            return self._create_error_response(str(e))
    
    async def _call_with_retry(
        self, 
        prompt: str, 
        generation_config: Any, 
        safety_settings: list,
        max_retries: int = 3
    ) -> Any:
        """Call Gemini API với retry logic."""
        last_error: Optional[Exception] = None
        
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self._model.generate_content(
                        prompt,
                        generation_config=generation_config,
                        safety_settings=safety_settings
                    )
                )
                return response
                
            except Exception as e:
                last_error = e
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Gemini API attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        if last_error:
            raise last_error
        raise RuntimeError("All retry attempts failed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Kiểm tra sức khỏe của Gemini Provider."""
        if not self.is_ready or self._model is None:
            return {
                "status": "unhealthy",
                "provider": self.provider_name,
                "model": self.model_name,
                "reason": "Client not initialized"
            }
        
        try:
            # Test với simple request
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._model.generate_content("Test")
            )
            
            return {
                "status": "healthy",
                "provider": self.provider_name,
                "model": self.model_name,
                "api_accessible": True
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider_name,
                "model": self.model_name,
                "api_accessible": False,
                "reason": str(e)
            }
