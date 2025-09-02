import base64
import cv2
import numpy as np
from pyzbar import pyzbar
from typing import Optional, Tuple
import time
from app.models.schemas import CCCDData, QRScanResponse
from app.services.qr_parser import QRCodeParser


class QRCodeScanner:
    """QR Code scanner for CCCD cards"""
    
    def __init__(self):
        self.parser = QRCodeParser()
    
    def scan_qr_from_base64(self, image_data: str) -> QRScanResponse:
        """
        Scan QR code from base64 encoded image
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
            
            # Scan for QR codes
            qr_codes = pyzbar.decode(image)
            
            if not qr_codes:
                return QRScanResponse(
                    success=False,
                    message="No QR code found in image"
                )
            
            # Process the first QR code found
            qr_code = qr_codes[0]
            qr_data = qr_code.data.decode('utf-8')
            
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
            
            processing_time = time.time() - start_time
            
            return QRScanResponse(
                success=True,
                data=cccd_data,
                message="QR code scanned successfully",
                processing_time=processing_time,
                confidence=1.0  # QR codes have high confidence when decoded
            )
            
        except Exception as e:
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
            print(f"Error decoding base64 image: {e}")
            return None
    
    def enhance_image_for_qr(self, image: np.ndarray) -> np.ndarray:
        """Enhance image quality for better QR code detection"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Apply adaptive threshold
            enhanced = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            return enhanced
            
        except Exception:
            return image
    
    def scan_with_enhancement(self, image_data: str) -> QRScanResponse:
        """Scan QR code with image enhancement"""
        try:
            # First try normal scanning
            result = self.scan_qr_from_base64(image_data)
            if result.success:
                return result
            
            # If failed, try with image enhancement
            image = self._decode_base64_image(image_data)
            if image is None:
                return QRScanResponse(
                    success=False,
                    message="Invalid image data"
                )
            
            enhanced_image = self.enhance_image_for_qr(image)
            
            # Encode enhanced image back to base64
            _, buffer = cv2.imencode('.jpg', enhanced_image)
            enhanced_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Try scanning enhanced image
            return self.scan_qr_from_base64(enhanced_base64)
            
        except Exception as e:
            return QRScanResponse(
                success=False,
                message=f"Error in enhanced scanning: {str(e)}"
            )
