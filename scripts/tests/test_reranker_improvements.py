"""
Test reranker improvements
"""

import os
import sys
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

from app.services.result_reranker import RerankerService

def test_keyword_extraction():
    """Test keyword extraction"""
    
    reranker = RerankerService()
    
    test_queries = [
        "đăng ký khai sinh có tốn phí không",
        "thủ tục kết hôn cần giấy tờ gì",
        "chứng thực hợp đồng mua bán nhà",
        "lệ phí đăng ký hộ tịch"
    ]
    
    print("🧪 TESTING KEYWORD EXTRACTION")
    print("=" * 50)
    
    for query in test_queries:
        keywords = reranker._extract_query_keywords(query)
        print(f"Query: {query}")
        print(f"Keywords: {keywords}")
        print()

def test_content_extraction():
    """Test relevant content extraction"""
    
    reranker = RerankerService()
    
    sample_content = """
    Tiêu đề: Đăng ký khai sinh
    Cơ quan thực hiện: UBND cấp xã
    
    Thành phần hồ sơ:
    - Tờ khai đăng ký khai sinh
    - Giấy chứng sinh
    - Giấy tờ tùy thân
    
    Phí, lệ phí:
    - Đăng ký khai sinh đúng hạn: MIỄN PHÍ
    - Đăng ký không đúng hạn: 8.000 đồng (trực tiếp), 4.000 đồng (trực tuyến)
    - Miễn lệ phí cho gia đình có công, hộ nghèo
    
    Thời gian xử lý: Ngay trong ngày
    """
    
    query = "đăng ký khai sinh có tốn phí không"
    keywords = reranker._extract_query_keywords(query)
    relevant_content = reranker._extract_relevant_content(sample_content, keywords, max_length=300)
    
    print("🎯 TESTING CONTENT EXTRACTION")
    print("=" * 50)
    print(f"Query: {query}")
    print(f"Keywords: {keywords}")
    print()
    print(f"Original content length: {len(sample_content)}")
    print(f"Extracted content length: {len(relevant_content)}")
    print()
    print("Extracted content:")
    print(relevant_content)

if __name__ == "__main__":
    try:
        test_keyword_extraction()
        print()
        test_content_extraction()
    except Exception as e:
        print(f"Error: {e}")
