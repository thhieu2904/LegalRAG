"""
Auto Model Loader - Tự động tải models khi khởi động
Không cần can thiệp thủ công, models sẽ được tải tự động nếu chưa có
"""

import os
import sys
import requests
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logger = logging.getLogger(__name__)

def ensure_model_exists(model_path: Path, download_url: str, model_name: str) -> bool:
    """Đảm bảo model tồn tại, tự động download nếu chưa có"""
    
    if model_path.exists():
        file_size = model_path.stat().st_size / (1024 * 1024)  # MB
        logger.info(f"✅ Model {model_name} already exists ({file_size:.1f}MB): {model_path}")
        return True
    
    logger.info(f"📥 Downloading {model_name} to {model_path}")
    
    try:
        # Tạo thư mục nếu cần
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download với progress
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(model_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Log progress every 100MB
                    if downloaded % (100 * 1024 * 1024) == 0:
                        progress = (downloaded / total_size * 100) if total_size > 0 else 0
                        logger.info(f"   Progress: {progress:.1f}% ({downloaded/(1024*1024):.1f}MB)")
        
        file_size = model_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Downloaded {model_name} successfully ({file_size:.1f}MB)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download {model_name}: {e}")
        if model_path.exists():
            model_path.unlink()
        return False

def ensure_huggingface_model(model_name: str) -> bool:
    """Đảm bảo HuggingFace model tồn tại, tự động download nếu chưa có"""
    
    try:
        if "Vietnamese_Embedding" in model_name:
            logger.info(f"📥 Loading embedding model: {model_name}")
            from sentence_transformers import SentenceTransformer
            
            # Kiểm tra xem model đã tải chưa
            try:
                model = SentenceTransformer(model_name, device='cpu')  # Load CPU first
                logger.info(f"✅ Embedding model loaded: {model_name}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model {model_name}: {e}")
                return False
                
        elif "Vietnamese_Reranker" in model_name:
            logger.info(f"📥 Loading reranker model: {model_name}")
            from transformers import AutoTokenizer, AutoModel
            
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModel.from_pretrained(model_name)
                logger.info(f"✅ Reranker model loaded: {model_name}")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to load reranker model {model_name}: {e}")
                return False
                
    except ImportError as e:
        logger.error(f"❌ Missing dependencies for {model_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error loading {model_name}: {e}")
        return False
    
    return False

def auto_setup_models(settings) -> dict:
    """
    Tự động setup tất cả models cần thiết
    Returns: Dictionary với status của từng model
    """
    
    logger.info("🚀 Starting automatic models setup...")
    
    results = {
        'llm_model': False,
        'embedding_model': False, 
        'reranker_model': False,
        'all_success': False
    }
    
    # 1. LLM Model (.gguf file) - use correct settings properties
    llm_path = Path(settings.llm_model_path)
    results['llm_model'] = ensure_model_exists(
        llm_path, 
        settings.llm_model_url, 
        f"PhoGPT LLM ({llm_path.name})"
    )
    
    # 2. Embedding Model (HuggingFace)
    results['embedding_model'] = ensure_huggingface_model(settings.embedding_model_name)
    
    # 3. Reranker Model (HuggingFace) - Optional for now
    results['reranker_model'] = ensure_huggingface_model(settings.reranker_model_name)
    
    # Check overall success (LLM + Embedding required, Reranker optional)
    required_models = results['llm_model'] and results['embedding_model']
    results['all_success'] = required_models
    
    if results['all_success']:
        logger.info("🎉 All required models are ready!")
    else:
        logger.warning("⚠️  Some required models failed to load. System may not work properly.")
    
    return results
