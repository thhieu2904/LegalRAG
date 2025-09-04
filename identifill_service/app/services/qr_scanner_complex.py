import base64
import cv2
import numpy as np
from pyzbar import pyzbar
from typing import Optional, Tuple, List, Dict, Any
import time
import logging
import os
from app.models.schemas import CCCDData, QRScanResponse
from app.services.qr_parser import QRCodeParser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QRCodeScanner:
    """
    Secure QR Code scanner for CCCD cards with optimized region extraction.
    Focuses on extracting correct QR regions and uses only local, secure libraries.
    No external data sharing - uses only OpenCV and pyzbar.
    """
    
    def __init__(self):
        self.parser = QRCodeParser()
        # Initialize QR code detector from OpenCV (secure, no external data sharing)
        self.qr_detector = cv2.QRCodeDetector()
        
        logger.info("QRCodeScanner initialized with secure local detectors only")
        
        # Configuration - simplified for better performance
        self.use_qr_region_extraction = True  # Focus on QR regions first
        self.use_geometric_scan = True        # Try rotations as fallback
        self.use_adaptive_scan = True         # Try adaptive thresholding as last resort
    
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
    
    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by the given angle in degrees"""
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # Get rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Perform rotation
        rotated = cv2.warpAffine(image, rotation_matrix, (width, height))
        
        return rotated
    
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
    
    def _try_opencv_qr_detect(self, image: np.ndarray) -> Tuple[bool, List[str], Optional[np.ndarray], Optional[List[np.ndarray]]]:
        """Try to detect and decode QR code using OpenCV"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
                
            # Detect and decode
            result = self.qr_detector.detectAndDecodeMulti(gray)
            points = result[2] if result[2] is not None else None
            straight_codes = list(result[3]) if result[3] is not None else None
            return result[0], list(result[1]), points, straight_codes
        except Exception as e:
            logger.debug(f"OpenCV QR detection error: {e}")
            return False, [], None, None
    
    def _extract_cccd_qr_regions(self, image: np.ndarray) -> List[Tuple[str, np.ndarray]]:
        """
        Extract potential QR regions from CCCD card based on known positions
        Returns list of (region_name, region_image) tuples
        """
        regions = []
        h, w = image.shape[:2]
        
        try:
            # Region 1: Bottom-right corner (most common for CCCD QR)
            # QR typically occupies about 1/4 to 1/3 of the card width/height
            qr_size_small = min(h, w) // 4
            qr_size_large = min(h, w) // 3
            
            # Small bottom-right region
            bottom_right_small = image[h-qr_size_small:h, w-qr_size_small:w]
            if bottom_right_small.size > 0:
                regions.append(("bottom_right_small", bottom_right_small))
            
            # Larger bottom-right region
            bottom_right_large = image[h-qr_size_large:h, w-qr_size_large:w]
            if bottom_right_large.size > 0:
                regions.append(("bottom_right_large", bottom_right_large))
            
            # Region 2: Right side (in case QR is positioned differently)
            right_width = w // 3
            right_region = image[h//4:h, w-right_width:w]
            if right_region.size > 0:
                regions.append(("right_side", right_region))
            
            # Region 3: Bottom side 
            bottom_height = h // 3
            bottom_region = image[h-bottom_height:h, w//4:w]
            if bottom_region.size > 0:
                regions.append(("bottom_side", bottom_region))
                
        except Exception as e:
            logger.debug(f"Error extracting QR regions: {e}")
        
        return regions

    def _try_secure_qr_detect(self, image: np.ndarray) -> Optional[str]:
        """
        Try QR detection using only secure local libraries (no external data sharing)
        """
        # Method 1: Try pyzbar (very reliable for clear QR codes)
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            qr_codes = pyzbar.decode(gray)
            if qr_codes:
                qr_data = qr_codes[0].data.decode('utf-8')
                logger.debug("✓ pyzbar detection successful")
                return qr_data
        except Exception as e:
            logger.debug(f"pyzbar detection error: {e}")
        
        # Method 2: Try OpenCV QR detector
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            retval, decoded_info, _, _ = self.qr_detector.detectAndDecodeMulti(gray)
            if retval and decoded_info and decoded_info[0]:
                logger.debug("✓ OpenCV detection successful")
                return decoded_info[0]
        except Exception as e:
            logger.debug(f"OpenCV detection error: {e}")
        
        return None
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
        """
        Try to detect and extract the ID card from the image
        Uses advanced contour filtering with solidity check
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
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
            
            # Take the top 5 contours (increased from 3)
            for contour in contours[:5]:
                # Get area
                area = cv2.contourArea(contour)
                
                # Skip small contours
                if area < 10000:  # Adjust threshold based on typical card size
                    continue
                
                # Calculate solidity (area / convex hull area)
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                solidity = float(area) / hull_area if hull_area > 0 else 0
                
                # Skip if solidity is too low (not solid enough to be a card)
                if solidity < 0.8:
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
                    
                    # Check aspect ratio (typical ID cards have ratio around 1.5-1.6)
                    aspect_ratio = float(w) / h
                    if aspect_ratio < 1.3 or aspect_ratio > 1.9:
                        continue
                    
                    # Get the card region
                    card_region = image[y:y+h, x:x+w]
                    
                    return card_region
            
            # If no suitable contour found, try Hough Line method
            return self._try_detect_card_with_hough_lines(image)
            
        except Exception as e:
            logger.debug(f"Error in card detection: {e}")
            return None
    
    def _try_detect_card_with_hough_lines(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Alternative card detection using Hough Line Transform"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply Canny edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find lines using Hough Transform
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
            
            if lines is None or len(lines) < 4:
                return None
            
            # Create a blank image to draw lines
            line_image = np.zeros_like(gray)
            
            # Draw lines
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(line_image, (x1, y1), (x2, y2), (255,), 2)
            
            # Dilate lines to connect gaps
            kernel = np.ones((5, 5), np.uint8)
            dilated_lines = cv2.dilate(line_image, kernel, iterations=1)
            
            # Find contours in the line image
            contours, _ = cv2.findContours(dilated_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Find the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Approximate the contour to a polygon
            peri = cv2.arcLength(largest_contour, True)
            approx = cv2.approxPolyDP(largest_contour, 0.02 * peri, True)
            
            # If the polygon has 4 points, it might be the card
            if len(approx) == 4:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(approx)
                
                # Check aspect ratio
                aspect_ratio = float(w) / h
                if aspect_ratio < 1.3 or aspect_ratio > 1.9:
                    return None
                
                # Get the card region
                card_region = image[y:y+h, x:x+w]
                
                return card_region
            
            return None
            
        except Exception as e:
            logger.debug(f"Error in Hough line detection: {e}")
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
        Optimized multi-stage QR code detection focusing on QR region extraction:
        
        1. QR Region Scan: Extract and scan known QR regions first
        2. Direct Scan: Try detection on full image  
        3. Geometric Scan: Rotation corrections (if needed)
        4. Adaptive Scan: Enhanced preprocessing (last resort)
        """
        start_time = time.time()
        
        # STAGE 1: QR Region Scan (most effective for CCCD)
        if self.use_qr_region_extraction:
            logger.debug("Stage 1: QR Region Scan - Extracting and scanning known QR positions")
            
            qr_regions = self._extract_cccd_qr_regions(image)
            for region_name, region in qr_regions:
                qr_data = self._try_secure_qr_detect(region)
                if qr_data:
                    logger.debug(f"✓ QR detected in {region_name}")
                    processing_time = time.time() - start_time
                    response = self._create_success_response(qr_data)
                    response.processing_time = processing_time
                    return response
        
        # STAGE 2: Direct Scan (full image without preprocessing)
        logger.debug("Stage 2: Direct Scan - Full image detection")
        qr_data = self._try_secure_qr_detect(image)
        if qr_data:
            logger.debug("✓ Direct detection successful")
            processing_time = time.time() - start_time
            response = self._create_success_response(qr_data)
            response.processing_time = processing_time
            return response
        
        # STAGE 3: Geometric Scan (rotations)
        if self.use_geometric_scan:
            logger.debug("Stage 3: Geometric Scan - Trying rotations")
            
            for angle in [90, 180, 270]:
                rotated = self._rotate_image(image, angle)
                
                # Try on rotated QR regions first
                if self.use_qr_region_extraction:
                    qr_regions = self._extract_cccd_qr_regions(rotated)
                    for region_name, region in qr_regions:
                        qr_data = self._try_secure_qr_detect(region)
                        if qr_data:
                            logger.debug(f"✓ QR detected in {region_name} after {angle}° rotation")
                            processing_time = time.time() - start_time
                            response = self._create_success_response(qr_data)
                            response.processing_time = processing_time
                            return response
                
                # Try on full rotated image
                qr_data = self._try_secure_qr_detect(rotated)
                if qr_data:
                    logger.debug(f"✓ Detection successful after {angle}° rotation")
                    processing_time = time.time() - start_time
                    response = self._create_success_response(qr_data)
                    response.processing_time = processing_time
                    return response
        
        # STAGE 4: Adaptive Scan (enhanced preprocessing)
        if self.use_adaptive_scan:
            logger.debug("Stage 4: Adaptive Scan - Enhanced preprocessing")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Try different preprocessing approaches
            preprocessing_methods = [
                ("adaptive_threshold", lambda img: cv2.adaptiveThreshold(
                    cv2.GaussianBlur(img, (5, 5), 0), 255, 
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )),
                ("otsu_threshold", lambda img: cv2.threshold(
                    img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )[1]),
                ("contrast_enhancement", lambda img: cv2.createCLAHE(
                    clipLimit=2.0, tileGridSize=(8,8)
                ).apply(img))
            ]
            
            for method_name, method_func in preprocessing_methods:
                try:
                    processed = method_func(gray)
                    
                    # Try on processed QR regions first
                    if self.use_qr_region_extraction:
                        qr_regions = self._extract_cccd_qr_regions(processed)
                        for region_name, region in qr_regions:
                            qr_data = self._try_secure_qr_detect(region)
                            if qr_data:
                                logger.debug(f"✓ QR detected in {region_name} with {method_name}")
                                processing_time = time.time() - start_time
                                response = self._create_success_response(qr_data)
                                response.processing_time = processing_time
                                return response
                    
                    # Try on full processed image
                    qr_data = self._try_secure_qr_detect(processed)
                    if qr_data:
                        logger.debug(f"✓ Detection successful with {method_name}")
                        processing_time = time.time() - start_time
                        response = self._create_success_response(qr_data)
                        response.processing_time = processing_time
                        return response
                        
                except Exception as e:
                    logger.debug(f"Error with {method_name}: {e}")
        
        # If all methods fail
        processing_time = time.time() - start_time
        logger.debug(f"All detection stages failed after {processing_time:.2f}s")
        return QRScanResponse(
            success=False, 
            message="QR code not detected with any method",
            processing_time=processing_time
        )
