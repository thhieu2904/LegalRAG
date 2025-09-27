"""
PathConfig Adapter for Admin Service
====================================

Reuses PathConfig from RAG service for Docker/Local compatibility.
This ensures consistent path handling across all services.
"""

import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add RAG service to path to import PathConfig
rag_service_path = Path(__file__).parent.parent.parent / "rag_service"
if str(rag_service_path) not in sys.path:
    sys.path.append(str(rag_service_path))

try:
    from app.core.path_config import PathConfig
    logger.info("✅ Successfully imported PathConfig from RAG service")
except ImportError as e:
    logger.error(f"❌ Failed to import PathConfig: {e}")
    raise ImportError("Cannot import PathConfig from RAG service. Check RAG service path.")

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