#!/usr/bin/env python3
"""
Models Setup Tool for LegalRAG
===============================

Tool setup models dựa trên fresh_install_setup.py và config.py:
- Tạo directory structure theo config từ fresh_install_setup.py
- Check và load models từ config settings
- Download missing models nếu cần (như fresh_install_setup.py)
- Test model functionality

Usage:
    cd backend
    python tools/1_setup_models.py
    python tools/1_setup_models.py --verify-only  # Chỉ kiểm tra
"""

import sys
import os
from pathlib import Path
import logging
import argparse

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directory_structure():
    """Tạo cấu trúc thư mục cần thiết - từ fresh_install_setup.py"""
    logger.info("📁 SETTING UP DIRECTORY STRUCTURE")
    logger.info("-" * 40)
    
    required_dirs = [
        'data',
        'data/documents',
        'data/models',
        'data/models/hf_cache',
        'data/models/llm_dir', 
        'data/vectordb',
        'data/cache',
        'data/router_examples'
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"   ✅ Created: {dir_path}")
            created_count += 1
        else:
            logger.info(f"   ✅ Exists: {dir_path}")
    
    if created_count > 0:
        logger.info(f"📁 Created {created_count} new directories")
    else:
        logger.info("📁 All required directories already exist")
    
    logger.info("")

def check_and_setup_models(verify_only: bool = False):
    """Kiểm tra và setup AI models - từ fresh_install_setup.py"""
    logger.info("🤖 CHECKING AI MODELS")
    logger.info("-" * 40)
    
    try:
        from app.core.config import settings
        settings.setup_environment()
        
        # Ensure models directory exists
        models_cache_dir = settings.hf_cache_path
        models_cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"   📁 Models cache directory: {models_cache_dir}")
        
        # Check embedding model
        logger.info("   📊 Embedding Model:")
        try:
            from sentence_transformers import SentenceTransformer
            # Use cache directory for download/load
            embedding_model = SentenceTransformer(
                settings.embedding_model_name,
                cache_folder=str(models_cache_dir)
            )
            logger.info(f"      ✅ {settings.embedding_model_name} loaded successfully")
            
            # Test với một câu
            test_embedding = embedding_model.encode("test sentence")
            logger.info(f"      📊 Embedding dimension: {len(test_embedding)}")
        except Exception as e:
            logger.error(f"      ❌ Error loading embedding model: {e}")
            if not verify_only:
                logger.info("      💡 Attempting to download...")
                try:
                    from sentence_transformers import SentenceTransformer
                    SentenceTransformer(
                        settings.embedding_model_name,
                        cache_folder=str(models_cache_dir)
                    )
                    logger.info("      ✅ Download successful!")
                except Exception as e2:
                    logger.error(f"      ❌ Download failed: {e2}")
                    return False
            else:
                return False
        
        # Check reranker model  
        logger.info("   🎯 Reranker Model:")
        try:
            from sentence_transformers import CrossEncoder
            # Use cache directory for download/load
            reranker_model = CrossEncoder(
                settings.reranker_model_name,
                cache_folder=str(models_cache_dir)
            )
            logger.info(f"      ✅ {settings.reranker_model_name} loaded successfully")
            
            # Test với một cặp câu
            test_scores = reranker_model.predict([("query test", "document test")])
            logger.info(f"      📊 Test score: {test_scores[0]:.3f}")
        except Exception as e:
            logger.error(f"      ❌ Error loading reranker model: {e}")
            if not verify_only:
                logger.info("      💡 Attempting to download...")
                try:
                    from sentence_transformers import CrossEncoder
                    CrossEncoder(
                        settings.reranker_model_name,
                        cache_folder=str(models_cache_dir)
                    )
                    logger.info("      ✅ Download successful!")
                except Exception as e2:
                    logger.error(f"      ❌ Download failed: {e2}")
                    return False
            else:
                return False
        
        # Check LLM model
        logger.info("   🧠 LLM Model:")
        llm_path = settings.llm_model_file_path  # Use the property that returns absolute path
        llm_dir = llm_path.parent
        
        if llm_path.exists():
            file_size_mb = llm_path.stat().st_size / (1024 * 1024)
            logger.info(f"      ✅ LLM model found: {llm_path}")
            logger.info(f"      📊 File size: {file_size_mb:.1f}MB")
        else:
            logger.error(f"      ❌ LLM model not found: {llm_path}")
            if not verify_only and settings.llm_model_url:
                logger.info("      💡 Attempting to download LLM model...")
                try:
                    # Create LLM directory if needed
                    llm_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Download using requests or wget
                    import requests
                    import shutil
                    
                    logger.info(f"      📥 Downloading from: {settings.llm_model_url}")
                    response = requests.get(settings.llm_model_url, stream=True)
                    response.raise_for_status()
                    
                    with open(llm_path, 'wb') as f:
                        shutil.copyfileobj(response.raw, f)
                    
                    file_size_mb = llm_path.stat().st_size / (1024 * 1024)
                    logger.info(f"      ✅ Download successful! Size: {file_size_mb:.1f}MB")
                    
                except Exception as e:
                    logger.error(f"      ❌ Download failed: {e}")
                    logger.info("      💡 Please manually download the LLM model")
                    return False
            else:
                logger.info("      💡 Please set LLM_MODEL_URL in .env or download manually")
                return False
        
        logger.info("   ✅ All models available!")
        logger.info("")
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Error checking models: {e}")
        return False

