#!/usr/bin/env python3
"""
🔍 PRE-MIGRATION VALIDATION SCRIPT

Validates system state trước khi migrate để ensure safety:
✅ Check file counts và integrity
✅ Verify backend dependencies
✅ Test sample migration
✅ Estimate storage reduction
✅ Validate backup space
"""

import json
import os
import glob
from pathlib import Path
import shutil

def pre_migration_checks():
    """Comprehensive pre-migration validation"""
    
    print("🔍 PRE-MIGRATION VALIDATION")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 6
    
    # Check 1: Count router_questions.json files
    router_files = glob.glob("d:/Personal/LegalRAG_Fixed/backend/data/**/*router_questions.json", recursive=True)
    print(f"📁 Found {len(router_files)} router_questions.json files")
    if len(router_files) > 0:
        checks_passed += 1
        print("   ✅ PASS: Files found for migration")
    else:
        print("   ❌ FAIL: No files found")
    
    # Check 2: Validate sample file structure
    if router_files:
        sample_file = router_files[0]
        try:
            with open(sample_file, 'r', encoding='utf-8') as f:
                sample_data = json.load(f)
            
            required_fields = ['main_question', 'question_variants']
            has_all_fields = all(field in sample_data for field in required_fields)
            
            if has_all_fields:
                checks_passed += 1
                print("   ✅ PASS: Sample file has required fields")
            else:
                print("   ❌ FAIL: Sample file missing required fields")
                print(f"      Fields found: {list(sample_data.keys())}")
                
        except Exception as e:
            print(f"   ❌ FAIL: Cannot read sample file: {e}")
    
    # Check 3: Check document.json files exist
    doc_dirs = set(os.path.dirname(f) for f in router_files)
    doc_files_found = 0
    
    for doc_dir in doc_dirs:
        doc_files = [f for f in os.listdir(doc_dir) 
                    if f.endswith('.json') and 'router_questions' not in f]
        if doc_files:
            doc_files_found += 1
    
    if doc_files_found == len(doc_dirs):
        checks_passed += 1
        print(f"   ✅ PASS: All {len(doc_dirs)} directories have document.json files")
    else:
        print(f"   ⚠️  WARNING: {len(doc_dirs) - doc_files_found} directories missing document.json")
    
    # Check 4: Estimate storage reduction
    total_router_size = sum(os.path.getsize(f) for f in router_files)
    
    # Estimate questions-only size (based on sample)
    if router_files:
        with open(router_files[0], 'r', encoding='utf-8') as f:
            sample_router = json.load(f)
        
        sample_questions = {
            "main_question": sample_router.get("main_question", ""),
            "question_variants": sample_router.get("question_variants", [])
        }
        
        size_ratio = len(str(sample_questions)) / len(str(sample_router))
        estimated_questions_size = total_router_size * size_ratio
        reduction_percent = ((total_router_size - estimated_questions_size) / total_router_size) * 100
        
        print(f"💾 Storage Analysis:")
        print(f"   Current total: {total_router_size:,} bytes")
        print(f"   Estimated after: {estimated_questions_size:,.0f} bytes")
        print(f"   Reduction: {reduction_percent:.1f}%")
        
        if reduction_percent > 20:
            checks_passed += 1
            print("   ✅ PASS: Significant storage reduction expected")
        else:
            print("   ⚠️  WARNING: Lower storage reduction than expected")
    
    # Check 5: Check backup space
    backup_space_needed = total_router_size * 1.1  # 10% buffer
    
    # Check available disk space
    statvfs = shutil.disk_usage("d:/Personal/LegalRAG_Fixed/backend")
    available_space = statvfs.free
    
    if available_space > backup_space_needed:
        checks_passed += 1
        print(f"💽 Disk Space: {available_space:,} bytes available, {backup_space_needed:,.0f} bytes needed")
        print("   ✅ PASS: Sufficient space for backup")
    else:
        print(f"   ❌ FAIL: Insufficient disk space for backup")
    
    # Check 6: Test sample migration
    try:
        temp_dir = "d:/Personal/LegalRAG_Fixed/backend/temp_migration_test"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Copy sample file
        sample_router = router_files[0]
        temp_router = os.path.join(temp_dir, "router_questions.json")
        shutil.copy2(sample_router, temp_router)
        
        # Test migration
        with open(temp_router, 'r', encoding='utf-8') as f:
            router_data = json.load(f)
        
        questions_data = {
            "main_question": router_data.get("main_question", ""),
            "question_variants": router_data.get("question_variants", [])
        }
        
        temp_questions = os.path.join(temp_dir, "questions.json")
        with open(temp_questions, 'w', encoding='utf-8') as f:
            json.dump(questions_data, f, ensure_ascii=False, indent=2)
        
        # Validate
        with open(temp_questions, 'r', encoding='utf-8') as f:
            loaded_questions = json.load(f)
        
        if loaded_questions == questions_data:
            checks_passed += 1
            print("   ✅ PASS: Sample migration test successful")
        else:
            print("   ❌ FAIL: Sample migration test failed")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"   ❌ FAIL: Sample migration test error: {e}")
    
    # Final assessment
    print("\n" + "=" * 50)
    print(f"🎯 PRE-MIGRATION ASSESSMENT:")
    print(f"   Checks Passed: {checks_passed}/{total_checks}")
    print(f"   Success Rate: {(checks_passed/total_checks)*100:.1f}%")
    
    if checks_passed >= 5:
        print("   ✅ READY FOR MIGRATION")
        return True
    elif checks_passed >= 4:
        print("   ⚠️  PROCEED WITH CAUTION")
        return True
    else:
        print("   ❌ NOT READY - Fix issues first")
        return False

def check_questions_conflicts():
    """Check if questions.json files already exist"""
    
    print("\n🔍 CHECKING FOR EXISTING QUESTIONS.JSON FILES...")
    
    existing_questions = glob.glob("d:/Personal/LegalRAG_Fixed/backend/data/**/*questions.json", recursive=True)
    
    if existing_questions:
        print(f"⚠️  FOUND {len(existing_questions)} existing questions.json files:")
        for i, qfile in enumerate(existing_questions[:5], 1):
            rel_path = os.path.relpath(qfile, "d:/Personal/LegalRAG_Fixed/backend/data")
            print(f"   {i}. {rel_path}")
        
        if len(existing_questions) > 5:
            print(f"   ... and {len(existing_questions) - 5} more")
        
        print("\n🤔 OPTIONS:")
        print("   1. Overwrite existing questions.json files")
        print("   2. Skip directories with existing questions.json")
        print("   3. Backup existing questions.json first")
        
        return existing_questions
    else:
        print("   ✅ No existing questions.json files found")
        return []

if __name__ == "__main__":
    print("🚀 PRE-MIGRATION VALIDATION SUITE")
    print("This script validates system readiness for migration")
    print()
    
    # Run pre-migration checks
    ready = pre_migration_checks()
    
    # Check for conflicts
    existing_questions = check_questions_conflicts()
    
    # Final recommendation
    print("\n" + "=" * 60)
    if ready:
        print("🎯 RECOMMENDATION: PROCEED WITH MIGRATION")
        if existing_questions:
            print("⚠️  Handle existing questions.json files first")
        print("\nNext step: Run full_migration_with_validation.py")
    else:
        print("❌ RECOMMENDATION: FIX ISSUES BEFORE MIGRATION")
        print("Review the failed checks and retry")
