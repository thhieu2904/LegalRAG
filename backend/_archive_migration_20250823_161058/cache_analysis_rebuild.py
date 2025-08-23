#!/usr/bin/env python3
"""
🔍 CACHE ANALYSIS & REBUILD SCRIPT

Phân tích cache hiện tại và rebuild cho new questions.json structure:
✅ Identify cache files cần update
✅ Find code references to old paths 
✅ Update cache builder tools
✅ Rebuild cache với new structure
"""

import os
import glob
import json
from datetime import datetime
import shutil

def analyze_current_cache():
    """Phân tích cache hiện tại và dependencies"""
    
    print("🔍 CACHE ANALYSIS")
    print("=" * 50)
    
    cache_analysis = {
        "cache_files": [],
        "cache_references": [],
        "old_path_references": [],
        "rebuild_needed": False
    }
    
    # 1. Find cache files
    cache_patterns = [
        "data/cache/*.pkl",
        "data/cache/*.json", 
        "data/cache/*.bin",
        "**/cache/**/*",
        "**/*cache*"
    ]
    
    for pattern in cache_patterns:
        cache_files = glob.glob(pattern, recursive=True)
        for cache_file in cache_files:
            if os.path.isfile(cache_file):
                size = os.path.getsize(cache_file)
                mtime = os.path.getmtime(cache_file)
                cache_analysis["cache_files"].append({
                    "path": cache_file,
                    "size": size,
                    "modified": datetime.fromtimestamp(mtime).isoformat()
                })
    
    print(f"📁 Found {len(cache_analysis['cache_files'])} cache files:")
    for cache_file in cache_analysis['cache_files']:
        print(f"   {cache_file['path']} ({cache_file['size']:,} bytes)")
    
    # 2. Find cache references trong code
    code_files = [
        "app/services/router.py",
        "app/api/router_crud.py", 
        "tools/4_build_router_cache_modernized.py",
        "tools/*.py"
    ]
    
    cache_keywords = ["cache", "Cache", "CACHE", "router_embeddings", "cache_file"]
    
    for pattern in code_files:
        files = glob.glob(pattern, recursive=True)
        for file_path in files:
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for keyword in cache_keywords:
                        if keyword in content:
                            count = content.count(keyword)
                            cache_analysis["cache_references"].append({
                                "file": file_path,
                                "keyword": keyword,
                                "count": count
                            })
                            break
                            
                except Exception as e:
                    print(f"   ⚠️  Error reading {file_path}: {e}")
    
    # 3. Find old structure references
    old_patterns = ["router_questions", "router_examples", "router_smart"]
    
    for pattern in code_files:
        files = glob.glob(pattern, recursive=True)
        for file_path in files:
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for old_pattern in old_patterns:
                        if old_pattern in content:
                            count = content.count(old_pattern)
                            cache_analysis["old_path_references"].append({
                                "file": file_path,
                                "pattern": old_pattern,
                                "count": count
                            })
                            
                except Exception as e:
                    pass
    
    print(f"\\n🔧 Cache references in code: {len(cache_analysis['cache_references'])}")
    for ref in cache_analysis['cache_references'][:5]:  # Show first 5
        print(f"   {ref['file']}: {ref['keyword']} ({ref['count']}x)")
    
    print(f"\\n⚠️  Old path references: {len(cache_analysis['old_path_references'])}")
    for ref in cache_analysis['old_path_references'][:5]:  # Show first 5  
        print(f"   {ref['file']}: {ref['pattern']} ({ref['count']}x)")
    
    # 4. Determine if rebuild needed
    if cache_analysis['cache_files']:
        # Check if cache is older than questions.json files
        questions_files = glob.glob("data/**/*questions.json", recursive=True)
        if questions_files:
            newest_questions = max(os.path.getmtime(f) for f in questions_files)
            oldest_cache = min(datetime.fromisoformat(c['modified']).timestamp() for c in cache_analysis['cache_files'])
            
            if newest_questions > oldest_cache:
                cache_analysis["rebuild_needed"] = True
                print(f"\\n🔄 REBUILD NEEDED: Cache older than questions.json files")
            else:
                print(f"\\n✅ Cache appears fresh")
        else:
            cache_analysis["rebuild_needed"] = True
            print(f"\\n⚠️  No questions.json files found - cache invalid")
    else:
        cache_analysis["rebuild_needed"] = True
        print(f"\\n📦 No cache files found - build needed")
    
    return cache_analysis

