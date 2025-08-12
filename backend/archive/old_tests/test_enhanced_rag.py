"""
Test Script cho Enhanced RAG Service
Kiểm tra tất cả tính năng mới:
1. Query preprocessing với clarification
2. Session management
3. Hybrid retrieval strategy
4. Context optimization
"""

import requests
import json
import time
from typing import Dict, Any, Optional, Tuple

class EnhancedRAGTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.session_id = None
    
    def test_health(self):
        """Test enhanced health endpoint"""
        print("🔍 Testing Enhanced Health Check...")
        try:
            response = requests.get(f"{self.api_base}/health")
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Enhanced Health Check Passed")
                print(f"   Service Type: {health_data.get('service_type', 'unknown')}")
                print(f"   Status: {health_data.get('status', 'unknown')}")
                print(f"   Active Sessions: {health_data.get('additional_info', {}).get('active_sessions', 0)}")
                print(f"   Enhanced Features: {health_data.get('additional_info', {}).get('enhanced_features', {})}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def create_session(self, metadata: Optional[Dict[str, Any]] = None):
        """Tạo session chat mới"""
        print("🔄 Creating Chat Session...")
        try:
            payload = {"metadata": metadata} if metadata else {}
            response = requests.post(f"{self.api_base}/session/create", json=payload)
            if response.status_code == 200:
                session_data = response.json()
                self.session_id = session_data["session_id"]
                print(f"✅ Session created: {self.session_id}")
                return True
            else:
                print(f"❌ Session creation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Session creation error: {e}")
            return False
    
    def test_enhanced_query(self, question: str, expect_clarification: bool = False) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Test enhanced query với preprocessing"""
        print(f"🧠 Testing Enhanced Query: '{question}'")
        
        payload = {
            "question": question,
            "session_id": self.session_id,
            "enable_clarification": True,
            "enable_context_synthesis": True,
            "clarification_threshold": "medium",
            "max_tokens": 1024,
            "temperature": 0.2
        }
        
        try:
            response = requests.post(f"{self.api_base}/enhanced-query", json=payload)
            if response.status_code == 200:
                result = response.json()
                response_type = result.get("type", "unknown")
                
                print(f"   Response Type: {response_type}")
                print(f"   Processing Steps: {result.get('preprocessing_steps', [])}")
                print(f"   Processing Time: {result.get('processing_time', 0):.2f}s")
                
                if response_type == "clarification_request":
                    print("🤔 Clarification Requested:")
                    for i, question in enumerate(result.get("clarification_questions", []), 1):
                        print(f"   {i}. {question}")
                    return "clarification", result
                
                elif response_type == "answer":
                    print("✅ Answer Generated:")
                    answer = result.get("answer", "")
                    print(f"   Answer: {answer[:200]}..." if len(answer) > 200 else f"   Answer: {answer}")
                    print(f"   Sources: {len(result.get('sources', []))} documents")
                    print(f"   Context Strategy: {result.get('context_strategy', {})}")
                    return "answer", result
                
            else:
                print(f"❌ Enhanced query failed: {response.status_code}")
                print(response.text)
                return "error", None
                
        except Exception as e:
            print(f"❌ Enhanced query error: {e}")
            return "error", None
    
    def provide_clarification(self, original_question: str, clarification_responses: Dict[str, str]):
        """Test clarification response"""
        print("💡 Providing Clarification...")
        
        payload = {
            "session_id": self.session_id,
            "original_question": original_question,
            "responses": clarification_responses
        }
        
        try:
            response = requests.post(f"{self.api_base}/clarify", json=payload)
            if response.status_code == 200:
                result = response.json()
                print("✅ Clarification Processed:")
                answer = result.get("answer", "")
                print(f"   Answer: {answer[:200]}..." if len(answer) > 200 else f"   Answer: {answer}")
                print(f"   Sources: {len(result.get('sources', []))} documents")
                return "success", result
            else:
                print(f"❌ Clarification failed: {response.status_code}")
                return "error", None
        except Exception as e:
            print(f"❌ Clarification error: {e}")
            return "error", None
    
    def get_session_info(self):
        """Lấy thông tin session"""
        print("📊 Getting Session Info...")
        try:
            response = requests.get(f"{self.api_base}/session/{self.session_id}")
            if response.status_code == 200:
                session_data = response.json()
                print("✅ Session Info:")
                print(f"   Session ID: {session_data.get('session_id', 'unknown')}")
                print(f"   Conversation Turns: {session_data.get('conversation_turns', 0)}")
                print(f"   Topics: {session_data.get('topics', [])}")
                print(f"   Recent Queries: {session_data.get('recent_queries', [])}")
                return session_data
            else:
                print(f"❌ Get session info failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Get session info error: {e}")
            return None
    
    def test_legacy_query(self, question: str):
        """Test legacy endpoint for backward compatibility"""
        print(f"⚡ Testing Legacy Query: '{question}'")
        
        payload = {
            "question": question,
            "max_tokens": 1024,
            "temperature": 0.2,
            "top_k": 5
        }
        
        try:
            response = requests.post(f"{self.api_base}/query", json=payload)
            if response.status_code == 200:
                result = response.json()
                print("✅ Legacy Query Success:")
                answer = result.get("answer", "")
                print(f"   Answer: {answer[:200]}..." if len(answer) > 200 else f"   Answer: {answer}")
                print(f"   Sources: {len(result.get('sources', []))} documents")
                return result
            else:
                print(f"❌ Legacy query failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Legacy query error: {e}")
            return None

def run_comprehensive_test():
    """Chạy test toàn diện cho Enhanced RAG Service"""
    print("="*80)
    print("🚀 ENHANCED RAG SERVICE COMPREHENSIVE TEST")
    print("="*80)
    
    tester = EnhancedRAGTester()
    
    # Test 1: Health Check
    print("\n" + "="*50)
    print("TEST 1: Enhanced Health Check")
    print("="*50)
    if not tester.test_health():
        print("❌ Health check failed, stopping tests")
        return
    
    # Test 2: Session Creation
    print("\n" + "="*50)
    print("TEST 2: Session Management")
    print("="*50)
    if not tester.create_session({"test": "comprehensive_test", "timestamp": time.time()}):
        print("❌ Session creation failed, stopping tests")
        return
    
    # Test 3: Clear Query (Should get direct answer)
    print("\n" + "="*50)
    print("TEST 3: Clear Query - Direct Answer")
    print("="*50)
    result_type, result = tester.test_enhanced_query(
        "Thủ tục đăng ký kết hôn cần những giấy tờ gì?"
    )
    
    # Test 4: Ambiguous Query (Should request clarification)
    print("\n" + "="*50)
    print("TEST 4: Ambiguous Query - Clarification Request")
    print("="*50)
    result_type, result = tester.test_enhanced_query(
        "Làm sao để nhận con nuôi?"
    )
    
    if result_type == "clarification":
        # Test 5: Provide Clarification
        print("\n" + "="*50)
        print("TEST 5: Clarification Response")
        print("="*50)
        clarification_responses = {
            "Bạn là công dân Việt Nam hay nước ngoài?": "công dân Việt Nam",
            "Bạn muốn nhận con nuôi trong nước hay nước ngoài?": "trong nước",
            "Bạn đã kết hôn chưa?": "đã kết hôn"
        }
        tester.provide_clarification(
            "Làm sao để nhận con nuôi?",
            clarification_responses
        )
    
    # Test 6: Context Synthesis (Follow-up question)
    print("\n" + "="*50)
    print("TEST 6: Context Synthesis - Follow-up Question")
    print("="*50)
    result_type, result = tester.test_enhanced_query(
        "Thời gian xử lý bao lâu?"
    )
    
    # Test 7: Session Info
    print("\n" + "="*50)
    print("TEST 7: Session Information")
    print("="*50)
    tester.get_session_info()
    
    # Test 8: Legacy Compatibility
    print("\n" + "="*50)
    print("TEST 8: Legacy API Compatibility")
    print("="*50)
    tester.test_legacy_query("Thủ tục xin visa du lịch như thế nào?")
    
    print("\n" + "="*80)
    print("🎉 COMPREHENSIVE TEST COMPLETED")
    print("="*80)

def run_performance_test():
    """Test hiệu năng của Enhanced RAG"""
    print("="*80)
    print("⚡ ENHANCED RAG PERFORMANCE TEST")
    print("="*80)
    
    tester = EnhancedRAGTester()
    
    if not tester.test_health():
        return
    
    if not tester.create_session({"test": "performance_test"}):
        return
    
    test_queries = [
        "Thủ tục làm bằng lái xe ô tô cần gì?",
        "Cách đăng ký kinh doanh online",
        "Hồ sơ xin cấp hộ chiếu mới",
        "Thủ tục chuyển đổi bằng lái xe",
        "Đăng ký tạm trú tạm vắng"
    ]
    
    total_time = 0
    success_count = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔸 Performance Test {i}/5: '{query}'")
        start_time = time.time()
        
        result_type, result = tester.test_enhanced_query(query)
        
        end_time = time.time()
        query_time = end_time - start_time
        total_time += query_time
        
        if result_type in ["answer", "clarification"]:
            success_count += 1
            print(f"   ✅ Success in {query_time:.2f}s")
        else:
            print(f"   ❌ Failed in {query_time:.2f}s")
    
    print(f"\n📊 Performance Summary:")
    print(f"   Total Tests: {len(test_queries)}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {len(test_queries) - success_count}")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"   Average Time: {total_time/len(test_queries):.2f}s")
    print(f"   Success Rate: {success_count/len(test_queries)*100:.1f}%")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "performance":
        run_performance_test()
    else:
        run_comprehensive_test()
