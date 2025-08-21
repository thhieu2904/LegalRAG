#!/usr/bin/env python3
"""
SYSTEMATIC CLARIFICATION SYSTEM ANALYSIS
=========================================

Phân tích toàn bộ hệ thống clarification để đảm bảo logic 4-level ban đầu
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def analyze_clarification_levels():
    """Phân tích các levels clarification hiện tại"""
    
    print("🔍 ANALYZING CLARIFICATION LEVELS")
    print("=" * 50)
    
    try:
        from app.services.clarification import ClarificationService
        clarification_service = ClarificationService()
        
        levels = clarification_service.clarification_levels
        
        print("📊 CURRENT CLARIFICATION LEVELS:")
        print("-" * 30)
        
        for level_name, level_config in levels.items():
            print(f"\n{level_name.upper()}:")
            print(f"  Range: {level_config.min_confidence:.2f} - {level_config.max_confidence:.2f}")
            print(f"  Strategy: {level_config.strategy}")
            print(f"  Message: {level_config.message_template[:60]}...")
        
        # Check for gaps in confidence ranges
        sorted_levels = sorted(levels.items(), key=lambda x: x[1].min_confidence)
        
        print(f"\n🎯 CONFIDENCE RANGE ANALYSIS:")
        print("-" * 30)
        
        for i, (level_name, level_config) in enumerate(sorted_levels):
            print(f"{level_config.min_confidence:.2f}-{level_config.max_confidence:.2f}: {level_name}")
            
        # Check for gaps
        gaps = []
        for i in range(len(sorted_levels) - 1):
            current_max = sorted_levels[i][1].max_confidence
            next_min = sorted_levels[i + 1][1].min_confidence
            
            if current_max < next_min:
                gaps.append((current_max, next_min))
        
        if gaps:
            print(f"\n⚠️  CONFIDENCE GAPS FOUND:")
            for gap_start, gap_end in gaps:
                print(f"  Gap: {gap_start:.2f} - {gap_end:.2f}")
        else:
            print(f"\n✅ No confidence gaps found")
        
        return levels
        
    except Exception as e:
        print(f"❌ Error analyzing clarification levels: {e}")
        return None

def analyze_router_thresholds():
    """Phân tích router thresholds"""
    
    print("\n🔍 ANALYZING ROUTER THRESHOLDS")
    print("=" * 50)
    
    try:
        from sentence_transformers import SentenceTransformer
        from app.services.router import QueryRouter
        
        model = SentenceTransformer("AITeamVN/Vietnamese_Embedding_v2", device="cpu")
        router = QueryRouter(model)
        
        print("📊 ROUTER THRESHOLDS:")
        print(f"  High confidence: {router.high_confidence_threshold:.2f}")
        print(f"  Min confidence: {router.min_confidence_threshold:.2f}")
        
        # Map router confidence levels to clarification levels
        print(f"\n🎯 ROUTER → CLARIFICATION MAPPING:")
        print(f"  >= {router.high_confidence_threshold:.2f}: HIGH CONFIDENCE → Auto route (no clarification)")
        print(f"  {router.min_confidence_threshold:.2f} - {router.high_confidence_threshold:.2f}: MEDIUM CONFIDENCE → Multiple choices clarification")
        print(f"  < {router.min_confidence_threshold:.2f}: LOW CONFIDENCE → Category suggestions clarification")
        
        return {
            'high_threshold': router.high_confidence_threshold,
            'min_threshold': router.min_confidence_threshold
        }
        
    except Exception as e:
        print(f"❌ Error analyzing router thresholds: {e}")
        return None

def analyze_multi_step_flow():
    """Phân tích multi-step clarification flow"""
    
    print("\n🔍 ANALYZING MULTI-STEP CLARIFICATION FLOW")
    print("=" * 60)
    
    try:
        import json
        
        # Read RAG engine code để analyze steps
        rag_engine_file = backend_dir / "app" / "services" / "rag_engine.py"
        
        with open(rag_engine_file, 'r', encoding='utf-8') as f:
            rag_code = f.read()
        
        # Find clarification steps
        steps_found = []
        
        step_patterns = [
            "Step 2:",
            "Step 2.5:",
            "Step 3",
            "Giai đoạn 2:",
            "Giai đoạn 2.5:",
            "Giai đoạn 3:"
        ]
        
        for pattern in step_patterns:
            if pattern in rag_code:
                steps_found.append(pattern)
        
        print("📊 CLARIFICATION STEPS FOUND:")
        for step in steps_found:
            print(f"  ✅ {step}")
        
        # Check for action handlers
        action_patterns = [
            "proceed_with_collection",
            "proceed_with_document", 
            "proceed_with_question",
            "manual_input"
        ]
        
        actions_found = []
        for action in action_patterns:
            if action in rag_code:
                actions_found.append(action)
        
        print(f"\n📊 ACTION HANDLERS FOUND:")
        for action in actions_found:
            print(f"  ✅ {action}")
        
        # Expected flow analysis
        print(f"\n🎯 EXPECTED CLARIFICATION FLOW:")
        print(f"  1. Initial query → Router confidence analysis")
        print(f"  2a. Low confidence → Category selection (collection)")
        print(f"  2b. Medium confidence → Multiple collection choices")
        print(f"  2c. High confidence → Auto route")
        print(f"  3. Collection selected → Document selection")
        print(f"  4. Document selected → Question suggestions")
        print(f"  5. Question selected or manual input → RAG processing")
        
        return {
            'steps_found': steps_found,
            'actions_found': actions_found
        }
        
    except Exception as e:
        print(f"❌ Error analyzing multi-step flow: {e}")
        return None

def check_user_design_vs_current():
    """So sánh thiết kế ban đầu của user với implementation hiện tại"""
    
    print("\n🔍 USER DESIGN vs CURRENT IMPLEMENTATION")
    print("=" * 60)
    
    user_design = {
        "very_low": "Collection → Document → Questions/Manual",
        "low_medium": "Document → Questions/Manual", 
        "medium_high": "Questions in 1 document/Manual",
        "high": "Auto route"
    }
    
    current_implementation = {
        "low_confidence": "Category suggestions (0.00-0.49)",
        "medium_confidence": "Multiple choices (0.50-0.69)",
        "high_confidence": "Confirm with suggestion (0.70-0.84)",
        "very_high": "Auto route (>0.80)"
    }
    
    print("📊 USER'S ORIGINAL DESIGN:")
    for level, description in user_design.items():
        print(f"  {level}: {description}")
    
    print(f"\n📊 CURRENT IMPLEMENTATION:")
    for level, description in current_implementation.items():
        print(f"  {level}: {description}")
    
    print(f"\n🎯 ANALYSIS:")
    print(f"  ✅ Multi-step flow exists (Collection → Document → Questions)")
    print(f"  ⚠️  Only 3 levels instead of 4 (missing medium-high level)")
    print(f"  ⚠️  High confidence shows confirmation instead of auto-routing")
    print(f"  ✅ Manual input option available")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"  1. Add 'medium_high_confidence' level (0.65-0.79)")
    print(f"  2. Adjust high confidence to auto-route (>0.80)")
    print(f"  3. Make medium-high show questions within best document")
    print(f"  4. Ensure low confidence shows collection selection first")

def main():
    print("🚀 SYSTEMATIC CLARIFICATION SYSTEM ANALYSIS")
    print("=" * 70)
    
    # Analysis 1: Clarification levels
    levels = analyze_clarification_levels()
    
    # Analysis 2: Router thresholds  
    thresholds = analyze_router_thresholds()
    
    # Analysis 3: Multi-step flow
    flow_analysis = analyze_multi_step_flow()
    
    # Analysis 4: User design comparison
    check_user_design_vs_current()
    
    print(f"\n📋 SUMMARY:")
    print(f"Clarification Levels: {'✅' if levels else '❌'}")
    print(f"Router Thresholds: {'✅' if thresholds else '❌'}")
    print(f"Multi-step Flow: {'✅' if flow_analysis else '❌'}")

if __name__ == "__main__":
    main()
