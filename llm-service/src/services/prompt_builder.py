"""
Prompt Builder Service - Xây dựng prompt từ template
Tham khảo từ AICenter-RAG pattern với điều chỉnh cho Legal domain
"""
import os
from pathlib import Path
from typing import List, Dict, Optional


class PromptBuilder:
    """
    Build prompts từ templates cho Legal RAG system
    
    Responsibilities:
    - Load system prompt từ file
    - Load citation rules từ file
    - Build context từ search results
    - Combine thành final prompt cho LLM
    """
    
    def __init__(self):
        """Initialize prompt builder với templates"""
        self.prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        self.system_prompt = self._load_system_prompt()
        self.citation_rules = self._load_citation_rules()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt từ file"""
        prompt_file = self.prompts_dir / "system_prompt.txt"
        
        if not prompt_file.exists():
            # Fallback nếu file không tồn tại
            return self._get_default_system_prompt()
        
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()
    
    def _load_citation_rules(self) -> str:
        """Load citation rules từ file"""
        rules_file = self.prompts_dir / "citation_rules.txt"
        
        if not rules_file.exists():
            return self._get_default_citation_rules()
        
        with open(rules_file, "r", encoding="utf-8") as f:
            return f.read()
    
    def _get_default_system_prompt(self) -> str:
        """Default system prompt nếu file không có"""
        return """Bạn là trợ lý AI pháp luật chuyên nghiệp.
Trả lời câu hỏi dựa trên văn bản pháp luật được cung cấp.
Luôn trích dẫn nguồn rõ ràng."""
    
    def _get_default_citation_rules(self) -> str:
        """Default citation rules"""
        return """Quy tắc trích dẫn:
1. Trích dẫn theo văn bản pháp luật (Nghị định, Thông tư, Luật)
2. Trích dẫn theo quy trình/thủ tục
3. Trích dẫn theo mục/điều cụ thể"""
    
    def build_context_from_chunks(self, chunks: List[Dict]) -> str:
        """
        Build context string từ search results
        
        Args:
            chunks: List of search results with keys:
                - content: chunk text
                - document_title: tên văn bản
                - metadata: dict chứa document_code, dates, etc.
                
        Returns:
            Formatted context string với trích dẫn
        """
        if not chunks:
            return "Không có văn bản pháp luật liên quan."
        
        context_parts = []
        
        for idx, chunk in enumerate(chunks, 1):
            content = chunk.get("content", "")
            doc_title = chunk.get("document_title", "Văn bản không rõ")
            metadata = chunk.get("metadata", {})
            
            # Lấy document_code nếu có
            doc_code = metadata.get("document_code", "")
            
            # Format trích dẫn
            if doc_code:
                citation = f"[{doc_title} - {doc_code}]"
            else:
                citation = f"[{doc_title}]"
            
            # Format chunk với citation
            context_parts.append(f"{citation}\n{content}\n")
        
        return "\n---\n".join(context_parts)
    
    def build_prompt(
        self,
        question: str,
        context: str,
        history: Optional[List[Dict]] = None
    ) -> str:
        """
        Build final prompt cho LLM theo Vistral/Mistral chat template format.
        
        Format: [INST] <<SYS>> system_prompt <</SYS>> user_message [/INST]
        
        Args:
            question: Câu hỏi của user
            context: Context từ search results
            history: Chat history (optional)
            
        Returns:
            Complete prompt string in Vistral format
        """
        # Build system message với context
        system_content = f"""{self.system_prompt}

{self.citation_rules}

