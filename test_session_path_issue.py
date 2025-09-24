#!/usr/bin/env python3
"""
Test Session Path Issue - Comprehensive testing for follow-up query path resolution
Tests the exact issue: Windows paths in session cache cause UnboundLocalError in Docker

Test Flow:
1. Initial query → verify session stores proper Docker paths
2. Follow-up query → verify path normalization works
3. Multiple scenarios → verify consistency
"""

import json
import requests
import time
import sys
from typing import Dict, Any

# Configuration
RAG_SERVICE_URL = "http://localhost:8000"
TEST_SESSION_ID = "test-session-path-fix"

class SessionPathTester:
    def __init__(self):
        self.session_id = TEST_SESSION_ID
        self.base_url = RAG_SERVICE_URL
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def send_query(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Send query to RAG service"""
        if session_id is None:
            session_id = self.session_id
            
        payload = {
            "query": query,
            "session_id": session_id
        }
        
        self.log(f"🔍 Sending query: '{query}' (session: {session_id})")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/query",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Query successful (processing_time: {data.get('processing_time', 'N/A'):.2f}s)")
                return data
            else:
                self.log(f"❌ Query failed: {response.status_code} - {response.text}", "ERROR")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.log(f"❌ Request error: {e}", "ERROR")
            return {"error": str(e)}
    
    def get_session_info(self, session_id: str = None) -> Dict[str, Any]:
        """Get session information"""
        if session_id is None:
            session_id = self.session_id
            
        try:
            response = requests.get(f"{self.base_url}/api/v1/session/{session_id}")
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"⚠️ Session not found: {session_id}", "WARN")
                return {}
        except Exception as e:
            self.log(f"❌ Session check error: {e}", "ERROR")
            return {}
    
    def analyze_response(self, response: Dict[str, Any], step: str) -> Dict[str, Any]:
        """Analyze response structure and extract path information"""
        analysis = {
            "step": step,
            "success": False,  # Will be set below
            "has_nucleus_chunks": False,
            "source_documents": [],
            "path_formats": [],
            "context_info": {}
        }
        
        # Debug: Log response keys
        self.log(f"🔍 Response keys for {step}: {response.keys()}")
        
        # Check for actual errors (error field with non-null value)
        if response.get("error"):
            analysis["error"] = response["error"]
            analysis["success"] = False
            self.log(f"❌ {step} failed: {response['error']}", "ERROR")
            return analysis
        
        # Success if no error
        analysis["success"] = True
        
        # Check context_info
        if "context_info" in response:
            analysis["context_info"] = response["context_info"]
            nucleus_chunks_count = response["context_info"].get("nucleus_chunks", 0)
            analysis["has_nucleus_chunks"] = nucleus_chunks_count > 0
            
            # Extract source documents and analyze path formats
            if "source_documents" in response["context_info"]:
                analysis["source_documents"] = response["context_info"]["source_documents"]
                
                for doc_path in analysis["source_documents"]:
                    if isinstance(doc_path, str):
                        # Analyze path format
                        if doc_path.startswith("/app/"):
                            analysis["path_formats"].append("Docker")
                        elif ":" in doc_path and "\\" in doc_path:
                            analysis["path_formats"].append("Windows")  
                        elif doc_path.startswith("data/"):
                            analysis["path_formats"].append("Relative")
                        else:
                            analysis["path_formats"].append("Unknown")
        
        self.log(f"📊 {step} Analysis:")
        self.log(f"   - Success: {analysis['success']}")
        self.log(f"   - Has nucleus_chunks: {analysis['has_nucleus_chunks']}")
        self.log(f"   - Source documents: {len(analysis['source_documents'])}")
        self.log(f"   - Path formats: {set(analysis['path_formats'])}")
        
        return analysis
    
    def test_initial_query(self) -> Dict[str, Any]:
        """Test Step 1: Initial query"""
        self.log("🚀 Step 1: Testing initial query")
        
        query = "thủ tục đăng ký khai sinh cần giấy tờ gì?"
        response = self.send_query(query)
        analysis = self.analyze_response(response, "Initial Query")
        
        # Check session storage
        session_info = self.get_session_info()
        if session_info:
            self.log(f"📝 Session metadata keys: {list(session_info.get('metadata', {}).keys())}")
            
        return analysis
    
    def test_followup_query(self) -> Dict[str, Any]:
        """Test Step 2: Follow-up query (this is where the error occurs)"""
        self.log("🔥 Step 2: Testing follow-up query (critical test)")
        
        query = "có cần đóng phí không?"
        response = self.send_query(query)
        analysis = self.analyze_response(response, "Follow-up Query")
        
        return analysis
    
    def test_multiple_followups(self) -> list:
        """Test Step 3: Multiple follow-ups to verify consistency"""
        self.log("🔄 Step 3: Testing multiple follow-ups")
        
        followup_queries = [
            "thời gian xử lý bao lâu?",
            "cần giấy tờ gì thêm?",
            "làm ở đâu?"
        ]
        
        results = []
        for i, query in enumerate(followup_queries, 1):
            self.log(f"   Follow-up {i}: {query}")
            response = self.send_query(query)
            analysis = self.analyze_response(response, f"Follow-up {i}")
            results.append(analysis)
            
            # Small delay between queries
            time.sleep(1)
            
        return results
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        self.log("=" * 60)
        self.log("🧪 COMPREHENSIVE SESSION PATH TEST")
        self.log("=" * 60)
        
        results = {
            "test_session_id": self.session_id,
            "initial_query": None,
            "followup_query": None,
            "multiple_followups": [],
            "summary": {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0,
                "path_consistency": True,
                "nucleus_chunks_consistent": True
            }
        }
        
        try:
            # Step 1: Initial query
            results["initial_query"] = self.test_initial_query()
            results["summary"]["total_tests"] += 1
            if results["initial_query"]["success"]:
                results["summary"]["successful_tests"] += 1
            else:
                results["summary"]["failed_tests"] += 1
            
            time.sleep(2)  # Wait for session to be established
            
            # Step 2: Follow-up query (critical test)
            results["followup_query"] = self.test_followup_query()
            results["summary"]["total_tests"] += 1
            if results["followup_query"]["success"]:
                results["summary"]["successful_tests"] += 1
            else:
                results["summary"]["failed_tests"] += 1
            
            time.sleep(1)
            
            # Step 3: Multiple follow-ups
            results["multiple_followups"] = self.test_multiple_followups()
            for followup_result in results["multiple_followups"]:
                results["summary"]["total_tests"] += 1
                if followup_result["success"]:
                    results["summary"]["successful_tests"] += 1
                else:
                    results["summary"]["failed_tests"] += 1
            
            # Analyze consistency
            all_results = [results["initial_query"], results["followup_query"]] + results["multiple_followups"]
            
            # Check path format consistency
            all_path_formats = []
            for result in all_results:
                if result["success"]:
                    all_path_formats.extend(result["path_formats"])
            
            if all_path_formats:
                unique_formats = set(all_path_formats)
                results["summary"]["path_consistency"] = len(unique_formats) <= 1
                self.log(f"📊 Path formats found: {unique_formats}")
            
            # Check nucleus_chunks consistency
            nucleus_chunks_status = [r["has_nucleus_chunks"] for r in all_results if r["success"]]
            results["summary"]["nucleus_chunks_consistent"] = all(nucleus_chunks_status) if nucleus_chunks_status else False
            
        except Exception as e:
            self.log(f"❌ Test suite error: {e}", "ERROR")
            results["error"] = str(e)
        
        return results
    
    def print_final_report(self, results: Dict[str, Any]):
        """Print comprehensive test report"""
        self.log("=" * 60)
        self.log("📋 FINAL TEST REPORT")
        self.log("=" * 60)
        
        summary = results["summary"]
        self.log(f"Total Tests: {summary['total_tests']}")
        self.log(f"Successful: {summary['successful_tests']}")
        self.log(f"Failed: {summary['failed_tests']}")
        self.log(f"Success Rate: {(summary['successful_tests']/summary['total_tests']*100):.1f}%")
        
        self.log("")
        self.log("🔍 Key Metrics:")
        self.log(f"   - Path Consistency: {'✅ PASS' if summary['path_consistency'] else '❌ FAIL'}")
        self.log(f"   - Nucleus Chunks Consistent: {'✅ PASS' if summary['nucleus_chunks_consistent'] else '❌ FAIL'}")
        
        if summary["failed_tests"] > 0:
            self.log("")
            self.log("❌ FAILED TESTS:")
            all_results = [results["initial_query"], results["followup_query"]] + results["multiple_followups"]
            for result in all_results:
                if not result["success"]:
                    self.log(f"   - {result['step']}: {result.get('error', 'Unknown error')}")
        
        # Overall status
        overall_success = summary["failed_tests"] == 0 and summary["path_consistency"] and summary["nucleus_chunks_consistent"]
        
        self.log("")
        self.log("🎯 OVERALL STATUS:")
        if overall_success:
            self.log("✅ ALL TESTS PASSED - Session path fix is working correctly!")
        else:
            self.log("❌ TESTS FAILED - Session path issue still exists")
            
        return overall_success

def main():
    """Main test execution"""
    print("🧪 Session Path Issue Tester")
    print("Testing Docker environment path normalization for follow-up queries")
    print()
    
    tester = SessionPathTester()
    
    # Check if RAG service is available
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ RAG service not available at {RAG_SERVICE_URL}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot reach RAG service: {e}")
        sys.exit(1)
    
    # Run comprehensive test
    results = tester.run_comprehensive_test()
    
    # Print final report
    success = tester.print_final_report(results)
    
    # Save detailed results
    with open("test_session_path_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Detailed results saved to: test_session_path_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()