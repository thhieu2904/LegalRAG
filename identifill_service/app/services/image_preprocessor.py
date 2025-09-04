import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """
    Advanced image preprocessing pipeline for QR code detection optimization.
    
    This class normalizes input images to improve QR detection reliability by:
    1. Standardizing image size while preserving aspect ratio
    2. Reducing noise that can interfere with QR detection
    3. Optimizing image quality for both pyzbar and OpenCV QR detectors
    """
    
    def __init__(
        self,
        target_width: int = 1200,
        max_width: int = 1600,
        min_width: int = 800,
        noise_reduction_strength: str = "medium"
    ):
        """
        Initialize the preprocessor with configurable parameters.
        
        Args:
            target_width: Preferred width for resized images
            max_width: Maximum width (images larger than this will be resized)
            min_width: Minimum width (images smaller than this will be upscaled)
            noise_reduction_strength: "light", "medium", or "strong"
        """
        self.target_width = target_width
        self.max_width = max_width
        self.min_width = min_width
        self.noise_reduction_strength = noise_reduction_strength
        
        # Noise reduction parameters
        self.noise_params = {
            "light": {
                "median_kernel": 3,
                "bilateral_d": 5,
                "bilateral_sigma_color": 20,
                "bilateral_sigma_space": 20
            },
            "medium": {
                "median_kernel": 5,
                "bilateral_d": 7,
                "bilateral_sigma_color": 40,
                "bilateral_sigma_space": 40
            },
            "strong": {
                "median_kernel": 7,
                "bilateral_d": 9,
                "bilateral_sigma_color": 60,
                "bilateral_sigma_space": 60
            }
        }
        
        logger.info(f"ImagePreprocessor initialized with target_width={target_width}, "
                   f"noise_reduction={noise_reduction_strength}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Main preprocessing pipeline.
        
        Args:
            image: Input image (BGR format from OpenCV)
            
        Returns:
            Preprocessed image optimized for QR detection
        """
        if image is None:
            raise ValueError("Input image is None")
        
        # Log original image properties
        original_height, original_width = image.shape[:2]
        original_size = original_width * original_height
        logger.debug(f"Original image: {original_width}x{original_height} "
                    f"({original_size:,} pixels)")
        
        # Step 1: Adaptive resize
        resized_image = self._adaptive_resize(image)
        
        # Step 2: Noise reduction
        denoised_image = self._reduce_noise(resized_image)
        
        # Step 3: Quality enhancement (optional, based on image analysis)
        enhanced_image = self._enhance_quality(denoised_image)
        
        # Log final image properties
        final_height, final_width = enhanced_image.shape[:2]
        final_size = final_width * final_height
        reduction_ratio = (1 - final_size / original_size) * 100
        
        logger.debug(f"Processed image: {final_width}x{final_height} "
                    f"({final_size:,} pixels, {reduction_ratio:.1f}% size reduction)")
        
        return enhanced_image
    
    def _adaptive_resize(self, image: np.ndarray) -> np.ndarray:
        """
        Intelligently resize image based on its current dimensions.
        
        Strategy:
        - Very large images (>max_width): Resize to target_width
        - Medium images (min_width to max_width): Keep original or slight adjustment
        - Small images (<min_width): Upscale to min_width
        """
        height, width = image.shape[:2]
        
        if width > self.max_width:
            # Large image: resize to target width
            new_width = self.target_width
            resize_reason = "large image downscale"
        elif width < self.min_width:
            # Small image: upscale to minimum width
            new_width = self.min_width
            resize_reason = "small image upscale"
        elif abs(width - self.target_width) > 200:
            # Medium image but far from target: adjust towards target
            new_width = self.target_width
            resize_reason = "adjustment to target"
        else:
            # Image size is acceptable, no resize needed
            logger.debug(f"Image size acceptable ({width}px), no resize needed")
            return image
        
        # Calculate new height maintaining aspect ratio
        aspect_ratio = height / width
        new_height = int(new_width * aspect_ratio)
        
        # Perform resize with high-quality interpolation
        resized = cv2.resize(
            image, 
            (new_width, new_height), 
            interpolation=cv2.INTER_LANCZOS4
        )
        
        logger.debug(f"Resized image: {width}x{height} -> {new_width}x{new_height} "
                    f"({resize_reason})")
        
        return resized
    
    def _reduce_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Apply noise reduction techniques while preserving important edges.
        
        Uses a combination of:
        1. Median filtering: Removes salt-and-pepper noise
        2. Bilateral filtering: Reduces noise while preserving edges
        """
        params = self.noise_params[self.noise_reduction_strength]
        
        # Step 1: Median filter for impulse noise
        median_filtered = cv2.medianBlur(image, params["median_kernel"])
        
        # Step 2: Bilateral filter for edge-preserving smoothing
        bilateral_filtered = cv2.bilateralFilter(
            median_filtered,
            params["bilateral_d"],
            params["bilateral_sigma_color"],
            params["bilateral_sigma_space"]
        )
        
        logger.debug(f"Applied {self.noise_reduction_strength} noise reduction")
        return bilateral_filtered
    
    def _enhance_quality(self, image: np.ndarray) -> np.ndarray:
        """
        Optional quality enhancement based on image analysis.
        
        This step analyzes the image and applies enhancements only if needed.
        """
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Analyze image quality metrics
        contrast = self._calculate_contrast(gray)
        sharpness = self._calculate_sharpness(gray)
        
        logger.debug(f"Image quality - Contrast: {contrast:.2f}, Sharpness: {sharpness:.2f}")
        
        enhanced = image.copy()
        
        # Apply CLAHE if contrast is low
        if contrast < 50:
            lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
            l_channel = lab[:, :, 0]
            
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_channel = clahe.apply(l_channel)
            
            lab[:, :, 0] = l_channel
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            logger.debug("Applied CLAHE for contrast enhancement")
        
        # Apply unsharp mask if sharpness is low
        if sharpness < 100:
            enhanced = self._unsharp_mask(enhanced)
            logger.debug("Applied unsharp mask for sharpness enhancement")
        
        return enhanced
    
    def _calculate_contrast(self, gray_image: np.ndarray) -> float:
        """Calculate RMS contrast of grayscale image."""
        return float(np.std(gray_image.astype(np.float64)))
    
    def _calculate_sharpness(self, gray_image: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance."""
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        return float(np.var(laplacian.astype(np.float64)))
    
    def _unsharp_mask(self, image: np.ndarray, sigma: float = 1.0, strength: float = 1.5) -> np.ndarray:
        """Apply unsharp mask for edge enhancement."""
        # Create Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), sigma)
        
        # Create unsharp mask
        unsharp = cv2.addWeighted(image, 1 + strength, blurred, -strength, 0)
        
        return unsharp
    
    def get_preprocessing_info(self) -> dict:
        """Return current preprocessing configuration."""
        return {
            "target_width": self.target_width,
            "max_width": self.max_width,
            "min_width": self.min_width,
            "noise_reduction_strength": self.noise_reduction_strength,
            "noise_params": self.noise_params[self.noise_reduction_strength]
        }
    
    @staticmethod
    def analyze_image_properties(image: np.ndarray) -> dict:
        """
        Analyze image properties for debugging and optimization.
        
        Returns detailed information about the image that can help
        in tuning preprocessing parameters.
        """
        if image is None:
            return {"error": "Image is None"}
        
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Basic properties
        properties = {
            "dimensions": {"width": int(width), "height": int(height)},
            "total_pixels": int(width * height),
            "aspect_ratio": float(width / height),
        }
        
        # Quality metrics
        properties["quality"] = {
            "mean_brightness": float(np.mean(gray.astype(np.float64))),
            "std_brightness": float(np.std(gray.astype(np.float64))),
            "contrast_rms": float(np.std(gray.astype(np.float64))),
            "sharpness_laplacian": float(np.var(cv2.Laplacian(gray, cv2.CV_64F).astype(np.float64))),
            "brightness_range": {
                "min": int(np.min(gray).item()),
                "max": int(np.max(gray).item())
            }
        }
        
        # Noise estimation (using high-pass filter)
        kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        noise_response = cv2.filter2D(gray, cv2.CV_32F, kernel)
        properties["estimated_noise_level"] = float(np.std(noise_response.astype(np.float64)))
        
        return properties