def update_cache_builder_tool():
    """Update cache builder tool để support new structure"""
    
    print("\\n🔧 UPDATING CACHE BUILDER TOOL")
    print("=" * 50)
    
    cache_builder_path = "tools/4_build_router_cache_modernized.py"
    
    if not os.path.exists(cache_builder_path):
        print(f"❌ Cache builder not found: {cache_builder_path}")
        return False
    
    # Read current content
    with open(cache_builder_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already updated for new structure
    if "questions.json" in content and "router_questions.json" not in content:
        print("✅ Cache builder already updated for new structure")
        return True
    
    # Create backup
    backup_path = cache_builder_path + ".pre_questions_backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"💾 Backup created: {backup_path}")
    
    # Update content để use questions.json instead of router_questions.json
    updated_content = content.replace("router_questions.json", "questions.json")
    
    # Add note about new structure
    note = '''
# NOTE: Updated for new questions.json + document.json structure
# This cache builder now works with clean questions.json files
# instead of the old router_questions.json god objects
'''
    
    # Insert note after initial comments
    lines = updated_content.split('\\n')
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith('"""') and '"""' in line and i > 0:
            insert_pos = i + 1
            break
        elif line.strip().endswith('"""') and i > 5:
            insert_pos = i + 1
            break
    
    if insert_pos > 0:
        lines.insert(insert_pos, note)
        updated_content = '\\n'.join(lines)
    
    # Write updated file
    with open(cache_builder_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Cache builder tool updated for new structure")
    return True

def update_router_service_cache():
    """Update router service cache logic"""
    
    print("\\n🔧 UPDATING ROUTER SERVICE CACHE")
    print("=" * 50)
    
    router_service_path = "app/services/router.py"
    
    if not os.path.exists(router_service_path):
        print(f"❌ Router service not found: {router_service_path}")
        return False
    
    # Read current content
    with open(router_service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check current state
    has_questions_json = "questions.json" in content
    has_router_questions = "router_questions.json" in content
    
    print(f"📊 Current state:")
    print(f"   questions.json references: {'✅' if has_questions_json else '❌'}")
    print(f"   router_questions.json references: {'⚠️' if has_router_questions else '✅'}")
    
    if has_questions_json and not has_router_questions:
        print("✅ Router service already updated")
        return True
    
    # Need updates
    backup_path = router_service_path + ".pre_questions_backup"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Backup created: {backup_path}")
    
    # Update cache logic to use new structure
    # This should already be done by previous migration, just verify
    print("🔍 Verifying cache logic...")
    
    if "_load_from_cache" in content and "questions.json" in content:
        print("✅ Cache logic appears updated for new structure")
        return True
    else:
        print("⚠️  Cache logic may need manual review")
        return False

def create_cache_rebuild_script():
    """Create comprehensive cache rebuild script"""
    
    script_content = '''#!/usr/bin/env python3
"""
🔄 REBUILD CACHE FOR NEW QUESTIONS.JSON STRUCTURE

Comprehensive cache rebuild script:
✅ Clean old cache
✅ Load new questions.json structure
✅ Generate embeddings 
✅ Save new cache
✅ Validate cache integrity
"""

import sys
import os
import json
import pickle
import glob
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_old_cache():
    """Clean old cache files"""
    cache_dir = "data/cache"
    if os.path.exists(cache_dir):
        cache_files = glob.glob(f"{cache_dir}/*")
        for cache_file in cache_files:
            if os.path.isfile(cache_file):
                os.remove(cache_file)
                logger.info(f"🗑️  Removed old cache: {cache_file}")
    
    logger.info("✅ Old cache cleaned")

def load_new_structure():
    """Load questions from new structure"""
    questions_data = {}
    
    # Find all questions.json files
    questions_files = glob.glob("data/**/*questions.json", recursive=True)
    
    logger.info(f"📁 Found {len(questions_files)} questions.json files")
    
    for questions_file in questions_files:
        try:
            # Extract collection and document info from path
            path_parts = questions_file.split(os.sep)
            
            # Find collection and document
            collection_idx = -1
            document_idx = -1
            
            for i, part in enumerate(path_parts):
                if part == "collections" and i + 1 < len(path_parts):
                    collection_name = path_parts[i + 1]
                    collection_idx = i + 1
                elif part == "documents" and i + 1 < len(path_parts):
                    document_name = path_parts[i + 1]
                    document_idx = i + 1
                    
            if collection_idx > 0 and document_idx > 0:
                # Load questions
                with open(questions_file, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                # Load corresponding document metadata
                doc_dir = os.path.dirname(questions_file)
                doc_files = [f for f in os.listdir(doc_dir) 
                           if f.endswith('.json') and f != 'questions.json']
                
                metadata = {}
                if doc_files:
                    doc_path = os.path.join(doc_dir, doc_files[0])
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        metadata = doc_data.get('metadata', {})
                
                # Store in structure
                if collection_name not in questions_data:
                    questions_data[collection_name] = {}
                
                questions_data[collection_name][document_name] = {
                    'questions': questions,
                    'metadata': metadata,
                    'file_path': questions_file
                }
                
        except Exception as e:
            logger.error(f"❌ Error loading {questions_file}: {e}")
    
    logger.info(f"✅ Loaded {len(questions_data)} collections")
    return questions_data

def generate_embeddings(questions_data):
    """Generate embeddings cho questions"""
    try:
        # Import embedding model
        from sentence_transformers import SentenceTransformer
        
        logger.info("🔄 Loading embedding model...")
        model = SentenceTransformer('keepitreal/vietnamese-sbert')
        
        embeddings_data = {}
        
        for collection_name, documents in questions_data.items():
            embeddings_data[collection_name] = {}
            
            for doc_name, doc_data in documents.items():
                questions = doc_data['questions']
                
                # Prepare text for embedding
                texts = [questions.get('main_question', '')]
                texts.extend(questions.get('question_variants', []))
                
                # Generate embeddings
                embeddings = model.encode(texts)
                
                embeddings_data[collection_name][doc_name] = {
                    'embeddings': embeddings,
                    'texts': texts,
                    'metadata': doc_data['metadata']
                }
                
                logger.info(f"✅ Generated embeddings for {collection_name}/{doc_name}")
        
        logger.info(f"✅ Generated embeddings for all collections")
        return embeddings_data
        
    except Exception as e:
        logger.error(f"❌ Error generating embeddings: {e}")
        return None

def save_cache(embeddings_data):
    """Save cache to file"""
    try:
        cache_dir = "data/cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        cache_file = os.path.join(cache_dir, "router_embeddings.pkl")
        
        with open(cache_file, 'wb') as f:
            pickle.dump(embeddings_data, f)
        
        cache_size = os.path.getsize(cache_file)
        logger.info(f"✅ Cache saved: {cache_file} ({cache_size:,} bytes)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving cache: {e}")
        return False

def validate_cache():
    """Validate cache integrity"""
    try:
        cache_file = "data/cache/router_embeddings.pkl"
        
        if not os.path.exists(cache_file):
            logger.error("❌ Cache file not found")
            return False
        
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        
        # Basic validation
        if not isinstance(cache_data, dict):
            logger.error("❌ Cache data invalid format")
            return False
        
        total_docs = sum(len(docs) for docs in cache_data.values())
        logger.info(f"✅ Cache validated: {len(cache_data)} collections, {total_docs} documents")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cache validation error: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔄 STARTING CACHE REBUILD FOR NEW STRUCTURE")
    
    # Step 1: Clean old cache
    clean_old_cache()
    
    # Step 2: Load new structure
    questions_data = load_new_structure()
    
    if not questions_data:
        logger.error("❌ No questions data loaded")
        exit(1)
    
    # Step 3: Generate embeddings
    embeddings_data = generate_embeddings(questions_data)
    
    if not embeddings_data:
        logger.error("❌ Failed to generate embeddings")
        exit(1)
    
    # Step 4: Save cache
    if not save_cache(embeddings_data):
        logger.error("❌ Failed to save cache")
        exit(1)
    
    # Step 5: Validate cache
    if not validate_cache():
        logger.error("❌ Cache validation failed")
        exit(1)
    
    logger.info("🎉 CACHE REBUILD COMPLETE!")
    logger.info("✅ New questions.json structure cached successfully")
'''

    script_path = "rebuild_cache_new_structure.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ Cache rebuild script created: {script_path}")
    return script_path

def main():
    """Main analysis và update process"""
    
    print("🔄 CACHE ANALYSIS & REBUILD FOR NEW STRUCTURE")
    print("=" * 60)
    
    # Step 1: Analyze current cache
    cache_analysis = analyze_current_cache()
    
    # Step 2: Update tools
    cache_builder_updated = update_cache_builder_tool()
    router_service_updated = update_router_service_cache()
    
    # Step 3: Create rebuild script
    rebuild_script = create_cache_rebuild_script()
    
    # Step 4: Summary và recommendations
    print("\\n" + "=" * 60)
    print("🎯 ANALYSIS SUMMARY:")
    print(f"   📁 Cache files found: {len(cache_analysis['cache_files'])}")
    print(f"   🔧 Cache references: {len(cache_analysis['cache_references'])}")
    print(f"   ⚠️  Old path references: {len(cache_analysis['old_path_references'])}")
    print(f"   🔄 Rebuild needed: {'✅' if cache_analysis['rebuild_needed'] else '❌'}")
    
    print(f"\\n🔧 UPDATES:")
    print(f"   Cache builder tool: {'✅' if cache_builder_updated else '❌'}")
    print(f"   Router service: {'✅' if router_service_updated else '⚠️'}")
    print(f"   Rebuild script: ✅")
    
    if cache_analysis['rebuild_needed']:
        print(f"\\n🚀 NEXT STEPS:")
        print(f"   1. Review updated tools")
        print(f"   2. Run: python {rebuild_script}")
        print(f"   3. Test cache với backend")
        print(f"\\n⚠️  REMEMBER: Start backend before testing cache!")
    else:
        print(f"\\n✅ CACHE APPEARS CURRENT")
        print(f"   Test với backend để confirm functionality")
    
    return cache_analysis['rebuild_needed']

if __name__ == "__main__":
    rebuild_needed = main()