VĂN BẢN PHÁP LUẬT THAM KHẢO:
{context}"""
        
        # Build conversation using Vistral/Mistral format
        # Format: [INST] <<SYS>>\n{system}\n<</SYS>>\n\n{user} [/INST] {assistant}
        
        prompt_parts = []
        
        # First message includes system prompt
        if history and len(history) > 0:
            # Build with history
            first_user_msg = None
            remaining_history = []
            
            for i, msg in enumerate(history[-6:]):  # Lấy tối đa 6 turns gần nhất (3 cặp Q&A)
                if msg.get("role") == "user" and first_user_msg is None:
                    first_user_msg = msg.get("content", "")
                else:
                    remaining_history.append(msg)
            
            if first_user_msg:
                # First turn with system
                prompt_parts.append(f"[INST] <<SYS>>\n{system_content}\n<</SYS>>\n\n{first_user_msg} [/INST]")
                
                # Add remaining history
                for msg in remaining_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "assistant":
                        prompt_parts.append(f" {content} </s>")
                    else:
                        prompt_parts.append(f"<s>[INST] {content} [/INST]")
            
            # Add current question
            prompt_parts.append(f"<s>[INST] {question} [/INST]")
        else:
            # No history - single turn with system prompt
            prompt_parts.append(f"[INST] <<SYS>>\n{system_content}\n<</SYS>>\n\n{question} [/INST]")
        
        return "".join(prompt_parts)
    
    def build_simple_prompt(self, question: str, context: str) -> str:
        """
        Build simple prompt không có system prompt đầy đủ
        Dùng cho testing hoặc khi cần prompt ngắn gọn
        
        Args:
            question: Câu hỏi
            context: Context văn bản
            
        Returns:
            Simple prompt
        """
        return f"""Dựa trên các văn bản pháp luật sau, trả lời câu hỏi một cách chính xác và trích dẫn rõ nguồn:

{context}

Câu hỏi: {question}

Trả lời:"""
    
    def build_prompt_for_provider(
        self,
        question: str,
        context: str,
        history: Optional[List[Dict]] = None,
        provider: str = "local"
    ) -> str:
        """
        Build prompt phù hợp với từng provider.
        
        Args:
            question: Câu hỏi của user
            context: Context từ search results
            history: Chat history (optional)
            provider: "local" | "gemini"
            
        Returns:
            Formatted prompt string cho provider tương ứng
        """
        if provider == "gemini":
            return self._build_prompt_gemini(question, context, history)
        else:
            return self.build_prompt(question, context, history)
    
    def _build_prompt_gemini(
        self,
        question: str,
        context: str,
        history: Optional[List[Dict]] = None
    ) -> str:
        """
        Build prompt cho Gemini API (plain text, không cần special tokens).
        
        Gemini xử lý tốt hơn với plain text format thay vì [INST]...[/INST].
        
        Args:
            question: Câu hỏi của user
            context: Context từ search results
            history: Chat history (optional)
            
        Returns:
            Plain text prompt cho Gemini
        """
        # Build system instructions
        prompt_parts = [
            "=== HƯỚNG DẪN HỆ THỐNG ===",
            self.system_prompt,
            "",
            self.citation_rules,
            "",
            "=== VĂN BẢN PHÁP LUẬT THAM KHẢO ===",
            context,
            ""
        ]
        
        # Add history if available
        if history and len(history) > 0:
            prompt_parts.append("=== LỊCH SỬ HỘI THOẠI ===")
            for msg in history[-6:]:  # Lấy tối đa 6 messages gần nhất
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    prompt_parts.append(f"Người dùng: {content}")
                else:
                    prompt_parts.append(f"Trợ lý: {content}")
            prompt_parts.append("")
        
        # Add current question
        prompt_parts.extend([
            "=== CÂU HỎI HIỆN TẠI ===",
            f"Người dùng: {question}",
            "",
            "=== TRẢ LỜI ===",
            "Trợ lý:"
        ])
        
        return "\n".join(prompt_parts)
    
    def extract_metadata_summary(self, chunks: List[Dict]) -> Dict:
        """
        Extract summary metadata từ chunks
        
        Returns:
            Dict with:
                - document_count: số văn bản
                - document_codes: list các mã văn bản
                - dates: list các ngày tháng đề cập
        """
        documents = set()
        doc_codes = set()
        dates = set()
        
        for chunk in chunks:
            doc_title = chunk.get("document_title")
            if doc_title:
                documents.add(doc_title)
            
            metadata = chunk.get("metadata", {})
            if metadata:
                code = metadata.get("document_code")
                if code:
                    doc_codes.add(code)
                
                chunk_dates = metadata.get("dates", [])
                dates.update(chunk_dates)
        
        return {
            "document_count": len(documents),
            "document_codes": list(doc_codes),
            "dates": sorted(list(dates))[:5],  # Top 5 dates
        }


# Singleton instance
prompt_builder = PromptBuilder()
