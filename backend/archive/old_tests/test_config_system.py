#!/usr/bin/env python3
"""
Test script for centralized config system
"""
import logging
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_config():
    """Test config system"""
    print("🧪 Testing Centralized Config System")
    print("=" * 50)
    
    # Test config loading
    try:
        from app.core.config import settings
        print("✅ Config loaded successfully")
        
        print(f"📋 Embedding model: {settings.embedding_model_name}")
        print(f"📋 Temperature: {settings.temperature}")
        print(f"📋 Context length: {settings.context_length}")  
        print(f"📋 N Threads: {settings.n_threads}")
        print(f"📋 Default search top_k: {settings.default_search_top_k}")
        print(f"📋 Default similarity threshold: {settings.default_similarity_threshold}")
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False
    
    print()
    return True

def test_vectordb_offline():
    """Test VectorDB with offline embedding model"""
    print("🔧 Testing VectorDB with Offline Embedding Model")
    print("=" * 50)
    
    try:
        # Check if model exists locally
        from app.core.config import settings
        
        model_path = settings.hf_cache_path / "hub" / "models--AITeamVN--Vietnamese_Embedding_v2"
        print(f"📁 Checking model path: {model_path}")
        print(f"📁 Model exists locally: {model_path.exists()}")
        
        if model_path.exists():
            snapshots = list((model_path / "snapshots").iterdir())
            if snapshots:
                print(f"📁 Found snapshot: {snapshots[0].name}")
                model_files = list(snapshots[0].iterdir())
                print(f"📁 Model files: {len(model_files)}")
        
        # Test environment variables
        print(f"🌍 HF_HOME: {os.environ.get('HF_HOME')}")
        print(f"🌍 HF_HUB_OFFLINE: {os.environ.get('HF_HUB_OFFLINE')}")
        print(f"🌍 TRANSFORMERS_OFFLINE: {os.environ.get('TRANSFORMERS_OFFLINE')}")
        
        # Try loading embedding model with explicit local path
        print("\n🔄 Testing embedding model loading...")
        from sentence_transformers import SentenceTransformer
        
        # Use the explicit local path
        local_model_path = str(model_path / "snapshots" / snapshots[0].name) if snapshots else settings.embedding_model_name
        print(f"📥 Loading from: {local_model_path}")
        
        # Force local loading
        embedding_model = SentenceTransformer(settings.embedding_model_name, local_files_only=True)
        print("✅ Embedding model loaded successfully (local)")
        
        # Test encoding
        test_embeddings = embedding_model.encode(["test sentence"])
        print(f"✅ Test embedding shape: {test_embeddings.shape}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ VectorDB test failed: {e}")
        return False

def test_query_router():
    """Test QueryRouter with config defaults"""
    print("🧭 Testing QueryRouter with Config Defaults")
    print("=" * 50)
    
    try:
        from app.services.query_router import QueryRouter
        from app.core.config import settings
        
        router = QueryRouter()
        print("✅ QueryRouter loaded")
        
        # Test routing with config defaults
        routes = router.route_query("đăng ký kết hôn")  # No top_k parameter
        print(f"✅ Route results: {len(routes)} routes (using config default: {settings.query_router_top_k})")
        
        for collection, score in routes:
            print(f"   - {collection}: {score:.3f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ QueryRouter test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Config System Tests")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Config system
    all_passed &= test_config()
    print()
    
    # Test 2: VectorDB with offline models
    all_passed &= test_vectordb_offline()  
    print()
    
    # Test 3: QueryRouter
    all_passed &= test_query_router()
    print()
    
    # Final result
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Centralized config system working perfectly!")
        print("🎯 All defaults now managed via .env file!")
    else:
        print("❌ Some tests failed")
        
    return all_passed

if __name__ == "__main__":
    main()
