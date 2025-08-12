"""
Ambiguous Query Detection and Processing Service
Phát hiện và xử lý câu hỏi mơ hồ để tối ưu hóa RAG
"""

import logging
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.config import settings

logger = logging.getLogger(__name__)

class AmbiguousQueryService:
    """Service xử lý câu hỏi mơ hồ với vector embedding approach"""
    
    def __init__(self, embedding_model: Optional[SentenceTransformer] = None):
        """
        Args:
            embedding_model: Reuse embedding model from VectorDBService (CPU)
        """
        self.embedding_model = embedding_model
        self.ambiguous_patterns = {}
        self.clarification_templates = {}
        
        # Thư mục lưu data câu hỏi mơ hồ
        self.data_dir = settings.base_dir / "data" / "ambiguous_queries"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing patterns
        self._load_ambiguous_patterns()
        
    def _load_ambiguous_patterns(self):
        """Load patterns from JSON files"""
        try:
            patterns_file = self.data_dir / "ambiguous_patterns.json"
            templates_file = self.data_dir / "clarification_templates.json"
            
            # Load ambiguous patterns
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.ambiguous_patterns = json.load(f)
                logger.info(f"Loaded {len(self.ambiguous_patterns)} ambiguous patterns")
            else:
                self._create_default_patterns()
                
            # Load clarification templates  
            if templates_file.exists():
                with open(templates_file, 'r', encoding='utf-8') as f:
                    self.clarification_templates = json.load(f)
                logger.info(f"Loaded {len(self.clarification_templates)} clarification templates")
            else:
                self._create_default_templates()
                
        except Exception as e:
            logger.error(f"Error loading ambiguous patterns: {e}")
            self._create_default_patterns()
            self._create_default_templates()
    
    def _create_default_patterns(self):
        """Tạo patterns mặc định cho câu hỏi mơ hồ"""
        self.ambiguous_patterns = {
            "general_procedure": {
                "examples": [
                    "thủ tục như thế nào",
                    "làm sao để xin",
                    "cần giấy tờ gì",
                    "thủ tục xin cấp",
                    "hồ sơ gồm những gì",
                    "quy trình thực hiện"
                ],
                "category": "procedure_inquiry",
                "confidence_threshold": 0.7
            },
            "time_related": {
                "examples": [
                    "mất bao lâu",
                    "thời gian xử lý",
                    "khi nào có kết quả", 
                    "bao giờ được duyệt",
                    "thời hạn giải quyết"
                ],
                "category": "time_inquiry", 
                "confidence_threshold": 0.75
            },
            "cost_related": {
                "examples": [
                    "tốn bao nhiều tiền",
                    "lệ phí",
                    "phí dịch vụ",
                    "chi phí",
                    "mức thu"
                ],
                "category": "cost_inquiry",
                "confidence_threshold": 0.8
            },
            "location_related": {
                "examples": [
                    "ở đâu làm",
                    "nộp hồ sơ tại",
                    "địa chỉ cơ quan", 
                    "phòng ban nào",
                    "cửa khẩu nào"
                ],
                "category": "location_inquiry",
                "confidence_threshold": 0.75
            }
        }
        
        # Save to file
        patterns_file = self.data_dir / "ambiguous_patterns.json"
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump(self.ambiguous_patterns, f, indent=2, ensure_ascii=False)
        logger.info("Created default ambiguous patterns")
        
    def _create_default_templates(self):
        """Tạo templates mặc định cho clarification"""
        self.clarification_templates = {
            "procedure_inquiry": {
                "template": "Bạn muốn hỏi về thủ tục gì cụ thể? Vui lòng chọn:",
                "options": [
                    "Thủ tục xin cấp giấy phép kinh doanh",
                    "Thủ tục đăng ký kết hôn", 
                    "Thủ tục xin visa",
                    "Thủ tục đăng ký xe",
                    "Thủ tục khác (xin nhập rõ)"
                ]
            },
            "time_inquiry": {
                "template": "Bạn muốn biết thời gian xử lý của thủ tục nào?",
                "options": [
                    "Thời gian cấp giấy phép kinh doanh",
                    "Thời gian đăng ký kết hôn",
                    "Thời gian xử lý visa",
                    "Thời gian đăng ký xe",
                    "Thủ tục khác (xin nhập rõ)"
                ]
            },
            "cost_inquiry": {
                "template": "Bạn muốn biết chi phí của thủ tục nào?", 
                "options": [
                    "Lệ phí giấy phép kinh doanh",
                    "Lệ phí đăng ký kết hôn",
                    "Lệ phí visa",
                    "Lệ phí đăng ký xe",
                    "Thủ tục khác (xin nhập rõ)"
                ]
            },
            "location_inquiry": {
                "template": "Bạn muốn biết địa điểm thực hiện thủ tục nào?",
                "options": [
                    "Nơi làm giấy phép kinh doanh", 
                    "Nơi đăng ký kết hôn",
                    "Nơi nộp hồ sơ visa",
                    "Nơi đăng ký xe",
                    "Thủ tục khác (xin nhập rõ)"
                ]
            }
        }
        
        # Save to file
        templates_file = self.data_dir / "clarification_templates.json"
        with open(templates_file, 'w', encoding='utf-8') as f:
            json.dump(self.clarification_templates, f, indent=2, ensure_ascii=False)
        logger.info("Created default clarification templates")
    
    def is_ambiguous(self, query: str) -> Tuple[bool, str, float]:
        """
        Kiểm tra câu hỏi có mơ hồ không
        
        Returns:
            (is_ambiguous, category, confidence)
        """
        if not self.embedding_model:
            return False, "", 0.0
            
        try:
            # Encode query
            query_vector = self.embedding_model.encode([query.lower().strip()])
            
            max_similarity = 0.0
            best_category = ""
            
            # So sánh với từng pattern
            for category, pattern_data in self.ambiguous_patterns.items():
                examples = pattern_data["examples"]
                threshold = pattern_data["confidence_threshold"]
                
                # Encode examples
                example_vectors = self.embedding_model.encode(examples)
                
                # Tính similarity
                similarities = cosine_similarity(query_vector, example_vectors)[0]
                max_sim_in_category = max(similarities)
                
                if max_sim_in_category > max_similarity:
                    max_similarity = max_sim_in_category
                    best_category = category
            
            # Quyết định dựa trên threshold
            if best_category and max_similarity >= self.ambiguous_patterns[best_category]["confidence_threshold"]:
                return True, best_category, max_similarity
            else:
                return False, "", max_similarity
                
        except Exception as e:
            logger.error(f"Error in ambiguity detection: {e}")
            return False, "", 0.0
    
    def get_clarification_prompt(self, category: str) -> Dict[str, Any]:
        """
        Lấy prompt làm rõ cho category
        """
        if category not in self.clarification_templates:
            return {
                "template": "Câu hỏi của bạn cần được làm rõ thêm. Bạn có thể cung cấp thêm chi tiết không?",
                "options": ["Vui lòng nhập chi tiết cụ thể"]
            }
        
        return self.clarification_templates[category]
    
    def generate_clarifying_questions(self, query: str, category: str, llm_service) -> List[str]:
        """
        Sử dụng LLM để sinh câu hỏi làm rõ động
        """
        try:
            prompt = f"""
Dựa vào câu hỏi người dùng: "{query}"
Và category đã xác định: "{category}"

Hãy tạo ra 3-4 câu hỏi làm rõ cụ thể để giúp người dùng trả lời chính xác hơn.
Câu hỏi phải:
1. Cụ thể và rõ ràng
2. Liên quan đến thủ tục hành chính Việt Nam
3. Giúp thu hẹp phạm vi truy vấn

Định dạng trả về:
1. [Câu hỏi 1]
2. [Câu hỏi 2]
3. [Câu hỏi 3]
"""
            
            response_data = llm_service.generate_response(prompt, max_tokens=200)
            
            # Extract response text from dict
            if isinstance(response_data, dict) and "response" in response_data:
                response = response_data["response"]
            elif isinstance(response_data, str):
                response = response_data
            else:
                response = str(response_data)
            
            # Parse response thành list
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            questions = []
            for line in lines:
                if line.startswith(('1.', '2.', '3.', '4.')):
                    questions.append(line[2:].strip())
            
            return questions if questions else ["Bạn có thể cung cấp thêm chi tiết cụ thể không?"]
            
        except Exception as e:
            logger.error(f"Error generating clarifying questions: {e}")
            return ["Bạn có thể cung cấp thêm chi tiết cụ thể không?"]
    
    def add_ambiguous_pattern(self, category: str, examples: List[str], threshold: float = 0.7):
        """Thêm pattern mới cho câu hỏi mơ hồ"""
        self.ambiguous_patterns[category] = {
            "examples": examples,
            "category": category, 
            "confidence_threshold": threshold
        }
        
        # Save to file
        patterns_file = self.data_dir / "ambiguous_patterns.json"
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump(self.ambiguous_patterns, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Added new ambiguous pattern: {category}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Thống kê hệ thống"""
        return {
            "total_patterns": len(self.ambiguous_patterns),
            "total_templates": len(self.clarification_templates), 
            "categories": list(self.ambiguous_patterns.keys()),
            "embedding_model_device": "CPU (optimized for VRAM)"
        }
