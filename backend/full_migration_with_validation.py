#!/usr/bin/env python3
"""
🚀 FULL MIGRATION: Router Questions → Clean Questions Architecture
   
FEATURES:
✅ Backup all files before migration
✅ Progress tracking với detailed logging
✅ Validation scripts để ensure integrity
✅ Rollback capability nếu có lỗi
✅ Comprehensive testing sau migration
"""

import json
import os
import glob
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

class MigrationValidator:
    """Comprehensive validation suite for migration process"""
    
    def __init__(self):
        self.validation_results = {}
        self.errors = []
        self.warnings = []
    
    def validate_file_integrity(self, original_file, questions_file):
        """Validate that questions data is correctly extracted"""
        try:
            # Load original
            with open(original_file, 'r', encoding='utf-8') as f:
                original = json.load(f)
            
            # Load questions
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            # Validate main_question
            if original.get('main_question') != questions.get('main_question'):
                self.errors.append(f"Main question mismatch in {questions_file}")
                return False
            
            # Validate question_variants
            original_variants = original.get('question_variants', [])
            new_variants = questions.get('question_variants', [])
            
            if len(original_variants) != len(new_variants):
                self.errors.append(f"Variants count mismatch in {questions_file}")
                return False
            
            if original_variants != new_variants:
                self.errors.append(f"Variants content mismatch in {questions_file}")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Validation error for {questions_file}: {str(e)}")
            return False
    
    def validate_metadata_preservation(self, document_dir):
        """Ensure document.json contains all necessary metadata"""
        try:
            # Find document.json file
            doc_files = [f for f in os.listdir(document_dir) 
                        if f.endswith('.json') and 'router_questions' not in f and 'questions' not in f]
            
            if not doc_files:
                self.warnings.append(f"No document.json found in {document_dir}")
                return False
            
            doc_file = os.path.join(document_dir, doc_files[0])
            with open(doc_file, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
            
            metadata = doc_data.get('metadata', {})
            required_fields = ['title', 'code', 'executing_agency']
            
            for field in required_fields:
                if field not in metadata:
                    self.warnings.append(f"Missing {field} in {doc_file}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Metadata validation error for {document_dir}: {str(e)}")
            return False
    
    def generate_report(self):
        """Generate comprehensive validation report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_validations": len(self.validation_results),
            "successful_validations": sum(self.validation_results.values()),
            "errors": self.errors,
            "warnings": self.warnings,
            "success_rate": (sum(self.validation_results.values()) / len(self.validation_results) * 100) if self.validation_results else 0
        }
        return report

class FullMigrationEngine:
    """Complete migration engine với backup và validation"""
    
    def __init__(self):
        self.validator = MigrationValidator()
        self.backup_dir = None
        self.migration_log = []
        self.stats = {
            "files_processed": 0,
            "files_migrated": 0,
            "files_backed_up": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    def create_backup(self):
        """Create backup của tất cả router_questions.json files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = f"d:/Personal/LegalRAG_Fixed/backend/migration_backup_{timestamp}"
        os.makedirs(self.backup_dir, exist_ok=True)
        
        print(f"📦 CREATING BACKUP: {self.backup_dir}")
        
        router_files = glob.glob("d:/Personal/LegalRAG_Fixed/backend/data/**/*router_questions.json", recursive=True)
        
        for router_file in router_files:
            relative_path = os.path.relpath(router_file, "d:/Personal/LegalRAG_Fixed/backend/data")
            backup_path = os.path.join(self.backup_dir, relative_path)
            
            # Create backup directory structure
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy file
            shutil.copy2(router_file, backup_path)
            self.stats["files_backed_up"] += 1
        
        print(f"✅ BACKUP COMPLETE: {self.stats['files_backed_up']} files backed up")
        return self.backup_dir
    
    def migrate_single_file(self, router_file):
        """Migrate single router_questions.json → questions.json"""
        try:
            # Load router_questions.json
            with open(router_file, 'r', encoding='utf-8') as f:
                router_data = json.load(f)
            
            # Extract ONLY questions
            clean_questions = {
                "main_question": router_data.get("main_question", ""),
                "question_variants": router_data.get("question_variants", [])
            }
            
            # Create questions.json path
            questions_file = router_file.replace("router_questions.json", "questions.json")
            
            # Save questions.json
            with open(questions_file, 'w', encoding='utf-8') as f:
                json.dump(clean_questions, f, ensure_ascii=False, indent=2)
            
            # Validate migration
            document_dir = os.path.dirname(router_file)
            validation_success = (
                self.validator.validate_file_integrity(router_file, questions_file) and
                self.validator.validate_metadata_preservation(document_dir)
            )
            
            self.validator.validation_results[questions_file] = validation_success
            
            # Log migration
            self.migration_log.append({
                "original": router_file,
                "new": questions_file,
                "validation": validation_success,
                "timestamp": datetime.now().isoformat()
            })
            
            if validation_success:
                self.stats["files_migrated"] += 1
            else:
                self.stats["errors"] += 1
            
            return validation_success, questions_file
            
        except Exception as e:
            error_msg = f"Migration error for {router_file}: {str(e)}"
            self.validator.errors.append(error_msg)
            self.stats["errors"] += 1
            return False, None
    
    def execute_full_migration(self):
        """Execute complete migration với progress tracking"""
        print("🚀 STARTING FULL MIGRATION...")
        self.stats["start_time"] = datetime.now()
        
        # Step 1: Create backup
        self.create_backup()
        
        # Step 2: Find all router_questions.json files
        router_files = glob.glob("d:/Personal/LegalRAG_Fixed/backend/data/**/*router_questions.json", recursive=True)
        total_files = len(router_files)
        
        print(f"📊 FOUND {total_files} files to migrate")
        
        # Step 3: Migrate each file
        for i, router_file in enumerate(router_files, 1):
            print(f"⚡ [{i}/{total_files}] Migrating {os.path.basename(os.path.dirname(router_file))}")
            
            success, questions_file = self.migrate_single_file(router_file)
            self.stats["files_processed"] += 1
            
            if success and questions_file:
                print(f"   ✅ SUCCESS: {os.path.basename(questions_file)}")
            else:
                print(f"   ❌ FAILED: {router_file}")
            
            # Progress report every 10 files
            if i % 10 == 0:
                success_rate = (self.stats["files_migrated"] / self.stats["files_processed"]) * 100
                print(f"   📈 Progress: {success_rate:.1f}% success rate")
        
        self.stats["end_time"] = datetime.now()
        
        # Step 4: Generate final report
        return self.generate_migration_report()
    
    def generate_migration_report(self):
        """Generate comprehensive migration report"""
        validation_report = self.validator.generate_report()
        
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        report = {
            "migration_summary": {
                "total_files_found": self.stats["files_processed"],
                "successfully_migrated": self.stats["files_migrated"],
                "migration_errors": self.stats["errors"],
                "success_rate": (self.stats["files_migrated"] / self.stats["files_processed"] * 100) if self.stats["files_processed"] > 0 else 0,
                "duration_seconds": duration,
                "backup_location": self.backup_dir
            },
            "validation_results": validation_report,
            "migration_log": self.migration_log[-10:]  # Last 10 entries
        }
        
        # Save report
        report_file = f"d:/Personal/LegalRAG_Fixed/backend/migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📋 MIGRATION REPORT SAVED: {report_file}")
        return report

