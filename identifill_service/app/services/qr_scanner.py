import base64
import cv2
import numpy as np
from pyzbar import pyzbar
from typing import Optional, Tuple, List
import time
import logging
from app.models.schemas import CCCDData, QRScanResponse
from app.services.qr_parser import QRCodeParser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QRCodeScanner:
    """Improved QR Code scanner for CCCD cards with advanced image processing"""
    
    def __init__(self):
        self.parser = QRCodeParser()
        # Initialize QR code detector from OpenCV
        self.qr_detector = cv2.QRCodeDetector()
    
    def scan_qr_from_base64(self, image_data: str) -> QRScanResponse:
        """
        Scan QR code from base64 encoded image using advanced techniques
        """
        start_time = time.time()
        
        try:
            # Decode base64 image
            image = self._decode_base64_image(image_data)
            if image is None:
                return QRScanResponse(
                    success=False,
                    message="Invalid image data"
                )
            
            # Try multiple approaches to detect and decode QR codes
            result = self._multi_stage_qr_detection(image)
            
            if result.success:
                processing_time = time.time() - start_time
                result.processing_time = processing_time
                return result
            
            # If no QR code found with any method
            return QRScanResponse(
                success=False,
                message="No QR code found in image"
            )
            
        except Exception as e:
            logger.error(f"Error scanning QR code: {str(e)}")
            return QRScanResponse(
                success=False,
                message=f"Error scanning QR code: {str(e)}"
            )
    
    def _decode_base64_image(self, base64_string: str) -> Optional[np.ndarray]:
        """Decode base64 string to OpenCV image"""
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]
            
            # Decode base64
            image_data = base64.b64decode(base64_string)
            
            # Convert to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            
            # Decode image
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return image
            
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None
    
    def _try_pyzbar_detect(self, image: np.ndarray) -> Optional[str]:
        """Try to decode QR code using pyzbar"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
                
            # Scan for QR codes
            qr_codes = pyzbar.decode(gray)
            
            if qr_codes:
                # Process the first QR code found
                qr_code = qr_codes[0]
                qr_data = qr_code.data.decode('utf-8')
                return qr_data
            
            return None
        except Exception as e:
            logger.debug(f"Pyzbar detection error: {e}")
            return None
    
    def _try_opencv_qr_detect(self, image: np.ndarray) -> Tuple[bool, List[str], Optional[np.ndarray], Optional[np.ndarray]]:
        """Try to detect and decode QR code using OpenCV"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
                
            # Detect and decode
            result = self.qr_detector.detectAndDecodeMulti(gray)
            return result[0], list(result[1]), result[2], result[3]
        except Exception as e:
            logger.debug(f"OpenCV QR detection error: {e}")
            return False, [], None, None
    
    def _extract_qr_region(self, image: np.ndarray, points: np.ndarray) -> Optional[np.ndarray]:
        """Extract QR code region using detected points"""
        try:
            # Ensure points is properly shaped
            if points.shape[1] < 4:
                return None
                
            # Get bounding rectangle
            rect = cv2.boundingRect(points)
            x, y, w, h = rect
            
            # Add some margin (10%)
            margin_x = int(w * 0.1)
            margin_y = int(h * 0.1)
            
            # Ensure boundaries are within image
            start_x = max(0, x - margin_x)
            start_y = max(0, y - margin_y)
            end_x = min(image.shape[1], x + w + margin_x)
            end_y = min(image.shape[0], y + h + margin_y)
            
            # Crop image
            qr_region = image[start_y:end_y, start_x:end_x]
            
            return qr_region
        except Exception as e:
            logger.debug(f"Error extracting QR region: {e}")
            return None
    
    def _get_enhanced_versions(self, image: np.ndarray) -> List[np.ndarray]:
        """Generate multiple enhanced versions of the image for QR detection"""
        enhanced_images = []
        
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Add original grayscale
            enhanced_images.append(gray)
            
            # 1. Basic enhancement with adaptive threshold
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            enhanced_images.append(thresh)
            
            # 2. Sharpen the image
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(gray, -1, kernel)
            enhanced_images.append(sharpened)
            
            # 3. Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced_contrast = clahe.apply(gray)
            enhanced_images.append(enhanced_contrast)
            
            # 4. Thresholding with Otsu's method
            _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            enhanced_images.append(otsu)
            
            # 5. Edge enhancement
            edges = cv2.Canny(gray, 100, 200)
            kernel = np.ones((3, 3), np.uint8)
            dilated_edges = cv2.dilate(edges, kernel, iterations=1)
            inverted = cv2.bitwise_not(dilated_edges)  # Invert for QR detection
            enhanced_images.append(inverted)
            
            # 6. Combining methods (threshold after contrast enhancement)
            _, thresh2 = cv2.threshold(enhanced_contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            enhanced_images.append(thresh2)
            
            return enhanced_images
            
        except Exception as e:
            logger.debug(f"Error in image enhancement: {e}")
            return [image] if len(image.shape) == 2 else [cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)]
    
    def _try_detect_card(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Try to detect and extract the ID card from the image"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply Canny edge detection
            edges = cv2.Canny(blurred, 75, 200)
            
            # Dilate edges to connect broken lines
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=1)
            
            # Find contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Sort contours by area (largest first) - the card should be one of the largest contours
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            
            # Take the top 3 contours
            for contour in contours[:3]:
                # Get area
                area = cv2.contourArea(contour)
                
                # Skip small contours
                if area < 10000:  # Adjust threshold based on typical card size
                    continue
                
                # Approximate the contour to a polygon
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                
                # If the polygon has 4 points, it might be the card
                if len(approx) == 4:
                    # Create a mask for the card
                    mask = np.zeros_like(gray)
                    cv2.drawContours(mask, [approx], 0, (255, 255, 255), -1)
                    
                    # Extract the card region
                    card_region = cv2.bitwise_and(image, image, mask=mask)
                    
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(approx)
                    card_region = image[y:y+h, x:x+w]
                    
                    return card_region
            
            return None
            
        except Exception as e:
            logger.debug(f"Error in card detection: {e}")
            return None
    
    def _extract_card_corners(self, card_image: np.ndarray) -> List[np.ndarray]:
        """Extract the four corners of the card image where QR codes are typically located"""
        corners = []
        try:
            h, w = card_image.shape[:2]
            
            # Define corner size (25% of the smaller dimension)
            corner_size = min(h, w) // 4
            
            # Extract four corners
            top_left = card_image[0:corner_size, 0:corner_size]
            top_right = card_image[0:corner_size, w-corner_size:w]
            bottom_left = card_image[h-corner_size:h, 0:corner_size]
            bottom_right = card_image[h-corner_size:h, w-corner_size:w]
            
            corners = [top_left, top_right, bottom_left, bottom_right]
            
            return corners
            
        except Exception as e:
            logger.debug(f"Error extracting corners: {e}")
            return corners
    
    def _create_success_response(self, qr_data: str) -> QRScanResponse:
        """Create success response with parsed QR data"""
        try:
            # Parse QR data
            cccd_data = self.parser.parse_qr_data(qr_data)
            
            if not cccd_data:
                return QRScanResponse(
                    success=False,
                    message="Invalid QR code format or data"
                )
            
            # Validate parsed data
            if not self.parser.validate_cccd_data(cccd_data):
                return QRScanResponse(
                    success=False,
                    message="Invalid CCCD data format",
                    data=cccd_data  # Still return data for debugging
                )
            
            return QRScanResponse(
                success=True,
                data=cccd_data,
                message="QR code scanned successfully",
                confidence=1.0  # QR codes have high confidence when decoded
            )
            
        except Exception as e:
            logger.error(f"Error parsing QR data: {e}")
            return QRScanResponse(
                success=False,
                message=f"Error parsing QR data: {str(e)}"
            )
            
    def _multi_stage_qr_detection(self, image: np.ndarray) -> QRScanResponse:
        """
        Multi-stage QR code detection with multiple techniques
        """
        # Method 1: Try direct pyzbar detection on original image
        qr_data = self._try_pyzbar_detect(image)
        if qr_data:
            return self._create_success_response(qr_data)
        
        # Method 2: Use OpenCV QR detector (can find QR code position even if can't decode)
        retval, decoded_info, points, straight_qrcode = self._try_opencv_qr_detect(image)
        
        # If OpenCV directly decoded the QR
        if retval and decoded_info and decoded_info[0]:
            qr_data = decoded_info[0]
            return self._create_success_response(qr_data)
        
        # Method 3: If QR position found but not decoded, crop and enhance the region
        if points is not None and len(points) > 0:
            qr_region = self._extract_qr_region(image, points)
            if qr_region is not None:
                # Try multiple enhancements on the cropped region
                for enhanced_img in self._get_enhanced_versions(qr_region):
                    # Try pyzbar on enhanced cropped region
                    qr_data = self._try_pyzbar_detect(enhanced_img)
                    if qr_data:
                        return self._create_success_response(qr_data)
        
        # Method 4: Try multiple image processing techniques on the whole image
        for processed_img in self._get_enhanced_versions(image):
            # Try pyzbar on processed images
            qr_data = self._try_pyzbar_detect(processed_img)
            if qr_data:
                return self._create_success_response(qr_data)
            
            # Try OpenCV QR detector on processed images
            retval, decoded_info, points, _ = self._try_opencv_qr_detect(processed_img)
            if retval and decoded_info and decoded_info[0]:
                qr_data = decoded_info[0]
                return self._create_success_response(qr_data)
        
        # Method 5: Try with image segmentation to identify card regions
        card_region = self._try_detect_card(image)
        if card_region is not None:
            # Try both detectors on the card region
            qr_data = self._try_pyzbar_detect(card_region)
            if qr_data:
                return self._create_success_response(qr_data)
            
            retval, decoded_info, points, _ = self._try_opencv_qr_detect(card_region)
            if retval and decoded_info and decoded_info[0]:
                qr_data = decoded_info[0]
                return self._create_success_response(qr_data)
            
            # If card found but QR not decoded, try corner crops (QR is often in corners of ID cards)
            corners = self._extract_card_corners(card_region)
            for corner in corners:
                qr_data = self._try_pyzbar_detect(corner)
                if qr_data:
                    return self._create_success_response(qr_data)
        
        # If all methods fail
        return QRScanResponse(success=False, message="QR code not detected with any method")
