"""
DEMO: Fix thứ tự context để LLM focus đúng thông tin
"""

# ❌ HIỆN TẠI - Metadata trước, Content sau:
def _load_full_document_OLD(self, file_path: str) -> str:
    # Build metadata trước
    if metadata:
        natural_metadata_parts = []
        if metadata.get('fee_vnd'):
            natural_metadata_parts.append(f"Phí: {metadata['fee_vnd']:,} đồng")
        complete_parts.extend(natural_metadata_parts)
    
    # Content chunks sau  
    if content_chunks:
        complete_parts.append("Nội dung chi tiết:")
        for chunk in content_chunks:
            complete_parts.append(f"**{chunk.get('section_title', '')}**")
            complete_parts.append(chunk.get('content', ''))

# ✅ FIXED - Content quan trọng trước, Metadata sau:
def _load_full_document_FIXED(self, file_path: str, query: str = "") -> str:
    complete_parts = []
    
    # 🎯 PHASE 1: Content chunks TRƯỚC (ưu tiên theo query)
    if content_chunks:
        # Query-aware prioritization
        prioritized_chunks = self._prioritize_chunks_by_query(content_chunks, query)
        
        for chunk in prioritized_chunks:
            section_title = chunk.get('section_title', '')
            content = chunk.get('content', '')
            
            if section_title and content:
                complete_parts.append(f"**{section_title}:**")
                complete_parts.append(content)
                complete_parts.append("")  # spacing
    
    # 🎯 PHASE 2: Metadata SAU (hỗ trợ)
    if metadata:
        complete_parts.append("**Thông tin bổ sung:**")
        
        if metadata.get('fee_vnd'):
            complete_parts.append(f"• Phí: {metadata['fee_vnd']:,} đồng")
        if metadata.get('processing_time_text'):
            complete_parts.append(f"• Thời gian: {metadata['processing_time_text']}")
        if metadata.get('executing_agency'):
            complete_parts.append(f"• Cơ quan: {metadata['executing_agency']}")
    
    return "\n".join(complete_parts)

def _prioritize_chunks_by_query(self, chunks: List[Dict], query: str) -> List[Dict]:
    """Ưu tiên chunks dựa trên query"""
    
    # Keywords mapping cho priority
    priority_map = {
        "giấy tờ|hồ sơ|thành phần": ["Thành phần hồ sơ", "Hồ sơ"],
        "phí|lệ phí|chi phí": ["Lệ phí", "Chi phí"],
        "thời gian|thời hạn": ["Thời hạn giải quyết"],
        "cơ quan|nơi làm": ["Cơ quan thực hiện"],
        "kết quả|nhận": ["Kết quả thực hiện"]
    }
    
    # Find priority chunks
    priority_chunks = []
    other_chunks = []
    
    for chunk in chunks:
        section_title = chunk.get('section_title', '').lower()
        is_priority = False
        
        for query_pattern, priority_sections in priority_map.items():
            if any(keyword in query.lower() for keyword in query_pattern.split('|')):
                if any(priority_section.lower() in section_title for priority_section in priority_sections):
                    priority_chunks.append(chunk)
                    is_priority = True
                    break
        
        if not is_priority:
            other_chunks.append(chunk)
    
    # Return prioritized order
    return priority_chunks + other_chunks
