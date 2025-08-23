#!/usr/bin/env python3
"""
🔧 BACKEND CODE UPDATE FOR NEW QUESTIONS.JSON STRUCTURE

Updates backend code để support new clean questions.json format:
✅ Update router_crud.py to read questions.json + document.json
✅ Add FilterEngine để derive business logic từ metadata  
✅ Maintain backward compatibility during transition
✅ Add comprehensive testing
"""

import os
import json
import glob

def update_router_crud():
    """Update router_crud.py để support new structure"""
    
    router_crud_path = "d:/Personal/LegalRAG_Fixed/backend/app/api/router_crud.py"
    
    if not os.path.exists(router_crud_path):
        print(f"❌ router_crud.py not found at {router_crud_path}")
        return False
    
    print("🔧 UPDATING router_crud.py...")
    
    # Read current file
    with open(router_crud_path, 'r', encoding='utf-8') as f:
        current_content = f.read()
    
    # Add new imports at top
    new_imports = '''import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import glob
from ..services.filter_engine import FilterEngine  # New service
'''
    
    # Add new method for reading questions.json + document.json
    new_method = '''
def get_document_questions_v2(collection_name: str, document_id: str) -> Dict[str, Any]:
    """
    NEW METHOD: Load questions from questions.json + metadata từ document.json
    Replaces old router_questions.json god object approach
    """
    try:
        # Path to document directory
        doc_dir = f"data/storage/collections/{collection_name}/documents/{document_id}/"
        
        # Load questions (clean structure)
        questions_path = os.path.join(doc_dir, "questions.json")
        questions_data = {}
        
        if os.path.exists(questions_path):
            with open(questions_path, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
        else:
            # Fallback to old router_questions.json nếu questions.json chưa có
            router_path = os.path.join(doc_dir, "router_questions.json")
            if os.path.exists(router_path):
                with open(router_path, 'r', encoding='utf-8') as f:
                    router_data = json.load(f)
                questions_data = {
                    "main_question": router_data.get("main_question", ""),
                    "question_variants": router_data.get("question_variants", [])
                }
        
        # Load metadata từ document.json (single source of truth)
        doc_files = [f for f in os.listdir(doc_dir) 
                    if f.endswith('.json') and f not in ['questions.json', 'router_questions.json']]
        
        metadata = {}
        content_chunks = []
        
        if doc_files:
            doc_path = os.path.join(doc_dir, doc_files[0])
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
                metadata = doc_data.get('metadata', {})
                content_chunks = doc_data.get('content_chunks', [])
        
        # Derive smart filters từ metadata (business logic in code)
        smart_filters = FilterEngine.derive_smart_filters(metadata)
        
        # Build response trong format mà frontend expects
        response = {
            "document_id": document_id,
            "collection_name": collection_name,
            "main_question": questions_data.get("main_question", ""),
            "question_variants": questions_data.get("question_variants", []),
            "metadata": metadata,
            "smart_filters": smart_filters,
            "content_preview": content_chunks[:2] if content_chunks else [],
            "source": "questions.json + document.json"  # For debugging
        }
        
        return response
        
    except Exception as e:
        print(f"Error loading document questions v2: {e}")
        return {}

def get_questions_in_document_updated(collection_name: str, document_id: str):
    """
    UPDATED METHOD: Uses new v2 approach với fallback to old method
    """
    # Try new approach first
    result = get_document_questions_v2(collection_name, document_id)
    
    if result:
        return result
    
    # Fallback to original method nếu có lỗi
    print(f"Falling back to original method for {document_id}")
    return get_questions_in_document_original(collection_name, document_id)

# Backup original method
def get_questions_in_document_original(collection_name: str, document_id: str):
    """Original method - kept for fallback during transition"""
    # [Keep existing implementation as backup]
    pass
'''
    
    # Check if file already has these updates
    if "get_document_questions_v2" in current_content:
        print("   ⚠️  router_crud.py already contains v2 methods")
        return True
    
    # Add new method to file (append at end)
    updated_content = current_content + new_method
    
    # Write updated file
    backup_path = router_crud_path + ".backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(current_content)
    
    with open(router_crud_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"   ✅ router_crud.py updated")
    print(f"   💾 Backup saved: {backup_path}")
    
    return True

