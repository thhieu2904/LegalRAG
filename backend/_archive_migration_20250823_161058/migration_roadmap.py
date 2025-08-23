"""
🎯 MIGRATION ROADMAP - STEP BY STEP
"""

# PHASE 1: FOUNDATION (1-2 days)
def phase_1_create_new_services():
    """Tạo services mới mà không break existing code"""
    
    # 1.1 Create FilterEngine
    create_file("services/filter_engine.py")
    create_file("services/collection_mapper.py") 
    create_file("config/router_config.py")
    
    # 1.2 Add unit tests  
    create_file("tests/test_filter_engine.py")
    create_file("tests/test_collection_mapper.py")
    
    # 1.3 Create migration script
    create_file("migrations/extract_questions_only.py")

# PHASE 2: DATA MIGRATION (2-3 days)  
def phase_2_migrate_data():
    """Migrate từ router_questions.json → questions.json thuần túy"""
    
    # 2.1 Extract questions only
    for router_file in glob("**/router_questions.json"):
        data = load_json(router_file)
        
        # Extract ONLY questions
        questions_only = {
            "main_question": data["main_question"],
            "question_variants": data["question_variants"]
        }
        
        # Save to new location
        questions_file = router_file.replace("router_questions.json", "questions.json")
        save_json(questions_file, questions_only)
        
        # Keep old file for rollback
        backup_file(router_file)

# PHASE 3: CODE MIGRATION (3-4 days)
def phase_3_migrate_code():
    """Update code để sử dụng new architecture"""
    
    # 3.1 Update DocumentService
    class DocumentService:
        def get_document_with_questions(self, doc_id: str):
            # Load từ single sources
            metadata = self._load_document_metadata(doc_id)
            questions = self._load_questions_only(doc_id)  # ← NEW simple file
            
            # Derive at runtime  
            smart_filters = FilterEngine.derive_smart_filters(metadata)
            collection = CollectionMapper.infer_collection(doc_path)
            
            return DocumentWithQuestions(...)
    
    # 3.2 Update Router.py
    class QueryRouter:
        def _load_document_data(self, doc_path):
            # OLD: load từ router_questions.json 
            # NEW: derive từ document.json + questions.json
            pass
    
    # 3.3 Update API endpoints
    update_file("api/router_crud.py")

# PHASE 4: TESTING & VALIDATION (2-3 days)
def phase_4_testing():
    """Comprehensive testing"""
    
    # 4.1 Unit tests
    test_filter_engine()
    test_collection_mapper() 
    test_document_service()
    
    # 4.2 Integration tests
    test_api_endpoints()
    test_router_functionality()
    
    # 4.3 Performance tests
    benchmark_before_after()
    test_memory_usage()
    test_query_speed()

# PHASE 5: CLEANUP (1 day)  
def phase_5_cleanup():
    """Remove old files and code"""
    
    # 5.1 Remove old router_questions.json files
    for old_file in glob("**/router_questions.json"):
        os.remove(old_file)
    
    # 5.2 Remove old code paths
    remove_deprecated_methods()
    
    # 5.3 Update documentation
    update_readme()
    update_api_docs()

# TOTAL TIME: 8-12 days for complete migration
# RISK: Low (backward compatible approach)
# IMPACT: High (31% storage reduction, better maintainability)
