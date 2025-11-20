"""
LLM Service Configuration - PhoGPT with llama-cpp-python
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service config
    service_name: str = "llm-service"
    service_port: int = 8006
    service_host: str = "0.0.0.0"
    
    # Model config - Vistral-7B-Chat
    model_name: str = "ggml-vistral-7B-chat-q4_0.gguf"
    model_path: str = "/app/models/ggml-vistral-7B-chat-q4_0.gguf"
    model_cache_dir: str = "/app/models"
    
    # HuggingFace download config
    hf_model_repo: str = "uonlp/Vistral-7B-Chat-gguf"
    hf_model_file: str = "ggml-vistral-7B-chat-q4_0.gguf"
    
    # Llama.cpp configuration
    n_ctx: int = 8192  # Context window
    n_gpu_layers: int = -1  # -1 = all layers on GPU, 0 = CPU only
    n_threads: int = 4  # CPU threads (if not using GPU)
    n_batch: int = 512  # Batch size for prompt processing
    
    # Generation parameters
    max_tokens: int = 2048
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
        env_file = ".env"
        case_sensitive = False


settings = Settings()