def verify_model_environment():
    """Verify environment variables được set đúng"""
    logger.info("🔧 VERIFYING MODEL ENVIRONMENT")
    logger.info("-" * 40)
    
    env_vars = {
        'HF_HOME': os.environ.get('HF_HOME'),
        'HF_HUB_CACHE': os.environ.get('HF_HUB_CACHE'),
        'HF_HUB_OFFLINE': os.environ.get('HF_HUB_OFFLINE'),
        'TRANSFORMERS_OFFLINE': os.environ.get('TRANSFORMERS_OFFLINE')
    }
    
    for var, value in env_vars.items():
        if value:
            logger.info(f"   ✅ {var}: {value}")
        else:
            logger.warning(f"   ⚠️  {var}: Not set")
    
    # Check if HF cache directory exists and has content
    hf_home = env_vars.get('HF_HOME')
    if hf_home and Path(hf_home).exists():
        hf_cache = Path(hf_home)
        cached_models = list(hf_cache.rglob('**/config.json'))
        logger.info(f"   📊 Cached models found: {len(cached_models)}")
    else:
        logger.warning("   ⚠️  HF cache directory not found")
    
    logger.info("")

def main():
    parser = argparse.ArgumentParser(
        description='Complete Models Setup for LegalRAG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/1_setup_models.py             # Full setup with downloads
  python tools/1_setup_models.py --verify    # Verify only, no downloads

This tool will:
1. Create required directory structure from fresh_install_setup.py
2. Setup HuggingFace environment variables  
3. Check and download Vietnamese embedding models
4. Verify LLM model availability
5. Test model functionality
        """
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing models, do not download'
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 LEGALRAG MODELS SETUP")
    logger.info("=" * 60)
    logger.info("This tool will setup the complete model environment")
    logger.info("")
    
    # Step 1: Directory structure
    setup_directory_structure()
    
    # Step 2: Verify environment
    verify_model_environment()
    
    # Step 3: Check models
    if not check_and_setup_models(verify_only=args.verify_only):
        logger.error("❌ SETUP FAILED: Models not available!")
        logger.info("💡 Please check your internet connection and try again")
        return False
    
    logger.info("🎉 SETUP COMPLETED SUCCESSFULLY!")
    logger.info("=" * 60)
    logger.info("✅ Directory structure created")
    logger.info("✅ Models loaded and tested")
    logger.info("✅ Environment verified")
    logger.info("")
    logger.info("🚀 Your model environment is ready!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
