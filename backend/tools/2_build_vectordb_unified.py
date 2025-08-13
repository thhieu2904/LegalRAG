#!/usr/bin/env python3
"""
Unified Vector Database Builder for LegalRAG
==========================================

Tool gộp chung việc xử lý JSON documents và build vector database.
Thay thế cho document_processor.py + 2_build_vectordb_final.py để đơn giản hóa.

Usage:
    cd backend
    python tools/2_build_vectordb_unified.py
    python tools/2_build_vectordb_unified.py --force  # Clear existing and rebuild
    python tools/2_build_vectordb_unified.py --clean  # Remove entire vectordb directory
"""

import sys
import os
import json
from pathlib import Path
import logging
import argparse
from typing import Dict, List, Any, Optional
import time

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import from app modules
from app.core.config import settings
from app.services.vector_database import VectorDBService  

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedVectorDBBuilder:
    """
    Unified builder gộp chung JSON processing và vector database building
    """
    
    def __init__(self):
        self.backend_dir = backend_dir
        self.data_dir = self.backend_dir / "data"
        self.documents_dir = self.data_dir / "documents"
        self.vectordb_dir = self.data_dir / "vectordb"
        
        # Collection mappings
        self.collection_mappings = {
            'quy_trinh_cap_ho_tich_cap_xa': 'ho_tich_cap_xa',
            'ho_tich_cap_xa_moi_nhat': 'ho_tich_cap_xa',
            'quy_trinh_chung_thuc': 'chung_thuc',
            'quy_trinh_nb_chung_thuc_dung_chung': 'chung_thuc',
            'quy_trinh_nuoi_con_nuoi': 'nuoi_con_nuoi',
            'iso_ncn_moi': 'nuoi_con_nuoi',
        }
        
        # Create directories if needed
        self.vectordb_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize VectorDBService with proper Vietnamese embedding  
        self.vectordb_service = VectorDBService(
            persist_directory=str(self.vectordb_dir),
            embedding_model=settings.embedding_model_name
        )
    
    def detect_collection_from_path(self, file_path: str) -> str:
        """Xác định collection dựa trên đường dẫn file"""
        path_obj = Path(file_path)
        path_parts = path_obj.parts
        
        for part in path_parts:
            for pattern, collection in self.collection_mappings.items():
                if pattern in part.lower():
                    return collection
        
        return 'general'
    
    def load_json_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load và validate JSON document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate cấu trúc cơ bản
            if not isinstance(data, dict):
                logger.error(f"Invalid JSON structure in {file_path}: not a dict")
                return None
            
            if 'metadata' not in data or 'content_chunks' not in data:
                logger.error(f"Invalid JSON structure in {file_path}: missing required fields")
                return None
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            return None
    
    def process_json_chunks(self, json_data: Dict[str, Any], file_path: str) -> List[Dict[str, Any]]:
        """Chuyển đổi content_chunks từ JSON thành format phù hợp với vector database"""
        metadata = json_data.get('metadata', {})
        content_chunks = json_data.get('content_chunks', [])
        
        processed_chunks = []
        
        # Lấy thông tin metadata quan trọng để thêm context
        document_title = metadata.get('title', '')
        executing_agency = metadata.get('executing_agency', '')
        applicant_type = metadata.get('applicant_type', [])
        processing_time = metadata.get('processing_time_text', '')
        fee_text = metadata.get('fee_text', '')
        has_form = metadata.get('has_form', False)
        requirements_conditions = metadata.get('requirements_conditions', '')
        
        for i, chunk in enumerate(content_chunks):
            # Lấy thông tin từ chunk
            chunk_id = chunk.get('chunk_id', i + 1)
            chunk_index_num = i  # Thêm chunk_index_num (0-based index)
            section_title = chunk.get('section_title', '')
            content = chunk.get('content', '')
            source_reference = chunk.get('source_reference', '')
            keywords = chunk.get('keywords', [])
            
            # Tăng cường ngữ cảnh cho mỗi chunk với metadata phong phú
            context_parts = []
            
            # 1. Tiêu đề tài liệu (quan trọng nhất)
            if document_title:
                context_parts.append(f"Tiêu đề tài liệu: {document_title}")
            
            # 2. Cơ quan thực hiện
            if executing_agency:
                context_parts.append(f"Cơ quan thực hiện: {executing_agency}")
            
            # 3. Đối tượng thực hiện
            if applicant_type and len(applicant_type) > 0:
                context_parts.append(f"Đối tượng thực hiện: {', '.join(applicant_type)}")
            
            # 4. Có biểu mẫu hay không
            if has_form:
                context_parts.append("Có biểu mẫu: Có")
            
            # 5. Điều kiện yêu cầu (nếu có)
            if requirements_conditions:
                context_parts.append(f"Điều kiện: {requirements_conditions}")
            
            # 6. Thời gian xử lý (rút gọn để không quá dài)
            if processing_time and len(processing_time) < 150:  # Chỉ thêm nếu không quá dài
                context_parts.append(f"Thời gian xử lý: {processing_time}")
            
            # 7. Thông tin lệ phí (rút gọn)
            if fee_text:
                # Lấy thông tin lệ phí chính, bỏ qua chi tiết quá dài
                fee_summary = fee_text.split('.')[0] if fee_text else fee_text
                if len(fee_summary) < 100:
                    context_parts.append(f"Lệ phí: {fee_summary}")
            
            # 8. Tiêu đề mục (section)
            if section_title:
                context_parts.append(f"Mục: {section_title}")
            
            # 9. Phần "Nội dung:" để phân tách rõ ràng
            if context_parts and content.strip():
                context_parts.append("Nội dung:")
            
            # Ghép tất cả lại với nội dung chính
            if context_parts:
                full_content = "\n".join(context_parts) + "\n" + content
            else:
                full_content = content
            
            # Tạo source information để frontend có thể truy vết
            source_info = {
                'file_path': file_path,
                'document_title': metadata.get('title', ''),
                'document_code': metadata.get('code', ''),
                'issuing_authority': metadata.get('issuing_authority', ''),
                'effective_date': metadata.get('effective_date', ''),
                'executing_agency': metadata.get('executing_agency', ''),
                'source_reference': source_reference,
                'section_title': section_title,
                'chunk_id': f"{Path(file_path).stem}_chunk_{chunk_id}",  # Tạo ID unique
                'chunk_index_num': chunk_index_num,  # Thêm chunk_index_num cho context expansion
                'document_id': Path(file_path).stem  # Thêm document_id để group chunks
            }
            
            # Tạo processed chunk
            processed_chunk = {
                'content': full_content.strip(),
                'chunk_id': f"{Path(file_path).stem}_chunk_{chunk_id}",
                'type': 'json_section',
                'char_start': 0,
                'char_end': len(full_content),
                'keywords': keywords,
                'source': source_info,
                'metadata': {
                    'document_metadata': metadata,
                    'section_title': section_title,
                    'source_reference': source_reference,
                    'processing_time': metadata.get('processing_time_text', ''),
                    'fee_info': metadata.get('fee_text', ''),
                    'legal_basis': metadata.get('legal_basis_references', [])
                }
            }
            
            processed_chunks.append(processed_chunk)
        
        return processed_chunks
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process single JSON document"""
        try:
            # Load JSON data
            json_data = self.load_json_document(file_path)
            if not json_data:
                return {"error": "Failed to load JSON document"}
            
            # Process chunks
            processed_chunks = self.process_json_chunks(json_data, file_path)
            
            if not processed_chunks:
                logger.warning(f"No chunks processed from {file_path}")
                return {"error": "No chunks processed"}
            
            # Detect collection
            collection_name = self.detect_collection_from_path(file_path)
            
            # Calculate total characters
            total_chars = sum(len(chunk['content']) for chunk in processed_chunks)
            
            return {
                "file_path": file_path,
                "collection": collection_name,
                "chunks": processed_chunks,
                "total_chunks": len(processed_chunks),
                "total_characters": total_chars,
                "document_metadata": json_data.get('metadata', {}),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error processing JSON document {file_path}: {e}")
            return {"error": str(e)}
    
    def process_all_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        """Process all JSON documents in directory, organized by collections"""
        collections_data = {}
        
        try:
            json_files = list(self.documents_dir.rglob("*.json"))
            logger.info(f"Found {len(json_files)} JSON files to process")
            
            for file_path in json_files:
                logger.info(f"Processing JSON file: {file_path}")
                
                doc_data = self.process_document(str(file_path))
                
                if "error" not in doc_data:
                    collection_name = doc_data["collection"]
                    
                    if collection_name not in collections_data:
                        collections_data[collection_name] = []
                    
                    # Thêm chunks vào collection
                    collections_data[collection_name].extend(doc_data["chunks"])
                    
                    logger.info(
                        f"Added {doc_data['total_chunks']} chunks from '{doc_data['document_metadata'].get('title', file_path.name)}' "
                        f"to collection '{collection_name}'"
                    )
                else:
                    logger.error(f"Failed to process {file_path}: {doc_data['error']}")
            
            # Log summary
            for collection_name, chunks in collections_data.items():
                logger.info(f"Collection '{collection_name}': {len(chunks)} total chunks")
            
            return collections_data
            
        except Exception as e:
            logger.error(f"Error processing documents directory {self.documents_dir}: {e}")
            return {}
    
    def check_prerequisites(self) -> bool:
        """Check if documents exist and are processable"""
        logger.info("📋 Checking prerequisites...")
        
        if not self.documents_dir.exists():
            logger.error(f"❌ Documents directory not found: {self.documents_dir}")
            return False
        
        # Count documents - scan recursively
        json_files = list(self.documents_dir.rglob("*.json"))
        if not json_files:
            logger.error("❌ No JSON documents found")
            return False
        
        logger.info(f"✅ Found {len(json_files)} document files")
        
        # Test process one file to check structure
        test_file = json_files[0]
        try:
            doc_data = self.process_document(str(test_file))
            if "error" not in doc_data:
                logger.info(f"✅ JSON structure validation passed")
                collections = set()
                for json_file in json_files[:5]:  # Test first 5 files
                    collection = self.detect_collection_from_path(str(json_file))
                    collections.add(collection)
                logger.info(f"✅ Detected collections: {list(collections)}")
                return True
            else:
                logger.error(f"❌ JSON structure validation failed: {doc_data['error']}")
                return False
        except Exception as e:
            logger.error(f"❌ Error testing JSON structure: {e}")
            return False
    
    def build_vector_database(self, force_rebuild: bool = False) -> bool:
        """Build complete vector database with integrated JSON processing"""
        logger.info("🔄 BUILDING VECTOR DATABASE (UNIFIED)")
        logger.info("-" * 40)
        
        try:
            # Clean rebuild if requested
            if force_rebuild:
                logger.info("   🗑️ Force rebuild - clearing existing collections...")
                try:
                    import shutil
                    if self.vectordb_dir.exists():
                        shutil.rmtree(self.vectordb_dir)
                        logger.info(f"      ✅ Removed: {self.vectordb_dir}")
                    self.vectordb_dir.mkdir(parents=True, exist_ok=True)
                    logger.info("      ✅ Created fresh vectordb directory")
                    
                    # Reinitialize VectorDBService
                    self.vectordb_service = VectorDBService(
                        persist_directory=str(self.vectordb_dir),
                        embedding_model=settings.embedding_model_name
                    )
                except Exception as e:
                    logger.warning(f"   ⚠️ Error clearing database: {e}")
            
            # Process all documents using integrated processing
            logger.info("   📊 Processing all JSON documents...")
            collections_data = self.process_all_documents()
            
            if not collections_data:
                logger.error("❌ No data processed from JSON files")
                return False
            
            # Process each collection
            total_chunks = 0
            
            for collection_name, chunks in collections_data.items():
                if not chunks:
                    logger.warning(f"      ⚠️ No chunks for collection {collection_name}")
                    continue
                
                logger.info(f"   📂 Processing collection: {collection_name}")
                logger.info(f"      📄 Chunks: {len(chunks)}")
                
                # Log first chunk to verify structure
                if chunks:
                    first_chunk = chunks[0]
                    logger.info(f"      📝 Sample chunk ID: {first_chunk.get('chunk_id', 'N/A')}")
                    logger.info(f"      📝 Document title: {first_chunk.get('source', {}).get('document_title', 'N/A')}")
                
                # Add documents to vector database using VectorDBService
                try:
                    added_count = self.vectordb_service.add_documents_to_collection(
                        collection_name=collection_name,
                        documents=chunks
                    )
                    logger.info(f"      ✅ Added {added_count} chunks to {collection_name}")
                    total_chunks += added_count
                    
                except Exception as e:
                    logger.error(f"      ❌ Error adding to collection {collection_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            logger.info(f"📊 Unified vector database build completed")
            logger.info(f"   📂 Collections: {len(collections_data)}")
            logger.info(f"   📄 Total chunks: {total_chunks}")
            logger.info(f"   💾 Database location: {self.vectordb_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error building vector database: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_vector_database(self) -> bool:
        """Test vector database functionality using VectorDBService"""
        logger.info("🧪 TESTING VECTOR DATABASE")
        logger.info("-" * 40)
        
        try:
            # Test search queries
            test_queries = {
                'ho_tich_cap_xa': 'thủ tục khai sinh',
                'chung_thuc': 'chứng thực hợp đồng',
                'nuoi_con_nuoi': 'nuôi con nuôi'
            }
            
            successful_tests = 0
            total_tests = 0
            
            for collection_name, query in test_queries.items():
                try:
                    # Get collection stats
                    stats = self.vectordb_service.get_collection_stats(collection_name)
                    count = stats.get('document_count', 0)
                    logger.info(f"   📊 {collection_name}: {count} documents")
                    
                    if count > 0:
                        # Test search
                        logger.info(f"   🔍 Testing search: '{query}'")
                        total_tests += 1
                        
                        results = self.vectordb_service.search_in_collection(
                            collection_name=collection_name,
                            query=query,
                            top_k=3
                        )
                        
                        if results:
                            logger.info(f"      ✅ Found {len(results)} results")
                            best_result = results[0]
                            similarity = best_result.get('similarity', best_result.get('score', 0))
                            logger.info(f"      📊 Best similarity: {similarity:.3f}")
                            
                            # Log additional info about the result
                            source_info = best_result.get('source', {})
                            document_title = source_info.get('document_title', 'N/A')
                            chunk_id = source_info.get('chunk_id', 'N/A')
                            logger.info(f"      📄 Best result: {document_title} (ID: {chunk_id})")
                            
                            successful_tests += 1
                        else:
                            logger.warning(f"      ⚠️ No results found")
                    else:
                        logger.warning(f"   ⚠️ Collection {collection_name} is empty")
                        
                except Exception as e:
                    logger.error(f"   ❌ Error testing collection {collection_name}: {e}")
            
            logger.info(f"📊 Test Summary: {successful_tests}/{total_tests} successful")
            
            if successful_tests > 0:
                logger.info("✅ Vector database test passed")
                return True
            else:
                logger.error("❌ All tests failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Unified vector database builder for LegalRAG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/2_build_vectordb_unified.py           # Build vector database
  python tools/2_build_vectordb_unified.py --force   # Force rebuild (clear existing)
  python tools/2_build_vectordb_unified.py --clean   # Clean rebuild (remove entire DB)

This unified tool will:
1. Process JSON documents and convert to vector database format
2. Ensure proper ID generation (document_id + chunk_id)
3. Maintain metadata enrichment for better search
4. Support context expansion via document grouping
5. Build complete vector database
6. Test search functionality across collections

Note: This replaces both document_processor.py and 2_build_vectordb_final.py
        """
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force rebuild - clear existing collections'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean rebuild - delete entire vectordb directory and start fresh'
    )
    
    args = parser.parse_args()
    
    logger.info("📊 LEGALRAG UNIFIED VECTOR DATABASE BUILDER")
    logger.info("=" * 60)
    
    # Clean rebuild if requested
    if args.clean:
        logger.info("🗑️ CLEAN REBUILD - Removing entire vectordb directory")
        import shutil
        import time
        
        # Don't initialize VectorDBService yet if we're doing clean rebuild
        if Path(str(settings.vectordb_path)).exists():
            try:
                # Wait a bit and try to remove
                time.sleep(1)
                shutil.rmtree(str(settings.vectordb_path))
                logger.info(f"   ✅ Removed: {settings.vectordb_path}")
            except PermissionError as e:
                logger.error(f"   ❌ Cannot remove vectordb directory: {e}")
                logger.info("   💡 Try closing all applications using the database and run again")
                return 1
        Path(str(settings.vectordb_path)).mkdir(parents=True, exist_ok=True)
        logger.info("   ✅ Created fresh vectordb directory")
    
    # Initialize unified builder (after clean if needed)
    builder = UnifiedVectorDBBuilder()
    
    # Check prerequisites
    if not builder.check_prerequisites():
        logger.error("❌ Prerequisites not met")
        return 1
    
    # Build vector database  
    force_rebuild = args.force or args.clean
    if not builder.build_vector_database(force_rebuild=force_rebuild):
        logger.error("❌ Failed to build vector database")
        return 1
    
    # Test vector database
    if not builder.test_vector_database():
        logger.warning("⚠️ Vector database test failed, but database was built")
        # Don't fail here - database might work even if test fails
    
    logger.info("🎉 UNIFIED VECTOR DATABASE BUILD COMPLETED SUCCESSFULLY!")
    return 0

if __name__ == "__main__":
    exit(main())