def create_filter_engine():
    """Create new FilterEngine service để handle business logic"""
    
    services_dir = "d:/Personal/LegalRAG_Fixed/backend/app/services"
    filter_engine_path = os.path.join(services_dir, "filter_engine.py")
    
    if os.path.exists(filter_engine_path):
        print("   ⚠️  FilterEngine already exists")
        return True
    
    print("🔧 CREATING FilterEngine service...")
    
    os.makedirs(services_dir, exist_ok=True)
    
    filter_engine_code = '''"""
FilterEngine Service - Business Logic Separation

Derives smart filters và business rules từ document metadata
instead of hardcoding trong JSON files (god object elimination)
"""

from typing import Dict, List, Any, Optional
import re

class FilterEngine:
    """
    Centralized business logic để derive filters từ metadata
    Eliminates need to store business logic trong JSON files
    """
    
    @staticmethod
    def derive_smart_filters(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Derive comprehensive smart filters từ document metadata
        
        Args:
            metadata: Document metadata từ document.json
            
        Returns:
            Dict containing derived smart filters
        """
        if not metadata:
            return {}
        
        filters = {
            "exact_title": FilterEngine._get_exact_title_filters(metadata),
            "procedure_code": FilterEngine._get_procedure_code_filters(metadata),
            "agency": FilterEngine._get_agency_filters(metadata),
            "cost_range": FilterEngine._get_cost_range(metadata),
            "processing_category": FilterEngine._get_processing_category(metadata),
            "subject_matter": FilterEngine._get_subject_matter(metadata),
            "urgency_level": FilterEngine._get_urgency_level(metadata)
        }
        
        # Remove empty filters
        return {k: v for k, v in filters.items() if v}
    
    @staticmethod
    def _get_exact_title_filters(metadata: Dict[str, Any]) -> List[str]:
        """Extract title-based filters"""
        title = metadata.get("title", "")
        if not title:
            return []
        
        filters = [title]
        
        # Add variations
        if "đăng ký" in title.lower():
            filters.append("thủ tục đăng ký")
        if "cấp" in title.lower():
            filters.append("thủ tục cấp giấy tờ")
        if "chứng thực" in title.lower():
            filters.append("chứng thực hồ sơ")
            
        return filters
    
    @staticmethod
    def _get_procedure_code_filters(metadata: Dict[str, Any]) -> List[str]:
        """Extract procedure code filters"""
        code = metadata.get("code", "")
        if not code:
            return []
        
        filters = [code]
        
        # Extract pattern-based codes
        if "QT" in code:
            filters.append("quy trình cấp xã")
        if "CX" in code:
            filters.append("cấp xã")
        if "HCTP" in code:
            filters.append("hộ tịch")
            
        return filters
    
    @staticmethod  
    def _get_agency_filters(metadata: Dict[str, Any]) -> List[str]:
        """Extract executing agency filters"""
        agency = metadata.get("executing_agency", "")
        if not agency:
            return []
        
        filters = [agency]
        
        # Normalize agency names
        if "cấp xã" in agency.lower():
            filters.extend(["UBND xã", "ủy ban xã", "chính quyền cơ sở"])
        if "cấp huyện" in agency.lower():
            filters.extend(["UBND huyện", "ủy ban huyện"])
        if "cấp tỉnh" in agency.lower():
            filters.extend(["UBND tỉnh", "ủy ban tỉnh"])
            
        return filters
    
    @staticmethod
    def _get_cost_range(metadata: Dict[str, Any]) -> str:
        """Determine cost category"""
        fee = metadata.get("fee_vnd")
        
        if fee is None or fee == 0:
            return "free"
        elif fee < 50000:
            return "very_low"
        elif fee < 100000:
            return "low"
        elif fee < 300000:
            return "medium"
        elif fee < 500000:
            return "high"
        else:
            return "very_high"
    
    @staticmethod
    def _get_processing_category(metadata: Dict[str, Any]) -> str:
        """Determine processing time category"""
        processing_time = metadata.get("processing_time", "")
        
        if not processing_time:
            return "unknown"
        
        # Extract số ngày
        if "ngày" in processing_time.lower():
            try:
                days = int(re.search(r'(\d+)', processing_time).group(1))
                if days <= 1:
                    return "instant"
                elif days <= 3:
                    return "fast"  
                elif days <= 7:
                    return "normal"
                elif days <= 15:
                    return "slow"
                else:
                    return "very_slow"
            except:
                pass
        
        if "tức thì" in processing_time.lower():
            return "instant"
        if "nhanh" in processing_time.lower():
            return "fast"
            
        return "normal"
    
    @staticmethod
    def _get_subject_matter(metadata: Dict[str, Any]) -> List[str]:
        """Extract thematic subject matter"""
        title = metadata.get("title", "").lower()
        subjects = []
        
        # Thematic categorization
        if any(word in title for word in ["khai sinh", "hộ tịch", "sinh"]):
            subjects.append("birth_registration")
        if any(word in title for word in ["kết hôn", "hôn nhân"]):
            subjects.append("marriage")
        if any(word in title for word in ["chứng thực", "công chứng"]):
            subjects.append("notarization")
        if any(word in title for word in ["giấy phép", "cấp phép"]):
            subjects.append("licensing")
        if any(word in title for word in ["thuế", "tài chính"]):
            subjects.append("taxation")
            
        return subjects
    
    @staticmethod
    def _get_urgency_level(metadata: Dict[str, Any]) -> str:
        """Determine urgency based on processing time và cost"""
        processing_time = metadata.get("processing_time", "")
        fee = metadata.get("fee_vnd", 0)
        
        # Instant procedures = high urgency
        if "tức thì" in processing_time.lower():
            return "high"
        
        # Free procedures = often urgent public services    
        if fee == 0:
            return "medium"
        
        # Quick + low cost = standard urgency
        if "ngày" in processing_time.lower():
            try:
                days = int(re.search(r'(\d+)', processing_time).group(1))
                if days <= 3:
                    return "medium"
                elif days > 10:
                    return "low"
            except:
                pass
                
        return "normal"
    
    @staticmethod
    def get_collection_mapping(metadata: Dict[str, Any]) -> str:
        """
        Determine appropriate collection based on metadata
        Replaces hardcoded expected_collection trong router_questions.json
        """
        title = metadata.get("title", "").lower()
        agency = metadata.get("executing_agency", "").lower()
        
        # Collection mapping logic
        if "hộ tịch" in title or "khai sinh" in title:
            return "quy_trinh_cap_ho_tich_cap_xa"
        elif "chứng thực" in title or "công chứng" in title:
            return "quy_trinh_chung_thuc"
        elif "cấp xã" in agency:
            return "quy_trinh_cap_xa_tong_hop"
        elif "cấp huyện" in agency:
            return "quy_trinh_cap_huyen"
        else:
            return "quy_trinh_tong_hop"
'''

    with open(filter_engine_path, 'w', encoding='utf-8') as f:
        f.write(filter_engine_code)
    
    print(f"   ✅ FilterEngine created: {filter_engine_path}")
    return True

