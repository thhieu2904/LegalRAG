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
        🎯 PHASE 2: Highlight nucleus chunk trong full content để AI focus đúng chỗ
        🚀 IMPROVED: Better content matching for full document content
        """
        nucleus_content = nucleus_chunk.get('content', '')
        
        if not nucleus_content:
            logger.warning("Nucleus chunk không có content để highlight")
            return full_content
        
        # 🔍 DEBUG: Log nucleus content for troubleshooting
        logger.debug(f"🔍 Nucleus content (first 200 chars): {nucleus_content[:200]}...")
        logger.debug(f"🔍 Full content (first 200 chars): {full_content[:200]}...")
        
        # 🚀 PHASE 2: Try exact match with nucleus content
        if nucleus_content in full_content:
            highlighted_content = full_content.replace(
                nucleus_content,
                f"[THÔNG TIN CHÍNH]\n{nucleus_content}\n[/THÔNG TIN CHÍNH]"
            )
            logger.info("✅ Successfully highlighted nucleus chunk trong full context")
            return highlighted_content
        
        # 🚀 PHASE 2: Try to find content from nucleus chunk metadata
        nucleus_source = nucleus_chunk.get('source', {})
        nucleus_metadata = nucleus_chunk.get('metadata', {})
        
        # Try to find content in nucleus chunk metadata
        nucleus_text_content = ""
        if nucleus_metadata.get('fused_text'):
            nucleus_text_content = nucleus_metadata['fused_text']
        elif nucleus_source.get('fused_text'):
            nucleus_text_content = nucleus_source['fused_text']
        
        # If we have fused text, try to extract content part
        if nucleus_text_content and " | CONTENT: " in nucleus_text_content:
            content_part = nucleus_text_content.split(" | CONTENT: ")[-1]
            if content_part in full_content:
                highlighted_content = full_content.replace(
                    content_part,
                    f"[THÔNG TIN CHÍNH]\n{content_part}\n[/THÔNG TIN CHÍNH]"
                )
                logger.info("✅ Successfully highlighted content from fused text")
                return highlighted_content
        
        # 🚀 PHASE 2: Try partial matching with nucleus content (improved)
        # Split nucleus content into sentences for better matching
        nucleus_sentences = nucleus_content.split('.')
        if len(nucleus_sentences) > 1:
            # Try to match first few sentences
            first_sentences = '. '.join(nucleus_sentences[:3])  # First 3 sentences
            if first_sentences in full_content:
                highlighted_content = full_content.replace(
                    first_sentences,
                    f"[THÔNG TIN CHÍNH]\n{first_sentences}\n[/THÔNG TIN CHÍNH]"
                )
                logger.info("✅ Found match with first 3 sentences, using sentence-based highlighting")
                return highlighted_content
        
        # 🚀 PHASE 2: Try word-based matching (improved)
        nucleus_words = nucleus_content.split()[:30]  # Increased from 20 to 30
        partial_match = ' '.join(nucleus_words)
        
        if partial_match in full_content:
            highlighted_content = full_content.replace(
                partial_match,
                f"[THÔNG TIN CHÍNH]\n{partial_match}\n[/THÔNG TIN CHÍNH]"
            )
            logger.info("✅ Found partial match with first 30 words, using word-based highlighting")
            return highlighted_content
        
        # 🚀 PHASE 2: Final fallback - add nucleus at top with better logging
        logger.warning(f"⚠️ No match found for nucleus chunk. Nucleus length: {len(nucleus_content)}, Full content length: {len(full_content)}")
        logger.info("⚠️ Nucleus chunk không tìm thấy trong full content, thêm lên đầu")
        
        # Create highlighted content with nucleus at top
        highlighted_content = f"[THÔNG TIN CHÍNH]\n{nucleus_content}\n[/THÔNG TIN CHÍNH]\n\n{full_content}"
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
            
            # 🔧 DEBUG: Log nucleus chunk structure to understand the problem
            logger.info(f"🔧 DEBUG nucleus chunk keys: {list(nucleus_chunk.keys())}")
            if 'source' in nucleus_chunk:
                logger.info(f"🔧 DEBUG source: {nucleus_chunk['source']}")
            if 'metadata' in nucleus_chunk:
                logger.info(f"🔧 DEBUG metadata keys: {list(nucleus_chunk['metadata'].keys()) if isinstance(nucleus_chunk['metadata'], dict) else nucleus_chunk['metadata']}")
            
            # Tìm source file JSON từ nucleus chunk metadata
            source_file = None
            
            # Thử nhiều cách để tìm source file
            if "source" in nucleus_chunk and isinstance(nucleus_chunk["source"], dict) and "file_path" in nucleus_chunk["source"]:
                source_file = nucleus_chunk["source"]["file_path"]
            elif "source" in nucleus_chunk and isinstance(nucleus_chunk["source"], str) and ".json" in nucleus_chunk["source"]:
                source_file = nucleus_chunk["source"]
            elif "metadata" in nucleus_chunk and isinstance(nucleus_chunk["metadata"], dict):
                if "file_path" in nucleus_chunk["metadata"]:
                    source_file = nucleus_chunk["metadata"]["file_path"]
                elif "source" in nucleus_chunk["metadata"]:
                    if isinstance(nucleus_chunk["metadata"]["source"], dict) and "file_path" in nucleus_chunk["metadata"]["source"]:
                        source_file = nucleus_chunk["metadata"]["source"]["file_path"]
                    elif isinstance(nucleus_chunk["metadata"]["source"], str):
                        source_file = nucleus_chunk["metadata"]["source"]
            
            # Nếu không tìm thấy source, tạo ra một fallback content từ nucleus chunk hiện tại
            if not source_file:
                logger.warning("Could not find source file for nucleus chunk")
                
                # Create fallback from nucleus chunk content
                chunk_content = nucleus_chunk.get("content", "")
                document_title = (
                    nucleus_chunk.get("source", {}).get("document_title", "") or 
                    nucleus_chunk.get("metadata", {}).get("document_title", "")
                )
                
                expanded_context["expanded_content"] = [{
                    "text": chunk_content,
                    "source": "fallback",
                    "document_title": document_title,
                    "type": "fallback_nucleus"
                }]
                expanded_context["total_length"] = len(chunk_content)
                expanded_context["expansion_strategy"] = "fallback_nucleus"
                
                # Try to extract metadata from nucleus chunk
                structured_metadata = {}
                if "metadata" in nucleus_chunk and isinstance(nucleus_chunk["metadata"], dict):
                    structured_metadata = nucleus_chunk["metadata"]
                expanded_context["structured_metadata"] = structured_metadata
                
                return expanded_context
                
            logger.info(f"Found source file: {source_file}")
            
            # 🔧 FIX PATH: Handle both relative và absolute paths correctly
            # Fix path to work with the new structure of documents
            try:
                # Normalize path separators
                source_file = source_file.replace('\\', '/') if '\\' in source_file else source_file
                
                # Handle different path formats
                if source_file.startswith("../"):
                    # Remove "../" and create absolute path from rag_service directory
                    relative_part = source_file.replace("../", "")
                    base_path = Path(__file__).parent.parent.parent  # from app/services -> rag_service
                    source_file_path = base_path / relative_part
                    logger.info(f"🔧 Converted relative path: {source_file} -> {source_file_path}")
                
                # Handle paths in data/storage/collections format (new correct format)
                elif source_file.startswith("data/storage/collections/"):
                    base_path = Path(__file__).parent.parent.parent  # rag_service directory
                    source_file_path = base_path / source_file
                    logger.info(f"🔧 Using storage path: {source_file_path}")
                
                # Handle paths in data/documents format (old incorrect format)
                elif "data/documents/" in source_file:
                    # Parse old path structure
                    parts = source_file.replace("data/documents/", "").split("/")
                    if len(parts) >= 2:
                        collection = parts[0]  # e.g., quy_trinh_cap_ho_tich_cap_xa
                        filename = parts[-1].replace(".doc", ".json")  # last part is filename
                        
                        # Look for the document in the correct structure
                        base_path = Path(__file__).parent.parent.parent  # rag_service directory
                        collections_path = base_path / "data" / "storage" / "collections"
                        
                        # Check if collection exists
                        collection_path = collections_path / collection
                        if collection_path.exists():
                            # Search for the file by filename in the documents directory
                            documents_path = collection_path / "documents"
                            if documents_path.exists():
                                # First try direct file search
                                potential_files = list(documents_path.glob(f"**/{filename}"))
                                
                                if potential_files:
                                    source_file_path = potential_files[0]
                                    logger.info(f"🔧 Found matching file: {source_file_path}")
                                else:
                                    # Try searching by DOC folder (slower but more thorough)
                                    doc_folders = [d for d in documents_path.iterdir() if d.is_dir()]
                                    for doc_folder in doc_folders:
                                        potential_file = doc_folder / filename
                                        if potential_file.exists():
                                            source_file_path = potential_file
                                            logger.info(f"🔧 Found in subfolder: {source_file_path}")
                                            break
                                    else:
                                        # No match found
                                        logger.warning(f"⚠️ Could not find file {filename} in {documents_path}")
                                        source_file_path = Path(source_file)  # Use original as fallback
                            else:
                                logger.warning(f"⚠️ Documents directory not found: {documents_path}")
                                source_file_path = Path(source_file)  # Use original as fallback
                        else:
                            logger.warning(f"⚠️ Collection not found: {collection_path}")
                            source_file_path = Path(source_file)  # Use original as fallback
                    else:
                        logger.warning(f"⚠️ Invalid path structure: {source_file}")
                        source_file_path = Path(source_file)  # Use original as fallback
                
                # Already absolute path
                elif Path(source_file).is_absolute():
                    source_file_path = Path(source_file)
                    logger.info(f"🔧 Using absolute path: {source_file_path}")
                
                # Other relative paths
                else:
                    base_path = Path(__file__).parent.parent.parent  # rag_service directory
                    source_file_path = base_path / source_file
                    logger.info(f"🔧 Converted to absolute path: {source_file_path}")
                
                # Check if file exists
                if not source_file_path.exists():
                    logger.warning(f"⚠️ File not found after path resolution: {source_file_path}")
                    
                    # Try an alternative approach - remove the "../" prefix if it exists in the path
                    alternative_path = str(source_file_path).replace("D:\\Personal\\LegalRAG_OCR\\rag_service\\..\\", "D:\\Personal\\LegalRAG_OCR\\")
                    alternative_path_obj = Path(alternative_path)
                    
                    if alternative_path_obj.exists():
                        logger.info(f"✅ Found file with alternative path: {alternative_path_obj}")
                        source_file_path = alternative_path_obj
                
                # Update source_file with resolved path
                source_file = str(source_file_path)
                
            except Exception as e:
                logger.error(f"⚠️ Error resolving file path: {e}")
                # Keep original path if there's an error
            
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
            # Use Path object for proper path handling
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                logger.warning(f"Source file not found: {file_path}")
                
                # Try to extract filename from path for fallback search
                filename = file_path_obj.name
                logger.info(f"🔍 Fallback - searching for file: {filename}")
                
                # Search for the file in all collections
                base_path = Path(__file__).parent.parent.parent
                collections_path = base_path / "data" / "storage" / "collections"
                
                if collections_path.exists():
                    # Search all collections for the file
                    found_files = list(collections_path.glob(f"**/{filename}"))
                    
                    if found_files:
                        file_path_obj = found_files[0]
                        logger.info(f"✅ Found file via fallback search: {file_path_obj}")
                    else:
                        logger.warning(f"⚠️ Fallback search failed, file not found: {filename}")
                        return self._generate_fallback_content(file_path)
                else:
                    logger.warning(f"⚠️ Collections directory not found: {collections_path}")
                    return self._generate_fallback_content(file_path)
            
            logger.info(f"Loading COMPLETE document content and metadata from: {file_path_obj}")
            
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Extract metadata and content
            metadata = json_data.get('metadata', {})
            content_chunks = json_data.get('content_chunks', [])
            
            # Build complete content với CLEAN FORMATTING - PHASE 3
            complete_parts = []
            
            # 🧹 PHASE 3: NATURAL metadata formatting - tránh raw output
            if metadata:
                natural_metadata_parts = []
                
                # Format từng field thành câu văn tự nhiên
                if metadata.get('fee_vnd') is not None and metadata['fee_vnd'] != 0:
                    fee_text = f"Thủ tục này có phí {metadata['fee_vnd']:,} đồng"
                    if metadata.get('fee_text'):
                        fee_text += f" ({metadata['fee_text']})"
                    natural_metadata_parts.append(fee_text)
                
                if metadata.get('processing_time_text'):
                    natural_metadata_parts.append(f"Thời gian xử lý: {metadata['processing_time_text']}")
                
                if metadata.get('executing_agency'):
                    natural_metadata_parts.append(f"Cơ quan thực hiện: {metadata['executing_agency']}")
                
                if metadata.get('jurisdiction'):
                    natural_metadata_parts.append(f"Thẩm quyền: {metadata['jurisdiction']}")
                
                if metadata.get('applicant_type'):
                    applicant_str = ", ".join(metadata['applicant_type']) if isinstance(metadata['applicant_type'], list) else metadata['applicant_type']
                    natural_metadata_parts.append(f"Đối tượng áp dụng: {applicant_str}")
                
                if metadata.get('requirements_conditions'):
                    natural_metadata_parts.append(f"Yêu cầu: {metadata['requirements_conditions']}")
                
                # Join natural metadata
                if natural_metadata_parts:
                    complete_parts.append("Thông tin thủ tục:")
                    complete_parts.extend(natural_metadata_parts)
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
            return self._generate_fallback_content(file_path)
    
    def _generate_fallback_content(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Generate fallback content when the document file cannot be found
        Returns: (content, metadata)
        """
        logger.info(f"Generating fallback content for: {file_path}")
        
        # Extract document and collection info from path
        try:
            path_parts = str(file_path).replace('\\', '/').split('/')
            
            # Extract collection name and filename
            collection_name = ""
            document_name = ""
            
            if "collections" in path_parts:
                collections_idx = path_parts.index("collections")
                if collections_idx + 1 < len(path_parts):
                    collection_name = path_parts[collections_idx + 1]
            
            if path_parts:
                document_name = path_parts[-1].replace('.json', '')
            
            # Create fallback metadata
            metadata = {
                "document_title": document_name,
                "collection": collection_name,
                "fallback": True
            }
            
            # Create fallback content from nucleus chunk if available
            content = (
                f"Thông tin về '{document_name}' (thuộc bộ '{collection_name}'):\n\n"
                f"Chi tiết thông tin đầy đủ không tìm thấy. "
                f"Vui lòng liên hệ cơ quan hành chính để biết thêm chi tiết."
            )
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"Error generating fallback content: {e}")
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
            
            # 🧹 PHASE 3: NATURAL metadata formatting - tránh raw output
            if metadata:
                natural_metadata_parts = []
                
                # Format từng field thành câu văn tự nhiên
                if metadata.get('fee_vnd') and metadata['fee_vnd'] != 0:
                    fee_text = f"Thủ tục này có phí {metadata['fee_vnd']:,} đồng"
                    if metadata.get('fee_text'):
                        fee_text += f" ({metadata['fee_text']})"
                    natural_metadata_parts.append(fee_text)
                
                if metadata.get('processing_time_text'):
                    natural_metadata_parts.append(f"Thời gian xử lý: {metadata['processing_time_text']}")
                
                if metadata.get('executing_agency'):
                    natural_metadata_parts.append(f"Cơ quan thực hiện: {metadata['executing_agency']}")
                
                if metadata.get('jurisdiction'):
                    natural_metadata_parts.append(f"Thẩm quyền: {metadata['jurisdiction']}")
                
                if metadata.get('applicant_type'):
                    applicant_str = ", ".join(metadata['applicant_type']) if isinstance(metadata['applicant_type'], list) else metadata['applicant_type']
                    natural_metadata_parts.append(f"Đối tượng áp dụng: {applicant_str}")
                
                if metadata.get('requirements_conditions'):
                    natural_metadata_parts.append(f"Yêu cầu: {metadata['requirements_conditions']}")
                
                # Join natural metadata
                if natural_metadata_parts:
                    complete_parts.append("Thông tin thủ tục:")
                    complete_parts.extend(natural_metadata_parts)
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
