#!/usr/bin/env python3
"""
Test V3 Hybrid Generator
========================
"""

import sys
from pathlib import Path
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Add app to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tools.generate_router_with_llm_v3_hybrid import SmartRouterLLMGeneratorV3
except ImportError as e:
    logger.error(f"❌ Cannot import SmartRouterLLMGeneratorV3: {e}")
    sys.exit(1)

def test_hybrid_generator():
    """Test the hybrid generator with a sample document."""
    print("🧪 Testing V3 Hybrid Generator")
    print("=" * 50)
    
    # Sample document for testing
    sample_doc = {
        "metadata": {
            "title": "Đăng ký kết hôn có yếu tố nước ngoài",
            "code": "QT 12/CX-HCTP",
            "applicant_type": ["Cá nhân"],
            "executing_agency": "Ủy ban nhân dân cấp xã",
            "processing_time_text": "Trong thời hạn 15 ngày làm việc",
            "fee_text": "50.000 VNĐ",
            "submission_method": ["Trực tiếp"],
            "result_delivery": ["Trực tiếp", "Bưu chính"]
        },
        "content_chunks": [
            {
                "section_title": "Thành phần hồ sơ",
                "content": "Đơn đăng ký kết hôn theo mẫu, Giấy tờ tùy thân của hai bên, Giấy chứng nhận độc thân của người nước ngoài..."
            }
        ]
    }
    
    try:
        # Initialize generator
        generator = SmartRouterLLMGeneratorV3()
        
        # Test metadata analysis
        print("🔍 Testing Enhanced Metadata Analysis:")
        file_path = "quy_trinh_cap_ho_tich_cap_xa/ho_tich_cap_xa_moi_nhat/12. Đăng ký kết hôn có yếu tố nước ngoài.json"
        analysis = generator.analyze_document_metadata_enhanced(sample_doc, file_path)
        
        print("📊 Smart Filters:")
        for key, value in analysis['smart_filters'].items():
            print(f"  - {key}: {value}")
        
        print(f"\n🔑 Key Attributes:")
        for key, value in analysis['key_attributes'].items():
            print(f"  - {key}: {value}")
        
        print(f"\n🏷️ Collection: {generator._detect_collection_from_path(file_path)}")
        
        # Test question generation
        print(f"\n🤖 Testing Question Generation:")
        questions = generator.generate_questions_with_llm_focused(sample_doc)
        
        print(f"✅ Main Question: {questions.get('main_question')}")
        print(f"📝 Variants ({len(questions.get('question_variants', []))}):")
        for i, variant in enumerate(questions.get('question_variants', []), 1):
            print(f"  {i}. {variant}")
        
        # Test complete structure
        print(f"\n📋 Complete Router Structure:")
        collection_name = generator._detect_collection_from_path(file_path)
        router_data = {
            'metadata': {
                'title': sample_doc['metadata']['title'],
                'code': sample_doc['metadata']['code'],
                'collection': collection_name,
            },
            'main_question': questions['main_question'],
            'question_variants': questions.get('question_variants', []),
            'smart_filters': analysis['smart_filters'],
            'key_attributes': analysis['key_attributes'],
        }
        
        print(json.dumps(router_data, ensure_ascii=False, indent=2))
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hybrid_generator()
