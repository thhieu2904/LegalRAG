"""
CCCD QR Code Scanner Service
Scans Vietnamese Citizen ID (CCCD) QR codes and extracts data.
Uses only local libraries (OpenCV, pyzbar) for security.
"""

import base64
import cv2
import numpy as np
from pyzbar import pyzbar
from typing import Optional, Tuple, List
import time
import logging
import re
from datetime import datetime

from src.models import CCCDData, CCCDScanResponse

logger = logging.getLogger(__name__)


class QRCodeParser:
    """Parser for CCCD QR code data"""
    
    @staticmethod
    def parse_qr_data(qr_string: str) -> Optional[CCCDData]:
        """
        Parse QR code string from CCCD.
        Format: citizen_id | old_id | full_name | date_of_birth | gender | address | issue_date
        """
        try:
            parts = qr_string.strip().split('|')
            # Some cards append empty reserved columns. Keep the same seven
            # validated identity fields; never guess at non-empty extensions.
            while len(parts) > 7 and not parts[-1].strip():
                parts.pop()
            
            if len(parts) != 7:
                return None
                
            citizen_id, old_id, full_name, date_of_birth, gender, address, issue_date = parts
            
            # Validate citizen ID (12 digits)
            if not re.fullmatch(r'[0-9]{12}', citizen_id.strip()):
                return None
                
            # Format dates (DDMMYYYY -> DD/MM/YYYY)
            dob_formatted = QRCodeParser._format_date(date_of_birth.strip())
            issue_date_formatted = QRCodeParser._format_date(issue_date.strip())
            
            if not dob_formatted or not issue_date_formatted:
                return None
            
            return CCCDData(
                field_cccd=citizen_id.strip(),
                field_cmnd=old_id.strip() if old_id.strip() else None,
                field_ho_ten=full_name.strip(),
                field_ngay_sinh=dob_formatted,
                field_gioi_tinh=gender.strip(),
                field_dia_chi=address.strip(), 
                field_ngay_cap=issue_date_formatted
            )
            
        except Exception as e:
            logger.debug('QR parse failed (%s)', type(e).__name__)
            return None
    
    @staticmethod
    def _format_date(date_str: str) -> Optional[str]:
        """Format date from DDMMYYYY to DD/MM/YYYY"""
        try:
            if re.fullmatch(r'[0-9]{8}', date_str):
                datetime.strptime(date_str, '%d%m%Y')
                return f'{date_str[:2]}/{date_str[2:4]}/{date_str[4:]}'
            return None
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def validate_cccd_data(data: CCCDData) -> bool:
        """Validate extracted CCCD data - basic checks only"""
        try:
            # CCCD number must be 12 digits
            if not re.fullmatch(r'[0-9]{12}', data.field_cccd):
                return False
            
            # Name must not be empty
            if not data.field_ho_ten or len(data.field_ho_ten) < 2:
                return False
            
            # Date format validation
            if not QRCodeParser._format_date(data.field_ngay_sinh.replace('/', '')):
                return False
            if not QRCodeParser._format_date(data.field_ngay_cap.replace('/', '')):
                return False
            
            return True
            
        except Exception:
            return False


