import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class JSONDocumentProcessor:
    """Processor để xử lý các file JSON đã được cấu trúc hóa thay vì file Word"""
    
    def __init__(self):
        self.supported_extensions = ['.json']
        
        # Collection mappings - tương tự như trước
        self.collection_mappings = {
            'quy_trinh_cap_ho_tich_cap_xa': 'ho_tich_cap_xa',
            'ho_tich_cap_xa_moi_nhat': 'ho_tich_cap_xa',
            'quy_trinh_chung_thuc': 'chung_thuc',
            'quy_trinh_nb_chung_thuc_dung_chung': 'chung_thuc',
            'quy_trinh_nuoi_con_nuoi': 'nuoi_con_nuoi',
            'iso_ncn_moi': 'nuoi_con_nuoi',
        }
    
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
    
    def process_directory(self, directory_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Process all JSON documents in directory, organized by collections"""
        collections_data = {}
        
        try:
            json_files = list(Path(directory_path).rglob("*.json"))
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
            logger.error(f"Error processing directory {directory_path}: {e}")
            return {}
    
    def get_collection_metadata(self, collection_name: str) -> Dict[str, str]:
        """Lấy metadata cho collection"""
        collection_info = {
            'ho_tich_cap_xa': {
                'name': 'Hộ tịch cấp xã',
                'description': 'Quy trình đăng ký hộ tịch cấp xã: khai sinh, kết hôn, khai tử, giám hộ',
                'keywords': 'hộ tịch, cấp xã, khai sinh, kết hôn, khai tử, giám hộ, trích lục, bản sao'
            },
            'chung_thuc': {
                'name': 'Chứng thực',
                'description': 'Dịch vụ chứng thực các loại giấy tờ, hợp đồng, giao dịch',
                'keywords': 'chứng thực, hợp đồng, giao dịch, chữ ký, bản sao, di chúc'
            },
            'nuoi_con_nuoi': {
                'name': 'Nuôi con nuôi',
                'description': 'Thủ tục liên quan đến việc nuôi con nuôi và các vấn đề liên quan',
                'keywords': 'nuôi con nuôi, nhận con nuôi, giấy phép nuôi con nuôi'
            }
        }
        
        return collection_info.get(collection_name, {
            'name': collection_name,
            'description': 'General collection',
            'keywords': ''
        })
    
    def get_document_summary(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo summary của document để dễ tra cứu"""
        metadata = json_data.get('metadata', {})
        content_chunks = json_data.get('content_chunks', [])
        
        return {
            'title': metadata.get('title', ''),
            'code': metadata.get('code', ''),
            'issuing_authority': metadata.get('issuing_authority', ''),
            'effective_date': metadata.get('effective_date', ''),
            'executing_agency': metadata.get('executing_agency', ''),
            'applicant_type': metadata.get('applicant_type', []),
            'processing_time': metadata.get('processing_time_text', ''),
            'fee_info': metadata.get('fee_text', ''),
            'total_sections': len(content_chunks),
            'sections': [
                {
                    'title': chunk.get('section_title', ''),
                    'reference': chunk.get('source_reference', ''),
                    'keywords': chunk.get('keywords', [])
                }
                for chunk in content_chunks
            ]
        }
