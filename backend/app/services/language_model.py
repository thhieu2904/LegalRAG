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
    """Service quản lý PhoGPT model từ HuggingFace với VRAM Optimization"""
    
    def __init__(self, model_path: Optional[str] = None, model_url: Optional[str] = None, **kwargs):
        # Use absolute path to avoid issues when running from different directories
        if model_path:
            self.model_path = Path(model_path)
        else:
            # Use the computed property from settings which gives absolute path
            self.model_path = settings.llm_model_file_path
            
        self.model_url = model_url or settings.llm_model_url
        self.model = None
        self.model_loaded = False
        
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
        logger.info(f"Checking model path: {self.model_path}")
        logger.info(f"Model exists: {self.model_path.exists()}")
        
        if not self.model_path.exists():
            logger.info("Model file not found, attempting to download...")
            self._download_model()
        else:
            logger.info("Model file found, skipping download")
        
        # VRAM Optimization: Load model khi cần thiết
        # self._load_model()  # Comment out để load on-demand
    
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
        if self.model_loaded:
            return
            
        try:
            logger.info(f"Loading LLM model from {self.model_path}")
            self.model = Llama(model_path=str(self.model_path), **self.model_kwargs)
            self.model_loaded = True
            logger.info("✅ LLM model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            self.model = None
            self.model_loaded = False
            raise
    
    def unload_model(self):
        """Unload model để giải phóng VRAM"""
        if self.model is not None:
            logger.info("🔄 Unloading LLM model to free VRAM...")
            del self.model
            self.model = None
            self.model_loaded = False
            
            # Force garbage collection
            import gc
            gc.collect()
            logger.info("✅ LLM model unloaded, VRAM freed")
    
    def ensure_loaded(self):
        """Ensure model is loaded - load nếu chưa có"""
        if not self.model_loaded or self.model is None:
            self._load_model()
    
    def is_model_loaded(self) -> bool:
        """Check if model is currently loaded"""
        return self.model_loaded and self.model is not None
    
    def _format_prompt(
        self, 
        system_prompt: str, 
        user_query: str, 
        context: str = "",
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Format prompt theo chuẩn ChatML template mà PhoGPT-Chat mong đợi.
        Template: <|im_start|>role\ncontent<|im_end|>
        
        Đây là cách ĐÚNG để sử dụng PhoGPT-Chat, thay vì format ### Câu hỏi: ### Trả lời:
        """
        messages = []
        
        # 1. System Prompt - chỉ dẫn vai trò và quy tắc
        if system_prompt:
            messages.append(f"<|im_start|>system\n{system_prompt}<|im_end|>")
        
        # 2. Chat History (nếu có) - lịch sử hội thoại có cấu trúc
        if chat_history:
            for turn in chat_history:
                role = turn.get("role")
                content = turn.get("content")
                if role and content:
                    messages.append(f"<|im_start|>{role}\n{content}<|im_end|>")

        # 3. User Query hiện tại (kèm context nếu có)
        user_content = ""
        if context:
            user_content += f"Dựa vào thông tin tài liệu sau đây:\n--- BẮT ĐẦU TÀI LIỆU ---\n{context}\n--- KẾT THÚC TÀI LIỆU ---\n\n"
        user_content += f"Hãy trả lời câu hỏi sau: {user_query}"
        
        messages.append(f"<|im_start|>user\n{user_content}<|im_end|>")
        
        # 4. Thêm dấu hiệu để model bắt đầu trả lời
        messages.append("<|im_start|>assistant")

        formatted_prompt = "\n".join(messages)
        
        # Log để debug (chỉ hiển thị các token đặc biệt)
        logger.debug(f"ChatML template structure: {len([m for m in messages if 'im_start' in m])} messages")
        
        return formatted_prompt
    
    def generate_response(
        self, 
        user_query: str, 
        context: str = "", 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None  # THAM SỐ MỚI cho ChatML
    ) -> Dict[str, Any]:
        """Sinh response từ model - VRAM optimized với on-demand loading"""
        
        # VRAM Optimization: Ensure model is loaded
        self.ensure_loaded()
        
        if not self.model:
            raise Exception("Model not loaded")
        
        # Sử dụng values từ config - LOẠI BỎ HARDCODE
        if max_tokens is None:
            max_tokens = settings.max_tokens  # Lấy từ .env thay vì hardcode
        if temperature is None:
            temperature = settings.temperature  # Lấy từ .env thay vì hardcode
        
        # System prompt tối ưu cho legal domain - IMPROVED VERSION
        if system_prompt is None:
            system_prompt = """Bạn là trợ lý AI chuyên về pháp luật Việt Nam. 

QUY TẮC BẮT BUỘC:
1. CHỈ trả lời dựa trên thông tin trong tài liệu
2. Trả lời NGẮN GỌN và TRỰC TIẾP 
3. KHÔNG tự sáng tạo thông tin
4. Nếu hỏi về phí/tiền - tìm chính xác thông tin "LỆ PHÍ"

Trả lời chính xác, ngắn gọn."""
        
        # Format prompt theo chuẩn ChatML thay vì ### Câu hỏi: ### Trả lời:
        formatted_prompt = self._format_prompt(
            system_prompt, 
            user_query, 
            context, 
            chat_history  # Truyền chat_history có cấu trúc
        )
        
        # ======================================================================
        # === QUẢN LÝ CONTEXT WINDOW CHỦ ĐỘNG (BẢO VỆ KHỎI OVERFLOW) ===
        # ======================================================================
        
        # 1. Ước tính kích thước token của prompt đầu vào (1 token ≈ 3 ký tự tiếng Việt)
        prompt_tokens_estimated = len(formatted_prompt) // 3
        
        # 2. Lấy tổng context window từ cấu hình (.env)
        total_context_window = self.model_kwargs.get('n_ctx', settings.n_ctx)
        
        # 3. Tính toán không gian còn lại để sinh token (trừ đi buffer an toàn)
        safety_buffer = 256  # Buffer an toàn để tránh edge cases
        available_space_for_response = total_context_window - prompt_tokens_estimated - safety_buffer
        
        if available_space_for_response <= 0:
            logger.error(f"🚨 Context window overflow! Prompt ({prompt_tokens_estimated} tokens) đã vượt quá giới hạn ({total_context_window}).")
            raise ValueError(f"Prompt đầu vào quá lớn ({prompt_tokens_estimated} tokens), không còn không gian để sinh câu trả lời. Giới hạn: {total_context_window} tokens.")
            
        # 4. Điều chỉnh động `max_tokens` để không vượt quá không gian còn lại
        original_max_tokens = max_tokens
        dynamic_max_tokens = min(max_tokens, available_space_for_response)
        
        logger.info(f"📏 Context Info: Total={total_context_window}, Prompt≈{prompt_tokens_estimated}, Available={available_space_for_response}")
        if dynamic_max_tokens != original_max_tokens:
            logger.warning(f"⚠️ Max Tokens adjusted: {original_max_tokens} → {dynamic_max_tokens} (to prevent overflow)")
        else:
            logger.info(f"✅ Max Tokens: {dynamic_max_tokens} (no adjustment needed)")
        
        # ======================================================================
        
        try:
            start_time = time.time()
            
            # Generate với parameters tối ưu để tránh lặp - SỬ DỤNG DYNAMIC MAX_TOKENS
            response = self.model(
                formatted_prompt,
                max_tokens=dynamic_max_tokens,  # ✨ SỬ DỤNG GIÁ TRỊ ĐÃ ĐIỀU CHỈNH
                temperature=temperature,
                top_p=0.9,  # Nucleus sampling để tăng đa dạng
                top_k=40,   # Top-K sampling
                repeat_penalty=1.1,  # Penalty cho từ lặp
                stop=["<|im_end|>", "<|im_start|>", "\n<|im_start|>"],  # ChatML stop tokens
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
                'total_tokens': total_tokens,
                # Thêm thông tin debug cho context management
                'context_info': {
                    'total_context_window': total_context_window,
                    'prompt_tokens_estimated': prompt_tokens_estimated,
                    'available_space': available_space_for_response,
                    'max_tokens_requested': original_max_tokens,
                    'max_tokens_used': dynamic_max_tokens,
                    'was_adjusted': dynamic_max_tokens != original_max_tokens
                }
            }
            
            logger.info(f"✅ Generated response in {processing_time:.2f}s, "
                       f"tokens: {result['total_tokens']} "
                       f"(prompt: {prompt_tokens}, completion: {completion_tokens})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _clean_repetitive_response(self, text: str) -> str:
        """Dọn dẹp response để loại bỏ patterns lặp lại và ChatML tokens rò rỉ"""
        import re
        
        # 🔥 QUAN TRỌNG: Loại bỏ ChatML tokens có thể rò rỉ
        text = re.sub(r'<\|im_start\|>', '', text)
        text = re.sub(r'<\|im_end\|>', '', text) 
        text = re.sub(r'<\|.*?\|>', '', text)  # Loại bỏ bất kỳ special token nào khác
        
        # 🔥 CRITICAL: Loại bỏ các pattern format cũ có thể rò rỉ từ context
        text = re.sub(r'###\s*Câu hỏi\s*:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'###\s*Trả lời\s*:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'CÂUHỎI\s*:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'TRẢ\s*LỜI\s*:', '', text, flags=re.IGNORECASE)
        
        # Loại bỏ role indicators có thể rò rỉ
        text = re.sub(r'^\s*(user|assistant|system)\s*[:]\s*', '', text, flags=re.MULTILINE)
        
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
