from pydantic_settings import BaseSettings
from pathlib import Path
import os
from typing import Optional

class Settings(BaseSettings):
    """
    LegalRAG Configuration Settings
    
    Tại sao có duplicate values với .env?
    1. .env: Production values (actual config)
    2. config.py: Fallback defaults + Type safety + Documentation
    3. Pydantic sẽ prioritize .env values over defaults
    
    => .env values sẽ override tất cả defaults này
    """
    # API Settings
    app_name: str = "LegalRAG API"
    app_version: str = "1.0.0"
    debug: bool = False  # Overridden by DEBUG in .env
    host: str = "0.0.0.0"  # Overridden by HOST in .env  
    port: int = 8000  # Overridden by PORT in .env
    
    # Data Paths - Load from environment
    data_root_dir: str = "data"  # Overridden by DATA_ROOT_DIR in .env
    documents_dir: str = "data/documents"  # Overridden by DOCUMENTS_DIR in .env (OLD STRUCTURE)
    vectordb_dir: str = "data/vectordb"  # Overridden by VECTORDB_DIR in .env
    models_dir: str = "data/models"  # Overridden by MODELS_DIR in .env
    
    # New Structure Paths (using PathConfig)
    storage_dir: str = "data/storage"  # New centralized storage
    collections_dir: str = "data/storage/collections"  # Collections
    registry_dir: str = "data/storage/registry"  # Registries
    
    # Model Configuration - Actual values từ .env file
    embedding_model_name: str = "AITeamVN/Vietnamese_Embedding_v2"  # From EMBEDDING_MODEL_NAME
    reranker_model_name: str = "AITeamVN/Vietnamese_Reranker"  # From RERANKER_MODEL_NAME
    llm_model_path: str = "data/models/llm_dir/PhoGPT-4B-Chat-q4_k_m.gguf"  # From LLM_MODEL_PATH
    llm_model_url: str = ""  # From LLM_MODEL_URL
    
    # HuggingFace Cache Configuration - For offline mode
    hf_cache_dir: str = "data/models/hf_cache"  # From HF_CACHE_DIR in .env
    hf_hub_offline: str = "1"  # From HF_HUB_OFFLINE in .env (forces local-only)
    transformers_offline: str = "1"  # From TRANSFORMERS_OFFLINE in .env
    
    # Model Settings - Performance tuned for Intel 12700H + Legal domain
    max_tokens: int = 2048  # From MAX_TOKENS in .env
    temperature: float = 0.1  # From TEMPERATURE in .env (low for accuracy)
    context_length: int = 8192  # From CONTEXT_LENGTH in .env (large context)
    n_ctx: int = 8192  # From N_CTX in .env (must match context_length)
    n_threads: int = 6  # From N_THREADS in .env (6 P-cores of 12700H)
    n_gpu_layers: int = -1  # From N_GPU_LAYERS in .env (-1 = all on GPU)
    n_batch: int = 512  # From N_BATCH in .env (batch size for processing)
    
    # RAG Configuration - Document processing parameters
    chunk_size: int = 800  # From CHUNK_SIZE in .env
    chunk_overlap: int = 200  # From CHUNK_OVERLAP in .env
    
    # Enhanced RAG Process Parameters - 4-step RAG: Search > Rerank > Expand > Synthesize
    broad_search_k: int = 12  # Optimized from 20 to 12 for better performance
    similarity_threshold: float = 0.3  # From SIMILARITY_THRESHOLD in .env (permissive)
    context_expansion_size: int = 1  # From CONTEXT_EXPANSION_SIZE in .env (adjacent chunks)
    use_routing: bool = True  # From USE_ROUTING in .env (smart collection routing)
    use_reranker: bool = True  # From USE_RERANKER in .env (Vietnamese reranking)
    
    # ChromaDB Configuration
    chroma_collection_name: str = "legal_documents"  # From CHROMA_COLLECTION_NAME in .env
    chroma_persist_directory: str = "data/vectordb"  # From VECTORDB_DIR in .env
    
    # Search Configuration - Default values for methods (can be overridden)
    default_search_top_k: int = 5  # From DEFAULT_SEARCH_TOP_K in .env
    default_similarity_threshold: float = 0.5  # Tăng từ 0.3 để giảm số chunks cần rerank (Performance Optimization)
    cross_collection_similarity_threshold: float = 0.7  # From CROSS_COLLECTION_SIMILARITY_THRESHOLD in .env
    query_router_top_k: int = 2  # From QUERY_ROUTER_TOP_K in .env
    best_collection_top_k: int = 1  # From BEST_COLLECTION_TOP_K in .env
    collections_top_k: int = 3  # From COLLECTIONS_TOP_K in .env
    
    # Computed Properties
    @property
    def base_dir(self) -> Path:
        return Path(__file__).parent.parent.parent  # backend/app/core -> backend
    
    @property 
    def data_path(self) -> Path:
        return self.base_dir / self.data_root_dir
    
    @property
    def documents_path(self) -> Path:
        return self.base_dir / self.documents_dir
    
    @property 
    def vectordb_path(self) -> Path:
        return self.base_dir / self.vectordb_dir
    
    @property
    def models_path(self) -> Path:
        return self.base_dir / self.models_dir
    
    @property
    def hf_cache_path(self) -> Path:
        return self.base_dir / self.hf_cache_dir
    
    @property
    def llm_model_file_path(self) -> Path:
        return self.base_dir / self.llm_model_path
    
    def setup_environment(self):
        """Setup environment variables for models"""
        hf_cache_abs = str(self.hf_cache_path.absolute())
        # Use HF_HOME instead of deprecated TRANSFORMERS_CACHE
        os.environ['HF_HOME'] = hf_cache_abs
        os.environ['HF_HUB_CACHE'] = str(self.hf_cache_path.absolute() / "hub")
        os.environ['HF_DATASETS_CACHE'] = hf_cache_abs
        os.environ['HF_HUB_OFFLINE'] = self.hf_hub_offline
        os.environ['TRANSFORMERS_OFFLINE'] = self.transformers_offline
        # Remove deprecated TRANSFORMERS_CACHE if set
        if 'TRANSFORMERS_CACHE' in os.environ:
            del os.environ['TRANSFORMERS_CACHE']
    
    class Config:
        env_file = '.env'
        case_sensitive = False
        protected_namespaces = ('settings_',)

# Create global settings instance
settings = Settings()

# Setup environment on import
settings.setup_environment()
