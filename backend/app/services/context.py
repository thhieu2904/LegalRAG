"""
Enhanced Context Expansion Service
Sử dụng "Nucleus Chunk" strategy để mở rộng ngữ cảnh hiệu quả
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import json

logger = logging.getLogger(__name__)

class ContextExpander:
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

    def _build_highlighted_context(self, full_content: str, nucleus_chunk: Dict) -> str:
        """
        🎯 PHASE 1: Highlight nucleus chunk trong full content để AI focus đúng chỗ
        """
        nucleus_content = nucleus_chunk.get('content', '')
        
        if not nucleus_content:
            logger.warning("Nucleus chunk không có content để highlight")
            return full_content
        
        # 🔍 DEBUG: Log nucleus content for troubleshooting
        logger.debug(f"🔍 Nucleus content (first 200 chars): {nucleus_content[:200]}...")
        logger.debug(f"🔍 Full content (first 200 chars): {full_content[:200]}...")
        
        # Tìm và highlight nucleus chunk
        if nucleus_content in full_content:
            highlighted_content = full_content.replace(
                nucleus_content,
                f"[THÔNG TIN CHÍNH]\n{nucleus_content}\n[/THÔNG TIN CHÍNH]"
            )
            logger.info("✅ Successfully highlighted nucleus chunk trong full context")
            return highlighted_content
        else:
            # Try fuzzy matching for partial matches
            nucleus_words = nucleus_content.split()[:10]  # First 10 words
            partial_match = ' '.join(nucleus_words)
            
            if partial_match in full_content:
                logger.info("✅ Found partial match with first 10 words, using fallback highlighting")
            else:
                logger.warning(f"⚠️ No match found for nucleus chunk. Nucleus length: {len(nucleus_content)}, Full content length: {len(full_content)}")
                
            # Fallback: add nucleus at top
            highlighted_content = f"[THÔNG TIN CHÍNH]\n{nucleus_content}\n[/THÔNG TIN CHÍNH]\n\n{full_content}"
            logger.info("⚠️ Nucleus chunk không tìm thấy trong full content, thêm lên đầu")
            return highlighted_content
    
    def expand_context_with_nucleus(
        self,
        nucleus_chunks: List[Dict[str, Any]], 
        max_context_length: int = 8000,  # INCREASED: Tăng từ 3000 lên 8000 để đủ context
        include_full_document: bool = True
    ) -> Dict[str, Any]:
        """
        Mở rộng ngữ cảnh dựa trên nucleus chunks - STRATEGY: 1 CHUNK → TOÀN BỘ DOCUMENT
        
        TRIẾT LÝ THIẾT KẾ CHÍNH:
        1. Lấy 1 nucleus chunk với rerank score cao nhất
        2. Tìm source file JSON chứa chunk đó  
        3. Load TOÀN BỘ nội dung document từ file JSON gốc
        4. Return FULL document content để đảm bảo ngữ cảnh pháp luật đầy đủ
        
        Args:
            nucleus_chunks: List chunks đã rerank (thường chỉ 1 chunk cao nhất)
            max_context_length: Độ dài context tối đa (ký tự) - CHỈ để truncate nếu QUÁ dài
            include_full_document: LUÔN True cho văn bản pháp luật
            
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
            logger.info("Loading FULL DOCUMENT content để đảm bảo ngữ cảnh pháp luật đầy đủ")
            
            # TRIẾT LÝ THIẾT KẾ: Load toàn bộ document gốc từ file JSON
            # Không cắt ghép, không smart expansion - chỉ FULL DOCUMENT
            final_content, structured_metadata = self._load_full_document_and_metadata(source_file)
            expansion_strategy = "full_document_legal_context"
            
            # Truncate CHỈ KHI document quá dài (giữ tối đa thông tin)
            if len(final_content) > max_context_length:
                logger.warning(f"Document dài {len(final_content)} chars > max {max_context_length}, truncating...")
                final_content = final_content[:max_context_length] + "..."
            
            # Build final result
            if final_content:
                expanded_context["expanded_content"] = [{
                    "text": final_content,
                    "source": source_file,
                    "document_title": nucleus_chunk.get("source", {}).get("document_title", ""),
                    "type": expansion_strategy
                }]
                expanded_context["source_documents"] = [source_file]
                expanded_context["total_length"] = len(final_content)
                expanded_context["expansion_strategy"] = expansion_strategy
                expanded_context["structured_metadata"] = structured_metadata  # ✅ THÊM: Structured metadata
                
                logger.info(f"Final context: {len(final_content)} chars, strategy: {expansion_strategy}")
                logger.info(f"Extracted metadata fields: {list(structured_metadata.keys()) if structured_metadata else 'None'}")
            else:
                logger.warning("Could not generate final content")
            
            return expanded_context
            
        except Exception as e:
            logger.error(f"Error in context expansion: {e}")
            # Fallback: return nucleus chunks as-is
            return {
                "nucleus_chunks": nucleus_chunks,
                "expanded_content": [{"text": chunk.get("content", ""), "source": "fallback", "type": "chunk_fallback"} for chunk in nucleus_chunks],
                "source_documents": [],
                "total_length": sum(len(chunk.get("content", "")) for chunk in nucleus_chunks),
                "expansion_strategy": "fallback",
                "structured_metadata": {}  # ✅ THÊM: Empty metadata for fallback
            }
    
    def _load_full_document_and_metadata(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Load TOÀN BỘ nội dung document + metadata có cấu trúc
        Returns: (content, structured_metadata)
        """
        try:
            if not Path(file_path).exists():
                logger.warning(f"Source file not found: {file_path}")
                return "", {}
                
            logger.info(f"Loading COMPLETE document content and metadata from: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Extract metadata and content
            metadata = json_data.get('metadata', {})
            content_chunks = json_data.get('content_chunks', [])
            
            # Build complete content với CLEAN FORMATTING - PHASE 3
            complete_parts = []
            
            # 🧹 PHASE 3: Clean metadata formatting - bỏ dấu ===
            if metadata:
                complete_parts.append("Thông tin thủ tục:")
                for key, value in metadata.items():
                    if value:  # Chỉ loại bỏ empty values
                        clean_key = key.replace('_', ' ').title()
                        complete_parts.append(f"{clean_key}: {value}")
                complete_parts.append("")  # Empty line separator
            
            # 🧹 PHASE 3: Clean content formatting - bỏ dấu ===
            if content_chunks:
                complete_parts.append("Nội dung chi tiết:")
                for chunk in content_chunks:
                    if chunk.get('content'):
                        complete_parts.append(chunk['content'])
                    if chunk.get('subcontent'):
                        for sub in chunk['subcontent']:
                            if sub.get('content'):
                                complete_parts.append(sub['content'])
                complete_parts.append("")
            
            # Join tất cả content
            complete_content = "\n".join(complete_parts)
            
            logger.info(f"Loaded COMPLETE document: {len(complete_content)} characters + structured metadata")
            return complete_content, metadata
            
        except Exception as e:
            logger.error(f"Error loading document and metadata: {e}")
            return "", {}

    def _load_full_document(self, file_path: str) -> str:
        """
        Load TOÀN BỘ nội dung document - không filtering, không truncation
        Đây là fix cho vấn đề user không nhận được đầy đủ thông tin
        """
        try:
            import json
            from pathlib import Path
            
            if not Path(file_path).exists():
                logger.warning(f"Source file not found: {file_path}")
                return ""
                
            logger.info(f"Loading COMPLETE document content from: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # LOAD TOÀN BỘ DOCUMENT - TẤT CẢ thông tin
            metadata = json_data.get('metadata', {})
            content_chunks = json_data.get('content_chunks', [])
            
            # 🧹 PHASE 3: Build COMPLETE document content với clean formatting
            complete_parts = []
            
            # 🧹 PHASE 3: Clean metadata formatting - bỏ dấu ===
            if metadata:
                complete_parts.append("Thông tin thủ tục:")
                for key, value in metadata.items():
                    if value:  # Chỉ loại bỏ empty values
                        clean_key = key.replace('_', ' ').title()
                        complete_parts.append(f"{clean_key}: {value}")
                complete_parts.append("")  # Empty line separator
            
            # 🧹 PHASE 3: Clean content formatting - bỏ dấu ===
            if content_chunks:
                complete_parts.append("Nội dung chi tiết:")
                for chunk in content_chunks:
                    if chunk.get('content'):
                        complete_parts.append(chunk['content'])
                    if chunk.get('subcontent'):
                        for sub in chunk['subcontent']:
                            if sub.get('content'):
                                complete_parts.append(sub['content'])
                complete_parts.append("")
            
            # Join tất cả content
            complete_content = "\n".join(complete_parts)
            
            logger.info(f"Loaded COMPLETE document: {len(complete_content)} characters (NO filtering, NO truncation)")
            return complete_content
            
        except Exception as e:
            logger.error(f"Error loading document: {e}")
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
