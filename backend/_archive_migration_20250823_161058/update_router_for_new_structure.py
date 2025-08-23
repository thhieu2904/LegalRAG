#!/usr/bin/env python3
"""
🔧 UPDATE ROUTER SERVICE FOR NEW QUESTIONS.JSON STRUCTURE

Updates router.py để load từ questions.json + document.json
instead of old router_examples_smart_v3 structure
"""

import os
import re

def update_router_service_for_new_structure():
    """Update router.py để load từ new questions.json structure"""
    
    router_path = "app/services/router.py"
    
    if not os.path.exists(router_path):
        print(f"❌ Router service not found: {router_path}")
        return False
    
    print("🔧 UPDATING ROUTER SERVICE FOR NEW STRUCTURE")
    print("=" * 50)
    
    # Read current content
    with open(router_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create backup
    backup_path = router_path + ".pre_new_structure_backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"💾 Backup created: {backup_path}")
    
    # Update base_path để point to new structure
    updated_content = content.replace(
        'self.base_path = "data/router_examples"',
        'self.base_path = "data/storage/collections"  # New questions.json structure'
    )
    
    # Update _load_config method để load từ questions.json files
    old_load_config = '''def _load_config(self) -> Dict[str, Any]:
        """Load configuration from router_examples_smart_v3 directory"""
        try:
            # New approach: Load from individual router files - Updated to V3
            router_smart_path = os.path.join(self.base_path.replace("router_examples", "router_examples_smart_v3"))
            
            if not os.path.exists(router_smart_path):
                logger.warning(f"Router examples directory not found: {router_smart_path}")
                return {}
            
            # Check for V3 summary file
            summary_file = os.path.join(router_smart_path, "llm_generation_summary_v3.json")
            if os.path.exists(summary_file):
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                logger.info(f"📋 Loaded router summary V3: {summary.get('statistics', {}).get('total_files_processed', 0)} files, {summary.get('statistics', {}).get('total_examples_generated', 0)} examples")
                
                # Build config from summary
                config = {
                    'metadata': {
                        'version': '2.0',
                        'generator': 'smart_router_individual',
                        'structure': 'individual_files'
                    },
                    'collection_mappings': {}
                }
                
                # Map collections from summary
                for collection_name, count in summary.get('collections', {}).items():
                    config['collection_mappings'][collection_name] = {
                        'description': collection_name.replace('_', ' ').title(),
                        'file_count': count,
                        'example_files': []  # Will be loaded dynamically
                    }
                
                return config
            
            # Fallback: scan directory structure
            else:
                logger.info("📁 Scanning router_examples_smart_v3 directory structure...")
                return self._scan_individual_files(router_smart_path)
            
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return {}'''
    
    new_load_config = '''def _load_config(self) -> Dict[str, Any]:
        """Load configuration from new questions.json structure"""
        try:
            # Load from new structure: data/storage/collections/*/documents/*/questions.json
            collections_path = self.base_path  # "data/storage/collections"
            
            if not os.path.exists(collections_path):
                logger.warning(f"Collections directory not found: {collections_path}")
                return {}
            
            config = {
                'metadata': {
                    'version': '3.0',
                    'generator': 'questions_json_structure',
                    'structure': 'questions_plus_document'
                },
                'collection_mappings': {}
            }
            
            # Scan collections
            for collection_name in os.listdir(collections_path):
                collection_path = os.path.join(collections_path, collection_name)
                if not os.path.isdir(collection_path):
                    continue
                
                documents_path = os.path.join(collection_path, "documents")
                if not os.path.exists(documents_path):
                    continue
                
                # Count documents với questions.json
                doc_count = 0
                for doc_name in os.listdir(documents_path):
                    doc_path = os.path.join(documents_path, doc_name)
                    if os.path.isdir(doc_path):
                        questions_file = os.path.join(doc_path, "questions.json")
                        if os.path.exists(questions_file):
                            doc_count += 1
                
                if doc_count > 0:
                    config['collection_mappings'][collection_name] = {
                        'description': collection_name.replace('_', ' ').title(),
                        'file_count': doc_count,
                        'path': collection_path,
                        'documents_path': documents_path
                    }
            
            logger.info(f"📋 Loaded new structure: {len(config['collection_mappings'])} collections")
            return config
            
        except Exception as e:
            logger.error(f"❌ Error loading new structure config: {e}")
            return {}'''
    
    # Replace _load_config method
    updated_content = updated_content.replace(old_load_config, new_load_config)
    
    # Update _load_example_questions method để load từ questions.json
    old_load_examples_start = "def _load_example_questions(self):"
    old_load_examples_end = "logger.info(f\"✅ Loaded {total_examples} examples from {len(self.collection_mappings)} collections\")"
    
    # Find the method
    start_idx = updated_content.find(old_load_examples_start)
    if start_idx != -1:
        # Find end of method (next def or class)
        lines = updated_content[start_idx:].split('\\n')
        method_lines = []
        indent_level = None
        
        for i, line in enumerate(lines):
            if i == 0:  # First line
                method_lines.append(line)
                if line.strip().startswith('def '):
                    indent_level = len(line) - len(line.lstrip())
                continue
            
            current_indent = len(line) - len(line.lstrip()) if line.strip() else float('inf')
            
            # If we hit another method/class at same or higher level, stop
            if (line.strip().startswith('def ') or line.strip().startswith('class ')) and current_indent <= indent_level:
                break
            
            method_lines.append(line)
            
            # Check for the end marker
            if old_load_examples_end in line:
                break
        
        old_method = '\\n'.join(method_lines)
        
        new_load_examples = '''def _load_example_questions(self):
        """Load example questions from new questions.json structure"""
        try:
            total_examples = 0
            
            for collection_name, collection_info in self.collection_mappings.items():
                documents_path = collection_info.get('documents_path')
                if not documents_path or not os.path.exists(documents_path):
                    continue
                
                collection_examples = []
                
                # Load questions from each document
                for doc_name in os.listdir(documents_path):
                    doc_path = os.path.join(documents_path, doc_name)
                    if not os.path.isdir(doc_path):
                        continue
                    
                    questions_file = os.path.join(doc_path, "questions.json")
                    if not os.path.exists(questions_file):
                        continue
                    
                    try:
                        # Load questions
                        with open(questions_file, 'r', encoding='utf-8') as f:
                            questions_data = json.load(f)
                        
                        # Load corresponding document metadata
                        doc_files = [f for f in os.listdir(doc_path) 
                                   if f.endswith('.json') and f != 'questions.json']
                        
                        metadata = {}
                        if doc_files:
                            doc_metadata_file = os.path.join(doc_path, doc_files[0])
                            with open(doc_metadata_file, 'r', encoding='utf-8') as f:
                                doc_data = json.load(f)
                                metadata = doc_data.get('metadata', {})
                        
                        # Extract questions
                        main_question = questions_data.get('main_question', '')
                        question_variants = questions_data.get('question_variants', [])
                        
                        # Add to collection examples
                        if main_question:
                            collection_examples.append({
                                'question': main_question,
                                'type': 'main',
                                'document_id': doc_name,
                                'metadata': metadata,
                                'source': 'questions.json'
                            })
                            total_examples += 1
                        
                        for variant in question_variants:
                            if variant and variant.strip():
                                collection_examples.append({
                                    'question': variant,
                                    'type': 'variant', 
                                    'document_id': doc_name,
                                    'metadata': metadata,
                                    'source': 'questions.json'
                                })
                                total_examples += 1
                                
                    except Exception as e:
                        logger.warning(f"Error loading questions from {questions_file}: {e}")
                        continue
                
                # Store examples for collection
                if collection_examples:
                    self.example_questions[collection_name] = collection_examples
                    logger.info(f"📂 {collection_name}: {len(collection_examples)} questions loaded")
            
            logger.info(f"✅ Loaded {total_examples} examples from {len(self.collection_mappings)} collections")
            
        except Exception as e:
            logger.error(f"❌ Error loading example questions: {e}")'''
        
        # Replace the method
        updated_content = updated_content.replace(old_method, new_load_examples)
        print("✅ Updated _load_example_questions method")
    
    # Remove old _scan_individual_files method (not needed anymore)
    scan_method_start = "def _scan_individual_files(self, router_smart_path: str) -> Dict[str, Any]:"
    scan_method_idx = updated_content.find(scan_method_start)
    
    if scan_method_idx != -1:
        # Find end of method
        lines = updated_content[scan_method_idx:].split('\\n')
        method_lines = []
        indent_level = None
        
        for i, line in enumerate(lines):
            if i == 0:
                method_lines.append(line)
                if line.strip().startswith('def '):
                    indent_level = len(line) - len(line.lstrip())
                continue
            
            current_indent = len(line) - len(line.lstrip()) if line.strip() else float('inf')
            
            if (line.strip().startswith('def ') or line.strip().startswith('class ')) and current_indent <= indent_level:
                break
            
            method_lines.append(line)
        
        old_scan_method = '\\n'.join(method_lines)
        
        # Replace with comment
        new_comment = '''# _scan_individual_files method removed - no longer needed with questions.json structure'''
        
        updated_content = updated_content.replace(old_scan_method, new_comment)
        print("✅ Removed obsolete _scan_individual_files method")
    
    # Update cache freshness check
    cache_check_old = '''# Get all questions.json files in new structure
                    router_files = path_config.get_all_router_files()'''
    
    cache_check_new = '''# Get all questions.json files in new structure  
                    router_files = path_config.get_all_router_files() if path_config else []'''
    
    updated_content = updated_content.replace(cache_check_old, cache_check_new)
    
    # Write updated file
    with open(router_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Router service updated for new questions.json structure")
    
    # Validate changes
    with open(router_path, 'r', encoding='utf-8') as f:
        new_content = f.read()
    
    new_structure_refs = new_content.count("questions.json")
    old_structure_refs = new_content.count("router_examples_smart_v3")
    
    print(f"📊 Validation:")
    print(f"   questions.json references: {new_structure_refs}")
    print(f"   old structure references: {old_structure_refs}")
    
    return True

if __name__ == "__main__":
    print("🔧 UPDATING ROUTER SERVICE FOR NEW STRUCTURE")
    print("=" * 60)
    
    success = update_router_service_for_new_structure()
    
    if success:
        print("\\n🎉 ROUTER SERVICE UPDATE COMPLETE!")
        print("✅ Now uses questions.json + document.json structure")
        print("✅ Old router_examples_smart_v3 dependencies removed")
        print("\\nNext: Rebuild cache với new structure")
    else:
        print("\\n❌ UPDATE FAILED")
        print("Check errors above")
