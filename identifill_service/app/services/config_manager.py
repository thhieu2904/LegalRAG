"""
Configuration management for QR Scanner system
Handles loading and validation of configuration parameters
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json

try:
    import toml
except ImportError:
    toml = None

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Centralized configuration management for the QR Scanner system.
    
    Supports multiple configuration sources:
    1. TOML file (preferred)
    2. JSON file (fallback)
    3. Environment variables (override)
    4. Default values (built-in)
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config.toml"
        self.config = {}
        self._load_defaults()
        self._load_config_file()
        self._load_environment_overrides()
        self._validate_config()
    
    def _load_defaults(self):
        """Load default configuration values"""
        self.config = {
            "image_preprocessing": {
                "target_width": 1200,
                "max_width": 1600,
                "min_width": 800,
                "noise_reduction_strength": "medium",
                "low_contrast_threshold": 50.0,
                "low_sharpness_threshold": 100.0
            },
            "qr_detection": {
                "enable_preprocessing": True,
                "enable_fast_scan": True,
                "enable_enhanced_scan": True,
                "enable_card_detection": True,
                "enable_corner_scan": True,
                "max_enhancement_methods": 6,
                "early_termination": True,
                "pyzbar_priority": 1,
                "opencv_priority": 2
            },
            "card_detection": {
                "min_card_area": 10000,
                "aspect_ratio_min": 1.4,
                "aspect_ratio_max": 1.8,
                "contour_area_threshold_ratio": 0.8,
                "corner_size_ratio": 0.25,
                "canny_low_threshold": 75,
                "canny_high_threshold": 200,
                "gaussian_blur_kernel": 5,
                "dilate_iterations": 1
            },
            "enhancement_methods": {
                "adaptive_threshold": {
                    "enabled": True,
                    "max_value": 255,
                    "adaptive_method": "ADAPTIVE_THRESH_GAUSSIAN_C",
                    "threshold_type": "THRESH_BINARY",
                    "block_size": 11,
                    "c_constant": 2
                },
                "sharpen": {
                    "enabled": True,
                    "kernel": [[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]
                },
                "clahe": {
                    "enabled": True,
                    "clip_limit": 2.0,
                    "tile_grid_size": [8, 8]
                },
                "otsu": {
                    "enabled": True,
                    "threshold_value": 0,
                    "max_value": 255,
                    "threshold_type": "THRESH_BINARY_OTSU"
                },
                "canny_edge": {
                    "enabled": True,
                    "low_threshold": 100,
                    "high_threshold": 200,
                    "dilate_kernel_size": 3,
                    "dilate_iterations": 1
                },
                "contrast_otsu": {
                    "enabled": True
                }
            },
            "logging": {
                "log_level": "INFO",
                "log_preprocessing": False,
                "log_detection_stages": True,
                "log_timing": True,
                "log_image_properties": False
            },
            "performance": {
                "max_processing_time": 10.0,
                "memory_limit_mb": 500,
                "enable_caching": False,
                "fast_scan_timeout": 2.0,
                "enhanced_scan_timeout": 5.0,
                "card_detection_timeout": 3.0
            },
            "api": {
                "default_processing_mode": "auto",
                "return_debug_info": False,
                "return_processing_stats": True,
                "max_image_size_mb": 10
            },
            "testing": {
                "test_images_dir": "test_images",
                "generate_performance_reports": True,
                "benchmark_mode": False,
                "save_debug_images": False
            },
            "experimental": {
                "enable_hough_lines": False,
                "enable_template_matching": False,
                "enable_color_segmentation": False,
                "enable_grid_scanning": False
            }
        }
    
    def _load_config_file(self):
        """Load configuration from file"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"Config file '{self.config_file}' not found, using defaults")
            return
        
        try:
            if config_path.suffix.lower() == '.toml':
                if toml is None:
                    logger.warning("TOML not available, trying JSON fallback")
                    self._try_load_json_config(config_path)
                else:
                    with open(config_path, 'r') as f:
                        file_config = toml.load(f)
                    self._merge_config(file_config)
                    logger.info(f"Configuration loaded from TOML file: {self.config_file}")
            
            elif config_path.suffix.lower() == '.json':
                self._try_load_json_config(config_path)
            
            else:
                logger.warning(f"Unsupported config file format: {config_path.suffix}")
        
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    
    def _try_load_json_config(self, config_path: Path):
        """Try to load JSON configuration"""
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
            self._merge_config(file_config)
            logger.info(f"Configuration loaded from JSON file: {config_path}")
        except Exception as e:
            logger.error(f"Error loading JSON config: {e}")
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Merge new configuration with existing defaults"""
        def deep_merge(base: dict, overlay: dict):
            for key, value in overlay.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(self.config, new_config)
    
    def _load_environment_overrides(self):
        """Load configuration overrides from environment variables"""
        # Map environment variables to config paths
        env_mappings = {
            'QR_TARGET_WIDTH': ['image_preprocessing', 'target_width'],
            'QR_MAX_WIDTH': ['image_preprocessing', 'max_width'],
            'QR_MIN_WIDTH': ['image_preprocessing', 'min_width'],
            'QR_NOISE_REDUCTION': ['image_preprocessing', 'noise_reduction_strength'],
            'QR_LOG_LEVEL': ['logging', 'log_level'],
            'QR_ENABLE_PREPROCESSING': ['qr_detection', 'enable_preprocessing'],
            'QR_ENABLE_CARD_DETECTION': ['qr_detection', 'enable_card_detection'],
            'QR_MAX_PROCESSING_TIME': ['performance', 'max_processing_time'],
            'QR_PROCESSING_MODE': ['api', 'default_processing_mode'],
            'QR_RETURN_DEBUG_INFO': ['api', 'return_debug_info']
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(value)
                
                # Navigate to the config location and set value
                current = self.config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                current[config_path[-1]] = converted_value
                logger.info(f"Environment override: {env_var} = {converted_value}")
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _validate_config(self):
        """Validate configuration values"""
        # Validate image preprocessing settings
        img_config = self.config['image_preprocessing']
        if img_config['target_width'] <= 0:
            raise ValueError("target_width must be positive")
        
        if img_config['noise_reduction_strength'] not in ['light', 'medium', 'strong']:
            raise ValueError("noise_reduction_strength must be 'light', 'medium', or 'strong'")
        
        # Validate card detection settings
        card_config = self.config['card_detection']
        if card_config['aspect_ratio_min'] >= card_config['aspect_ratio_max']:
            raise ValueError("aspect_ratio_min must be less than aspect_ratio_max")
        
        # Validate performance settings
        perf_config = self.config['performance']
        if perf_config['max_processing_time'] <= 0:
            raise ValueError("max_processing_time must be positive")
        
        logger.info("Configuration validation passed")
    
    def get(self, *keys: str) -> Any:
        """Get configuration value by path"""
        current = self.config
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.config.get(section, {})
    
    def set(self, value: Any, *keys: str):
        """Set configuration value by path"""
        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def save_config(self, file_path: Optional[str] = None):
        """Save current configuration to file"""
        output_path = file_path or self.config_file
        
        try:
            if output_path.endswith('.toml') and toml is not None:
                with open(output_path, 'w') as f:
                    toml.dump(self.config, f)
            else:
                with open(output_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to: {output_path}")
        
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get_preprocessing_config(self) -> Dict[str, Any]:
        """Get preprocessor configuration"""
        return self.get_section('image_preprocessing')
    
    def get_detection_config(self) -> Dict[str, Any]:
        """Get QR detection configuration"""
        return self.get_section('qr_detection')
    
    def get_card_detection_config(self) -> Dict[str, Any]:
        """Get card detection configuration"""
        return self.get_section('card_detection')
    
    def get_enhancement_config(self) -> Dict[str, Any]:
        """Get enhancement methods configuration"""
        return self.get_section('enhancement_methods')
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get('logging', 'log_level') == 'DEBUG'
    
    def should_log_timing(self) -> bool:
        """Check if timing should be logged"""
        return self.get('logging', 'log_timing') or False
    
    def should_log_detection_stages(self) -> bool:
        """Check if detection stages should be logged"""
        return self.get('logging', 'log_detection_stages') or False
    
    def get_max_processing_time(self) -> float:
        """Get maximum processing time"""
        return self.get('performance', 'max_processing_time') or 10.0
    
    def __str__(self) -> str:
        """String representation of current configuration"""
        return json.dumps(self.config, indent=2)


# Global configuration instance
_config_instance = None

def get_config() -> ConfigManager:
    """Get global configuration instance (singleton pattern)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance

def reload_config(config_file: Optional[str] = None):
    """Reload configuration from file"""
    global _config_instance
    _config_instance = ConfigManager(config_file)
