"""
Test script to verify rerank service logic
Tests document-first reranking with real scenario
"""
import asyncio
import httpx

async def test_rerank_logic():
    """Test rerank service with 12 chunks from 4 documents"""
    
    # Simulate 12 chunks from 4 different legal documents
    test_query = "điều kiện kết hôn là gì"
    
    test_documents = [
        # 5 chunks from Luật Hôn Nhân (doc_A)
        "Điều 8: Điều kiện kết hôn. Nam từ đủ 20 tuổi trở lên, nữ từ đủ 18 tuổi trở lên có quyền kết hôn theo quy định của Luật này.",
        "Khoản 1: Nam từ 20 tuổi trở lên có quyền kết hôn. Điều kiện này nhằm đảm bảo sức khỏe và nhận thức đầy đủ.",
        "Điều 16: Đăng ký kết hôn. Việc đăng ký kết hôn được thực hiện tại Ủy ban nhân dân cấp xã nơi một bên hoặc cả hai bên cư trú.",
        "Khoản 2: Nữ từ 18 tuổi trở lên có quyền kết hôn. Độ tuổi này phù hợp với sự trưởng thành về thể chất và tinh thần.",
        "Điều 9: Cấm kết hôn. Nghiêm cấm kết hôn trong các trường hợp: có quan hệ huyết thống, đang có vợ hoặc chồng.",
        
        # 3 chunks from Luật Hộ Tịch (doc_B)
        "Điều 47: Đăng ký khai sinh. Việc đăng ký khai sinh phải được thực hiện trong vòng 60 ngày kể từ ngày sinh.",
        "Khoản 1: Thời hạn đăng ký khai sinh. Cha mẹ hoặc người giám hộ phải đăng ký khai sinh cho trẻ trong thời hạn quy định.",
        "Điều 48: Hồ sơ khai sinh. Giấy chứng sinh do cơ sở y tế cấp, giấy tờ tùy thân của cha mẹ, sổ hộ khẩu.",
        
        # 2 chunks from Bộ Luật Dân Sự (doc_C)
        "Điều 123: Quyền của người có năng lực hành vi dân sự đầy đủ. Cá nhân từ đủ 18 tuổi trở lên có năng lực hành vi dân sự đầy đủ.",
        "Khoản 3: Nghĩa vụ của cá nhân. Mọi cá nhân phải thực hiện đầy đủ nghĩa vụ theo quy định của pháp luật.",
        
        # 2 chunks from Nghị định 158 (doc_D)
        "Điều 5: Thủ tục hành chính về hộ tịch. Quy định trình tự, thủ tục đăng ký các sự kiện hộ tịch.",
        "Khoản 1: Đối tượng áp dụng. Nghị định này áp dụng cho công dân Việt Nam và người nước ngoài cư trú tại Việt Nam."
    ]
    
    # Document IDs mapping (which document each chunk belongs to)
    document_ids = [
        "doc_A", "doc_A", "doc_A", "doc_A", "doc_A",  # 5 chunks from Luật Hôn Nhân
        "doc_B", "doc_B", "doc_B",                     # 3 chunks from Luật Hộ Tịch
        "doc_C", "doc_C",                              # 2 chunks from Bộ Luật Dân Sự
        "doc_D", "doc_D"                               # 2 chunks from Nghị định 158
    ]
    
    print("=" * 80)
    print("🧪 TESTING RERANK SERVICE - DOCUMENT-FIRST LOGIC")
    print("=" * 80)
    print(f"\n📝 Query: '{test_query}'")
    print(f"📦 Input: {len(test_documents)} chunks from {len(set(document_ids))} documents")
    print(f"   - doc_A (Luật Hôn Nhân): 5 chunks")
    print(f"   - doc_B (Luật Hộ Tịch): 3 chunks")
    print(f"   - doc_C (Bộ Luật Dân Sự): 2 chunks")
    print(f"   - doc_D (Nghị định 158): 2 chunks")
    print("\n" + "-" * 80)
    
    # Test cases
    test_cases = [
        {
            "name": "WITH document filtering (same_document_only=True)",
            "same_document_only": True,
            "expected": "Should return ALL chunks from best document (doc_A)"
        },
        {
            "name": "WITHOUT document filtering (same_document_only=False)",
            "same_document_only": False,
            "expected": "Should return top 5 chunks regardless of document"
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔬 TEST CASE {i}: {test_case['name']}")
            print(f"   Expected: {test_case['expected']}")
            print()
            
            try:
                # Call rerank service
                response = await client.post(
                    "http://localhost:8013/rerank",
                    json={
                        "query": test_query,
                        "documents": test_documents,
                        "document_ids": document_ids,
                        "top_k": 5,
                        "same_document_only": test_case["same_document_only"]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    processing_time = data.get("processing_time", 0)
                    
                    print(f"   ✅ Status: SUCCESS")
                    print(f"   ⏱️  Processing time: {processing_time:.3f}s")
                    print(f"   📊 Returned: {len(results)} chunks")
                    print()
                    
                    # Analyze results
                    result_doc_ids = [document_ids[r["index"]] for r in results]
                    unique_docs = set(result_doc_ids)
                    
                    print(f"   📋 Result Analysis:")
                    print(f"      - Unique documents: {len(unique_docs)} → {unique_docs}")
                    print(f"      - Document distribution:")
                    for doc_id in sorted(unique_docs):
                        count = result_doc_ids.count(doc_id)
                        print(f"        • {doc_id}: {count} chunks")
                    print()
                    
                    # Show top 3 results
                    print(f"   🏆 Top 3 Results:")
                    for idx, result in enumerate(results[:3], 1):
                        doc_id = document_ids[result["index"]]
                        text_preview = result["text"][:80] + "..." if len(result["text"]) > 80 else result["text"]
                        print(f"      {idx}. [{doc_id}] Score: {result['score']:.4f}")
                        print(f"         {text_preview}")
                    
                    # Validation
                    print()
                    if test_case["same_document_only"]:
                        if len(unique_docs) == 1:
                            print(f"   ✅ VALIDATION PASSED: Single document returned ({unique_docs.pop()})")
                            if len(results) == 5:  # Should have all 5 chunks from doc_A
                                print(f"   ✅ VALIDATION PASSED: All chunks from best document returned")
                            else:
                                print(f"   ⚠️  NOTE: Expected 5 chunks from doc_A, got {len(results)}")
                        else:
                            print(f"   ❌ VALIDATION FAILED: Multiple documents returned: {unique_docs}")
                    else:
                        if len(unique_docs) > 1:
                            print(f"   ✅ VALIDATION PASSED: Mixed documents allowed ({unique_docs})")
                        else:
                            print(f"   ℹ️  INFO: Only one document scored highest")
                    
                else:
                    print(f"   ❌ Status: FAILED (HTTP {response.status_code})")
                    print(f"   Error: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            
            print("\n" + "-" * 80)
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🚀 Starting rerank service test...\n")
    asyncio.run(test_rerank_logic())
