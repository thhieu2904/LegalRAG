#!/usr/bin/env python3
"""
Test Demo for Multi-Aspect Multi-Persona Router Generator
========================================================

Demonstration script to show the new multi-aspect generation approach
without requiring the actual LLM service.
"""

import json
from pathlib import Path

def demo_multi_aspect_generation():
    """Demonstrate the multi-aspect multi-persona approach."""
    
    print("🚀 Multi-Aspect Multi-Persona Router Generator Demo")
    print("=" * 60)
    
    # Demo personas
    personas = {
        "nguoi_lan_dau": {
            "name": "Người Lần Đầu",
            "description": "Người chưa từng làm thủ tục, cần hướng dẫn cơ bản",
            "concerns": ["thủ tục cơ bản", "giấy tờ cần thiết", "bước đầu tiên"]
        },
        "nguoi_ban_ron": {
            "name": "Người Bận Rộn", 
            "concerns": ["thời gian xử lý", "cách nhanh nhất", "online/offline"]
        },
        "nguoi_can_than": {
            "name": "Người Cẩn Thận",
            "concerns": ["điều kiện cụ thể", "trường hợp đặc biệt", "lưu ý quan trọng"]
        },
        "nguoi_lam_ho": {
            "name": "Người Làm Hộ",
            "concerns": ["ủy quyền", "giấy tờ đại diện", "quyền hạn"]
        },
        "nguoi_gap_van_de": {
            "name": "Người Gặp Vấn Đề",
            "concerns": ["thiếu giấy tờ", "trường hợp đặc biệt", "giải quyết khó khăn"]
        }
    }
    
    # Demo document structure
    demo_document = {
        "metadata": {
            "title": "Đăng ký khai sinh",
            "code": "QT 01/CX-HCTP"
        },
        "content_chunks": [
            {
                "chunk_id": 1,
                "section_title": "Thành phần hồ sơ",
                "content": "Tờ khai đăng ký khai sinh, Giấy chứng sinh, Giấy tờ tùy thân...",
                "keywords": ["hồ sơ", "giấy tờ", "tài liệu"]
            },
            {
                "chunk_id": 2, 
                "section_title": "Thời gian xử lý",
                "content": "Ngay trong ngày tiếp nhận yêu cầu, trường hợp nhận hồ sơ sau 15 giờ...",
                "keywords": ["thời gian", "xử lý", "ngày"]
            },
            {
                "chunk_id": 3,
                "section_title": "Lệ phí",
                "content": "Lệ phí thay đổi tùy theo trường hợp, có các mức 8.000đ, 5.000đ, 4.000đ...",
                "keywords": ["lệ phí", "chi phí", "tiền"]
            }
        ]
    }
    
    print("👥 Defined Personas:")
    for key, persona in personas.items():
        print(f"   • {persona['name']}: {', '.join(persona['concerns'])}")
    
    print(f"\n📄 Demo Document: {demo_document['metadata']['title']}")
    print(f"📊 Content Chunks: {len(demo_document['content_chunks'])}")
    
    # Demo aspect classification
    aspect_mapping = {
        "hồ sơ": ["nguoi_lan_dau", "nguoi_can_than", "nguoi_gap_van_de"],
        "thời gian": ["nguoi_ban_ron", "nguoi_lan_dau"],
        "chi phí": ["nguoi_ban_ron", "nguoi_can_than"]
    }
    
    print("\n🔧 Chunk × Persona Matrix Generation:")
    total_questions = 0
    
    for chunk in demo_document['content_chunks']:
        print(f"\n   📝 Chunk: {chunk['section_title']}")
        
        # Classify aspects
        aspects = []
        content = chunk['content'].lower()
        if any(word in content for word in ['hồ sơ', 'giấy tờ', 'tài liệu']):
            aspects.append('hồ sơ')
        if any(word in content for word in ['thời gian', 'ngày', 'giờ']):
            aspects.append('thời gian')
        if any(word in content for word in ['lệ phí', 'chi phí', 'tiền']):
            aspects.append('chi phí')
            
        print(f"      Aspects: {aspects}")
        
        # Get relevant personas
        relevant_personas = set()
        for aspect in aspects:
            if aspect in aspect_mapping:
                relevant_personas.update(aspect_mapping[aspect])
        
        print(f"      Relevant personas: {list(relevant_personas)}")
        
        # Simulate question generation
        chunk_questions = 0
        for persona_key in relevant_personas:
            questions_per_persona = 2  # Assume 2 questions per persona
            chunk_questions += questions_per_persona
            print(f"         • {personas[persona_key]['name']}: {questions_per_persona} questions")
        
        total_questions += chunk_questions
        print(f"      Chunk total: {chunk_questions} questions")
    
    print("\n📊 GENERATION RESULTS:")
    print(f"   🎯 Target: 30+ questions per document")
    print(f"   📈 Achieved: {total_questions} questions")
    print(f"   ✅ Success: {'ACHIEVED' if total_questions >= 30 else 'NEEDS MORE CHUNKS/PERSONAS'}")
    
    print("\n🔄 This demonstrates the core algorithm:")
    print("   1. Split document into content_chunks (aspects)")
    print("   2. Define user personas with specific concerns") 
    print("   3. Map which personas are relevant for each aspect")
    print("   4. Generate questions for each (chunk, persona) pair")
    print("   5. Result: 30+ comprehensive, diverse questions")
    
    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")

if __name__ == "__main__":
    demo_multi_aspect_generation()