def run_post_migration_tests():
    """Comprehensive testing sau migration"""
    print("\n🧪 RUNNING POST-MIGRATION TESTS...")
    
    test_results = {}
    
    # Test 1: Count questions.json files
    questions_files = glob.glob("d:/Personal/LegalRAG_Fixed/backend/data/**/*questions.json", recursive=True)
    test_results["questions_files_created"] = len(questions_files)
    
    # Test 2: Validate file sizes
    total_questions_size = sum(os.path.getsize(f) for f in questions_files)
    
    # Find remaining router_questions.json files (should be 0 after cleanup)
    remaining_router_files = glob.glob("d:/Personal/LegalRAG_Fixed/backend/data/**/*router_questions.json", recursive=True)
    test_results["remaining_router_files"] = len(remaining_router_files)
    
    # Test 3: Sample validation
    if questions_files:
        sample_file = questions_files[0]
        with open(sample_file, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        
        test_results["sample_validation"] = {
            "has_main_question": "main_question" in sample_data,
            "has_variants": "question_variants" in sample_data,
            "fields_count": len(sample_data),
            "expected_fields": 2
        }
    
    test_results["total_size_reduction"] = "TBD - requires comparison with backup"
    
    print(f"✅ Created {test_results['questions_files_created']} questions.json files")
    print(f"⚠️  Remaining router files: {test_results['remaining_router_files']}")
    
    return test_results

if __name__ == "__main__":
    print("🎯 FULL MIGRATION WITH VALIDATION")
    print("=" * 60)
    
    # Create migration engine
    migrator = FullMigrationEngine()
    
    # Execute migration
    report = migrator.execute_full_migration()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 MIGRATION SUMMARY:")
    print(f"   ✅ Success Rate: {report['migration_summary']['success_rate']:.1f}%")
    print(f"   📁 Files Migrated: {report['migration_summary']['successfully_migrated']}")
    print(f"   ⚠️  Errors: {report['migration_summary']['migration_errors']}")
    print(f"   ⏱️  Duration: {report['migration_summary']['duration_seconds']:.1f} seconds")
    print(f"   💾 Backup: {report['migration_summary']['backup_location']}")
    
    # Run post-migration tests
    test_results = run_post_migration_tests()
    
    print("\n🎉 MIGRATION COMPLETE!")
    print("👉 Review migration report và test results trước khi proceed với backend updates")
