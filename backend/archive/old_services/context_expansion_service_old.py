import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class ContextExpansionService:
    """Service mở rộng ngữ cảnh xung quanh chunk hạt nhân"""
    
    def __init__(self, vectordb_service):
        self.vectordb_service = vectordb_service
    
    def expand_context(
        self, 
        core_document: Dict[str, Any], 
        expansion_size: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Mở rộng ngữ cảnh xung quanh document hạt nhân bằng cách lấy các chunks trước và sau
        
        Args:
            core_document: Document hạt nhân (có rerank score cao nhất)
            expansion_size: Số lượng chunks trước và sau cần lấy (mặc định là 1)
        
        Returns:
            List các documents đã được mở rộng theo thứ tự [trước...hạt nhân...sau]
        """
        try:
            # Lấy thông tin metadata của core document
            source_info = core_document.get('source', {})
            collection_name = core_document.get('collection', 'unknown')
            chunk_index_num = core_document.get('metadata', {}).get('chunk_index_num')
            document_id = source_info.get('document_id') or source_info.get('file_path', '')
            
            logger.info(f"Expanding context for document in collection '{collection_name}' "
                       f"with chunk_index_num {chunk_index_num}")
            
            if chunk_index_num is None or not document_id:
                logger.warning("Cannot expand context: missing chunk_index_num or document_id")
                return [core_document]
            
            # Tìm các chunks liền kề
            expanded_chunks = self._find_adjacent_chunks(
                collection_name=collection_name,
                document_id=document_id,
                core_chunk_index=chunk_index_num,
                expansion_size=expansion_size
            )
            
            if not expanded_chunks:
                logger.warning("No adjacent chunks found, returning only core document")
                return [core_document]
            
            # Sắp xếp các chunks theo chunk_index_num
            expanded_chunks.sort(key=lambda x: x.get('metadata', {}).get('chunk_index_num', 0))
            
            logger.info(f"Context expanded: found {len(expanded_chunks)} chunks "
                       f"(including core document)")
            
            return expanded_chunks
            
        except Exception as e:
            logger.error(f"Error expanding context: {e}")
            return [core_document]
    
    def _find_adjacent_chunks(
        self,
        collection_name: str,
        document_id: str,
        core_chunk_index: int,
        expansion_size: int
    ) -> List[Dict[str, Any]]:
        """
        Tìm các chunks liền kề trong cùng document
        
        Args:
            collection_name: Tên collection
            document_id: ID của document  
            core_chunk_index: Index của chunk hạt nhân
            expansion_size: Số chunks trước và sau cần lấy
        
        Returns:
            List các chunks liền kề (bao gồm cả core chunk)
        """
        try:
            # Tính toán range cần tìm
            start_index = max(0, core_chunk_index - expansion_size)
            end_index = core_chunk_index + expansion_size
            
            # Tìm tất cả chunks trong document này
            all_chunks = self._get_document_chunks(collection_name, document_id)
            
            # Lọc chunks trong range cần thiết
            adjacent_chunks = []
            for chunk in all_chunks:
                chunk_index_num = chunk.get('metadata', {}).get('chunk_index_num')
                if chunk_index_num is not None and start_index <= chunk_index_num <= end_index:
                    adjacent_chunks.append(chunk)
            
            logger.info(f"Found {len(adjacent_chunks)} chunks in range [{start_index}, {end_index}] "
                       f"for document {document_id}")
            
            return adjacent_chunks
            
        except Exception as e:
            logger.error(f"Error finding adjacent chunks: {e}")
            return []
    
    def _get_document_chunks(self, collection_name: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Lấy tất cả chunks của một document cụ thể
        
        Args:
            collection_name: Tên collection
            document_id: ID của document
        
        Returns:
            List tất cả chunks của document
        """
        try:
            # Lấy collection
            collection = self.vectordb_service._get_or_create_collection(collection_name)
            
            # Query tất cả chunks của document này
            # Sử dụng where clause để lọc theo document_id
            results = collection.get(
                where={"$or": [
                    {"document_id": document_id},
                    {"file_path": document_id}
                ]},
                include=["documents", "metadatas"]
            )
            
            # Chuyển đổi kết quả về format chuẩn
            chunks = []
            if results and results.get('documents') and results.get('metadatas'):
                documents = results.get('documents') or []
                metadatas = results.get('metadatas') or []
                ids = results.get('ids') or []
                
                # Ensure we have valid lists
                if isinstance(documents, list) and isinstance(metadatas, list):
                    for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
                        chunk = {
                            'content': str(doc) if doc else "",
                            'metadata': dict(metadata) if metadata else {},
                            'collection': collection_name,
                            'id': ids[i] if isinstance(ids, list) and i < len(ids) else None
                        }
                        
                        # Thêm source info từ metadata
                        if metadata:
                            chunk['source'] = {
                                'document_id': metadata.get('document_id', ''),
                                'file_path': metadata.get('file_path', ''),
                                'document_title': metadata.get('document_title', ''),
                                'section_title': metadata.get('section_title', ''),
                                'source_reference': metadata.get('source_reference', ''),
                                'document_code': metadata.get('document_code', ''),
                                'issuing_authority': metadata.get('issuing_authority', ''),
                                'executing_agency': metadata.get('executing_agency', ''),
                                'effective_date': metadata.get('effective_date', '')
                            }
                        
                        chunks.append(chunk)
            
            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting document chunks: {e}")
            return []
    
    def create_coherent_context(self, expanded_chunks: List[Dict[str, Any]]) -> str:
        """
        Tạo ngữ cảnh mạch lạc từ các chunks đã mở rộng
        
        Args:
            expanded_chunks: List các chunks theo thứ tự
        
        Returns:
            Chuỗi ngữ cảnh liền mạch
        """
        if not expanded_chunks:
            return ""
        
        try:
            # Sắp xếp chunks theo chunk_index để đảm bảo thứ tự đúng
            sorted_chunks = sorted(
                expanded_chunks, 
                key=lambda x: x.get('metadata', {}).get('chunk_index', 0)
            )
            
            # Lấy thông tin document từ chunk đầu tiên
            first_chunk = sorted_chunks[0]
            source_info = first_chunk.get('source', {})
            
            # Tạo header cho context
            document_title = source_info.get('document_title', 'unknown')
            section_title = source_info.get('section_title', '')
            source_reference = source_info.get('source_reference', '')
            
            context_header = f"Từ: {document_title}"
            if section_title:
                context_header += f" - {section_title}"
            if source_reference:
                context_header += f" ({source_reference})"
            
            # Nối nội dung các chunks
            contents = [chunk['content'].strip() for chunk in sorted_chunks]
            coherent_content = " ".join(contents)
            
            # Tạo context hoàn chỉnh
            final_context = f"{context_header}\nNội dung: {coherent_content}"
            
            logger.info(f"Created coherent context from {len(sorted_chunks)} chunks, "
                       f"total length: {len(coherent_content)} characters")
            
            return final_context
            
        except Exception as e:
            logger.error(f"Error creating coherent context: {e}")
            # Fallback: chỉ trả về nội dung chunk đầu tiên
            return expanded_chunks[0]['content'] if expanded_chunks else ""
