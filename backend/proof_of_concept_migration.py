#!/usr/bin/env python3
"""
🚀 PROOF OF CONCEPT: Migrate 1 document từ GOD FILE → CLEAN STRUCTURE

Test ngay để thấy sự khác biệt:
- TRƯỚC: 70+ dòng router_questions.json (god object)  
- SAU: 4 dòng questions.json + metadata từ document.json
"""

import json
import os
import glob
from pathlib import Path

def demonstrate_god_object_elimination():
    """Demo migration cho 1 document để thấy immediate benefit"""
    
    print("🔍 TÌEM 1 DOCUMENT TO DEMO...")
    
    # Find first router_questions.json file
    router_files = glob.glob("d:/Personal/LegalRAG_Fixed/backend/data/**/*router_questions.json", recursive=True)
    
    if not router_files:
        print("❌ Không tìm thấy router_questions.json files")
        return
    
    demo_file = router_files[0]
    print(f"📁 DEMO FILE: {demo_file}")
    
    # Load current god object
    with open(demo_file, 'r', encoding='utf-8') as f:
        god_data = json.load(f)
    
    print(f"\n📊 CURRENT GOD OBJECT SIZE: {len(str(god_data))} characters")
    print(f"📋 FIELDS: {list(god_data.keys())}")
    
    # Extract ONLY questions (eliminate god pattern)
    clean_questions = {
        "main_question": god_data.get("main_question", ""),
        "question_variants": god_data.get("question_variants", [])
    }
    
    print(f"\n✨ CLEAN QUESTIONS SIZE: {len(str(clean_questions))} characters")
    print(f"📋 FIELDS: {list(clean_questions.keys())}")
    
    # Calculate reduction
    reduction = ((len(str(god_data)) - len(str(clean_questions))) / len(str(god_data))) * 100
    print(f"\n🎯 COMPLEXITY REDUCTION: {reduction:.1f}%")
    
    # Save demo files
    demo_dir = Path(demo_file).parent
    
    # Save clean questions.json
    questions_file = demo_dir / "questions.json"
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump(clean_questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ CREATED: {questions_file}")
    print("📝 CONTENT:")
    print(json.dumps(clean_questions, ensure_ascii=False, indent=2))
    
    # Find corresponding document.json for metadata
    doc_files = [f for f in os.listdir(demo_dir) if f.endswith('.json') and 'router_questions' not in f and 'questions' not in f]
    
    if doc_files:
        doc_file = demo_dir / doc_files[0]
        with open(doc_file, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
        
        metadata = doc_data.get('metadata', {})
        print(f"\n📋 METADATA FROM {doc_files[0]}:")
        print(f"   Title: {metadata.get('title', 'N/A')}")
        print(f"   Code: {metadata.get('code', 'N/A')}")
        print(f"   Agency: {metadata.get('executing_agency', 'N/A')}")
        print(f"   Fee: {metadata.get('fee_vnd', 'N/A')} VND")
        
        print(f"\n💡 METADATA SOURCE: Single source of truth từ document.json")
        print(f"🚫 ELIMINATED: Duplicate metadata trong router_questions.json")
    
    return {
        "demo_file": demo_file,
        "questions_file": questions_file,
        "reduction_percent": reduction,
        "clean_questions": clean_questions
    }

def create_filter_engine_demo():
    """Demo FilterEngine để derive business logic từ metadata"""
    
    print("\n🔧 DEMO: FILTER ENGINE (Business logic separation)")
    
    # Sample metadata từ document.json
    sample_metadata = {
        "title": "Thủ tục cấp hộ tịch cấp xã",
        "code": "TT-01-2023",
        "executing_agency": "UBND Xã",
        "fee_vnd": 50000,
        "processing_time": "3 ngày"
    }
    
    class FilterEngine:
        @staticmethod
        def derive_smart_filters(metadata):
            """Derive filters từ metadata instead of hardcoding trong JSON"""
            return {
                "exact_title": [metadata.get("title")],
                "procedure_code": [metadata.get("code")],
                "agency": [metadata.get("executing_agency")],
                "cost_range": FilterEngine._get_cost_range(metadata.get("fee_vnd", 0)),
                "processing_category": FilterEngine._get_processing_category(metadata.get("processing_time", ""))
            }
        
        @staticmethod
        def _get_cost_range(fee):
            if fee == 0: return "free"
            elif fee < 100000: return "low" 
            elif fee < 500000: return "medium"
            else: return "high"
        
        @staticmethod
        def _get_processing_category(time_str):
            if "ngày" in time_str:
                days = int(time_str.split()[0])
                if days <= 1: return "instant"
                elif days <= 5: return "fast"
                elif days <= 15: return "normal"
                else: return "slow"
            return "unknown"
    
    derived_filters = FilterEngine.derive_smart_filters(sample_metadata)
    
    print(f"📊 SAMPLE METADATA:")
    print(json.dumps(sample_metadata, ensure_ascii=False, indent=2))
    
    print(f"\n⚡ DERIVED FILTERS (Business logic in code):")
    print(json.dumps(derived_filters, ensure_ascii=False, indent=2))
    
    print(f"\n💡 BENEFIT:")
    print(f"   ✅ Business logic = trong code (dễ maintain)")
    print(f"   ✅ Filters = derived từ metadata (single source)")
    print(f"   ✅ JSON = chỉ chứa data thuần túy")
    
    return derived_filters

if __name__ == "__main__":
    print("🚀 STARTING PROOF OF CONCEPT...")
    print("=" * 60)
    
    # Demo 1: God object elimination
    demo_result = demonstrate_god_object_elimination()
    
    print("\n" + "=" * 60)
    
    # Demo 2: Filter engine  
    derived_filters = create_filter_engine_demo()
    
    print("\n" + "=" * 60)
    print("🎯 PROOF OF CONCEPT COMPLETE!")
    
    if demo_result:
        print(f"✅ God object reduced by {demo_result['reduction_percent']:.1f}%")
        print(f"✅ Clean architecture demonstrated")
        print(f"✅ Business logic separated from data")
        
        print(f"\n🤔 NEXT STEP:")
        print(f"   1️⃣ Review demo files")
        print(f"   2️⃣ Confirm approach")  
        print(f"   3️⃣ Full migration (53 files)")
    else:
        print("⚠️ Demo file not found, but Filter Engine concept demonstrated")
