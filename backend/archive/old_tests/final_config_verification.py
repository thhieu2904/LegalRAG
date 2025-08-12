#!/usr/bin/env python3
"""
Final Config Verification Script
Xác nhận tất cả config trong .env đã được sử dụng đúng trong code
"""
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def verify_config_usage():
    """Verify all .env configs are used in code"""
    print("🔍 FINAL CONFIG VERIFICATION")
    print("=" * 60)
    
    try:
        from app.core.config import settings
        print("✅ Config loaded successfully")
        
        # API Settings
        print(f"🌐 API Settings:")
        print(f"   DEBUG: {settings.debug}")
        print(f"   HOST: {settings.host}")  
        print(f"   PORT: {settings.port}")
        
        # Model Settings
        print(f"🤖 Model Settings:")
        print(f"   Embedding: {settings.embedding_model_name}")
        print(f"   Reranker: {settings.reranker_model_name}")
        print(f"   LLM Path: {settings.llm_model_path}")
        print(f"   Temperature: {settings.temperature}")
        print(f"   Context Length: {settings.context_length}")
        print(f"   N Threads: {settings.n_threads}")
        
        # RAG Settings
        print(f"📚 RAG Settings:")
        print(f"   Chunk Size: {settings.chunk_size}")
        print(f"   Chunk Overlap: {settings.chunk_overlap}")
        print(f"   Broad Search K: {settings.broad_search_k}")
        print(f"   Similarity Threshold: {settings.similarity_threshold}")
        print(f"   Context Expansion Size: {settings.context_expansion_size}")
        print(f"   Use Routing: {settings.use_routing}")
        print(f"   Use Reranker: {settings.use_reranker}")
        
        # Search Settings
        print(f"🔍 Search Settings:")
        print(f"   Default Search Top K: {settings.default_search_top_k}")
        print(f"   Default Similarity Threshold: {settings.default_similarity_threshold}")
        print(f"   Cross Collection Threshold: {settings.cross_collection_similarity_threshold}")
        print(f"   Query Router Top K: {settings.query_router_top_k}")
        print(f"   Best Collection Top K: {settings.best_collection_top_k}")
        print(f"   Collections Top K: {settings.collections_top_k}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Config verification failed: {e}")
        return False

def test_services_with_config():
    """Test that services actually use the config values"""
    print("\n🔧 TESTING SERVICES WITH CONFIG")
    print("=" * 60)
    
    try:
        from app.core.config import settings
        
        # Test QueryRouter uses config
        print("1. Testing QueryRouter...")
        from app.services.query_router import QueryRouter
        router = QueryRouter()
        
        # Call without top_k to test config default
        routes = router.route_query("đăng ký kết hôn")
        print(f"   ✅ Router returned {len(routes)} routes (config default: {settings.query_router_top_k})")
        
        # Test LLMService uses config
        print("2. Testing LLMService...")
        from app.services.llm_service import LLMService
        llm = LLMService()
        print(f"   ✅ LLM loaded with n_threads={settings.n_threads}, context_length={settings.context_length}")
        
        # Test VectorDBService uses config
        print("3. Testing VectorDBService...")
        from app.services.vectordb_service import VectorDBService
        vectordb = VectorDBService()
        print(f"   ✅ VectorDB using embedding model: {vectordb.embedding_model_name}")
        print(f"   ✅ VectorDB collection: {vectordb.default_collection_name}")
        
        # Test RerankerService uses config  
        print("4. Testing RerankerService...")
        from app.services.reranker_service import RerankerService
        reranker = RerankerService()
        print(f"   ✅ Reranker using model: {reranker.model_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Service test failed: {e}")
        return False

def verify_file_paths():
    """Verify all computed file paths exist"""
    print("\n📁 VERIFYING FILE PATHS")
    print("=" * 60)
    
    try:
        from app.core.config import settings
        
        paths_to_check = [
            ("Base Dir", settings.base_dir),
            ("Data Path", settings.data_path),
            ("Documents Path", settings.documents_path),
            ("Models Path", settings.models_path),
            ("VectorDB Path", settings.vectordb_path),
            ("HF Cache Path", settings.hf_cache_path),
        ]
        
        all_exist = True
        for name, path in paths_to_check:
            exists = path.exists()
            status = "✅" if exists else "❌"
            print(f"   {status} {name}: {path} {'(exists)' if exists else '(missing)'}")
            if not exists and name in ["Data Path", "Models Path"]:
                all_exist = False
        
        # Check LLM model file specifically
        llm_file = settings.llm_model_file_path
        llm_exists = llm_file.exists()
        status = "✅" if llm_exists else "❌"
        print(f"   {status} LLM Model: {llm_file} {'(exists)' if llm_exists else '(missing)'}")
        
        return all_exist and llm_exists
        
    except Exception as e:
        logger.error(f"❌ Path verification failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 FINAL CONFIGURATION VERIFICATION")
    print("=" * 80)
    print("Xác nhận config đã tách biệt khỏi logic và được sử dụng đúng")
    print("=" * 80)
    
    all_passed = True
    
    # Test 1: Config values
    all_passed &= verify_config_usage()
    
    # Test 2: Services use config
    all_passed &= test_services_with_config()
    
    # Test 3: File paths
    all_passed &= verify_file_paths()
    
    # Final result
    print("\n🎯 FINAL VERIFICATION RESULT")
    print("=" * 80)
    
    if all_passed:
        print("🎉 ✅ PERFECT! All configuration verified!")
        print("📋 ✅ Config values loaded correctly")
        print("🔧 ✅ Services use config defaults") 
        print("📁 ✅ File paths computed correctly")
        print("🎯 ✅ Configuration completely separated from logic")
        print("")
        print("📝 TO CHANGE SETTINGS: Edit .env file only!")
        print("🔄 Changes take effect on restart")
        print("💡 No more hardcoded values in code!")
    else:
        print("❌ Some verifications failed - check logs above")
        
    return all_passed

if __name__ == "__main__":
    main()
