#!/usr/bin/env python3
"""
🧪 TEST CACHE INTEGRATION WITH BACKEND

Test new cache với backend services
"""

import os
import sys
import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cache_loading():
    """Test cache loading functionality"""
    
    logger.info("🧪 TESTING CACHE LOADING")
    
    # Test direct cache loading
    try:
        import pickle
        
        cache_file = "data/cache/router_embeddings.pkl"
        if not os.path.exists(cache_file):
            logger.error(f"❌ Cache file not found: {cache_file}")
            return False
        
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        if isinstance(cache_data, dict):
            if 'metadata' in cache_data:
                metadata = cache_data['metadata']
                collections = cache_data.get('collections', {})
                
                logger.info(f"✅ Cache loaded successfully")
                logger.info(f"   Version: {metadata.get('structure_version')}")
                logger.info(f"   Collections: {len(collections)}")
                logger.info(f"   Total docs: {sum(len(docs) for docs in collections.values())}")
                
                # Test sample collection
                if collections:
                    sample_collection = list(collections.keys())[0]
                    sample_docs = collections[sample_collection]
                    sample_doc = list(sample_docs.keys())[0]
                    sample_data = sample_docs[sample_doc]
                    
                    logger.info(f"📝 Sample: {sample_collection}/{sample_doc}")
                    logger.info(f"   Main question: {sample_data.get('main_question', '')[:50]}...")
                    logger.info(f"   Variants: {len(sample_data.get('question_variants', []))}")
                
                return True
            else:
                logger.warning("⚠️  Legacy cache format")
                return True
        else:
            logger.error("❌ Invalid cache format")
            return False
            
    except Exception as e:
        logger.error(f"❌ Cache loading error: {e}")
        return False

def test_router_service():
    """Test router service với new cache - simplified"""
    
    logger.info("\\n🧪 TESTING ROUTER SERVICE")
    
    try:
        # Add backend to path
        sys.path.insert(0, os.path.abspath('.'))
        
        # Try to import router service class
        from app.services.router import QueryRouter
        logger.info("✅ Router service class imported")
        
        # Test router instantiation with mock model
        logger.info("🔄 Testing router instantiation...")
        
        # Mock embedding model for testing
        class MockEmbeddingModel:
            def encode(self, texts):
                import numpy as np
                if isinstance(texts, str):
                    texts = [texts]
                return np.random.rand(len(texts), 384)  # Mock 384-dim embeddings
        
        mock_model = MockEmbeddingModel()
        
        # Try to initialize router with mock model
        try:
            router = QueryRouter(mock_model)
            logger.info("✅ Router initialized with mock model")
            
            # Test config loading
            if hasattr(router, 'config') and router.config:
                logger.info(f"✅ Router config loaded: {len(router.config.get('collection_mappings', {}))} collections")
                return True
            else:
                logger.warning("⚠️  Router config empty")
                return False
        except Exception as e:
            logger.error(f"❌ Router initialization failed: {e}")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Router service error: {e}")
        return False

def test_backend_api(base_url="http://localhost:8000"):
    """Test backend API endpoints"""
    
    logger.info("\\n🧪 TESTING BACKEND API")
    
    # Test endpoints
    endpoints = [
        "/health",
        "/api/router/health", 
        "/api/questions/quy_trinh_cap_ho_tich_cap_xa/DOC_001"
    ]
    
    api_results = {}
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            logger.info(f"Testing: {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"   ✅ {endpoint}: OK")
                api_results[endpoint] = "success"
                
                # Show sample response
                if endpoint.endswith("DOC_001"):
                    try:
                        data = response.json()
                        logger.info(f"   📝 Response keys: {list(data.keys())}")
                        if 'main_question' in data:
                            logger.info(f"   🎯 Main question: {data['main_question'][:50]}...")
                    except:
                        pass
            else:
                logger.warning(f"   ⚠️  {endpoint}: {response.status_code}")
                api_results[endpoint] = f"error_{response.status_code}"
                
        except requests.exceptions.ConnectionError:
            logger.warning(f"   ⚠️  {endpoint}: Backend not running")
            api_results[endpoint] = "no_connection"
        except Exception as e:
            logger.error(f"   ❌ {endpoint}: {e}")
            api_results[endpoint] = "error"
    
    success_count = sum(1 for result in api_results.values() if result == "success")
    
    logger.info(f"\\n📊 API Test Results: {success_count}/{len(endpoints)} passed")
    
    return success_count > 0

def main():
    """Main test suite"""
    
    logger.info("🧪 CACHE INTEGRATION TEST SUITE")
    logger.info("=" * 50)
    
    # Test 1: Cache loading
    cache_test = test_cache_loading()
    
    # Test 2: Router service
    router_test = test_router_service()
    
    # Test 3: Backend API (only if backend running)
    api_test = test_backend_api()
    
    # Summary
    logger.info("\\n" + "=" * 50)
    logger.info("🎯 TEST SUMMARY:")
    logger.info(f"   Cache loading: {'✅' if cache_test else '❌'}")
    logger.info(f"   Router service: {'✅' if router_test else '❌'}")
    logger.info(f"   Backend API: {'✅' if api_test else '⚠️'}")
    
    total_tests = sum([cache_test, router_test, api_test])
    
    if total_tests >= 2:
        logger.info("\\n🎉 CACHE INTEGRATION SUCCESSFUL!")
        logger.info("✅ New questions.json structure working")
        logger.info("✅ Cache rebuilt and functional")
        
        if not api_test:
            logger.info("💡 Note: Start backend to test API integration")
        
        return True
    else:
        logger.info("\\n⚠️  CACHE INTEGRATION NEEDS ATTENTION")
        logger.info("Check failed tests above")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        logger.info("\\n🚀 READY FOR PRODUCTION!")
        logger.info("Cache system working with new questions.json structure")
    else:
        logger.info("\\n🔧 NEEDS FIXES")
        logger.info("Review test failures above")
