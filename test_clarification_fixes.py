#!/usr/bin/env python3
"""
Test Script for Clarification Flow Fixes
==========================================

Tests the 3 key fixes:
1. Manual input inline display (frontend behavior - manual verification)
2. Force routing from clarification (backend routing logic)  
3. Confidence scores in options (backend confidence mapping)

Usage: python test_clarification_fixes.py
Requirement: Backend must be running on port 8000
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_force_routing():
    """Test force routing functionality"""
    print("🔥 TEST 1: Force Routing from Clarification")
    print("=" * 50)
    
    # Test force routing via API
    test_data = {
        "query": "Tôi muốn đăng ký kết hôn",
        "force_collection": "quy_trinh_cap_ho_tich_cap_xa",
        "force_document": "DOC_011"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/query", json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Status: {response.status_code}")
            print(f"📋 Response type: {result.get('type', 'N/A')}")
            
            # Check if routing was forced
            routing_info = result.get('routing_info', {})
            if routing_info.get('confidence_level') == 'forced_high' or routing_info.get('was_overridden'):
                print("🔒 FORCE ROUTING: SUCCESS - Query was force routed!")
            else:
                print("⚠️  FORCE ROUTING: Not detected in response")
            
            # Check target collection
            target_collection = routing_info.get('target_collection')
            if target_collection == "quy_trinh_cap_ho_tich_cap_xa":
                print(f"✅ Target Collection: {target_collection} (CORRECT)")
            else:
                print(f"❌ Target Collection: {target_collection} (EXPECTED: quy_trinh_cap_ho_tich_cap_xa)")
            
            print(f"⏱️  Processing Time: {result.get('processing_time', 0):.3f}s")
            print()
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test Error: {e}")

def test_clarification_with_confidence():
    """Test clarification with confidence scores"""
    print("🔥 TEST 2: Clarification with Confidence Scores")
    print("=" * 50)
    
    # Test medium confidence query to trigger clarification
    test_data = {
        "query": "tuổi kết hôn",
        "session_id": f"test_session_{int(time.time())}"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/query", json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Status: {response.status_code}")
            print(f"📋 Response type: {result.get('type', 'N/A')}")
            
            # Check for clarification
            clarification = result.get('clarification')
            if clarification:
                print("📋 CLARIFICATION FOUND:")
                print(f"  - Message: {clarification.get('message', 'N/A')[:80]}...")
                print(f"  - Style: {clarification.get('style', 'N/A')}")
                print(f"  - Show Manual Input: {clarification.get('show_manual_input', False)}")
                
                # Check options with confidence
                options = clarification.get('options', [])
                print(f"  - Options Count: {len(options)}")
                
                confidence_found = False
                for i, option in enumerate(options[:3]):  # Show first 3
                    confidence_percent = option.get('confidence_percent')
                    if confidence_percent is not None:
                        confidence_found = True
                        print(f"    Option {i+1}: {option.get('title', 'N/A')[:50]}... (confidence: {confidence_percent}%)")
                    else:
                        print(f"    Option {i+1}: {option.get('title', 'N/A')[:50]}... (no confidence)")
                
                if confidence_found:
                    print("✅ CONFIDENCE SCORES: Found in options!")
                else:
                    print("❌ CONFIDENCE SCORES: Not found in options")
                    
            else:
                print("❌ No clarification found in response")
                
            print(f"⏱️  Processing Time: {result.get('processing_time', 0):.3f}s")
            print()
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test Error: {e}")

def test_manual_input_context_preservation():
    """Test manual input context preservation"""
    print("🔥 TEST 3: Manual Input Context Preservation")
    print("=" * 50)
    
    # First, get a clarification
    session_id = f"test_session_{int(time.time())}"
    
    # Step 1: Trigger clarification
    test_data = {
        "query": "tuổi kết hôn",
        "session_id": session_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/query", json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            clarification = result.get('clarification')
            
            if clarification and clarification.get('options'):
                # Find manual input option
                manual_option = None
                for option in clarification['options']:
                    if option.get('action') == 'manual_input':
                        manual_option = option
                        break
                
                if manual_option:
                    print("📋 Found manual input option:")
                    print(f"  - Title: {manual_option.get('title', 'N/A')}")
                    print(f"  - Collection: {manual_option.get('collection', 'N/A')}")
                    print(f"  - Document: {manual_option.get('document', 'N/A')}")
                    
                    # Step 2: Simulate manual input selection
                    clarify_data = {
                        "session_id": session_id,
                        "original_query": "tuổi kết hôn",
                        "selected_option": manual_option
                    }
                    
                    clarify_response = requests.post(f"{BASE_URL}/api/v1/clarify", json=clarify_data, timeout=30)
                    
                    if clarify_response.status_code == 200:
                        clarify_result = clarify_response.json()
                        
                        print("✅ Manual Input Response:")
                        print(f"  - Type: {clarify_result.get('type', 'N/A')}")
                        print(f"  - Context Preserved: {clarify_result.get('context_preserved', False)}")
                        print(f"  - Force Routing: {clarify_result.get('force_routing', False)}")
                        
                        routing_info = clarify_result.get('routing_info', {})
                        force_collection = routing_info.get('force_collection')
                        force_document = routing_info.get('force_document')
                        
                        if force_collection:
                            print(f"✅ CONTEXT PRESERVATION: Force collection = {force_collection}")
                        else:
                            print("❌ CONTEXT PRESERVATION: No force collection found")
                            
                        if force_document:
                            print(f"✅ CONTEXT PRESERVATION: Force document = {force_document}")
                        else:
                            print("⚠️  CONTEXT PRESERVATION: No force document (might be normal)")
                            
                    else:
                        print(f"❌ Clarify API Error: {clarify_response.status_code}")
                        
                else:
                    print("❌ No manual input option found in clarification")
                    
            else:
                print("❌ No clarification or options found")
                print(f"Response type: {result.get('type', 'N/A')}")
                
        else:
            print(f"❌ Initial API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test Error: {e}")
    
    print()

def test_health_check():
    """Test if backend is running"""
    print("🔥 HEALTH CHECK")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Please ensure the backend is running on port 8000")
        return False

def main():
    """Run all tests"""
    print("🧪 CLARIFICATION FLOW FIXES - TEST SUITE")
    print("=" * 70)
    print()
    
    # Health check
    if not test_health_check():
        print("❌ Backend not available. Please start the backend service.")
        return
    
    print()
    
    # Run tests
    test_force_routing()
    test_clarification_with_confidence()
    test_manual_input_context_preservation()
    
    print("=" * 70)
    print("🎯 TESTING COMPLETE")
    print()
    print("MANUAL TESTS TO VERIFY:")
    print("1. 🖥️  Frontend Manual Input Display:")
    print("   - Open frontend, trigger clarification")
    print("   - Check if 'Câu hỏi khác...' shows inline input field")
    print("   - NOT as separate chatbot response")
    print()
    print("2. 🔄 End-to-End Force Routing:")
    print("   - Trigger clarification → select document → choose 'Câu hỏi khác...'")
    print("   - Enter manual question → verify it routes to correct collection")
    print("   - Check logs for 'FORCE ROUTING' messages")
    print()
    print("3. 📊 Confidence Badges:")
    print("   - Check if clarification options show confidence percentages")
    print("   - Look for colored badges (📊 XX%)")

if __name__ == "__main__":
    main()