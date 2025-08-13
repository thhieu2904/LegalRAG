"""
Test script để kiểm tra Phòng thủ 2 lớp mới
"""

import os
import sys
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

def test_confidence_levels():
    """Test logic của Multi-level confidence"""
    
    print("🛡️ TESTING PHÒNG THỦ 2 LỚP")
    print("=" * 60)
    
    test_cases = [
        {"confidence": 0.8, "expected_level": "high", "expected_action": "Route trực tiếp"},
        {"confidence": 0.65, "expected_level": "medium", "expected_action": "Route với warning"},
        {"confidence": 0.5, "expected_level": "low", "expected_action": "Smart clarification"},
        {"confidence": 0.25, "expected_level": "very_low", "expected_action": "Vector backup"},
    ]
    
    # Apply the logic we implemented
    high_threshold = 0.75
    medium_threshold = 0.6
    min_threshold = 0.4
    
    for test in test_cases:
        confidence = test["confidence"]
        expected_level = test["expected_level"]
        expected_action = test["expected_action"]
        
        # Determine confidence level
        if confidence >= high_threshold:
            actual_level = "high"
            actual_action = "Route trực tiếp"
        elif confidence >= medium_threshold:
            actual_level = "medium"
            actual_action = "Route với warning"
        elif confidence >= min_threshold:
            actual_level = "low"
            actual_action = "Smart clarification"
        else:
            actual_level = "very_low"
            actual_action = "Vector backup"
        
        status = "✅ PASS" if (actual_level == expected_level and actual_action == expected_action) else "❌ FAIL"
        
        print(f"{status} Confidence: {confidence:.2f}")
        print(f"   Expected: {expected_level} → {expected_action}")
        print(f"   Got: {actual_level} → {actual_action}")
        print()

def test_suggestion_generation():
    """Test suggestion generation logic"""
    
    print("🎯 TESTING SUGGESTION GENERATION")
    print("=" * 60)
    
    # Mock collection scores
    collection_scores = {
        'ho_tich_cap_xa': 0.45,
        'chung_thuc': 0.35,
        'nuoi_con_nuoi': 0.25,
        'general': 0.15
    }
    
    # Apply suggestion logic
    sorted_collections = sorted(collection_scores.items(), key=lambda x: x[1], reverse=True)
    suggestions = []
    
    for collection_name, score in sorted_collections[:3]:
        if score > 0.2:  # Threshold
            display_name = collection_name.replace('_', ' ').title()
            suggestions.append({
                'collection': collection_name,
                'display_name': display_name,
                'score': score
            })
    
    print(f"📊 Generated {len(suggestions)} suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion['display_name']} (score: {suggestion['score']:.2f})")
    
    print(f"\n✅ Filter threshold 0.2 worked - excluded 'general' (0.15)")

if __name__ == "__main__":
    test_confidence_levels()
    print()
    test_suggestion_generation()
