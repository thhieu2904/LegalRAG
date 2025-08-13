#!/usr/bin/env python3
"""
Download Models Script for LegalRAG
Tải về các models cần thiết cho hệ thống LegalRAG
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

import logging
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer
import torch

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment variables for model download"""
    # Đảm bảo HF_HOME được set
    hf_home = os.environ.get('HF_HOME', 'D:\\AI_Models\\huggingface')
    os.environ['HF_HOME'] = hf_home
    os.environ['HUGGINGFACE_HUB_CACHE'] = hf_home
    
    # Tạo thư mục nếu chưa có
    os.makedirs(hf_home, exist_ok=True)
    
    logger.info(f"🏠 HF_HOME: {hf_home}")
    return hf_home

def download_embedding_model():
    """Download Vietnamese embedding model"""
    model_name = "AITeamVN/Vietnamese_Embedding_v2"
    logger.info(f"📥 Downloading embedding model: {model_name}")
    
    try:
        # Download model files
        cache_dir = snapshot_download(
            repo_id=model_name,
            cache_dir=None,  # Use default cache
            local_files_only=False,
            resume_download=True
        )
        logger.info(f"✅ Downloaded to: {cache_dir}")
        
        # Test loading
        logger.info("🧪 Testing model loading...")
        model = SentenceTransformer(model_name)
        test_text = "Đây là một câu thử nghiệm"
        embedding = model.encode([test_text])
        logger.info(f"✅ Model loaded successfully! Embedding shape: {embedding.shape}")
        
        # Clear model from memory
        del model
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download embedding model: {e}")
        return False

def download_reranker_model():
    """Download Vietnamese reranker model"""
    model_name = "AITeamVN/Vietnamese_Reranker"
    logger.info(f"📥 Downloading reranker model: {model_name}")
    
    try:
        # Download model files
        cache_dir = snapshot_download(
            repo_id=model_name,
            cache_dir=None,  # Use default cache
            local_files_only=False,
            resume_download=True
        )
        logger.info(f"✅ Downloaded to: {cache_dir}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download reranker model: {e}")
        return False

def main():
    """Main function to download all models"""
    logger.info("🚀 LEGALRAG MODELS DOWNLOAD")
    logger.info("=" * 60)
    
    # Setup environment
    hf_home = setup_environment()
    
    # Download models
    success = True
    
    logger.info("\n📦 DOWNLOADING EMBEDDING MODEL")
    logger.info("-" * 40)
    if not download_embedding_model():
        success = False
    
    logger.info("\n📦 DOWNLOADING RERANKER MODEL")
    logger.info("-" * 40)
    if not download_reranker_model():
        success = False
    
    # Final result
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✅ ALL MODELS DOWNLOADED SUCCESSFULLY!")
        logger.info("💡 You can now run the main application")
    else:
        logger.info("❌ SOME MODELS FAILED TO DOWNLOAD")
        logger.info("💡 Please check your internet connection and try again")
    
    return success

if __name__ == "__main__":
    main()
