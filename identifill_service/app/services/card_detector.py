import base64
import cv2
import numpy as np
from typing import Optional, List, Tuple
import time
from app.models.schemas import CardDetectionResponse


class CardDetector:
    """Card detection service for automatic cropping"""
    
    def __init__(self):
        self.min_card_area = 10000  # Minimum area for card detection
        self.aspect_ratio_range = (1.4, 1.8)  # Typical ID card aspect ratio
    
    def detect_card_from_base64(self, image_data: str, auto_crop: bool = True) -> CardDetectionResponse:
        """Detect and optionally crop card from base64 image"""
        try:
            # Decode image
            image = self._decode_base64_image(image_data)
            if image is None:
                return CardDetectionResponse(
                    success=False,
                    card_detected=False,
                    message="Invalid image data"
                )
            
            # Detect card contours
            card_contour, confidence = self._detect_card_contour(image)
            
            if card_contour is None:
                return CardDetectionResponse(
                    success=True,
                    card_detected=False,
                    message="No card detected in image",
                    confidence=0.0
                )
            
            cropped_image_b64 = None
            if auto_crop:
                # Crop and straighten card
                cropped_image = self._crop_and_straighten_card(image, card_contour)
                if cropped_image is not None:
                    cropped_image_b64 = self._encode_image_to_base64(cropped_image)
            
            return CardDetectionResponse(
                success=True,
                card_detected=True,
                cropped_image=cropped_image_b64,
                confidence=confidence,
                message="Card detected successfully"
            )
            
        except Exception as e:
            return CardDetectionResponse(
                success=False,
                card_detected=False,
                message=f"Error detecting card: {str(e)}"
            )
    
    def _decode_base64_image(self, base64_string: str) -> Optional[np.ndarray]:
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
    
    def _encode_image_to_base64(self, image: np.ndarray) -> str:
        """Encode OpenCV image to base64 string"""
        try:
            _, buffer = cv2.imencode('.jpg', image)
            image_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
            return f"data:image/jpeg;base64,{image_base64}"
        except Exception as e:
            print(f"Error encoding image to base64: {e}")
            return ""
    
    def _detect_card_contour(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], float]:
        """Detect the main card contour in the image"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find the best card contour
            best_contour = None
            best_confidence = 0.0
            
            for contour in contours:
                # Calculate area
                area = cv2.contourArea(contour)
                if area < self.min_card_area:
                    continue
                
                # Approximate contour to rectangle
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if it's roughly rectangular (4 corners)
                if len(approx) == 4:
                    # Calculate aspect ratio
                    rect = cv2.minAreaRect(contour)
                    width, height = rect[1]
                    aspect_ratio = max(width, height) / min(width, height)
                    
                    # Check if aspect ratio matches card proportions
                    if self.aspect_ratio_range[0] <= aspect_ratio <= self.aspect_ratio_range[1]:
                        # Calculate confidence based on area and shape
                        confidence = min(area / (image.shape[0] * image.shape[1]), 1.0)
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_contour = approx
            
            return best_contour, best_confidence
            
        except Exception as e:
            print(f"Error detecting card contour: {e}")
            return None, 0.0
    
    def _crop_and_straighten_card(self, image: np.ndarray, contour: np.ndarray) -> Optional[np.ndarray]:
        """Crop and straighten the detected card"""
        try:
            # Get the four corner points
            if len(contour) != 4:
                return None
            
            # Reshape contour points
            pts = contour.reshape(4, 2).astype(np.float32)
            
            # Order points: top-left, top-right, bottom-right, bottom-left
            ordered_pts = self._order_points(pts)
            
            # Calculate dimensions for the output image
            width = max(
                np.linalg.norm(ordered_pts[0] - ordered_pts[1]),
                np.linalg.norm(ordered_pts[2] - ordered_pts[3])
            )
            height = max(
                np.linalg.norm(ordered_pts[0] - ordered_pts[3]),
                np.linalg.norm(ordered_pts[1] - ordered_pts[2])
            )
            
            # Define destination points for perspective transform
            dst_pts = np.array([
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1]
            ], dtype=np.float32)
            
            # Get perspective transform matrix and apply it
            matrix = cv2.getPerspectiveTransform(ordered_pts, dst_pts)
            cropped = cv2.warpPerspective(image, matrix, (int(width), int(height)))
            
            return cropped
            
        except Exception as e:
            print(f"Error cropping and straightening card: {e}")
            return None
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order points in clockwise order: top-left, top-right, bottom-right, bottom-left"""
        # Sort points based on x-coordinates
        x_sorted = pts[np.argsort(pts[:, 0]), :]
        
        # Get left and right points
        left_points = x_sorted[:2, :]
        right_points = x_sorted[2:, :]
        
        # Sort left points by y-coordinate (top-left, bottom-left)
        left_points = left_points[np.argsort(left_points[:, 1]), :]
        top_left, bottom_left = left_points
        
        # Sort right points by y-coordinate (top-right, bottom-right)  
        right_points = right_points[np.argsort(right_points[:, 1]), :]
        top_right, bottom_right = right_points
        
        return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)
