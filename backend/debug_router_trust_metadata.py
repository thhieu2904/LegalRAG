"""
Debug script để check metadata mapping trong router trust mode
"""

def analyze_router_trust_issue():
    print("🔍 ANALYZING ROUTER TRUST METADATA ISSUE")
    print("="*60)
    
    print("📋 PROBLEM ANALYSIS:")
    print("1. Router chọn đúng: DOC_011 (confidence 0.9183)")
    print("2. Router trust mode kích hoạt: ✅")
    print("3. Reranker trả về documents[0] từ vector search")
    print("4. NHƯNG documents[0] có metadata trỏ tới DOC_031 ❌")
    print("5. Context expansion load sai file: DOC_031 thay vì DOC_011")
    print()
    
    print("🎯 ROOT CAUSE:")
    print("- Vector search trả về chunks từ multiple documents")
    print("- documents[0] không nhất thiết từ document mà router chọn")
    print("- Router trust mode cần tìm chunk từ ĐÚNG document")
    print()
    
    print("💡 SOLUTION:")
    print("Fix reranker.py để khi router trust mode:")
    print("1. Không trả về documents[0] mà tìm chunk từ router-selected document")
    print("2. Filter documents để chỉ lấy chunks từ DOC_011")
    print("3. Trả về chunk từ đúng document với metadata chính xác")
    print()
    
    print("🔧 CODE FIX NEEDED:")
    print("In reranker.py, replace:")
    print("   return documents[0] if documents else None")
    print("With:")
    print("   return find_chunk_from_router_document(documents, router_decision)")
    
if __name__ == "__main__":
    analyze_router_trust_issue()
