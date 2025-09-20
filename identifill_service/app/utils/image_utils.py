import base64
import cv2
import numpy as np
from typing import Optional


def decode_base64_image(base64_string: str) -> Optional[np.ndarray]:
    """Decode base64 string to OpenCV image"""
    try:
        # Remove data URL prefix if present
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return image
        
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return None


def encode_image_to_base64(image: np.ndarray, format: str = 'jpg') -> str:
    """Encode OpenCV image to base64 string"""
    try:
        _, buffer = cv2.imencode(f'.{format}', image)
        image_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
        return f"data:image/{format};base64,{image_base64}"
    except Exception as e:
        print(f"Error encoding image to base64: {e}")
        return ""


def validate_image_data(base64_string: str) -> bool:
    """Validate if base64 string contains valid image data"""
    try:
        image = decode_base64_image(base64_string)
        return image is not None
    except Exception:
        return False


def resize_image(image: np.ndarray, max_width: int = 1024, max_height: int = 1024) -> np.ndarray:
    """Resize image while maintaining aspect ratio"""
    try:
        height, width = image.shape[:2]
        
        # Calculate scaling factor
        scale_w = max_width / width
        scale_h = max_height / height
        scale = min(scale_w, scale_h, 1.0)  # Don't upscale
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            return resized
        
        return image
        
    except Exception as e:
        print(f"Error resizing image: {e}")
        return image
