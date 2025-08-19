#!/usr/bin/env python3
"""
Multi-Aspect Multi-Persona Smart Router Generator - Version 4
===========================================================

Sinh câu hỏi đa khía cạnh và đa vai trò để đạt mục tiêu 30+ câu hỏi/văn bản.
Phương pháp: Kết hợp từng content_chunk với từng persona người dùng phù hợp.
"""

import json
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sys
import argparse
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add app to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.services.language_model import LLMService
except ImportError as e:
    logger.error(f"❌ Cannot import LLMService: {e}")
    logger.error("   This could be due to missing dependencies (llama_cpp, etc.)")
    logger.error("   Make sure you're in the backend directory and all requirements are installed")
    logger.error("   You can install missing dependencies with: pip install llama-cpp-python")
    sys.exit(1)

class MultiAspectPersonaRouter:
    """Multi-aspect multi-persona router generator for comprehensive question generation."""
    
    def __init__(self, documents_dir: Optional[str] = None, output_dir: Optional[str] = None):
        self.documents_dir = Path(documents_dir or "data/documents")
        self.output_dir = Path(output_dir or "data/router_examples_smart_v3")
        
        # Initialize LLM service
        try:
            self.llm_service = LLMService()
            logger.info(f"✅ LLM Service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM Service: {e}")
            raise
        
        # Define 5 distinct user personas
        self.personas = {
            "nguoi_lan_dau": {
                "name": "Người Lần Đầu",
                "description": "Người chưa từng làm thủ tục, cần hướng dẫn cơ bản",
                "question_style": "Câu hỏi cơ bản, từng bước, dễ hiểu",
                "concerns": ["thủ tục cơ bản", "giấy tờ cần thiết", "bước đầu tiên"]
            },
            "nguoi_ban_ron": {
                "name": "Người Bận Rộn", 
                "description": "Người bận việc, muốn giải quyết nhanh, quan tâm thời gian",
                "question_style": "Câu hỏi về thời gian, tốc độ, hiệu quả",
                "concerns": ["thời gian xử lý", "cách nhanh nhất", "online/offline"]
            },
            "nguoi_can_than": {
                "name": "Người Cẩn Thận",
                "description": "Người muốn biết chi tiết, điều kiện, lưu ý đặc biệt",
                "question_style": "Câu hỏi chi tiết về điều kiện, rủi ro, lưu ý",
                "concerns": ["điều kiện cụ thể", "trường hợp đặc biệt", "lưu ý quan trọng"]
            },
            "nguoi_lam_ho": {
                "name": "Người Làm Hộ",
                "description": "Người đại diện, làm hộ cho người khác",
                "question_style": "Câu hỏi về ủy quyền, đại diện, làm hộ",
                "concerns": ["ủy quyền", "giấy tờ đại diện", "quyền hạn"]
            },
            "nguoi_gap_van_de": {
                "name": "Người Gặp Vấn Đề", 
                "description": "Người gặp khó khăn, cần giải quyết tình huống đặc biệt",
                "question_style": "Câu hỏi về xử lý sự cố, trường hợp khó khăn",
                "concerns": ["thiếu giấy tờ", "trường hợp đặc biệt", "giải quyết khó khăn"]
            }
        }
        
        # Define aspect-persona mapping (which personas are most relevant for each content type)
        self.aspect_persona_mapping = {
            "hồ sơ": ["nguoi_lan_dau", "nguoi_can_than", "nguoi_gap_van_de"],
            "thời gian": ["nguoi_ban_ron", "nguoi_lan_dau"],
            "chi phí": ["nguoi_ban_ron", "nguoi_can_than"],
            "điều kiện": ["nguoi_can_than", "nguoi_lan_dau"],
            "quy trình": ["nguoi_lan_dau", "nguoi_can_than"],
            "ủy quyền": ["nguoi_lam_ho", "nguoi_can_than"],
            "nơi thực hiện": ["nguoi_ban_ron", "nguoi_lan_dau"],
            "kết quả": ["nguoi_ban_ron", "nguoi_can_than"],
            "lưu ý": ["nguoi_can_than", "nguoi_gap_van_de"],
            "trường hợp đặc biệt": ["nguoi_gap_van_de", "nguoi_can_than"],
            "giấy tờ": ["nguoi_lan_dau", "nguoi_can_than", "nguoi_gap_van_de"]
        }

    def _classify_chunk_aspects(self, chunk: Dict[str, Any]) -> List[str]:
        """Phân loại chunk thuộc khía cạnh nào."""
        content = (chunk.get('content', '') + ' ' + chunk.get('section_title', '')).lower()
        keywords = chunk.get('keywords', [])
        
        aspects = []
        
        # Check for specific aspects based on content and keywords
        if any(word in content for word in ['hồ sơ', 'giấy tờ', 'tài liệu', 'chứng từ']):
            aspects.append('hồ sơ')
            aspects.append('giấy tờ')
            
        if any(word in content for word in ['thời gian', 'thời hạn', 'ngày', 'giờ']):
            aspects.append('thời gian')
            
        if any(word in content for word in ['lệ phí', 'chi phí', 'phí', 'tiền']):
            aspects.append('chi phí')
            
        if any(word in content for word in ['điều kiện', 'yêu cầu', 'quy định']):
            aspects.append('điều kiện')
            
        if any(word in content for word in ['quy trình', 'trình tự', 'bước', 'thủ tục']):
            aspects.append('quy trình')
            
        if any(word in content for word in ['ủy quyền', 'đại diện', 'thay mặt']):
            aspects.append('ủy quyền')
            
        if any(word in content for word in ['nơi', 'địa điểm', 'cơ quan', 'phòng']):
            aspects.append('nơi thực hiện')
            
        if any(word in content for word in ['kết quả', 'giấy', 'chứng', 'bằng']):
            aspects.append('kết quả')
            
        if any(word in content for word in ['lưu ý', 'chú ý', 'quan trọng', 'đặc biệt']):
            aspects.append('lưu ý')
            
        if any(word in content for word in ['trường hợp', 'ngoại lệ', 'đặc biệt', 'riêng']):
            aspects.append('trường hợp đặc biệt')
            
        # Default fallback
        if not aspects:
            aspects = ['quy trình', 'điều kiện']
            
        return list(set(aspects))  # Remove duplicates

    def _get_relevant_personas(self, aspects: List[str]) -> List[str]:
        """Lấy danh sách personas phù hợp với các aspects."""
        relevant_personas = set()
        
        for aspect in aspects:
            if aspect in self.aspect_persona_mapping:
                relevant_personas.update(self.aspect_persona_mapping[aspect])
        
        # Ensure we always have at least 2-3 personas
        if len(relevant_personas) < 2:
            relevant_personas.update(['nguoi_lan_dau', 'nguoi_can_than'])
            
        return list(relevant_personas)

    def _generate_questions_for_chunk_persona(self, chunk: Dict[str, Any], persona_key: str, 
                                            document_title: str, max_questions: int = 2) -> List[str]:
        """
        Sinh câu hỏi theo quy trình 2 bước: 1. Trích xuất thông tin, 2. Sinh câu hỏi.
        """
        persona = self.personas[persona_key]
        chunk_content = chunk.get('content', '')
        section_title = chunk.get('section_title', '')

        try:
            # === BƯỚC 1: TRÍCH XUẤT THÔNG TIN CỐT LÕI ===
            # Mục tiêu: Bắt LLM đọc và tóm tắt các ý chính một cách ngắn gọn, chính xác.
            # Chúng ta dùng temperature=0.0 để yêu cầu sự chính xác tuyệt đối, không sáng tạo.
            extraction_system_prompt = "Bạn là trợ lý AI chỉ chuyên trích xuất thông tin. Liệt kê các điểm thông tin chính từ văn bản sau thành các gạch đầu dòng ngắn gọn. Không giải thích, không bình luận."
            extraction_user_query = f"Văn bản về '{section_title}' của thủ tục '{document_title}':\n\n{chunk_content[:1500]}\n\nCác điểm thông tin chính:"
            
            extraction_response = self.llm_service.generate_response(
                user_query=extraction_user_query,
                system_prompt=extraction_system_prompt,
                max_tokens=250,
                temperature=0.0  # Yêu cầu sự chính xác, không "ảo giác"
            )
            extracted_topics = extraction_response.get('response', '').strip()

            # Nếu bước 1 thất bại, không có thông tin để làm bước 2 -> dừng lại
            if not extracted_topics or len(extracted_topics) < 10:
                logger.warning(f"      ⚠️ Bước 1 thất bại: Không trích xuất được thông tin từ chunk cho persona {persona_key}.")
                return []

            logger.info(f"      ✅ Bước 1 ({persona_key}): Trích xuất thành công chủ đề.")

            # === BƯỚC 2: SINH CÂU HỎI TỪ THÔNG TIN ĐÃ TRÍCH XUẤT ===
            # Mục tiêu: Dựa trên các ý chính sạch sẽ từ Bước 1, LLM sẽ đóng vai và đặt câu hỏi.
            # Yêu cầu này đơn giản hơn nhiều, nên chất lượng sẽ cao hơn.
            # Chúng ta dùng temperature=0.7 để cho phép một chút sáng tạo trong cách đặt câu hỏi.
            generation_system_prompt = f"""Đóng vai một '{persona['name']}' ({persona['description']}). Dựa vào các thông tin dưới đây, hãy đặt {max_questions} câu hỏi thực tế mà bạn quan tâm.

YÊU CẦU:
- Chỉ trả lời bằng câu hỏi.
- Mỗi câu hỏi trên một dòng.
- Không lặp lại thông tin, không giải thích, không đánh số.
"""
            generation_user_query = f"Thông tin về thủ tục '{document_title}':\n{extracted_topics}\n\nHãy đặt câu hỏi:"

            generation_response = self.llm_service.generate_response(
                user_query=generation_user_query,
                system_prompt=generation_system_prompt,
                max_tokens=200,
                temperature=0.7  # Cho phép sáng tạo trong cách hỏi
            )
            response_text = generation_response.get('response', '').strip()
            
            # Sử dụng lại các hàm làm sạch và xác thực mạnh mẽ của bạn
            questions = []
            for line in response_text.split('\n'):
                cleaned_question = self._clean_question_v4(line)
                if cleaned_question and self._is_valid_question(cleaned_question):
                    questions.append(cleaned_question)
            
            if questions:
                 logger.info(f"         ✅ Bước 2 ({persona_key}): Sinh ra {len(questions)} câu hỏi chất lượng.")
            else:
                 logger.warning(f"      ⚠️ Bước 2 ({persona_key}): Không sinh được câu hỏi nào.")

            return questions[:max_questions] if questions else []

        except Exception as e:
            logger.error(f"      ❌ Lỗi trong quy trình 2 bước cho persona {persona_key}: {e}")
            return []

    def _clean_question_v4(self, question: str) -> str:
        """Clean and standardize questions with enhanced cleaning."""
        # Filter out answer-like responses first (NEW)
        answer_keywords = [
            'trả lời:', 'theo thông tin', 'dựa trên nội dung', 'trong tài liệu',
            'sau khi nhận được', 'cán bộ tiếp nhận sẽ', 'giấy tờ nước ngoài',
            'yêu cầu về giấy tờ', 'tuy nhiên với', 'ví dụ:', 'theo quy định tại'
        ]
        if any(keyword in question.lower() for keyword in answer_keywords):
            return ""
        
        # Filter out statements that are clearly answers (not questions)  
        if question.strip().startswith(('Theo', 'Dựa vào', 'Như vậy', 'Do đó', 'Vì vậy')):
            return ""
            
        # Remove common prefixes and numbering
        question = re.sub(r'^(\d+[\.\)]?\s*)', '', question)
        question = re.sub(r'^[•\-\*]\s*', '', question)
        
        # Remove "Câu hỏi" prefixes (case insensitive)
        question = re.sub(r'^(câu hỏi\s*\d*[:\.]?\s*)', '', question, flags=re.IGNORECASE)
        
        # Remove meta-questions about question format
        if any(phrase in question.lower() for phrase in ['câu hỏi kết thúc', 'dấu ?', 'tại sao']):
            return ""
        
        # Ensure proper punctuation
        question = question.strip()
        if question and not question.endswith('?'):
            question += '?'
            
        # Filter out too short or generic questions
        if len(question) < 10:
            return ""
            
        return question

    def _is_valid_question(self, question: str) -> bool:
        """Validate if a string is actually a question, not a statement with '?' added."""
        # Remove the trailing '?' for analysis
        content = question.rstrip('?').strip()
        
        # Check if it starts with question words (Vietnamese)
        question_starters = [
            'ai', 'gì', 'đâu', 'khi nào', 'bao giờ', 'như thế nào', 'sao', 'tại sao',
            'có', 'có thể', 'có cần', 'có được', 'có phải', 'làm', 'làm sao', 'làm thế nào',
            'cần', 'cần gì', 'cần làm', 'phải', 'phải làm', 'giấy tờ nào', 'điều kiện',
            'thủ tục', 'quy trình', 'chi phí', 'thời gian', 'hồ sơ', 'địa điểm'
        ]
        
        content_lower = content.lower()
        
        # If it starts with typical question words, it's likely a valid question
        if any(content_lower.startswith(word) for word in question_starters):
            return True
            
        # If it contains question patterns in the middle
        question_patterns = ['có thể', 'có cần', 'bao nhiêu', 'mất bao lâu', 'ở đâu', 'như thế nào']
        if any(pattern in content_lower for pattern in question_patterns):
            return True
            
        # If it's too declarative (starts with statements), reject it
        declarative_starters = [
            'sau khi', 'cán bộ', 'giấy tờ', 'theo quy định', 'dựa trên', 'trong trường hợp',
            'việc', 'người', 'hồ sơ bao gồm', 'yêu cầu', 'quy định', 'trường hợp'
        ]
        
        if any(content_lower.startswith(word) for word in declarative_starters):
            return False
            
        return True  # Default to accepting if unclear

    def _deduplicate_questions(self, questions: List[str]) -> List[str]:
        """Loại bỏ câu hỏi trùng lặp hoặc tương tự với thuật toán cải tiến."""
        if not questions:
            return []
        
        # For small lists, use the detailed similarity check
        if len(questions) <= 50:
            return self._deduplicate_questions_similarity(questions)
        else:
            # For large lists, use the faster normalized check
            return self._deduplicate_questions_fast(questions)

    def _deduplicate_questions_similarity(self, questions: List[str]) -> List[str]:
        """Detailed similarity-based deduplication for smaller lists."""
        deduplicated = []
        seen_questions = set()
        
        for question in questions:
            # Create a normalized version for comparison
            normalized = re.sub(r'[^\w\s]', '', question.lower())
            normalized = ' '.join(normalized.split())
            
            # Check if this question is similar to any existing one
            is_duplicate = False
            for seen in seen_questions:
                # Jaccard similarity check based on common words
                seen_words = set(seen.split())
                new_words = set(normalized.split())
                
                if len(seen_words & new_words) / len(seen_words | new_words) > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(question)
                seen_questions.add(normalized)
                
        return deduplicated

    def _deduplicate_questions_fast(self, questions: List[str]) -> List[str]:
        """Fast normalized deduplication for larger lists."""
        deduplicated = []
        seen_normalized = set()
        
        for question in questions:
            # Normalize: remove punctuation, lowercase, remove extra spaces
            normalized = re.sub(r'[^\w\s]', '', question.lower())
            normalized = ' '.join(normalized.split())
            
            if normalized not in seen_normalized:
                deduplicated.append(question)
                seen_normalized.add(normalized)
                
        return deduplicated

    def generate_comprehensive_questions(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sinh câu hỏi đa khía cạnh cho một document.
        Đây là method chính thực hiện thuật toán ma trận chunk x persona.
        """
        metadata = doc.get('metadata', {})
        title = metadata.get('title', 'Thủ tục')
        content_chunks = doc.get('content_chunks', [])
        
        if not content_chunks:
            logger.warning(f"⚠️ No content_chunks found for document: {title}")
            return self._generate_fallback_questions(title, metadata)
        
        logger.info(f"📊 Analyzing {len(content_chunks)} chunks for: {title}")
        
        all_questions = []
        chunk_persona_stats = defaultdict(int)
        
        # BƯỚC 1: Lặp qua từng content_chunk
        for i, chunk in enumerate(content_chunks):
            logger.info(f"   🔍 Processing chunk {i+1}: {chunk.get('section_title', 'Untitled')}")
            
            # BƯỚC 2: Phân loại chunk thuộc aspects nào
            aspects = self._classify_chunk_aspects(chunk)
            logger.info(f"      Aspects: {aspects}")
            
            # BƯỚC 3: Xác định personas phù hợp
            relevant_personas = self._get_relevant_personas(aspects)
            logger.info(f"      Relevant personas: {relevant_personas}")
            
            # BƯỚC 4: Sinh câu hỏi cho từng cặp (chunk, persona)
            chunk_questions = []
            personas_success = 0
            for persona_key in relevant_personas:
                persona_questions = self._generate_questions_for_chunk_persona(
                    chunk, persona_key, title, max_questions=2
                )
                
                if persona_questions:
                    chunk_questions.extend(persona_questions)
                    chunk_persona_stats[f"{chunk.get('section_title', 'Unknown')} x {persona_key}"] = len(persona_questions)
                    personas_success += 1
                    logger.info(f"         ✅ Generated {len(persona_questions)} questions from {persona_key}")
                else:
                    logger.info(f"         ⚠️ No questions generated from {persona_key}")
                
                # Small delay to avoid overwhelming the LLM
                time.sleep(0.2)
            
            success_rate = (personas_success / len(relevant_personas)) * 100 if relevant_personas else 0
            all_questions.extend(chunk_questions)
            logger.info(f"      📝 Chunk total: {len(chunk_questions)} questions (Success: {success_rate:.1f}%)")
        
        # BƯỚC 5: Loại bỏ trùng lặp và tổng hợp
        logger.info(f"🔄 Deduplicating from {len(all_questions)} total questions...")
        deduplicated_questions = self._deduplicate_questions(all_questions)
        
        deduplication_effectiveness = (len(all_questions) - len(deduplicated_questions)) / len(all_questions) * 100 if all_questions else 0
        logger.info(f"   📊 Deduplication: {len(all_questions)} → {len(deduplicated_questions)} ({deduplication_effectiveness:.1f}% duplicates removed)")
        
        # Generate main question
        main_question = self._generate_main_question_enhanced(title, metadata, deduplicated_questions)
        
        logger.info(f"✅ Final result: 1 main + {len(deduplicated_questions)} variants = {1 + len(deduplicated_questions)} total")
        
        return {
            "main_question": main_question,
            "question_variants": deduplicated_questions,
            "generation_stats": {
                "total_chunks_processed": len(content_chunks),
                "total_questions_generated": len(all_questions),
                "questions_after_deduplication": len(deduplicated_questions),
                "deduplication_effectiveness_percent": round(deduplication_effectiveness, 1),
                "chunk_persona_breakdown": dict(chunk_persona_stats),
                "personas_activated": len(set(persona_key.split(' x ')[1] for persona_key in chunk_persona_stats.keys() if ' x ' in persona_key)),
                "aspects_covered": len(set().union(*[self._classify_chunk_aspects(chunk) for chunk in content_chunks])),
                "generation_method": "chunk_x_persona_matrix_v4_improved"
            }
        }

    def _generate_main_question_enhanced(self, title: str, metadata: Dict, variants: List[str]) -> str:
        """Generate a comprehensive main question based on variants."""
        if variants:
            # Use the first high-quality variant as inspiration for main question
            first_variant = variants[0] if variants else ""
            if title.lower() in first_variant.lower():
                return first_variant
        
        # Fallback to a generic but proper main question
        return f"Thủ tục {title} được thực hiện như thế nào?"

    def _generate_fallback_questions(self, title: str, metadata: Dict) -> Dict[str, Any]:
        """Fallback when no content_chunks available."""
        logger.warning(f"Using fallback question generation for: {title}")
        
        fallback_variants = [
            f"Làm {title} cần giấy tờ gì?",
            f"Chi phí {title} là bao nhiêu?",
            f"Thời gian xử lý {title} mất bao lâu?", 
            f"Làm {title} ở đâu?",
            f"Điều kiện để được {title}?",
            f"Quy trình {title} như thế nào?",
            f"Có thể làm {title} online không?",
            f"Lưu ý khi làm {title}?"
        ]
        
        return {
            "main_question": f"Thủ tục {title} được thực hiện như thế nào?",
            "question_variants": fallback_variants,
            "generation_stats": {
                "fallback_mode": True,
                "reason": "No content_chunks available"
            }
        }

    # Additional utility methods from the original script (simplified versions)
    
    def _detect_collection_from_path(self, file_path: str) -> str:
        """Detect collection name from file path."""
        path_lower = file_path.lower()
        
        if 'ho_tich_cap_xa' in path_lower:
            return 'ho_tich_cap_xa'
        elif 'chung_thuc' in path_lower:
            return 'chung_thuc'
        elif 'nuoi_con_nuoi' in path_lower:
            return 'nuoi_con_nuoi'
        elif 'hanh_chinh' in path_lower:
            return 'administrative_procedures'
        elif 'kinh_doanh' in path_lower:
            return 'business_procedures'
        elif 'dat_dai' in path_lower:
            return 'land_procedures'
        elif 'xay_dung' in path_lower:
            return 'construction_procedures'
        elif 'tu_phap' in path_lower:
            return 'judicial_procedures'
        else:
            return 'general_procedures'

    def analyze_document_metadata_enhanced(self, doc: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Enhanced metadata analysis to create rich smart_filters with detailed logic."""
        metadata = doc.get('metadata', {})
        title = metadata.get('title', '')
        code = metadata.get('code', '')
        
        # Create comprehensive smart_filters with detailed analysis
        smart_filters = {
            "exact_title": [title] if title else [],
            "title_keywords": self._extract_title_keywords(title),
            "procedure_code": [code] if code else [],
            "agency": self._extract_agency(metadata),
            "agency_level": self._determine_agency_level(metadata, file_path),
            "cost_type": self._determine_cost_type(metadata),
            "processing_speed": self._determine_processing_speed(metadata),
            "applicant_type": metadata.get('applicant_type', ['Cá nhân'])
        }
        
        # Create key_attributes with proper mapping
        key_attributes = {
            "speed": self._map_processing_speed(smart_filters["processing_speed"]),
            "cost": self._map_cost_type(smart_filters["cost_type"]),
            "level": self._map_agency_level(smart_filters["agency_level"]),
            "applicant_scope": smart_filters["applicant_type"]
        }
        
        return {
            'metadata': metadata,
            'smart_filters': smart_filters,
            'key_attributes': key_attributes,
            'confidence_threshold': 0.8,
            'priority_score': 1.2  # Higher priority for multi-aspect generated content
        }

    def _extract_agency(self, metadata: Dict) -> List[str]:
        """Extract agency from metadata with detailed parsing."""
        agency = metadata.get('executing_agency', '')
        if not agency:
            return []
        return [agency]

    def _determine_agency_level(self, metadata: Dict, file_path: str) -> List[str]:
        """Determine agency level from metadata and path with detailed logic."""
        agency = metadata.get('executing_agency', '').lower()
        path_lower = file_path.lower()
        
        if 'cấp xã' in agency or 'cap_xa' in path_lower:
            return ['commune']
        elif 'cấp huyện' in agency:
            return ['district'] 
        elif 'cấp tỉnh' in agency:
            return ['province']
        else:
            return ['commune']  # Default

    def _determine_cost_type(self, metadata: Dict) -> List[str]:
        """Determine cost type from metadata with detailed analysis."""
        fee_text = metadata.get('fee_text', '') or metadata.get('fee', '')
        if not fee_text:
            return []
        
        fee_lower = fee_text.lower()
        if 'miễn phí' in fee_lower or 'không phí' in fee_lower:
            return ['free']
        else:
            return ['paid']

    def _determine_processing_speed(self, metadata: Dict) -> List[str]:
        """Determine processing speed from metadata with detailed parsing."""
        processing_time = metadata.get('processing_time_text', '') or metadata.get('processing_time', '')
        if not processing_time:
            return []
        
        time_lower = processing_time.lower()
        if 'ngay' in time_lower and ('nhận' in time_lower or 'khi' in time_lower):
            return ['immediate']
        elif 'ngày' in time_lower or 'tuần' in time_lower:
            return ['multiple_days']  
        elif 'tháng' in time_lower:
            return ['slow']
        else:
            return ['multiple_days']

    def _map_processing_speed(self, speed_list: List[str]) -> str:
        """Map processing speed to key_attributes format."""
        if not speed_list:
            return "unknown"
        speed = speed_list[0]
        mapping = {
            'immediate': 'immediate',
            'multiple_days': 'multi_day', 
            'slow': 'slow'
        }
        return mapping.get(speed, 'multi_day')

    def _map_cost_type(self, cost_list: List[str]) -> str:
        """Map cost type to key_attributes format."""
        if not cost_list:
            return "unknown"
        return cost_list[0]

    def _map_agency_level(self, level_list: List[str]) -> str:
        """Map agency level to key_attributes format."""
        if not level_list:
            return "commune"
        return level_list[0]

    def _extract_title_keywords(self, title: str) -> List[str]:
        """Extract keywords from title."""
        if not title:
            return []
        
        # Simple keyword extraction
        words = title.lower().split()
        keywords = [word for word in words if len(word) > 2 and word not in ['thủ', 'tục', 'của', 'cho', 'với', 'theo']]
        return keywords

    def generate_all_smart_examples(self, force_rebuild: bool = False) -> int:
        """
        Main method to process all documents and generate comprehensive router examples.
        """
        if not self.documents_dir.exists():
            logger.error(f"❌ Documents directory not found: {self.documents_dir}")
            return 0

        # Find all JSON files
        json_files = list(self.documents_dir.rglob("*.json"))
        if not json_files:
            logger.error(f"❌ No JSON files found in {self.documents_dir}")
            return 0

        logger.info(f"🔍 Found {len(json_files)} JSON files to process")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        processed_files = 0
        total_examples = 0
        
        for i, json_file in enumerate(json_files):
            logger.info("=" * 80)
            logger.info(f"Processing file {i+1}/{len(json_files)}: {json_file.name}")
            logger.info("=" * 80)
            
            # Create mirrored directory structure like V3
            relative_path = json_file.relative_to(self.documents_dir)
            output_file = self.output_dir / relative_path
            
            # Ensure output maintains the same directory structure as source
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if not force_rebuild and output_file.exists():
                logger.info(f"   ⏩ Skipping, router file already exists. Use --force to overwrite.")
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    doc = json.load(f)
                
                # STEP 1: Enhanced metadata analysis
                analysis = self.analyze_document_metadata_enhanced(doc, str(json_file))
                collection_name = self._detect_collection_from_path(str(json_file))
                
                # STEP 2: Multi-aspect comprehensive question generation
                questions = self.generate_comprehensive_questions(doc)
                
                # STEP 3: Create structured router data
                router_data = {
                    'metadata': {
                        'title': doc.get('metadata', {}).get('title', ''),
                        'code': doc.get('metadata', {}).get('code', ''),
                        'collection': collection_name,
                        'source_document': str(relative_path),
                        'generated_by': 'multi_aspect_persona_generator_v4.0',
                        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'generation_method': 'chunk_x_persona_matrix'
                    },
                    'main_question': questions['main_question'],
                    'question_variants': questions.get('question_variants', []),
                    'smart_filters': analysis['smart_filters'],
                    'key_attributes': analysis['key_attributes'],
                    'expected_collection': collection_name,
                    'confidence_threshold': analysis.get('confidence_threshold', 0.8),
                    'priority_score': analysis.get('priority_score', 1.2),
                    'generation_stats': questions.get('generation_stats', {})
                }
                
                # Ensure output directory exists
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Save router data
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(router_data, f, ensure_ascii=False, indent=2)
                
                processed_files += 1
                num_questions = 1 + len(questions.get('question_variants', []))
                total_examples += num_questions
                
                logger.info("📊 GENERATION RESULTS:")
                logger.info(f"   📝 Questions generated: {num_questions} total (1 main + {len(questions.get('question_variants', []))} variants)")
                logger.info(f"   💾 Saved to: {output_file.name}")
                if 'generation_stats' in questions:
                    stats = questions['generation_stats']
                    logger.info(f"   🔍 Chunks processed: {stats.get('total_chunks_processed', 0)}")
                    logger.info(f"   🎯 Success rate: {stats.get('overall_success_rate', 'N/A')}")
                    logger.info(f"   📈 Questions: {stats.get('questions_after_deduplication', 0)}/{stats.get('total_questions_generated', 0)} after deduplication")
                
                # Brief pause between files
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"   ❌ Error processing {json_file.name}: {e}")
                continue
        
        # Generate comprehensive summary
        self._generate_comprehensive_summary(processed_files, total_examples, json_files)
        return processed_files

    def _generate_comprehensive_summary(self, processed_files: int, total_examples: int, json_files: List[Path]):
        """Generate comprehensive summary report."""
        collections = {}
        for json_file in json_files:
            collection = self._detect_collection_from_path(str(json_file))
            collections[collection] = collections.get(collection, 0) + 1
        
        summary = {
            'generator_info': {
                'version': 'multi_aspect_persona_v4.0',
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'method': 'chunk_x_persona_matrix_generation',
                'llm_model': 'PhoGPT-4B-Chat',
                'personas_used': list(self.personas.keys()),
                'target_questions_per_document': '30+',
                'approach': 'comprehensive_multi_perspective_generation'
            },
            'statistics': {
                'total_files_processed': processed_files,
                'total_source_files': len(json_files),
                'total_examples_generated': total_examples,
                'avg_questions_per_document': round(total_examples / processed_files, 2) if processed_files > 0 else 0,
                'collections_distribution': collections,
                'success_rate_percent': round((processed_files / len(json_files)) * 100, 2) if json_files else 0
            },
            'quality_metrics': {
                'generation_approach': 'multi_aspect_multi_persona',
                'deduplication': 'advanced_similarity_based',
                'context_coverage': 'full_content_chunks_analysis',
                'persona_diversity': len(self.personas),
                'aspect_coverage': list(self.aspect_persona_mapping.keys()),
                'target_achievement': 'optimized_for_30plus_questions'
            },
            'personas_definition': self.personas,
            'aspect_persona_mapping': self.aspect_persona_mapping
        }
        
        summary_file = self.output_dir / "multi_aspect_generation_summary_v4.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 COMPREHENSIVE GENERATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"🎯 Target: 30+ questions per document")
        logger.info(f"📈 Achieved: {summary['statistics']['avg_questions_per_document']} questions per document on average")
        logger.info(f"📁 Summary saved to: {summary_file}")
        logger.info("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate comprehensive multi-aspect router examples V4')
    parser.add_argument('--force', action='store_true', help='Force rebuild existing examples')
    parser.add_argument('--docs', type=str, default='data/documents', help='Documents directory')
    parser.add_argument('--output', type=str, default='data/router_examples_smart_v3', help='Output directory')
    
    args = parser.parse_args()
    
    try:
        generator = MultiAspectPersonaRouter(args.docs, args.output)
        
        logger.info("🚀 Starting Multi-Aspect Multi-Persona Router Generation V4...")
        logger.info("🎯 Target: 30+ comprehensive questions per document")
        logger.info("🔧 Method: Chunk × Persona Matrix Generation")
        
        start_time = time.time()
        
        processed_count = generator.generate_all_smart_examples(force_rebuild=args.force)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ MULTI-ASPECT GENERATION COMPLETED!")
        logger.info("=" * 80)
        logger.info(f"📊 Files processed: {processed_count}")
        logger.info(f"⏱️ Total duration: {duration:.2f} seconds")
        logger.info(f"📁 Output directory: {args.output}")
        logger.info(f"🎯 Achievement: Comprehensive multi-perspective question generation")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
