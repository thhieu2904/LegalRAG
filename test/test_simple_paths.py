#!/usr/bin/env python3
"""
Simple Path Test Script
=======================
Quick test to verify path resolution works correctly
Can be run immediately to check current status
"""

import os
import sys
from pathlib import Path

def test_current_paths():
    """Test current path calculation patterns"""
    print("🔍 Testing Current Path Patterns")
    print("-" * 50)
    
    # Get current script location
    script_path = Path(__file__).resolve()
    print(f"Script location: {script_path}")
    
    # Test the pattern used in the services
    # From test/ -> rag_service/
    current_base = script_path.parent.parent
    print(f"Calculated base (rag_service): {current_base}")
    
    # From app/services/ -> rag_service/ (simulated)
    simulated_service_file = current_base / "app" / "services" / "simple_form_detection.py"
    simulated_base = simulated_service_file.parent.parent.parent
    print(f"Simulated service base: {simulated_base}")
    
    # Data paths
    data_path = current_base / "data"
    storage_path = data_path / "storage"
    collections_path = storage_path / "collections"
    
    print(f"Data path: {data_path}")
    print(f"Storage path: {storage_path}")
    print(f"Collections path: {collections_path}")
    
    # Check existence
    paths_to_check = {
        "Base": current_base,
        "Data": data_path,
        "Storage": storage_path,
        "Collections": collections_path
    }
    
    print("\nPath existence check:")
    for name, path in paths_to_check.items():
        exists = path.exists()
        is_dir = path.is_dir() if exists else False
        status = "✅" if exists and is_dir else "❌"
        print(f"  {status} {name}: {path}")
    
    print()

def test_windows_vs_docker_paths():
    """Compare Windows vs Docker path calculations"""
    print("🖥️ Windows vs Docker Path Comparison")
    print("-" * 50)
    
    # Current Windows environment
    current_file = Path(__file__).resolve()
    windows_base = current_file.parent.parent
    windows_data = windows_base / "data" / "storage" / "collections"
    
    # Simulated Docker environment
    docker_file = Path("/app/app/services/simple_form_detection.py")
    docker_base = docker_file.parent.parent.parent  # /app
    docker_data = docker_base / "data" / "storage" / "collections"
    
    print("Windows calculation:")
    print(f"  File: {current_file}")
    print(f"  Base: {windows_base}")
    print(f"  Collections: {windows_data}")
    
    print("\nDocker calculation:")
    print(f"  File: {docker_file}")
    print(f"  Base: {docker_base}")
    print(f"  Collections: {docker_data}")
    
    print(f"\nDocker mount: ./rag_service/data:/app/data")
    print(f"Expected Docker collections path: /app/data/storage/collections")
    print(f"Calculated Docker collections path: {docker_data}")
    print(f"Paths match: {str(docker_data) == '/app/data/storage/collections'}")
    
    print()

def test_problematic_windows_path():
    """Test the problematic Windows path replacement from context.py"""
    print("⚠️ Testing Problematic Windows Path Logic")
    print("-" * 50)
    
    # This is the problematic line from context.py:
    # alternative_path = str(source_file_path).replace("D:\\Personal\\LegalRAG_OCR\\rag_service\\..\\", "D:\\Personal\\LegalRAG_OCR\\")
    
    test_path = "D:\\Personal\\LegalRAG_OCR\\rag_service\\..\\data\\storage\\collections\\test.json"
    problematic_replacement = test_path.replace("D:\\Personal\\LegalRAG_OCR\\rag_service\\..\\", "D:\\Personal\\LegalRAG_OCR\\")
    
    print(f"Original path: {test_path}")
    print(f"After replacement: {problematic_replacement}")
    print(f"Problem: This is Windows-specific and will fail in Docker")
    
    # Better approach
    better_path = Path(test_path).resolve()
    print(f"Better approach: {better_path}")
    
    # Docker equivalent
    docker_equivalent = "/app/data/storage/collections/test.json"
    print(f"Docker equivalent: {docker_equivalent}")
    
    print()

def test_environment_detection():
    """Test simple environment detection"""
    print("🌍 Testing Environment Detection")
    print("-" * 50)
    
    # Check various indicators
    indicators = {
        "PYTHONPATH": os.getenv("PYTHONPATH"),
        "Current working directory": str(Path.cwd()),
        "Script location": str(Path(__file__)),
        "Platform": os.name,
        "Environment var ENVIRONMENT": os.getenv("ENVIRONMENT")
    }
    
    print("Environment indicators:")
    for name, value in indicators.items():
        print(f"  {name}: {value}")
    
    # Simple detection logic
    is_docker = (
        os.getenv("PYTHONPATH") == "/app" or
        str(Path(__file__)).startswith("/app/") or
        os.getenv("ENVIRONMENT") == "docker"
    )
    
    print(f"\nDetected environment: {'Docker' if is_docker else 'Local'}")
    print()

def simulate_service_usage():
    """Simulate how services would use paths"""
    print("🔧 Simulating Service Usage")
    print("-" * 50)
    
    # Simulate simple_form_detection.py usage
    print("SimpleFormDetectionService simulation:")
    
    # Current logic: Path(__file__).parent.parent.parent / "data" / "storage" / "collections"
    # Simulated from app/services/simple_form_detection.py
    script_dir = Path(__file__).parent.parent
    service_file = script_dir / "app" / "services" / "simple_form_detection.py"
    
    if service_file.parent.exists():
        storage_base_path = service_file.parent.parent.parent / "data" / "storage" / "collections"
        print(f"  Storage base path: {storage_base_path}")
        print(f"  Path exists: {storage_base_path.exists()}")
        
        if storage_base_path.exists():
            collections = [d.name for d in storage_base_path.iterdir() if d.is_dir()]
            print(f"  Collections found: {len(collections)}")
            if collections:
                print(f"  First few: {collections[:3]}")
    else:
        print("  Service file structure not found")
    
    print()

def main():
    """Run simple path tests"""
    print("🧪 Simple LegalRAG Path Tests")
    print("=" * 50)
    print()
    
    try:
        test_current_paths()
        test_windows_vs_docker_paths()
        test_problematic_windows_path()
        test_environment_detection()
        simulate_service_usage()
        
        print("✅ Simple tests completed!")
        print("💡 Key findings:")
        print("   - Path calculations should work in Docker (/app structure)")
        print("   - Windows-specific string replacement needs to be removed")
        print("   - Environment detection can distinguish local vs Docker")
        print("   - Current structure uses rag_service/data -> should map to /app/data")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())