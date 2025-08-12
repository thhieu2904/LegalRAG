"""
Enhanced Context Expansion Service
Sử dụng "Nucleus Chunk" strategy để mở rộng ngữ cảnh hiệu quả
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import json

logger = logging.getLogger(__name__)

class EnhancedContextExpansionService:
    """Service mở rộng ngữ cảnh với Nucleus Chunk strategy"""
    
    def __init__(self, vectordb_service, documents_dir: str):
        self.vectordb_service = vectordb_service
        self.documents_dir = Path(documents_dir)
        
        # Cache metadata của documents
        self.document_metadata_cache = {}
        self._build_document_metadata_cache()
    
    def _build_document_metadata_cache(self):
        """Xây dựng cache metadata để map chunk -> document"""
        try:
            # Lấy tất cả collections
            collections = self.vectordb_service.list_collections()
            
            for collection_info in collections:
                collection_name = collection_info["name"]
                collection = self.vectordb_service.get_collection(collection_name)
                
                # Lấy tất cả documents trong collection
                try:
                    results = collection.get()
                    
                    for i, chunk_id in enumerate(results["ids"]):
                        metadata = results.get("metadatas", [{}])[i] if i < len(results.get("metadatas", [])) else {}
                        
                        if metadata and "source" in metadata:
                            source_file = metadata["source"]
                            
                            # Build cache entry
                            self.document_metadata_cache[chunk_id] = {
                                "source_file": source_file,
                                "collection": collection_name,
                                "metadata": metadata,
                                "chunk_index": metadata.get("chunk_index", 0)
                            }
                            
                except Exception as e:
                    logger.warning(f"Could not process collection {collection_name}: {e}")
                    
            logger.info(f"Built metadata cache for {len(self.document_metadata_cache)} chunks")
            
        except Exception as e:
            logger.error(f"Error building document metadata cache: {e}")
    
    def expand_context_with_nucleus(
        self,
        nucleus_chunks: List[Dict[str, Any]], 
        max_context_length: int = 3000,
        include_full_document: bool = True
    ) -> Dict[str, Any]:
        """
        Mở rộng ngữ cảnh dựa trên nucleus chunks - STRATEGY: 1 CHUNK → TOÀN BỘ DOCUMENT
        
        Flow tối ưu:
        1. Lấy 1 nucleus chunk với rerank score cao nhất
        2. Tìm source file JSON chứa chunk đó  
        3. Load toàn bộ nội dung document từ file JSON gốc
        4. Return full document content thay vì chỉ 1 chunk
        
        Args:
            nucleus_chunks: List chunks đã rerank (thường chỉ 1 chunk cao nhất)
            max_context_length: Độ dài context tối đa (ký tự)
            include_full_document: True = lấy toàn bộ document, False = chỉ chunks liền kề
            
        Returns:
            Expanded context với toàn bộ document content và metadata
        """
        try:
            expanded_context = {
                "nucleus_chunks": nucleus_chunks,
                "expanded_content": [],
                "source_documents": [],
                "total_length": 0,
                "expansion_strategy": "single_nucleus_full_document"
            }
            
            # CHỈ XỬ LÝ 1 NUCLEUS CHUNK ĐẦU TIÊN (chunk có rerank score cao nhất)
            if not nucleus_chunks:
                logger.warning("No nucleus chunks provided")
                return expanded_context
                
            nucleus_chunk = nucleus_chunks[0]  # Lấy chunk cao nhất sau rerank
            logger.info(f"Processing nucleus chunk with ID: {nucleus_chunk.get('id', 'N/A')}")
            
            # Tìm source file JSON từ nucleus chunk metadata
            source_file = None
            
            # Thử nhiều cách để tìm source file
            if "source" in nucleus_chunk and "file_path" in nucleus_chunk["source"]:
                source_file = nucleus_chunk["source"]["file_path"]
            elif "metadata" in nucleus_chunk and "source" in nucleus_chunk["metadata"]:
                source_file = nucleus_chunk["metadata"]["source"].get("file_path")
            
            if not source_file:
                logger.warning("Could not find source file for nucleus chunk")
                return expanded_context
                
            logger.info(f"Found source file: {source_file}")
            logger.info("Loading FULL DOCUMENT content (not just chunks)")
            
            # QUAN TRỌNG: Load toàn bộ document gốc từ file JSON thay vì chỉ lấy chunks
            full_document_content = self._load_full_document(source_file)
            
            if full_document_content:
                # Giới hạn context length
                if len(full_document_content) > max_context_length:
                    # Truncate nhưng giữ phần đầu và thông tin quan trọng
                    full_document_content = full_document_content[:max_context_length] + "..."
                
                expanded_context["expanded_content"] = [{
                    "text": full_document_content,
                    "source": source_file,
                    "document_title": nucleus_chunk.get("source", {}).get("document_title", ""),
                    "type": "full_document"
                }]
                expanded_context["source_documents"] = [source_file]
                expanded_context["total_length"] = len(full_document_content)
                
                logger.info(f"Expanded context: {len(full_document_content)} chars from 1 document")
            else:
                logger.warning("Could not load full document content")
            
            return expanded_context
            
        except Exception as e:
            logger.error(f"Error in context expansion: {e}")
            # Fallback: return nucleus chunks as-is
            return {
                "nucleus_chunks": nucleus_chunks,
                "expanded_content": [{"text": chunk.get("content", ""), "source": "fallback", "type": "chunk_fallback"} for chunk in nucleus_chunks],
                "source_documents": [],
                "total_length": sum(len(chunk.get("content", "")) for chunk in nucleus_chunks),
                "expansion_strategy": "fallback"
            }
    
    def _load_full_document(self, file_path: str) -> str:
        """
        Load toàn bộ nội dung document từ file JSON gốc
        QUAN TRỌNG: Đây là thay đổi chính - thay vì lấy chỉ 1 chunk, 
        ta lấy toàn bộ document để cung cấp context đầy đủ cho LLM
        """
        try:
            import json
            from pathlib import Path
            
            if not Path(file_path).exists():
                logger.warning(f"Source file not found: {file_path}")
                return ""
                
            logger.info(f"Loading full document from: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Build full document content với cấu trúc hoàn chỉnh
            metadata = json_data.get('metadata', {})
            content_chunks = json_data.get('content_chunks', [])
            
            # Tạo full document content với metadata đầy đủ và cấu trúc rõ ràng
            full_parts = []
            
            # HEADER - Thông tin quan trọng nhất
            if metadata.get('title'):
                full_parts.append(f"📋 TIÊU ĐỀ: {metadata['title']}")
            
            if metadata.get('executing_agency'):
                full_parts.append(f"🏢 CƠ QUAN THỰC HIỆN: {metadata['executing_agency']}")
                
            if metadata.get('applicant_type'):
                applicant_text = ', '.join(metadata['applicant_type']) if isinstance(metadata['applicant_type'], list) else metadata['applicant_type']
                full_parts.append(f"👥 ĐỐI TƯỢNG: {applicant_text}")
            
            if metadata.get('processing_time_text'):
                full_parts.append(f"⏰ THỜI GIAN XỬ LÝ: {metadata['processing_time_text']}")
                
            if metadata.get('fee_text'):
                full_parts.append(f"💰 LỆ PHÍ: {metadata['fee_text']}")
                
            if metadata.get('legal_basis'):
                full_parts.append(f"📜 CĂN CỨ PHÁP LÝ: {metadata['legal_basis']}")
            
            full_parts.append("=" * 80)  # Separator rõ ràng
            
            # BODY - Nội dung chính từng phần với cấu trúc rõ ràng  
            for i, chunk in enumerate(content_chunks, 1):
                # Section header nếu có
                if chunk.get('section_title'):
                    full_parts.append(f"\n📖 PHẦN {i}: {chunk['section_title']}")
                    full_parts.append("-" * 60)
                else:
                    full_parts.append(f"\n📄 NỘI DUNG {i}:")
                    full_parts.append("-" * 40)
                    
                # Nội dung chính
                if chunk.get('content'):
                    full_parts.append(chunk['content'].strip())
            
            full_content = "\n".join(full_parts)
            logger.info(f"Loaded full document: {len(full_content)} characters, {len(content_chunks)} sections")
            
            return full_content
            
        except Exception as e:
            logger.error(f"Error loading full document {file_path}: {e}")
            return ""
    
    def _get_all_chunks_from_document(self, source_file: str) -> List[Dict[str, Any]]:
        """Lấy tất cả chunks từ một document"""
        document_chunks = []
        
        for chunk_id, metadata in self.document_metadata_cache.items():
            if metadata["source_file"] == source_file:
                # Lấy chunk content từ vector database
                try:
                    collection = self.vectordb_service.get_collection(metadata["collection"])
                    result = collection.get(ids=[chunk_id])
                    
                    if result["documents"]:
                        document_chunks.append({
                            "id": chunk_id,
                            "content": result["documents"][0],
                            "metadata": metadata,
                            "chunk_index": metadata["chunk_index"]
                        })
                        
                except Exception as e:
                    logger.warning(f"Could not retrieve chunk {chunk_id}: {e}")
        
        # Sắp xếp theo chunk_index
        document_chunks.sort(key=lambda x: x["chunk_index"])
        
        return document_chunks
    
    def _get_surrounding_chunks(self, source_file: str, nucleus_chunks: List[Dict[str, Any]], window_size: int = 2) -> List[Dict[str, Any]]:
        """Lấy các chunks xung quanh nucleus chunks"""
        # Tìm nucleus chunk indices trong document này
        nucleus_indices = set()
        for nucleus_chunk in nucleus_chunks:
            chunk_id = nucleus_chunk.get("id", "")
            if chunk_id in self.document_metadata_cache:
                metadata = self.document_metadata_cache[chunk_id]
                if metadata["source_file"] == source_file:
                    nucleus_indices.add(metadata["chunk_index"])
        
        if not nucleus_indices:
            return []
        
        # Xác định range để lấy surrounding chunks
        min_index = min(nucleus_indices) - window_size
        max_index = max(nucleus_indices) + window_size
        
        # Lấy chunks trong range
        surrounding_chunks = []
        for chunk_id, metadata in self.document_metadata_cache.items():
            if metadata["source_file"] == source_file:
                chunk_idx = metadata["chunk_index"]
                if min_index <= chunk_idx <= max_index:
                    try:
                        collection = self.vectordb_service.get_collection(metadata["collection"])
                        result = collection.get(ids=[chunk_id])
                        
                        if result["documents"]:
                            surrounding_chunks.append({
                                "id": chunk_id,
                                "content": result["documents"][0],
                                "metadata": metadata,
                                "chunk_index": chunk_idx
                            })
                            
                    except Exception as e:
                        logger.warning(f"Could not retrieve chunk {chunk_id}: {e}")
        
        # Sắp xếp theo chunk_index
        surrounding_chunks.sort(key=lambda x: x["chunk_index"])
        
        return surrounding_chunks
    
    def _merge_document_chunks(self, chunks: List[Dict[str, Any]], source_file: str) -> Dict[str, Any]:
        """Merge các chunks thành một document context"""
        if not chunks:
            return {}
        
        merged_text = "\n\n".join([chunk["content"] for chunk in chunks])
        
        return {
            "text": merged_text,
            "source": source_file,
            "chunk_count": len(chunks),
            "chunk_indices": [chunk["chunk_index"] for chunk in chunks],
            "total_chars": len(merged_text)
        }
    
    def get_document_summary(self, source_file: str) -> Dict[str, Any]:
        """Lấy thông tin tóm tắt về một document"""
        chunks = self._get_all_chunks_from_document(source_file)
        
        if not chunks:
            return {"error": f"No chunks found for {source_file}"}
        
        return {
            "source_file": source_file,
            "total_chunks": len(chunks),
            "total_length": sum(len(chunk["content"]) for chunk in chunks),
            "chunk_indices": [chunk["chunk_index"] for chunk in chunks],
            "collections": list(set(self.document_metadata_cache[chunk["id"]]["collection"] for chunk in chunks))
        }
    
    def rebuild_metadata_cache(self):
        """Rebuild metadata cache (sau khi có documents mới)"""
        self.document_metadata_cache.clear()
        self._build_document_metadata_cache()
        
    def get_stats(self) -> Dict[str, Any]:
        """Thống kê context expansion service"""
        source_files = set()
        collections = set()
        
        for metadata in self.document_metadata_cache.values():
            source_files.add(metadata["source_file"])
            collections.add(metadata["collection"])
        
        return {
            "total_chunks": len(self.document_metadata_cache),
            "total_documents": len(source_files),
            "total_collections": len(collections),
            "documents": list(source_files),
            "collections": list(collections)
        }
