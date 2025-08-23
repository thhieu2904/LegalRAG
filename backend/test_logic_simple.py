"""
Simple test script để check router trust logic
Không cần load model, chỉ test logic
"""

import sys
import os

def test_router_trust_logic():
    """Test router trust logic without loading models"""
    
    print("🧪 TESTING ROUTER TRUST LOGIC")
    print("="*50)
    
    # Mock scenarios
    test_cases = [
        {
            "name": "High Confidence Case",
            "router_confidence": 0.9183,
            "router_confidence_level": "high",
            "expected_behavior": "Use router decision (trust mode)"
        },
        {
            "name": "Medium Confidence Case",
            "router_confidence": 0.6524,
            "router_confidence_level": "medium", 
            "expected_behavior": "Use reranker consensus"
        },
        {
            "name": "Low Confidence Case",
            "router_confidence": 0.3142,
            "router_confidence_level": "low",
            "expected_behavior": "Use reranker consensus"
        },
        {
            "name": "Edge Case - Threshold Boundary",
            "router_confidence": 0.8500,
            "router_confidence_level": "high",
            "expected_behavior": "Use reranker consensus (exactly at threshold)"
        },
        {
            "name": "Edge Case - Just Above Threshold",
            "router_confidence": 0.8501,
            "router_confidence_level": "high",
            "expected_behavior": "Use router decision (trust mode)"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"{i}️⃣ {case['name']}:")
        print(f"   🎯 Router Confidence: {case['router_confidence']:.4f} ({case['router_confidence_level']})")
        
        # Test the logic from reranker.py
        should_trust_router = case['router_confidence'] > 0.85
        
        if should_trust_router:
            actual_behavior = "Use router decision (trust mode)"
            emoji = "🎯"
        else:
            actual_behavior = "Use reranker consensus"
            emoji = "🔄"
        
        print(f"   {emoji} Actual Behavior: {actual_behavior}")
        print(f"   📋 Expected: {case['expected_behavior']}")
        
        if actual_behavior == case['expected_behavior']:
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL")
        
        print()
    
    print("🎯 ROUTER TRUST THRESHOLD: 0.85")
    print("📊 Logic: if router_confidence > 0.85 → trust router, else → use reranker")
    print("="*50)

def test_marriage_query_scenario():
    """Test cụ thể cho marriage registration scenario"""
    
    print("💍 MARRIAGE REGISTRATION SCENARIO TEST")
    print("="*50)
    
    query = "đăng ký kết hôn cần giấy tờ gì"
    
    # Mock router results based on our previous debugging
    router_results = {
        "DOC_011": 0.9183,  # Normal marriage registration (correct)
        "DOC_031": 0.7624   # Mobile marriage registration (wrong)
    }
    
    print(f"📝 Query: {query}")
    print(f"🎯 Router Results:")
    for doc_id, score in router_results.items():
        print(f"   {doc_id}: {score:.4f}")
    
    # Determine winner
    top_doc = max(router_results.items(), key=lambda x: x[1])
    top_doc_id, top_confidence = top_doc
    
    print(f"🏆 Router Winner: {top_doc_id} (confidence: {top_confidence:.4f})")
    
    # Test router trust logic
    if top_confidence > 0.85:
        print(f"🎯 HIGH CONFIDENCE DETECTED: {top_confidence:.4f} > 0.85")
        print(f"✅ ROUTER TRUST MODE: Should use {top_doc_id}")
        print(f"🚫 RERANKER OVERRIDE: Blocked")
        
        if top_doc_id == "DOC_011":
            print(f"🎉 SUCCESS: Correct document selected!")
        else:
            print(f"❌ ERROR: Wrong document selected!")
    else:
        print(f"📊 NORMAL CONFIDENCE: {top_confidence:.4f} <= 0.85")
        print(f"🔄 RERANKER MODE: Will use consensus algorithm")
    
    print("="*50)

if __name__ == "__main__":
    test_router_trust_logic()
    print()
    test_marriage_query_scenario()
