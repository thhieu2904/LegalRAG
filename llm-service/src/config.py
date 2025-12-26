"""LLM Service Configuration - Multi-Provider Support (Local Vistral / Gemini API)

Provider Pattern:
- LLM_PROVIDER=local → Use Vistral 7B with llama-cpp-python (requires GPU)
- LLM_PROVIDER=gemini → Use Gemini API (no GPU required)
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service config
    service_name: str = "llm-service"
    service_port: int = 8014
    service_host: str = "0.0.0.0"
    
    # ============================================
    # LLM Provider Selection
    # ============================================
    llm_provider: str = "local"  # "local" | "gemini"
    
    # ============================================
    # Gemini Settings (khi llm_provider = "gemini")
    # ============================================
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_temperature: float = 0.3
    gemini_max_output_tokens: int = 1024
    gemini_top_p: float = 0.95
    gemini_top_k: int = 40
    
    # ============================================
    # Local Model Settings (khi llm_provider = "local")
    # ============================================
    # Model config - Vistral-7B-Chat
    model_name: str = "ggml-vistral-7B-chat-q4_0.gguf"
    model_path: str = "/app/models/ggml-vistral-7B-chat-q4_0.gguf"
    model_cache_dir: str = "/app/models"
    
    # HuggingFace download config
    hf_model_repo: str = "uonlp/Vistral-7B-Chat-gguf"
    hf_model_file: str = "ggml-vistral-7B-chat-q4_0.gguf"
    
    # Llama.cpp configuration
    n_ctx: int = 5120  # Context window
    n_gpu_layers: int = -1  # -1 = all layers on GPU, 0 = CPU only
    n_threads: int = 4  # CPU threads (if not using GPU)
    n_batch: int = 512  # Batch size for prompt processing
    
    # Generation parameters
    max_tokens: int = 1280
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    
    # Hardware config
    device: str = "cuda"  # 'cuda' or 'cpu'
    
    # Performance tuning
    use_mmap: bool = True  # Memory-map model file
    use_mlock: bool = False  # Lock model in RAM
    verbose: bool = False  # Verbose llama.cpp logging
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        # Allow loading from local and default env files; container env vars still take precedence.
        env_file = (".env.local", ".env")
        case_sensitive = False


settings = Settings()
