import logging
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import hashlib
import json
from ..core.config import settings

logger = logging.getLogger(__name__)

class VectorDBService:
    """Service quản lý ChromaDB và embeddings với hỗ trợ multi-collection"""
    
    def __init__(self, persist_directory: Optional[str] = None, embedding_model: Optional[str] = None, default_collection_name: Optional[str] = None):
        self.persist_directory = persist_directory or str(settings.vectordb_path)
        self.default_collection_name = default_collection_name or settings.chroma_collection_name
        self.embedding_model_name = embedding_model or settings.embedding_model_name
        
        # Validate embedding model name
        if not self.embedding_model_name:
            raise ValueError("Embedding model name cannot be None or empty")
        
        # Khởi tạo ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Load embedding model với retry logic
        self.embedding_model = self._load_embedding_model()
        
        if not self.embedding_model:
            raise RuntimeError(f"Failed to load embedding model: {self.embedding_model_name}")
        
        # Cache for collections
        self.collections_cache = {}
    
    def _load_embedding_model(self):
        """Load embedding model với fallback strategies"""
        # Strategy 1: Load từ explicit local cache path FIRST - CPU for VRAM optimization
        try:
            logger.info(f"Loading embedding model from local cache: {self.embedding_model_name}")
            model = self._load_from_cache_path()
            logger.info(f"✅ Embedding model loaded successfully from local cache on CPU")
            return model
        except Exception as e:
            logger.warning(f"Local cache loading failed: {e}")
        
        # Strategy 2: Force local loading (fallback) - CPU for VRAM optimization
        try:
            logger.info(f"Loading embedding model with local_files_only: {self.embedding_model_name}")
            model = SentenceTransformer(self.embedding_model_name, local_files_only=True, device='cpu')
            logger.info(f"✅ Embedding model loaded successfully with local_files_only on CPU")
            return model
        except Exception as e:
            logger.warning(f"local_files_only loading failed: {e}")
        
        # Strategy 3: Normal loading (last resort - dev only) - CPU for VRAM optimization
        if not settings.hf_hub_offline == "1":
            try:
                logger.info(f"Loading embedding model normally: {self.embedding_model_name}")
                model = SentenceTransformer(self.embedding_model_name, device='cpu')
                logger.info(f"✅ Embedding model loaded successfully with normal loading on CPU")
                return model
            except Exception as e:
                logger.warning(f"Normal loading failed: {e}")
        
        logger.error(f"❌ All strategies failed to load embedding model: {self.embedding_model_name}")
        return None
    
    def _load_from_cache_path(self):
        """Try loading từ explicit local cache path"""
        cache_path = settings.hf_cache_path / "hub"
        model_folders = list(cache_path.glob(f"models--{self.embedding_model_name.replace('/', '--')}"))
        
        if not model_folders:
            raise FileNotFoundError(f"No cached model found for {self.embedding_model_name}")
        
        # Lấy folder đầu tiên (thường chỉ có 1)
        model_folder = model_folders[0]
        snapshots = list((model_folder / "snapshots").iterdir())
        
        if not snapshots:
            raise FileNotFoundError(f"No snapshots found in {model_folder}")
        
        # Load từ snapshot path - FORCE CPU để tiết kiệm VRAM
        snapshot_path = str(snapshots[0])  # Lấy snapshot đầu tiên
        logger.info(f"Loading from explicit path: {snapshot_path}")
        return SentenceTransformer(snapshot_path, device='cpu')
    
    def _get_or_create_collection(self, collection_name: str, metadata: Optional[Dict] = None):
        """Tạo hoặc lấy collection theo tên"""
        if collection_name in self.collections_cache:
            return self.collections_cache[collection_name]
            
        try:
            
            collection = self.client.get_collection(collection_name)
            logger.info(f"Retrieved existing collection: {collection_name}")
        except:
            collection_metadata = metadata or {}
            collection_metadata["hnsw:space"] = "cosine"
            if metadata is None:
                metadata = {"description": f"Collection for {collection_name} documents"}
            
            collection = self.client.create_collection(
                name=collection_name,
                metadata=collection_metadata
            )
            logger.info(f"Created new collection: {collection_name}")
        
        # Cache collection
        self.collections_cache[collection_name] = collection
        return collection
    
    def get_collection(self, collection_name: str):
        """Lấy collection theo tên"""
        return self._get_or_create_collection(collection_name)
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """Liệt kê tất cả collections"""
        collections = self.client.list_collections()
        result = []
        
        for collection in collections:
            try:
                count = collection.count()
                result.append({
                    'name': collection.name,
                    'metadata': collection.metadata,
                    'document_count': count,
                    'total_chunks': count
                })
            except Exception as e:
                logger.error(f"Error getting stats for collection {collection.name}: {e}")
                result.append({
                    'name': collection.name,
                    'metadata': collection.metadata,
                    'document_count': 0,
                    'total_chunks': 0
                })
        
        return result

    def _generate_document_id(self, text: str, source: str, chunk_index: int = 0) -> str:
        """Tạo ID duy nhất cho document chunk"""
        content = f"{source}_{chunk_index}_{text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def embed_text(self, texts: List[str]) -> List[List[float]]:
        """Tạo embeddings cho list texts"""
        if not self.embedding_model:
            raise Exception("Embedding model not loaded")
        
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            # Convert to proper format
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            else:
                return [emb.tolist() if hasattr(emb, 'tolist') else list(emb) for emb in embeddings]
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            raise
    
    def add_documents_to_collection(self, collection_name: str, documents: List[Dict[str, Any]], collection_metadata: Optional[Dict] = None) -> int:
        """Thêm documents vào collection cụ thể - đã cập nhật cho JSON format"""
        collection = self._get_or_create_collection(collection_name, collection_metadata)
        total_chunks = 0
        
        # documents là list chunks từ JSONDocumentProcessor
        if not documents:
            return 0
        
        # Trích xuất content và metadata từ chunks
        chunk_texts = []
        metadatas = []
        ids = []
        
        for chunk_data in documents:
            content = chunk_data.get('content', '')
            if not content:
                continue
            
            # Lấy source info và metadata
            source_info = chunk_data.get('source', {})
            metadata_info = chunk_data.get('metadata', {})
            
            # Tạo metadata đầy đủ cho ChromaDB
            full_metadata = {
                # Source information for traceability
                'file_path': source_info.get('file_path', ''),
                'document_title': source_info.get('document_title', ''),
                'document_code': source_info.get('document_code', ''),
                'section_title': source_info.get('section_title', ''),
                'source_reference': source_info.get('source_reference', ''),
                'chunk_id': source_info.get('chunk_id', ''),
                'chunk_index_num': source_info.get('chunk_index_num', 0),  # Thêm chunk_index_num
                'document_id': source_info.get('document_id', ''),  # Thêm document_id
                'issuing_authority': source_info.get('issuing_authority', ''),
                'executing_agency': source_info.get('executing_agency', ''),
                'effective_date': source_info.get('effective_date', ''),
                
                # Content metadata
                'type': chunk_data.get('type', 'json_section'),
                'keywords': json.dumps(chunk_data.get('keywords', []), ensure_ascii=False),
                'processing_time': metadata_info.get('processing_time', ''),
                'fee_info': metadata_info.get('fee_info', ''),
                'legal_basis': json.dumps(metadata_info.get('legal_basis', []), ensure_ascii=False),
                
                # Collection info
                'collection': collection_name
            }
            
            chunk_texts.append(content)
            metadatas.append(full_metadata)
            
            # Sử dụng chunk_id từ source làm ID, đảm bảo là string
            chunk_id_raw = source_info.get('chunk_id', '')
            if chunk_id_raw:
                unique_id = str(chunk_id_raw)
            else:
                unique_id = self._generate_document_id(
                    content, 
                    source_info.get('file_path', 'unknown'), 
                    len(ids)
                )
            ids.append(unique_id)
        
        if chunk_texts:
            try:
                # Tạo embeddings
                embeddings = self.embed_text(chunk_texts)
                
                # Thêm vào collection
                collection.add(
                    embeddings=embeddings,
                    documents=chunk_texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                total_chunks += len(chunk_texts)
                logger.info(f"Added {len(chunk_texts)} chunks to collection {collection_name}")
                
            except Exception as e:
                logger.error(f"Error adding chunks to collection {collection_name}: {e}")
        
        logger.info(f"Total {total_chunks} chunks added to collection {collection_name}")
        return total_chunks

    def search_in_collection(self, collection_name: str, query: str, top_k: Optional[int] = None, similarity_threshold: Optional[float] = None, where_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Tìm kiếm trong collection cụ thể - sử dụng config defaults"""
        # Sử dụng values từ config nếu không được truyền vào
        if top_k is None:
            top_k = settings.default_search_top_k
        if similarity_threshold is None:
            similarity_threshold = settings.default_similarity_threshold
        try:
            collection = self.get_collection(collection_name)
            
            # Tạo embedding cho query
            query_embedding = self.embed_text([query])[0]
            
            # Convert smart_filters to ChromaDB where clause
            where_clause = self._build_where_clause(where_filter) if where_filter else None
            
            # Base query parameters
            query_params = {
                'query_embeddings': [query_embedding],
                'n_results': top_k,
                'include': ['documents', 'metadatas', 'distances']
            }
            
            # 🔧 DEBUG: Test different approaches  
            if where_clause:
                query_params['where'] = where_clause
                logger.info(f"🔍 Searching WITH filters: {where_clause}")
                
                # DEBUG: Test a simple search first to see if collection has data
                try:
                    simple_results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=min(3, top_k),
                        include=['documents', 'metadatas']
                    )
                    simple_count = 0
                    if simple_results and simple_results.get('documents') and simple_results['documents']:
                        simple_count = len(simple_results['documents'][0])
                    logger.info(f"🔍 Simple search (no filters): {simple_count} results")
                except Exception as e:
                    logger.warning(f"🔍 Simple search failed: {e}")
                
            else:
                logger.info(f"🔍 Search WITHOUT filters")
            
            # Execute the main search with fallback
            try:
                results = collection.query(**query_params)
            except Exception as filter_error:
                logger.warning(f"🔍 Filtered search failed: {filter_error}")
                # Fallback: search without filters
                if where_clause:
                    logger.info("🔄 Falling back to search without filters")
                    fallback_params = {
                        'query_embeddings': [query_embedding],
                        'n_results': top_k,
                        'include': ['documents', 'metadatas', 'distances']
                    }
                    results = collection.query(**fallback_params)
                else:
                    # If no filters were used and still failed, raise the error
                    raise filter_error
            
            # Xử lý kết quả
            formatted_results = []
            if results and results.get('documents') and results['documents']:
                documents = results['documents'][0]
                distances = results.get('distances', [[]])[0]
                metadatas = results.get('metadatas', [[]])[0]
                
                for i, doc in enumerate(documents):
                    distance = distances[i] if i < len(distances) else 1.0
                    similarity = 1 - distance  # Chuyển distance thành similarity
                    
                    if similarity >= similarity_threshold:
                        metadata = metadatas[i] if i < len(metadatas) else {}                        # Parse keywords và legal_basis từ JSON strings
                        keywords = []
                        legal_basis = []
                        try:
                            keywords_str = metadata.get('keywords')
                            if keywords_str and isinstance(keywords_str, str):
                                keywords = json.loads(keywords_str)
                        except:
                            pass
                        
                        try:
                            legal_basis_str = metadata.get('legal_basis')
                            if legal_basis_str and isinstance(legal_basis_str, str):
                                legal_basis = json.loads(legal_basis_str)
                        except:
                            pass
                        
                        # Tạo source information để frontend sử dụng
                        source_info = {
                            'file_path': metadata.get('file_path', ''),
                            'document_title': metadata.get('document_title', ''),
                            'document_code': metadata.get('document_code', ''),
                            'section_title': metadata.get('section_title', ''),
                            'source_reference': metadata.get('source_reference', ''),
                            'chunk_id': metadata.get('chunk_id', ''),
                            'issuing_authority': metadata.get('issuing_authority', ''),
                            'executing_agency': metadata.get('executing_agency', ''),
                            'effective_date': metadata.get('effective_date', '')
                        }
                        
                        formatted_results.append({
                            'content': doc,
                            'metadata': metadata,
                            'source': source_info,
                            'keywords': keywords,
                            'legal_basis': legal_basis,
                            'similarity': similarity,
                            'collection': collection_name,
                            'processing_time': metadata.get('processing_time', ''),
                            'fee_info': metadata.get('fee_info', '')
                        })
            
            logger.info(f"Search in collection {collection_name}: {len(formatted_results)} results above threshold {similarity_threshold}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching in collection {collection_name}: {e}")
            return []
    
    def search_across_collections(self, query: str, collections: Optional[List[str]] = None, top_k: Optional[int] = None, similarity_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Tìm kiếm qua nhiều collections - sử dụng config defaults"""
        # Sử dụng values từ config nếu không được truyền vào
        if top_k is None:
            top_k = settings.default_search_top_k
        if similarity_threshold is None:
            similarity_threshold = settings.cross_collection_similarity_threshold
        if collections is None:
            available_collections = self.list_collections()
            collections = [c['name'] for c in available_collections]
        
        all_results = []
        for collection_name in collections:
            results = self.search_in_collection(collection_name, query, top_k, similarity_threshold)
            all_results.extend(results)
        
        # Sắp xếp theo similarity và lấy top_k
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        return all_results[:top_k]
    
    def get_chunks_by_source(self, collection_name: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Lấy tất cả chunks của một file cụ thể từ collection
        """
        try:
            collection = self.get_collection(collection_name)
            
            # Query tất cả documents trong collection
            results = collection.get(
                include=['documents', 'metadatas', 'embeddings']
            )
            
            if not results or not results.get('ids'):
                return []
            
            # Filter chunks theo file_path
            matching_chunks = []
            ids = results.get('ids') or []
            documents = results.get('documents') or []
            metadatas = results.get('metadatas') or []
            
            for i, doc_id in enumerate(ids):
                if i >= len(documents) or i >= len(metadatas):
                    continue
                    
                document = documents[i]
                metadata = metadatas[i]
                
                if not metadata:
                    continue
                
                # Parse metadata để lấy source info
                source_info: Dict[str, Any] = {}
                if 'source' in metadata:
                    try:
                        source_value = metadata['source']
                        if isinstance(source_value, str):
                            source_info = json.loads(source_value)
                        elif isinstance(source_value, dict):
                            source_info = source_value
                        else:
                            source_info = {'file_path': str(source_value)}
                    except:
                        source_info = {'file_path': str(metadata.get('source', ''))}
                
                # Check if this chunk belongs to the requested file
                chunk_file_path = source_info.get('file_path', source_info.get('document_title', ''))
                
                if isinstance(chunk_file_path, str) and (chunk_file_path == file_path or file_path in chunk_file_path):
                    chunk_data = {
                        'id': doc_id,
                        'content': document,
                        'metadata': metadata,
                        'source': source_info,
                        'collection': collection_name
                    }
                    matching_chunks.append(chunk_data)
            
            logger.info(f"Found {len(matching_chunks)} chunks for file: {file_path}")
            return matching_chunks
            
        except Exception as e:
            logger.error(f"Error getting chunks by source {file_path} from {collection_name}: {e}")
            return []
    
    def clear_collection(self, collection_name: str) -> bool:
        """Xóa tất cả data trong collection"""
        try:
            collection = self.get_collection(collection_name)
            results = collection.get()
            if results['ids']:
                collection.delete(ids=results['ids'])
                logger.info(f"Cleared collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection {collection_name}: {e}")
            return False
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Lấy thống kê của collection"""
        try:
            collection = self.get_collection(collection_name)
            count = collection.count()
            
            return {
                'collection_name': collection_name,
                'document_count': count,
                'total_chunks': count,
                'embedding_model': self.embedding_model_name
            }
        except Exception as e:
            logger.error(f"Error getting stats for collection {collection_name}: {e}")
            return {
                'collection_name': collection_name,
                'document_count': 0,
                'total_chunks': 0,
                'embedding_model': self.embedding_model_name
            }
    
    def _build_where_clause(self, smart_filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert smart_filters from router to ChromaDB where clause
        
        ChromaDB requires $and operator for multiple conditions
        """
        # 🔍 DEBUG: Log input filters
        logger.info(f"🔍 _build_where_clause input: {smart_filters}")
        
        conditions = []
        
        try:
            # 🎯 PRIORITY STRATEGY: Use exact_title ONLY if available (highest precision)
            if 'exact_title' in smart_filters and smart_filters['exact_title']:
                exact_titles = smart_filters['exact_title']
                logger.info(f"🔍 Found exact_title: {exact_titles}, type: {type(exact_titles)}")
                if isinstance(exact_titles, list) and exact_titles:
                    # Đảm bảo list không rỗng và có giá trị hợp lệ
                    valid_titles = [title for title in exact_titles if title and title.strip()]
                    if valid_titles:
                        if len(valid_titles) == 1:
                            filter_result = {"document_title": valid_titles[0]}
                        else:
                            filter_result = {"document_title": {"$in": valid_titles}}
                        # 🔥 HIGH PRECISION: If we have exact title, use ONLY that filter
                        logger.info(f"🎯 Using HIGH PRECISION filter: {filter_result}")
                        return filter_result
                elif isinstance(exact_titles, str) and exact_titles.strip():
                    filter_result = {"document_title": exact_titles.strip()}
                    logger.info(f"🎯 Using HIGH PRECISION filter (string): {filter_result}")
                    return filter_result
            
            # 🔥 NEW: Support direct document_title filter (for forced routing)
            if 'document_title' in smart_filters and smart_filters['document_title']:
                doc_title = smart_filters['document_title']
                if isinstance(doc_title, str) and doc_title.strip():
                    logger.info(f"🎯 Using FORCED document filter: {doc_title}")
                    return {"document_title": doc_title.strip()}
                elif isinstance(doc_title, list) and doc_title:
                    logger.info(f"🎯 Using FORCED document filter: {doc_title}")
                    return {"document_title": {"$in": [t.strip() for t in doc_title if t.strip()]}}
            
            # 🎯 FALLBACK: If no exact_title or document_title, use other filters
            # Procedure code matching
            if 'procedure_code' in smart_filters and smart_filters['procedure_code']:
                codes = smart_filters['procedure_code']
                if isinstance(codes, list) and codes:
                    if len(codes) == 1:
                        conditions.append({'document_code': codes[0]})
                    else:
                        conditions.append({'document_code': {"$in": codes}})
            
            # Agency matching
            if 'agency' in smart_filters and smart_filters['agency']:
                agencies = smart_filters['agency']
                if isinstance(agencies, list) and agencies:
                    if len(agencies) == 1:
                        conditions.append({'executing_agency': agencies[0]})
                    else:
                        conditions.append({'executing_agency': {"$in": agencies}})
            
            # Cost type filtering - không có trong metadata, bỏ qua
            # if 'cost_type' in smart_filters and smart_filters['cost_type']:
            #     cost_types = smart_filters['cost_type']
            #     if isinstance(cost_types, list) and cost_types:
            #         if len(cost_types) == 1:
            #             conditions.append({'cost_type': cost_types[0]})
            #         else:
            #             conditions.append({'cost_type': {"$in": cost_types}})
            
            # Processing speed filtering - không có trong metadata, bỏ qua
            # if 'processing_speed' in smart_filters and smart_filters['processing_speed']:
            #     speeds = smart_filters['processing_speed']
            #     if isinstance(speeds, list) and speeds:
            #         if len(speeds) == 1:
            #             conditions.append({'processing_speed': speeds[0]})
            #         else:
            #             conditions.append({'processing_speed': {"$in": speeds}})
            
            # Agency level filtering - không có trong metadata, bỏ qua
            # if 'agency_level' in smart_filters and smart_filters['agency_level']:
            #     levels = smart_filters['agency_level']
            #     if isinstance(levels, list) and levels:
            #         if len(levels) == 1:
            #             conditions.append({'agency_level': levels[0]})
            #         else:
            #             conditions.append({'agency_level': {"$in": levels}})
            
            # Build final where clause
            if len(conditions) == 0:
                logger.info(f"🔍 No conditions found, returning empty filter")
                return {}
            elif len(conditions) == 1:
                where_clause = conditions[0]
            else:
                where_clause = {"$and": conditions}
                        
            logger.info(f"🔧 Built where clause with {len(conditions)} conditions: {where_clause}")
            return where_clause
            
        except Exception as e:
            logger.warning(f"⚠️ Error building where clause from {smart_filters}: {e}")
            logger.info(f"🔍 Returning empty filter due to error")
            return {}
    
    def collection_exists(self, collection_name: str) -> bool:
        """Kiểm tra collection có tồn tại không"""
        try:
            collection = self.client.get_collection(collection_name)
            return collection.count() > 0
        except:
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Xóa collection"""
        try:
            self.client.delete_collection(collection_name)
            if collection_name in self.collections_cache:
                del self.collections_cache[collection_name]
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
