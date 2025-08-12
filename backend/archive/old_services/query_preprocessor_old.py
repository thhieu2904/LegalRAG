"""
Query Preprocessor Service - Module Tiền xử lý Thông minh
Xử lý câu hỏi trước khi đưa vào RAG để:
1. Làm rõ câu hỏi mơ hồ
2. Quản lý lịch sử hội thoại hiệu quả
3. Tạo context-aware query từ conversation history
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Lưu trữ một lượt hội thoại"""
    user_query: str
    assistant_response: str
    timestamp: float
    topic_tags: Optional[List[str]] = None  # Tags chủ đề để nén lịch sử

class QueryPreprocessor:
    """
    Module tiền xử lý thông minh cho RAG system
    """
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.conversation_history: List[ConversationTurn] = []
        self.max_history_length = 10  # Giới hạn lịch sử để tiết kiệm VRAM
        
        # Templates cho các loại xử lý khác nhau
        self.clarification_template = """Bạn là chuyên gia phân tích câu hỏi pháp luật. Phân tích câu hỏi và xác định có cần làm rõ không.

### Quy tắc phân tích NGHIÊM NGẶT:
1. Nếu câu hỏi có ĐỦ thông tin cụ thể → trả lời "CLEAR"
2. Nếu câu hỏi thiếu bất kỳ thông tin quan trọng nào → YÊU CẦU LÀM RÕ

### Các dấu hiệu BẮT BUỘC làm rõ:
- Thiếu đối tượng cụ thể: "mình/tôi/anh/chị" (cần biết công dân VN hay nước ngoài)
- Thiếu loại thủ tục: "nhận con nuôi" (trong nước hay quốc tế? đơn thân hay vợ chồng?)
- Thiếu ngữ cảnh: "làm gì?" (cần biết tình huống cụ thể)
- Từ mơ hồ: "thủ tục này", "việc đó", "như thế nào"

### Ví dụ câu hỏi CẦN làm rõ:
- "mình muốn làm thủ tục nhận nuôi con" → Cần hỏi: đối tượng? loại con nuôi?
- "làm sao để kết hôn?" → Cần hỏi: công dân VN? kết hôn với ai?
- "thủ tục này cần gì?" → Cần hỏi: thủ tục nào cụ thể?

### Câu hỏi cần phân tích:
{user_query}

### Phân tích (nếu cần làm rõ, đưa ra 2-3 câu hỏi cụ thể):"""

        self.context_synthesis_template = """Bạn là trợ lý tổng hợp thông tin. Dựa vào lịch sử hội thoại, tạo một câu hỏi độc lập, đầy đủ ngữ cảnh.

### Nguyên tắc tổng hợp:
1. Kết hợp câu hỏi mới với ngữ cảnh từ lịch sử
2. Tạo câu hỏi CỤ THỂ, ĐỦ THÔNG TIN để tìm kiếm
3. Giữ ý định chính của người dùng
4. Loại bỏ thông tin không liên quan

### Lịch sử hội thoại:
{conversation_history}

### Câu hỏi hiện tại:
{current_query}

### Câu hỏi tổng hợp (trả về CHỈ câu hỏi, không giải thích):"""

        self.topic_extraction_template = """Trích xuất 2-3 từ khóa chính từ câu trả lời để gắn tag chủ đề.

### Nội dung:
{content}

### Từ khóa chủ đề (phân cách bằng dấu phẩy):"""

    def add_conversation_turn(self, user_query: str, assistant_response: str, topic_tags: Optional[List[str]] = None):
        """Thêm một lượt hội thoại vào lịch sử"""
        turn = ConversationTurn(
            user_query=user_query,
            assistant_response=assistant_response,
            timestamp=time.time(),
            topic_tags=topic_tags or []
        )
        
        self.conversation_history.append(turn)
        
        # Giới hạn độ dài lịch sử để tiết kiệm VRAM
        if len(self.conversation_history) > self.max_history_length:
            # Giữ lại các turn gần đây nhất
            self.conversation_history = self.conversation_history[-self.max_history_length:]
        
        logger.debug(f"Added conversation turn. History length: {len(self.conversation_history)}")

    def extract_topic_tags(self, content: str) -> List[str]:
        """Trích xuất topic tags từ nội dung để nén lịch sử"""
        try:
            prompt = self.topic_extraction_template.format(content=content[:500])
            
            result = self.llm_service.generate_response(
                user_query=prompt,
                max_tokens=50,
                temperature=0.1,
                system_prompt="Bạn là trợ lý trích xuất từ khóa."
            )
            
            tags_text = result['response'].strip()
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            return tags[:3]  # Chỉ lấy tối đa 3 tags
            
        except Exception as e:
            logger.error(f"Error extracting topic tags: {e}")
            return []

    def analyze_query_clarity(self, user_query: str) -> Dict[str, Any]:
        """
        Phân tích xem câu hỏi có cần làm rõ không
        Returns: {'needs_clarification': bool, 'clarification_questions': List[str], 'analysis': str}
        """
        try:
            prompt = self.clarification_template.format(user_query=user_query)
            
            result = self.llm_service.generate_response(
                user_query=prompt,
                max_tokens=200,
                temperature=0.3,
                system_prompt="Bạn là chuyên gia phân tích câu hỏi pháp luật."
            )
            
            analysis = result['response'].strip()
            
            # Parse kết quả
            if "CLEAR" in analysis.upper():
                return {
                    'needs_clarification': False,
                    'clarification_questions': [],
                    'analysis': analysis,
                    'confidence': 'high'
                }
            else:
                # Trích xuất các câu hỏi làm rõ
                lines = analysis.split('\n')
                questions = []
                for line in lines:
                    line = line.strip()
                    if line and ('?' in line or line.startswith('-') or line.startswith('•')):
                        questions.append(line.lstrip('- •').strip())
                
                return {
                    'needs_clarification': len(questions) > 0,
                    'clarification_questions': questions[:3],  # Tối đa 3 câu hỏi
                    'analysis': analysis,
                    'confidence': 'medium' if len(questions) > 0 else 'low'
                }
                
        except Exception as e:
            logger.error(f"Error analyzing query clarity: {e}")
            return {
                'needs_clarification': False,
                'clarification_questions': [],
                'analysis': f"Error: {str(e)}",
                'confidence': 'error'
            }

    def synthesize_contextual_query(self, current_query: str) -> str:
        """
        Tổng hợp câu hỏi hiện tại với ngữ cảnh từ lịch sử hội thoại
        Trả về câu hỏi độc lập, đầy đủ ngữ cảnh
        """
        if not self.conversation_history:
            return current_query
        
        try:
            # Tạo tóm tắt lịch sử nén gọn
            history_summary = self._create_compressed_history()
            
            prompt = self.context_synthesis_template.format(
                conversation_history=history_summary,
                current_query=current_query
            )
            
            result = self.llm_service.generate_response(
                user_query=prompt,
                max_tokens=150,
                temperature=0.2,
                system_prompt="Bạn là trợ lý tổng hợp thông tin chuyên nghiệp."
            )
            
            synthesized_query = result['response'].strip()
            
            # Validate kết quả
            if len(synthesized_query) > 10 and '?' in synthesized_query:
                logger.info(f"Query synthesized: '{current_query}' → '{synthesized_query}'")
                return synthesized_query
            else:
                logger.warning("Synthesis failed, using original query")
                return current_query
                
        except Exception as e:
            logger.error(f"Error synthesizing contextual query: {e}")
            return current_query

    def _create_compressed_history(self) -> str:
        """Tạo tóm tắt lịch sử hội thoại nén gọn"""
        if not self.conversation_history:
            return ""
        
        # Chỉ lấy 5 lượt gần nhất để tránh context quá dài
        recent_history = self.conversation_history[-5:]
        
        compressed_items = []
        for i, turn in enumerate(recent_history):
            # Rút gọn câu trả lời chỉ giữ ý chính
            response_summary = turn.assistant_response[:200] + "..." if len(turn.assistant_response) > 200 else turn.assistant_response
            
            compressed_items.append(f"Lần {i+1}:")
            compressed_items.append(f"Q: {turn.user_query}")
            compressed_items.append(f"A: {response_summary}")
            if turn.topic_tags:
                compressed_items.append(f"Tags: {', '.join(turn.topic_tags)}")
            compressed_items.append("")  # Empty line separator
        
        return '\n'.join(compressed_items)

    def process_query(
        self, 
        user_query: str, 
        enable_clarification: bool = True,
        enable_context_synthesis: bool = True,
        clarification_threshold: str = 'medium'  # 'low', 'medium', 'high'
    ) -> Dict[str, Any]:
        """
        Xử lý câu hỏi đầy đủ với tất cả các bước tiền xử lý
        
        Returns:
        {
            'processed_query': str,  # Câu hỏi đã xử lý 
            'needs_clarification': bool,
            'clarification_questions': List[str],
            'processing_steps': List[str],
            'original_query': str,
            'context_synthesized': bool
        }
        """
        start_time = time.time()
        processing_steps = []
        
        result = {
            'processed_query': user_query,
            'needs_clarification': False,
            'clarification_questions': [],
            'processing_steps': processing_steps,
            'original_query': user_query,
            'context_synthesized': False,
            'processing_time': 0
        }
        
        try:
            # BƯỚC 1: Context Synthesis (ưu tiên trước)
            if enable_context_synthesis and self.conversation_history:
                processing_steps.append("context_synthesis")
                synthesized_query = self.synthesize_contextual_query(user_query)
                if synthesized_query != user_query:
                    result['processed_query'] = synthesized_query
                    result['context_synthesized'] = True
                    logger.info("Context synthesis applied")
                else:
                    processing_steps.append("context_synthesis_skipped")
            
            # BƯỚC 2: Clarity Analysis
            if enable_clarification:
                processing_steps.append("clarity_analysis")
                clarity_result = self.analyze_query_clarity(result['processed_query'])
                
                # LOGIC MẠNH HƠN: Luôn ưu tiên clarification nếu phát hiện mơ hồ
                if clarity_result['needs_clarification']:
                    result['needs_clarification'] = True
                    result['clarification_questions'] = clarity_result['clarification_questions']
                    processing_steps.append("clarification_required")
                    logger.info(f"🤔 Clarification required for: '{user_query}' - {len(result['clarification_questions'])} questions")
                    logger.info(f"Questions: {result['clarification_questions']}")
                else:
                    processing_steps.append("clarity_sufficient")
                    logger.info(f"✅ Query clear enough: '{user_query}'")
            
            result['processing_time'] = time.time() - start_time
            logger.info(f"Query processing completed in {result['processing_time']:.2f}s with steps: {processing_steps}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in query processing: {e}")
            result['processing_steps'].append("error")
            result['processing_time'] = time.time() - start_time
            return result

    def clear_history(self):
        """Xóa lịch sử hội thoại"""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    def get_history_summary(self) -> Dict[str, Any]:
        """Lấy tóm tắt lịch sử hội thoại"""
        if not self.conversation_history:
            return {
                'total_turns': 0,
                'topics': [],
                'recent_queries': []
            }
        
        # Thu thập tất cả topics
        all_topics = []
        for turn in self.conversation_history:
            all_topics.extend(turn.topic_tags or [])
        
        unique_topics = list(set(all_topics))
        recent_queries = [turn.user_query for turn in self.conversation_history[-3:]]
        
        return {
            'total_turns': len(self.conversation_history),
            'topics': unique_topics,
            'recent_queries': recent_queries,
            'oldest_timestamp': self.conversation_history[0].timestamp if self.conversation_history else None,
            'newest_timestamp': self.conversation_history[-1].timestamp if self.conversation_history else None
        }