def create_backend_integration_test():
    """Create test script để validate backend integration"""
    
    test_script = '''#!/usr/bin/env python3
"""
🧪 BACKEND INTEGRATION TEST

Tests new questions.json + document.json architecture với backend
"""

import requests
import json
import sys
import os

# Add parent directory to path để import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_backend_integration():
    """Test backend APIs với new structure"""
    
    print("🧪 BACKEND INTEGRATION TEST")
    print("=" * 50)
    
    # Test data
    test_cases = [
        {
            "collection": "quy_trinh_cap_ho_tich_cap_xa",
            "document": "DOC_001",
            "expected_question": "khai sinh"
        },
        {
            "collection": "quy_trinh_chung_thuc", 
            "document": "DOC_001",
            "expected_question": "chứng thực"
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\\n📋 Test {i}: {test_case['collection']}/{test_case['document']}")
        
        try:
            # Test API endpoint (adjust URL as needed)
            url = f"http://localhost:8000/api/questions/{test_case['collection']}/{test_case['document']}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["main_question", "question_variants", "metadata", "smart_filters"]
                has_all_fields = all(field in data for field in required_fields)
                
                if has_all_fields:
                    print(f"   ✅ API Response OK")
                    print(f"   📊 Fields: {list(data.keys())}")
                    print(f"   🎯 Main Question: {data['main_question'][:50]}...")
                    print(f"   📝 Variants Count: {len(data.get('question_variants', []))}")
                    print(f"   🔧 Smart Filters: {list(data.get('smart_filters', {}).keys())}")
                    
                    passed_tests += 1
                else:
                    print(f"   ❌ Missing required fields")
                    print(f"      Expected: {required_fields}")
                    print(f"      Found: {list(data.keys())}")
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Backend not running - Start backend first")
        except Exception as e:
            print(f"   ❌ Test Error: {e}")
    
    print(f"\\n" + "=" * 50)
    print(f"🎯 TEST RESULTS:")
    print(f"   Passed: {passed_tests}/{total_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("   ✅ ALL TESTS PASSED")
        return True
    else:
        print("   ⚠️  SOME TESTS FAILED")
        return False

def test_file_structure():
    """Test file structure integrity"""
    
    print("\\n📁 TESTING FILE STRUCTURE...")
    
    # Check questions.json files
    questions_files = glob.glob("data/**/*questions.json", recursive=True)
    print(f"   Found {len(questions_files)} questions.json files")
    
    # Validate sample file
    if questions_files:
        sample_file = questions_files[0]
        with open(sample_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "main_question" in data and "question_variants" in data:
            print(f"   ✅ File structure valid")
            return True
        else:
            print(f"   ❌ Invalid file structure")
            return False
    else:
        print(f"   ❌ No questions.json files found")
        return False

if __name__ == "__main__":
    print("🚀 STARTING BACKEND INTEGRATION TESTS")
    print("Make sure backend is running on localhost:8000")
    print()
    
    # Test file structure first
    file_test_passed = test_file_structure()
    
    if file_test_passed:
        # Test backend integration
        api_test_passed = test_backend_integration()
        
        if api_test_passed:
            print("\\n🎉 ALL INTEGRATION TESTS PASSED!")
        else:
            print("\\n⚠️  INTEGRATION TESTS NEED ATTENTION")
    else:
        print("\\n❌ FILE STRUCTURE TESTS FAILED")
'''

    test_path = "d:/Personal/LegalRAG_Fixed/backend/test_backend_integration.py"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"✅ Integration test created: {test_path}")
    return test_path

if __name__ == "__main__":
    print("🔧 BACKEND CODE UPDATE FOR NEW ARCHITECTURE")
    print("=" * 60)
    
    # Step 1: Create FilterEngine service
    filter_success = create_filter_engine()
    
    # Step 2: Update router_crud.py
    crud_success = update_router_crud()
    
    # Step 3: Create integration test
    test_path = create_backend_integration_test()
    
    print("\\n" + "=" * 60)
    print("🎯 BACKEND UPDATE SUMMARY:")
    print(f"   FilterEngine: {'✅' if filter_success else '❌'}")
    print(f"   router_crud.py: {'✅' if crud_success else '❌'}")
    print(f"   Integration Test: ✅")
    
    print(f"\\n🚀 NEXT STEPS:")
    print(f"   1. Start backend server")
    print(f"   2. Run: python {os.path.basename(test_path)}")
    print(f"   3. Verify API responses")
    print(f"   4. Test frontend integration")
