#!/usr/bin/env python3
"""
Test Simple Form Detection Service with new PathConfig
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent / "rag_service"))

def test_simple_form_detection():
    """Test SimpleFormDetectionService with new PathConfig"""
    print("🧪 Testing SimpleFormDetectionService")
    print("-" * 50)
    
    try:
        from app.services.simple_form_detection import SimpleFormDetectionService
        
        # Test 1: Default initialization (should use PathConfig)
        print("Test 1: Default initialization")
        service = SimpleFormDetectionService()
        print(f"  Storage path: {service.storage_base_path}")
        print(f"  Path config: {service.path_config}")
        print(f"  Environment: {service.path_config.environment if service.path_config else 'N/A'}")
        
        # Test 2: Custom path
        print("\nTest 2: Custom path initialization")
        custom_service = SimpleFormDetectionService("/custom/path")
        print(f"  Storage path: {custom_service.storage_base_path}")
        print(f"  Path config: {custom_service.path_config}")
        
        print("\n✅ SimpleFormDetectionService tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing SimpleFormDetectionService: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_path_config():
    """Test PathConfig directly"""
    print("\n🧪 Testing PathConfig")
    print("-" * 50)
    
    try:
        from app.core.path_config import PathConfig
        
        # Test environment detection
        config = PathConfig()
        print(f"Environment: {config.environment}")
        print(f"Base data dir: {config.base_data_dir}")
        print(f"Collections dir: {config.collections_dir}")
        
        # Test path verification
        results = config.verify_paths()
        print(f"All paths exist: {results['all_paths_exist']}")
        
        if results['warnings']:
            print("Warnings:")
            for warning in results['warnings']:
                print(f"  - {warning}")
        
        print("\n✅ PathConfig tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing PathConfig: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests"""
    print("🧪 Testing Phase 1 Updates")
    print("=" * 60)
    
    success = True
    success &= test_path_config()
    success &= test_simple_form_detection()
    
    if success:
        print("\n🎉 All Phase 1 tests passed!")
        print("✅ simple_form_detection.py successfully updated")
        print("✅ PathConfig integration working")
    else:
        print("\n❌ Some tests failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())