class CCCDScanner:
    """
    CCCD QR Code Scanner.
    Uses multi-stage detection for high accuracy.
    """
    
    def __init__(self):
        self.parser = QRCodeParser()
        self.qr_detector = cv2.QRCodeDetector()
        logger.info("CCCDScanner initialized")
    
    def scan(self, image_data: str) -> CCCDScanResponse:
        """
        Scan CCCD QR code from base64 image.
        
        Args:
            image_data: Base64 encoded image
            
        Returns:
            CCCDScanResponse with parsed data
        """
        start_time = time.perf_counter()
        
        try:
            # Decode image
            image = self._decode_base64_image(image_data)
            if image is None:
                return CCCDScanResponse(
                    success=False,
                    message="Không đọc được ảnh. Hãy chọn ảnh có mã QR rõ nét."
                )
            
            # Multi-stage detection
            result = self._multi_stage_detection(image)
            result.processing_time = time.perf_counter() - start_time
            logger.info('QR-only scan: success=%s duration_ms=%d', result.success,
                        round(result.processing_time * 1000))
            return result
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return CCCDScanResponse(
                success=False,
                message=f"Scan error: {str(e)}"
            )
    
    def _decode_base64_image(self, base64_string: str) -> Optional[np.ndarray]:
        """Decode base64 string to OpenCV image"""
        try:
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]

            if len(base64_string) > 14_000_000:
                return None
            image_data = base64.b64decode(base64_string, validate=True)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            logger.error(f"Error decoding image: {e}")
            return None
    
    def _extract_qr_regions(self, image: np.ndarray) -> List[Tuple[str, np.ndarray]]:
        """Extract potential QR regions from CCCD layout"""
        regions = []
        h, w = image.shape[:2]
        
        try:
            # Bottom-right corner (typical CCCD QR location)
            qr_size_small = min(h, w) // 4
            qr_size_large = min(h, w) // 3
            
            bottom_right_small = image[h-qr_size_small:h, w-qr_size_small:w]
            if bottom_right_small.size > 0:
                regions.append(("bottom_right_small", bottom_right_small))
            
            bottom_right_large = image[h-qr_size_large:h, w-qr_size_large:w]
            if bottom_right_large.size > 0:
                regions.append(("bottom_right_large", bottom_right_large))
            
            # Right side region
            right_width = w // 3
            right_region = image[h//4:h, w-right_width:w]
            if right_region.size > 0:
                regions.append(("right_side", right_region))
            
            # Bottom side region
            bottom_height = h // 3
            bottom_region = image[h-bottom_height:h, w//4:w]
            if bottom_region.size > 0:
                regions.append(("bottom_side", bottom_region))
                
        except Exception as e:
            logger.debug(f"Region extraction error: {e}")
        
        return regions
    
    def _detect_qr(self, image: np.ndarray) -> Optional[str]:
        """Only QR symbols with valid CCCD payloads, never OCR or barcodes.

        Try every candidate: a URL/unrelated QR in the image must not hide a
        later citizen-identity QR. Invalid candidates do not stop later stages.
        """
        # Method 1: pyzbar
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            qr_codes = pyzbar.decode(gray, symbols=[pyzbar.ZBarSymbol.QRCODE])
            for code in qr_codes:
                if code.type != 'QRCODE':
                    continue
                try:
                    payload = code.data.decode('utf-8')
                except UnicodeDecodeError:
                    continue
                parsed = self.parser.parse_qr_data(payload)
                if parsed is not None and self.parser.validate_cccd_data(parsed):
                    return payload
        except Exception as e:
            logger.debug(f"pyzbar error: {e}")
        
        # Method 2: OpenCV
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            retval, decoded_info, _, _ = self.qr_detector.detectAndDecodeMulti(gray)
            if retval:
                for payload in decoded_info:
                    parsed = self.parser.parse_qr_data(payload)
                    if parsed is not None and self.parser.validate_cccd_data(parsed):
                        return payload
        except Exception as e:
            logger.debug(f"OpenCV error: {e}")
        
        return None

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by angle in degrees"""
        # These recovery stages use right angles. Unlike warpAffine with the
        # old dimensions, they retain the edges of a portrait camera frame.
        if angle == 90:
            return np.rot90(image, 1).copy()
        if angle == 180:
            return np.rot90(image, 2).copy()
        if angle == 270:
            return np.rot90(image, 3).copy()
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, rotation_matrix, (w, h))
    
    def _create_success_response(self, qr_data: str) -> CCCDScanResponse:
        """Create success response with parsed data"""
        cccd_data = self.parser.parse_qr_data(qr_data)
        
        if not cccd_data:
            return CCCDScanResponse(
                success=False,
                message="Invalid QR code format"
            )
        
        if not self.parser.validate_cccd_data(cccd_data):
            return CCCDScanResponse(
                success=False,
                message="Invalid CCCD data",
                data=None
            )
        
        return CCCDScanResponse(
            success=True,
            data=cccd_data,
            message="QR code scanned successfully",
            confidence=1.0
        )
    
    def _multi_stage_detection(self, image: np.ndarray) -> CCCDScanResponse:
        """
        Multi-stage QR detection:
        1. Region-based detection (target known CCCD QR positions)
        2. Full image detection
        3. Rotation correction
        4. Image preprocessing
        """
        # Stage 1: Region-based
        for region_name, region in self._extract_qr_regions(image):
            qr_data = self._detect_qr(region)
            if qr_data:
                logger.debug(f"QR detected in {region_name}")
                return self._create_success_response(qr_data)
        
        # Stage 2: Full image
        qr_data = self._detect_qr(image)
        if qr_data:
            return self._create_success_response(qr_data)
        
        # Stage 3: Rotation correction
        for angle in [90, 180, 270]:
            rotated = self._rotate_image(image, angle)
            
            for region_name, region in self._extract_qr_regions(rotated):
                qr_data = self._detect_qr(region)
                if qr_data:
                    logger.debug(f"QR detected after {angle}° rotation")
                    return self._create_success_response(qr_data)
            
            qr_data = self._detect_qr(rotated)
            if qr_data:
                return self._create_success_response(qr_data)
        
        # Stage 4: Preprocessing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        preprocessing = [
            cv2.adaptiveThreshold(cv2.GaussianBlur(gray, (5, 5), 0), 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),
            cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(gray)
        ]
        
        for processed in preprocessing:
            for region_name, region in self._extract_qr_regions(processed):
                qr_data = self._detect_qr(region)
                if qr_data:
                    return self._create_success_response(qr_data)
            
            qr_data = self._detect_qr(processed)
            if qr_data:
                return self._create_success_response(qr_data)
        
        return CCCDScanResponse(
            success=False,
            message="Chưa đọc được mã QR căn cước hợp lệ. Đưa rõ mã QR vào khung hoặc chọn ảnh nét hơn; ảnh chỉ có chữ sẽ không được nhận diện."
        )
