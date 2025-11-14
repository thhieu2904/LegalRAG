"""
PathConfig Adapter for Admin Service
====================================

Reuses PathConfig from RAG service for Docker/Local compatibility.
This ensures consistent path handling across all services.
"""

import sys
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def _find_rag_service_path():
    """Find RAG service path for PathConfig import"""
    
    # Method 1: Docker with mounted RAG service app
    if os.getenv("ENVIRONMENT") == "docker":
        # Check for mounted RAG service app (as configured in docker-compose.dev.yml)
        rag_app_mount = Path("/app/rag_service_app")
        if rag_app_mount.exists() and (rag_app_mount / "core" / "path_config.py").exists():
            # Create a fake rag_service structure to make imports work
            rag_root = Path("/app/rag_service_temp")
            rag_root.mkdir(exist_ok=True)
            (rag_root / "app").mkdir(exist_ok=True)
            
            # Create symlink or copy structure
            import shutil
            if not (rag_root / "app" / "core").exists():
                shutil.copytree(rag_app_mount / "core", rag_root / "app" / "core")
            
            logger.info(f"🐳 Using Docker mounted RAG app: {rag_root}")
            return rag_root
    
    # Method 2: Local development - relative path
    current_file = Path(__file__).resolve()
    admin_service_root = current_file.parent.parent.parent  # admin_service/
    rag_service_path = admin_service_root.parent / "rag_service"  # ../rag_service/
    
    if rag_service_path.exists() and (rag_service_path / "app" / "core" / "path_config.py").exists():
        logger.info(f"🏠 Using local RAG path: {rag_service_path}")
        return rag_service_path
    
    # Method 3: Try other common patterns
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "rag_service",  # ../../rag_service
        Path.cwd().parent / "rag_service",  # ../rag_service from cwd
        Path("/app"),  # Direct Docker path (fallback)
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "app" / "core" / "path_config.py").exists():
            logger.info(f"🔍 Found RAG service at: {path}")
            return path
    
    return None

# Find and add RAG service to path
rag_service_path = _find_rag_service_path()

if rag_service_path is None:
    logger.error("❌ Cannot locate RAG service directory")
    raise ImportError("RAG service not found. Admin service requires access to RAG service PathConfig.")

if str(rag_service_path) not in sys.path:
    sys.path.insert(0, str(rag_service_path))
    logger.info(f"📁 Added to Python path: {rag_service_path}")

try:
    from app.core.path_config import PathConfig
    logger.info("✅ Successfully imported PathConfig from RAG service")
except ImportError as e:
    logger.error(f"❌ Failed to import PathConfig: {e}")
    logger.error(f"RAG service path: {rag_service_path}")
    logger.error(f"Python path: {sys.path}")
    raise ImportError(f"Cannot import PathConfig from RAG service at {rag_service_path}. Error: {e}")

# Global PathConfig instance
_path_config_instance = None

def get_path_config() -> PathConfig:
    """
    Get global PathConfig instance (singleton pattern)
    
    Returns:
        PathConfig instance with auto-detected environment
    """
    global _path_config_instance
    
    if _path_config_instance is None:
        _path_config_instance = PathConfig()
        logger.info(f"🔧 Initialized PathConfig for Admin Service:")
        logger.info(f"   Environment: {_path_config_instance.environment}")
        logger.info(f"   Base data dir: {_path_config_instance.base_data_dir}")
        logger.info(f"   Collections dir: {_path_config_instance.collections_dir}")
    
    return _path_config_instance

def verify_path_config():
    """
    Verify PathConfig is working correctly
    
    Returns:
        Dict with verification results
    """
    try:
        path_config = get_path_config()
        
        return {
            "success": True,
            "environment": path_config.environment,
            "base_data_dir": str(path_config.base_data_dir),
            "collections_dir": str(path_config.collections_dir),
            "collections_exist": path_config.collections_dir.exists(),
            "can_list_collections": hasattr(path_config, 'list_collections')
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }