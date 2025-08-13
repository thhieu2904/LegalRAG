import logging
import os
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any
from llama_cpp import Llama
import time
from ..core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service quản lý PhoGPT model từ HuggingFace"""
    
    def __init__(self, model_path: Optional[str] = None, model_url: Optional[str] = None, **kwargs):
        self.model_path = Path(model_path or settings.llm_model_path)
        self.model_url = model_url or settings.llm_model_url
        self.model = None
        
        # Cấu hình GPU + CPU hybrid cho tối ưu performance
        self.model_kwargs = {
            'n_ctx': kwargs.get('n_ctx', settings.n_ctx),
            'n_threads': kwargs.get('n_threads', settings.n_threads),
            'n_gpu_layers': kwargs.get('n_gpu_layers', settings.n_gpu_layers),  # GPU acceleration
            'n_batch': kwargs.get('n_batch', settings.n_batch),  # Batch size for prompt processing
            'verbose': False,
            # Thêm GPU acceleration settings
            'use_mmap': True,  # Memory-mapped files
            'use_mlock': True,  # Keep model in RAM
            'f16_kv': True,    # Use half precision for key/value cache
        }
        
        # Tải model nếu chưa có
        if not self.model_path.exists():
            self._download_model()
        
        # Load model
        self._load_model()
    
    def _download_model(self):
        """Tải model từ HuggingFace"""
        logger.info(f"Downloading model from {self.model_url}")
        
        try:
            # Tạo thư mục nếu chưa có
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = requests.get(self.model_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(self.model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            if downloaded_size % (1024 * 1024 * 100) == 0:  # Log every 100MB
                                logger.info(f"Downloaded {progress:.1f}% ({downloaded_size / (1024**3):.2f} GB)")
            
            logger.info(f"Model downloaded successfully: {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            if self.model_path.exists():
                self.model_path.unlink()  # Xóa file bị lỗi
            raise
    
    def _load_model(self):
        """Load model vào memory"""
        try:
            logger.info(f"Loading model from {self.model_path}")
            self.model = Llama(model_path=str(self.model_path), **self.model_kwargs)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            raise
    
    def _format_prompt(self, system_prompt: str, user_query: str, context: str = "") -> str:
        """Format prompt theo template chính xác của PhoGPT"""
        # Tạo instruction bao gồm system prompt, context và user query
        if context:
            instruction = f"""{system_prompt}

Ngữ cảnh thông tin:
{context}

Câu hỏi của người dùng: {user_query}"""
        else:
            instruction = f"""{system_prompt}

Câu hỏi của người dùng: {user_query}"""
        
        # Sử dụng format chính xác của PhoGPT
        full_prompt = f"### Câu hỏi: {instruction}\n### Trả lời:"
        
        return full_prompt
    
    def generate_response(
        self, 
        user_query: str, 
        context: str = "", 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sinh response từ model - tối ưu để tránh lặp"""
        
        if not self.model:
            raise Exception("Model not loaded")
        
        # Sử dụng values từ config với tối ưu
        if max_tokens is None:
            max_tokens = min(settings.max_tokens, 512)  # Giảm max_tokens để tránh lặp
        if temperature is None:
            temperature = max(settings.temperature, 0.3)  # Tăng temperature để tránh lặp
        
        # System prompt tối ưu cho legal domain
        if system_prompt is None:
            system_prompt = """Bạn là trợ lý AI chuyên về pháp luật Việt Nam. Trả lời ngắn gọn, chính xác và có cấu trúc rõ ràng. Không lặp lại thông tin."""
        
        # Format prompt
        formatted_prompt = self._format_prompt(system_prompt, user_query, context)
        
        try:
            start_time = time.time()
            
            # Generate với parameters tối ưu để tránh lặp
            response = self.model(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,  # Nucleus sampling để tăng đa dạng
                top_k=40,   # Top-K sampling
                repeat_penalty=1.1,  # Penalty cho từ lặp
                stop=["### Câu hỏi:", "### Trả lời:", "\n\n###", "Câu hỏi:", "Question:"],
                echo=False,
                stream=False  # Ensure non-streaming response
            )
            
            processing_time = time.time() - start_time
            
            # Safely extract text from response
            if isinstance(response, dict) and 'choices' in response:
                generated_text = response['choices'][0]['text'].strip()
                
                # Get token usage safely
                usage = response.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
            else:
                raise Exception("Invalid response format from model")
            
            # Clean up response - remove repetitive patterns
            generated_text = self._clean_repetitive_response(generated_text)
            
            result = {
                'response': generated_text,
                'processing_time': processing_time,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens
            }
            
            logger.info(f"Generated response in {processing_time:.2f}s, "
                       f"tokens: {result['total_tokens']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _clean_repetitive_response(self, text: str) -> str:
        """Dọn dẹp response để loại bỏ patterns lặp lại"""
        import re
        
        # Loại bỏ patterns lặp kiểu A. B. C. XI. XI. XI.
        text = re.sub(r'([A-Z]\.)\s*THỦ\s*TỤC\s*NUÔI\s*CON\s*NUÔI\s*TRONG\s*NƯỚC\s*\n*', '', text, flags=re.IGNORECASE)
        
        # Loại bỏ repetitive numbered/lettered lists
        text = re.sub(r'([A-Z]{1,3}\.)\s*(.+?)\n(\1\s*\2\n){2,}', r'\1 \2\n', text, flags=re.IGNORECASE)
        
        # Loại bỏ câu lặp lại liên tiếp (3+ lần)
        lines = text.split('\n')
        cleaned_lines = []
        prev_line = ""
        repeat_count = 0
        
        for line in lines:
            line = line.strip()
            if line == prev_line and line:
                repeat_count += 1
                if repeat_count < 2:  # Cho phép lặp tối đa 1 lần
                    cleaned_lines.append(line)
            else:
                repeat_count = 0
                cleaned_lines.append(line)
                prev_line = line
        
        cleaned_text = '\n'.join(cleaned_lines).strip()
        
        # Giới hạn độ dài response hợp lý
        if len(cleaned_text) > 2000:
            # Cắt tại câu cuối cùng trong 2000 ký tự đầu
            truncated = cleaned_text[:2000]
            last_sentence = truncated.rfind('.')
            if last_sentence > 1000:  # Chỉ cắt nếu còn đủ nội dung
                cleaned_text = truncated[:last_sentence + 1]
        
        return cleaned_text
    
    def is_loaded(self) -> bool:
        """Kiểm tra model đã được load chưa"""
        return self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Lấy thông tin về model"""
        return {
            'model_path': str(self.model_path),
            'model_url': self.model_url,
            'is_loaded': self.is_loaded(),
            'model_size_mb': self.model_path.stat().st_size / (1024**2) if self.model_path.exists() else 0,
            'model_kwargs': self.model_kwargs
        }
