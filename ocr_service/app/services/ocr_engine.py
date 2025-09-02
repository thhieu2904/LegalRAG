"""
VietOCR Engine Implementation for CCCD Recognition
CPU-optimized version with comprehensive text extraction
"""
import asyncio
import logging
import re
import time
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
import torch

from ..core.config import get_settings
from ..models.schemas import CCCDExtractedData, ConfidenceScores, CCCDSide


logger = logging.getLogger(__name__)
settings = get_settings()


class VietOCREngine:
    """Vietnamese OCR Engine optimized for CCCD processing"""
    
    def __init__(self):
        self.predictor = None
        self.is_loaded = False
        self._load_start_time = None
        self._total_extractions = 0
        self._successful_extractions = 0
        
        # CCCD field patterns
        self.patterns = {
            'id_number': [
                r'(?:Số|So)\s*:?\s*(\d{12})',
                r'(\d{12})',
                r'ID\s*:?\s*(\d{12})',
                r'CCCD\s*:?\s*(\d{12})'
            ],
            'full_name': [
                r'(?:Họ và tên|Ho va ten|Họ tên|Ho ten)\s*:?\s*([A-ZÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾỂỄỆĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỠỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ\s]+)',
                r'(?:Full name|Name)\s*:?\s*([A-ZÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾỂỄỆĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỠỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ\s]+)',
                r'^([A-ZÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾỂỄỆĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỠỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ\s]{10,50})$'
            ],
            'date_of_birth': [
                r'(?:Ngày sinh|Ngay sinh|Date of birth|DOB)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'(?:Born|Birth)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})'
            ],
            'gender': [
                r'(?:Giới tính|Gioi tinh|Sex|Gender)\s*:?\s*(Nam|Nữ|Nu|Male|Female|M|F)',
                r'\b(Nam|Nữ|Nu|Male|Female)\b'
            ],
            'nationality': [
                r'(?:Quốc tịch|Quoc tich|Nationality)\s*:?\s*(Việt Nam|Viet Nam|Vietnamese)',
                r'(Việt Nam|Viet Nam|Vietnamese)'
            ],
            'hometown': [
                r'(?:Quê quán|Que quan|Place of origin|Origin)\s*:?\s*([A-ZÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾỂỄỆĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỠỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ\s,.-]+)',
                r'(?:Hometown|Home)\s*:?\s*([A-ZÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾỂỄỆĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỠỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ\s,.-]+)'
            ],
            'residence': [
                r'(?:Nơi thường trú|Noi thuong tru|Residence|Address)\s*:?\s*([A-ZÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾỂỄỆĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỠỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ\s,.-0-9]+)',
                r'(?:Thường trú|Thuong tru)\s*:?\s*([A-ZÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾỂỄỆĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỠỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ\s,.-0-9]+)'
            ],
            'issue_date': [
                r'(?:Ngày cấp|Ngay cap|Date of issue|Issued)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'(?:Cấp ngày|Cap ngay)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})'
            ],
            'expiry_date': [
                r'(?:Có giá trị đến|Co gia tri den|Valid until|Expires)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'(?:Hết hạn|Het han|Expiry)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})',
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})(?=\s*$)'
            ],
            'issued_by': [
                r'(?:Nơi cấp|Noi cap|Issued by)\s*:?\s*([A-ZÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾỂỄỆĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỠỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ\s,.-]+)',
                r'(?:Cơ quan cấp|Co quan cap)\s*:?\s*([A-ZÀÁÃẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẺẼÊỀẾỂỄỆĐÌÍĨỈỊÒÓÕỌỎÔỐỒỔỖỘƠỚỜỞỠỢÙÚŨỤỦƯỨỪỬỮỰỲÝỴỶỸ\s,.-]+)'
            ]
        }
        
        # Confidence calculation weights
        self.confidence_weights = {
            'id_number': 0.25,
            'full_name': 0.20,
            'date_of_birth': 0.15,
            'gender': 0.10,
            'nationality': 0.05,
            'hometown': 0.10,
            'residence': 0.10,
            'issue_date': 0.05
        }
    
    async def load_model(self) -> bool:
        """Load VietOCR model with CPU optimization"""
        try:
            self._load_start_time = time.time()
            logger.info("Loading VietOCR model with CPU optimization...")
            
            # Force CPU usage
            torch.set_num_threads(settings.TORCH_CPU_THREADS)
            
            # Set local cache directory for models
            import os
            model_cache_dir = Path(__file__).parent.parent.parent / "data" / "models"
            model_cache_dir.mkdir(parents=True, exist_ok=True)
            os.environ['TORCH_HOME'] = str(model_cache_dir / "torch_cache")
            os.environ['TRANSFORMERS_CACHE'] = str(model_cache_dir / "hf_cache")
            
            # Configure VietOCR for CPU usage
            config = Cfg.load_config_from_name('vgg_transformer')
            config['device'] = 'cpu'
            config['predictor']['beamsearch'] = False  # Disable beam search for speed
            config['predictor']['batch_size'] = 1
            
            # Create predictor
            self.predictor = Predictor(config)
            
            self.is_loaded = True
            load_time = time.time() - self._load_start_time
            logger.info(f"VietOCR model loaded successfully in {load_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load VietOCR model: {str(e)}")
            self.is_loaded = False
            return False
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive threshold for better text contrast
            adaptive = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply morphological operations to clean up text
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}")
            return image
    
    def detect_cccd_side(self, text: str) -> CCCDSide:
        """Detect if image is front or back side of CCCD"""
        text_lower = text.lower()
        
        # Front side indicators
        front_indicators = [
            'số căn cước công dân', 'so can cuoc cong dan',
            'họ và tên', 'ho va ten', 'ngày sinh', 'ngay sinh',
            'giới tính', 'gioi tinh', 'quê quán', 'que quan'
        ]
        
        # Back side indicators  
        back_indicators = [
            'đặc điểm nhận dạng', 'dac diem nhan dang',
            'ngày cấp', 'ngay cap', 'có giá trị đến', 'co gia tri den',
            'nơi cấp', 'noi cap', 'nơi thường trú', 'noi thuong tru'
        ]
        
        front_count = sum(1 for indicator in front_indicators if indicator in text_lower)
        back_count = sum(1 for indicator in back_indicators if indicator in text_lower)
        
        return CCCDSide.FRONT if front_count > back_count else CCCDSide.BACK
    
    def extract_field(self, text: str, field_name: str) -> Tuple[Optional[str], float]:
        """Extract a specific field from text with confidence score"""
        if field_name not in self.patterns:
            return None, 0.0
        
        patterns = self.patterns[field_name]
        best_match = None
        best_confidence = 0.0
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                value = match.group(1).strip() if match.groups() else match.group(0).strip()
                
                if not value:
                    continue
                
                # Calculate confidence based on pattern specificity and text quality
                confidence = self._calculate_field_confidence(field_name, value, pattern, text)
                
                if confidence > best_confidence:
                    best_match = value
                    best_confidence = confidence
        
        # Post-process the extracted value
        if best_match:
            best_match = self._post_process_field(field_name, best_match)
        
        return best_match, best_confidence
    
    def _calculate_field_confidence(self, field_name: str, value: str, pattern: str, full_text: str) -> float:
        """Calculate confidence score for extracted field"""
        base_confidence = 0.5
        
        # Pattern specificity bonus
        if ':' in pattern:
            base_confidence += 0.2
        if field_name.lower() in pattern.lower():
            base_confidence += 0.2
        
        # Value quality checks
        if field_name == 'id_number':
            if len(value) == 12 and value.isdigit():
                base_confidence += 0.3
            else:
                base_confidence -= 0.3
        
        elif field_name == 'full_name':
            if 10 <= len(value) <= 50 and not any(char.isdigit() for char in value):
                base_confidence += 0.2
            else:
                base_confidence -= 0.2
        
        elif field_name in ['date_of_birth', 'issue_date', 'expiry_date']:
            if self._validate_date_format(value):
                base_confidence += 0.3
            else:
                base_confidence -= 0.3
        
        elif field_name == 'gender':
            valid_genders = ['Nam', 'Nữ', 'Nu', 'Male', 'Female', 'M', 'F']
            if value in valid_genders:
                base_confidence += 0.3
            else:
                base_confidence -= 0.3
        
        # Context bonus - if field appears near related keywords
        context_keywords = {
            'id_number': ['căn cước công dân', 'can cuoc cong dan', 'CCCD', 'ID'],
            'full_name': ['họ và tên', 'ho va ten', 'name'],
            'date_of_birth': ['ngày sinh', 'ngay sinh', 'birth'],
            'gender': ['giới tính', 'gioi tinh', 'sex'],
            'nationality': ['quốc tịch', 'quoc tich', 'nationality'],
            'hometown': ['quê quán', 'que quan', 'origin'],
            'residence': ['thường trú', 'thuong tru', 'residence'],
            'issue_date': ['ngày cấp', 'ngay cap', 'issued'],
            'expiry_date': ['có giá trị', 'co gia tri', 'valid'],
            'issued_by': ['nơi cấp', 'noi cap', 'issued by']
        }
        
        if field_name in context_keywords:
            for keyword in context_keywords[field_name]:
                if keyword.lower() in full_text.lower():
                    base_confidence += 0.1
                    break
        
        return min(1.0, max(0.0, base_confidence))
    
    def _validate_date_format(self, date_str: str) -> bool:
        """Validate date format (DD/MM/YYYY or DD-MM-YYYY)"""
        try:
            # Replace - with /
            date_str = date_str.replace('-', '/')
            parts = date_str.split('/')
            
            if len(parts) != 3:
                return False
            
            day, month, year = map(int, parts)
            
            # Basic validation
            if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100):
                return False
            
            return True
            
        except (ValueError, AttributeError):
            return False
    
    def _post_process_field(self, field_name: str, value: str) -> str:
        """Post-process extracted field value"""
        value = value.strip()
        
        if field_name == 'full_name':
            # Capitalize properly
            value = ' '.join(word.capitalize() for word in value.split())
        
        elif field_name == 'gender':
            # Normalize gender values
            gender_map = {
                'Nam': 'Nam', 'Nữ': 'Nữ', 'Nu': 'Nữ',
                'Male': 'Nam', 'Female': 'Nữ',
                'M': 'Nam', 'F': 'Nữ'
            }
            value = gender_map.get(value, value)
        
        elif field_name in ['date_of_birth', 'issue_date', 'expiry_date']:
            # Normalize date format to DD/MM/YYYY
            value = value.replace('-', '/')
        
        elif field_name in ['hometown', 'residence', 'issued_by']:
            # Clean up address/location fields
            value = ' '.join(value.split())  # Remove extra whitespace
            value = value.replace(',', ', ')  # Fix comma spacing
        
        return value
    
    async def extract_text_from_image(self, image: np.ndarray) -> str:
        """Extract text from image using VietOCR"""
        if not self.is_loaded:
            raise RuntimeError("VietOCR model not loaded")
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Convert to PIL Image
            if len(processed_image.shape) == 2:
                pil_image = Image.fromarray(processed_image, mode='L')
            else:
                pil_image = Image.fromarray(processed_image)
            
            # Extract text using VietOCR
            start_time = time.time()
            text = self.predictor.predict(pil_image)
            extraction_time = time.time() - start_time
            
            logger.debug(f"Text extraction completed in {extraction_time:.2f}s")
            return text
            
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise
    
    async def process_cccd_image(self, image: np.ndarray, side: CCCDSide = None) -> Tuple[CCCDExtractedData, ConfidenceScores, CCCDSide]:
        """Process CCCD image and extract structured data"""
        if not self.is_loaded:
            raise RuntimeError("VietOCR model not loaded")
        
        start_time = time.time()
        self._total_extractions += 1
        
        try:
            # Extract text from image
            text = await self.extract_text_from_image(image)
            logger.debug(f"Extracted text: {text[:200]}...")
            
            # Auto-detect side if not provided
            if side is None:
                side = self.detect_cccd_side(text)
                logger.debug(f"Detected CCCD side: {side}")
            
            # Extract structured data
            extracted_data = CCCDExtractedData()
            confidence_scores = ConfidenceScores()
            
            # Extract all fields
            for field_name in self.patterns.keys():
                value, confidence = self.extract_field(text, field_name)
                
                if value:
                    setattr(extracted_data, field_name, value)
                    setattr(confidence_scores, field_name, confidence)
                    logger.debug(f"Extracted {field_name}: {value} (confidence: {confidence:.2f})")
            
            # Calculate overall confidence
            total_weight = 0.0
            weighted_confidence = 0.0
            
            for field_name, weight in self.confidence_weights.items():
                field_confidence = getattr(confidence_scores, field_name, None)
                if field_confidence is not None:
                    weighted_confidence += field_confidence * weight
                    total_weight += weight
            
            if total_weight > 0:
                confidence_scores.overall_confidence = weighted_confidence / total_weight
            else:
                confidence_scores.overall_confidence = 0.0
            
            # Track success
            if confidence_scores.overall_confidence > 0.5:
                self._successful_extractions += 1
            
            processing_time = time.time() - start_time
            logger.info(f"CCCD processing completed in {processing_time:.2f}s with confidence {confidence_scores.overall_confidence:.2f}")
            
            return extracted_data, confidence_scores, side
            
        except Exception as e:
            logger.error(f"CCCD processing failed: {str(e)}")
            raise
    
    async def process_both_sides(
        self, 
        front_image: np.ndarray, 
        back_image: Optional[np.ndarray] = None
    ) -> Tuple[CCCDExtractedData, ConfidenceScores]:
        """Process both sides of CCCD and merge results"""
        
        # Process front side
        front_data, front_confidence, _ = await self.process_cccd_image(front_image, CCCDSide.FRONT)
        
        if back_image is None:
            return front_data, front_confidence
        
        # Process back side
        back_data, back_confidence, _ = await self.process_cccd_image(back_image, CCCDSide.BACK)
        
        # Merge results - prioritize data from appropriate sides
        merged_data = CCCDExtractedData()
        merged_confidence = ConfidenceScores()
        
        # Front side fields (prioritized)
        front_fields = ['id_number', 'full_name', 'date_of_birth', 'gender', 'nationality', 'hometown']
        back_fields = ['residence', 'issue_date', 'expiry_date', 'issued_by']
        
        # Use front side data for front fields, back side data for back fields
        for field in front_fields:
            front_value = getattr(front_data, field)
            back_value = getattr(back_data, field)
            front_conf = getattr(front_confidence, field, 0.0) or 0.0
            back_conf = getattr(back_confidence, field, 0.0) or 0.0
            
            if front_value and front_conf >= back_conf:
                setattr(merged_data, field, front_value)
                setattr(merged_confidence, field, front_conf)
            elif back_value:
                setattr(merged_data, field, back_value)
                setattr(merged_confidence, field, back_conf)
        
        for field in back_fields:
            front_value = getattr(front_data, field)
            back_value = getattr(back_data, field)
            front_conf = getattr(front_confidence, field, 0.0) or 0.0
            back_conf = getattr(back_confidence, field, 0.0) or 0.0
            
            if back_value and back_conf >= front_conf:
                setattr(merged_data, field, back_value)
                setattr(merged_confidence, field, back_conf)
            elif front_value:
                setattr(merged_data, field, front_value)
                setattr(merged_confidence, field, front_conf)
        
        # Recalculate overall confidence
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for field_name, weight in self.confidence_weights.items():
            field_confidence = getattr(merged_confidence, field_name, None)
            if field_confidence is not None:
                weighted_confidence += field_confidence * weight
                total_weight += weight
        
        if total_weight > 0:
            merged_confidence.overall_confidence = weighted_confidence / total_weight
        else:
            merged_confidence.overall_confidence = 0.0
        
        logger.info(f"Merged CCCD data with overall confidence: {merged_confidence.overall_confidence:.2f}")
        
        return merged_data, merged_confidence
    
    def get_stats(self) -> Dict[str, Any]:
        """Get OCR engine statistics"""
        return {
            'is_loaded': self.is_loaded,
            'total_extractions': self._total_extractions,
            'successful_extractions': self._successful_extractions,
            'success_rate': self._successful_extractions / max(1, self._total_extractions),
            'load_time': time.time() - self._load_start_time if self._load_start_time else None,
            'model_config': {
                'device': 'cpu',
                'cpu_threads': settings.TORCH_CPU_THREADS,
                'batch_size': 1
            }
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.predictor:
            del self.predictor
            self.predictor = None
        self.is_loaded = False
        logger.info("VietOCR engine cleaned up")


# Global engine instance
_ocr_engine = None


async def get_ocr_engine() -> VietOCREngine:
    """Get or create global OCR engine instance"""
    global _ocr_engine
    
    if _ocr_engine is None:
        _ocr_engine = VietOCREngine()
        await _ocr_engine.load_model()
    
    return _ocr_engine


async def cleanup_ocr_engine():
    """Cleanup global OCR engine"""
    global _ocr_engine
    
    if _ocr_engine is not None:
        await _ocr_engine.cleanup()
        _ocr_engine = None
