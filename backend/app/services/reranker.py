import logging
import os
import time
import torch
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import CrossEncoder
import numpy as np
from ..core.config import settings

logger = logging.getLogger(__name__)

class RerankerService:
    """Service quản lý Vietnamese Reranker model - VRAM optimized với on-demand loading"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.reranker_model_name
        self.model = None
        self.model_loaded = False
        
        # VRAM Optimization: Load model khi cần thiết
        
    def get_optimal_device(self) -> str:
        """Get optimal device for reranker"""
        if torch.cuda.is_available():
            logger.info("🎮 CUDA available - using GPU for reranker")
            return 'cuda'
        else:
            logger.info("💻 CUDA not available - falling back to CPU")
            return 'cpu'
        # self._load_model()  # Comment out để load on-demand
    
    def _load_model(self):
        """Load model từ cache local hoặc download nếu cần - GPU for optimal performance"""
        if self.model_loaded:
            return
            
        try:
            logger.info(f"Loading reranker model: {self.model_name}")
            
            # Thử load từ local cache trước - sử dụng GPU với max_length=2304 theo documentation
            local_model_path = self._get_local_model_path()
            if local_model_path and local_model_path.exists():
                logger.info(f"Found local model at: {local_model_path}")
                try:
                    # 🚀 CORRECT CONFIG: max_length=2304 theo Vietnamese_Reranker documentation
                    # (256 for query + 2048 for passages = 2304 total)
                    # Model config có max_position_embeddings=8194 nhưng trained với 2304
                    # Tokenizer có model_max_length=8192 nhưng optimal performance ở 2304
                    
                    # Sử dụng model_kwargs để optimize memory và performance
                    model_kwargs = {
                        'torch_dtype': 'auto'  # Sử dụng dtype từ model config (float32)
                    }
                    
                    self.model = CrossEncoder(
                        str(local_model_path), 
                        device=self.get_optimal_device(),  # ← Dynamic device selection
                        max_length=2304,
                        trust_remote_code=False,  # Security best practice  
                        model_kwargs=model_kwargs
                    )
                    self.model_loaded = True
                    logger.info(f"✅ Reranker model loaded from local cache on {self.get_optimal_device().upper()} (max_length=2304, trained optimal)")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load from local cache on CPU: {e}")
            
            # Fallback: load từ HuggingFace với max_length=2304 theo documentation
            logger.info("Loading from HuggingFace (may download) on CPU with correct max_length=2304 (trained optimal)")
            # Model hỗ trợ max 8192 tokens nhưng trained với 2304 để đảm bảo quality
            
            # Sử dụng model_kwargs để optimize memory và performance
            model_kwargs = {
                'torch_dtype': 'auto'  # Sử dụng dtype từ model config (float32)
            }
            
            self.model = CrossEncoder(
                self.model_name, 
                device=self.get_optimal_device(),  # ← Dynamic device selection
                max_length=2304,
                trust_remote_code=False,  # Security best practice
                model_kwargs=model_kwargs
            )
            self.model_loaded = True
            logger.info(f"✅ Reranker model loaded from HuggingFace on {self.get_optimal_device().upper()} (max_length=2304, trained optimal)")
            
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            self.model = None
            self.model_loaded = False
            raise
    
    def unload_model(self):
        """Unload reranker model để giải phóng VRAM"""
        if self.model is not None:
            logger.info("🔄 Unloading Reranker model to free VRAM...")
            del self.model
            self.model = None
            self.model_loaded = False
            
            # Force garbage collection và CUDA cache clear
            import gc
            gc.collect()
            
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("✅ CUDA cache cleared")
            except ImportError:
                pass
                
            logger.info("✅ Reranker model unloaded, VRAM freed")
    
    def ensure_loaded(self):
        """Ensure reranker model is loaded"""
        if not self.model_loaded or self.model is None:
            self._load_model()
    
    def is_model_loaded(self) -> bool:
        """Check if reranker model is loaded"""
        return self.model_loaded and self.model is not None
    
    def _get_local_model_path(self):
        """Tìm đường dẫn local model nếu có"""
        try:
            # Sử dụng config path
            cache_hub_path = settings.hf_cache_path / "hub"
            model_dir = cache_hub_path / "models--AITeamVN--Vietnamese_Reranker"
            
            if model_dir.exists():
                # Tìm snapshot directory
                snapshots_dir = model_dir / "snapshots"
                if snapshots_dir.exists():
                    # Lấy snapshot mới nhất
                    snapshot_dirs = [d for d in snapshots_dir.iterdir() if d.is_dir()]
                    if snapshot_dirs:
                        latest_snapshot = max(snapshot_dirs, key=lambda x: x.stat().st_mtime)
                        logger.info(f"Found local snapshot: {latest_snapshot}")
                        return latest_snapshot
            
            return None
        except Exception as e:
            logger.warning(f"Error finding local model path: {e}")
            return None
    
    def rerank_documents(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        top_k: Optional[int] = None,
        router_confidence: Optional[float] = None,
        router_confidence_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank danh sách documents dựa trên độ liên quan với query
        
        Args:
            query: Câu hỏi cần tìm
            documents: Danh sách documents cần rerank
            top_k: Số lượng documents tốt nhất cần trả về (nếu None thì trả về tất cả)
            router_confidence: Confidence score từ router (0.0-1.0)
            router_confidence_level: Level từ router ('low', 'medium', 'high')
        
        Returns:
            Danh sách documents đã được sắp xếp lại theo độ liên quan
        """
        # VRAM Optimization: Ensure model is loaded
        self.ensure_loaded()
        
        if not self.model:
            logger.warning("Reranker model not loaded, returning original order")
            return documents[:top_k] if top_k else documents
        
        if not documents:
            return []
        
        # 🛡️ ROUTER TRUST MODE: Khi router có HIGH confidence, tin tưởng router hơn
        trust_router = (router_confidence_level == 'high' and router_confidence and router_confidence >= 0.85)
        if trust_router:
            logger.info(f"🛡️ ROUTER TRUST MODE: Router confidence {router_confidence:.3f} (HIGH) - Minimal rerank interference")
        
        try:
            # 🔍 DEBUG: Log số lượng documents và thời gian rerank
            rerank_start_time = time.time()
            logger.info(f"🔍 RERANK QUERY: '{query}' ({len(query)} chars)")
            logger.info(f"🔢 RERANK INPUT: {len(documents)} documents to process")
            
            # 🚀 PERFORMANCE OPTIMIZATION: Loại bỏ CPU preprocessing 
            # Chuẩn bị pairs (query, document_content) trực tiếp cho reranker
            pairs = []
            for i, doc in enumerate(documents):
                content = doc['content']
                
                # 🚀 CORRECT PROCESSING: Phù hợp với max_length=2304 (256 query + 2048 passage)
                # CrossEncoder sẽ tự xử lý với max_length=2304 đã được set
                cleaned_content = content.replace("**", "").replace("*", "").replace("#", "")
                cleaned_content = " ".join(cleaned_content.split())  # Normalize whitespace
                
                # Truncate theo documentation: max ~2048 tokens cho passage (≈ 6000 chars Vietnamese)
                if len(cleaned_content) > 6000:  # Soft limit trước khi tokenization
                    cleaned_content = cleaned_content[:6000] + "..."
                
                logger.info(f"🔍 RERANK DOC[{i}]: {len(cleaned_content)} chars")
                pairs.append((query, cleaned_content))
            
            # Tính rerank scores
            logger.info(f"🔥 RERANKING {len(documents)} documents with optimized settings...")
            scores = self.model.predict(pairs)
            rerank_time = time.time() - rerank_start_time
            logger.info(f"⏱️ RERANK COMPLETED in {rerank_time:.2f}s ({len(documents)} docs)")
            
            # Gán điểm rerank vào mỗi document
            reranked_docs = []
            for doc, score in zip(documents, scores):
                doc_copy = doc.copy()
                doc_copy['rerank_score'] = float(score)
                reranked_docs.append(doc_copy)
            
            # Sắp xếp theo rerank score giảm dần
            reranked_docs.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            # Log thông tin về top document
            if reranked_docs:
                top_doc = reranked_docs[0]
                logger.info(f"Top document after reranking: score={top_doc['rerank_score']:.4f}, "
                          f"similarity={top_doc.get('similarity', 'N/A')}")
                
                # 🛡️ ROUTER TRUST MODE: Không trigger conservative strategy khi router HIGH confidence
                if trust_router:
                    logger.info(f"🛡️ TRUSTING ROUTER: Accepting rerank results without conservative override (router: {router_confidence:.3f})")
                elif top_doc['rerank_score'] < 0.2:
                    logger.warning(f"⚠️  LOW RERANK SCORE ({top_doc['rerank_score']:.4f}) - Conservative strategy may be triggered")
            
            # Trả về top_k documents nếu được chỉ định
            if top_k:
                return reranked_docs[:top_k]
            
            return reranked_docs
            
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            # Fallback về sắp xếp theo similarity score ban đầu
            return sorted(documents, key=lambda x: x.get('similarity', 0), reverse=True)[:top_k] if top_k else documents
    
    # 🗑️ REMOVED: CPU intensive preprocessing functions
    # _extract_query_keywords() và _extract_relevant_content() đã được loại bỏ
    # để tối ưu hóa performance và để GPU CrossEncoder tự xử lý
    
    def get_consensus_document(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        top_k: int = 20,
        consensus_threshold: float = 0.3,
        min_rerank_score: float = 0.03,
        router_confidence: Optional[float] = None,
        router_confidence_level: Optional[str] = None,
        router_selected_document: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Tìm document có consensus cao nhất dựa trên nhiều chunks được rerank
        
        Args:
            query: Câu hỏi từ user
            documents: Danh sách documents để rerank
            top_k: Số lượng chunks tốt nhất để xem xét
            consensus_threshold: Ngưỡng consensus tối thiểu (0.0-1.0)
            min_rerank_score: Điểm rerank tối thiểu để xem xét chunk
            router_confidence: Confidence score từ router (0.0-1.0)
            router_confidence_level: Mức độ confidence từ router ('low', 'medium', 'high')
            router_selected_document: Document ID mà router đã chọn (VD: 'DOC_011')
        
        Returns:
            Document chunk tốt nhất hoặc None
        """
        if not documents:
            return None
        
        # ⚡ ROUTER TRUST MODE: Nếu router có confidence cao, tin tưởng router decision
        if router_confidence and router_confidence > 0.85:
            logger.info(f"🎯 ROUTER TRUST MODE: High confidence {router_confidence:.3f} > 0.85 - Using router decision")
            
            # 🔍 FIXED: Tìm chunk từ document mà router đã chọn
            if router_selected_document:
                router_chunk = self._find_chunk_from_document(documents, router_selected_document)
                if router_chunk:
                    logger.info(f"✅ Found chunk from router-selected document: {router_selected_document}")
                    return router_chunk
                else:
                    logger.warning(f"⚠️ No chunk found from router-selected document {router_selected_document}, falling back to first document")
            
            # Fallback: Trả về document đầu tiên
            return documents[0] if documents else None
            
        # Bước 1: Rerank tất cả documents và lấy top-k
        reranked = self.rerank_documents(query, documents, top_k=top_k)

    def _analyze_document_consensus(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phân tích xem chunks thuộc documents nào và với tần suất ra sao
        
        Returns:
            Dict mapping document_id -> {chunks: [...], scores: [...], best_chunk: chunk}
        """
        document_groups = {}
        
        for chunk in chunks:
            # Tìm document identifier từ chunk metadata
            doc_id = self._extract_document_id(chunk)
            
            if doc_id not in document_groups:
                document_groups[doc_id] = {
                    'chunks': [],
                    'scores': [],
                    'best_chunk': None,
                    'best_score': -1
                }
            
            # Thêm chunk vào group
            rerank_score = chunk.get('rerank_score', 0)
            document_groups[doc_id]['chunks'].append(chunk)
            document_groups[doc_id]['scores'].append(rerank_score)
            
            # Cập nhật best chunk cho document này
            if rerank_score > document_groups[doc_id]['best_score']:
                document_groups[doc_id]['best_score'] = rerank_score
                document_groups[doc_id]['best_chunk'] = chunk
                
        return document_groups

    def _extract_document_id(self, chunk: Dict[str, Any]) -> str:
        """
        Trích xuất document identifier từ chunk metadata
        Thử nhiều cách để tìm unique document ID
        """
        # Thử cách 1: source.file_path
        if 'source' in chunk and isinstance(chunk['source'], dict):
            if 'file_path' in chunk['source']:
                return chunk['source']['file_path']
            if 'document_title' in chunk['source']:
                return chunk['source']['document_title']
        
        # Thử cách 2: metadata.source
        if 'metadata' in chunk and isinstance(chunk['metadata'], dict):
            if 'source' in chunk['metadata']:
                source = chunk['metadata']['source']
                if isinstance(source, dict):
                    if 'file_path' in source:
                        return source['file_path']
                    if 'document_title' in source:
                        return source['document_title']
                elif isinstance(source, str):
                    return source
        
        # Thử cách 3: document_title trực tiếp
        if 'document_title' in chunk:
            return chunk['document_title']
            
        # Fallback: dùng id hoặc content hash
        if 'id' in chunk:
            return f"doc_from_chunk_{chunk['id']}"
            
        # Last resort: hash content
        content = chunk.get('content', '')
        import hashlib
        return f"doc_hash_{hashlib.md5(content.encode()).hexdigest()[:8]}"

    def _find_best_consensus(
        self, 
        document_analysis: Dict[str, Any], 
        consensus_threshold: float,
        total_chunks: int
    ) -> Optional[Dict[str, Any]]:
        """
        Tìm document có consensus ratio cao nhất và đạt threshold
        
        Returns:
            Best consensus info hoặc None nếu không có document nào đạt threshold
        """
        best_consensus = None
        
        for doc_id, info in document_analysis.items():
            chunk_count = len(info['chunks'])
            consensus_ratio = chunk_count / total_chunks
            
            logger.info(f"📊 Document '{doc_id}': {chunk_count}/{total_chunks} chunks "
                       f"(ratio: {consensus_ratio:.2f}, threshold: {consensus_threshold})")
            
            # Kiểm tra xem có đạt threshold không
            if consensus_ratio >= consensus_threshold:
                if (best_consensus is None or 
                    consensus_ratio > best_consensus['consensus_ratio'] or
                    (consensus_ratio == best_consensus['consensus_ratio'] and 
                     info['best_score'] > best_consensus['best_score'])):
                    
                    best_consensus = {
                        'document_id': doc_id,
                        'chunk_count': chunk_count,
                        'consensus_ratio': consensus_ratio,
                        'best_chunk': info['best_chunk'],
                        'best_score': info['best_score'],
                        'all_chunks': info['chunks']
                    }
        
        return best_consensus
    
    # ❌ DEPRECATED METHOD REMOVED
    # def get_best_document(self, query: str, documents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    #     """
    #     DEPRECATED: Use get_consensus_document() instead for better accuracy
    #     """
    #     pass
        return reranked[0] if reranked else None
    
    def _find_chunk_from_document(self, documents: List[Dict[str, Any]], target_document_id: str) -> Optional[Dict[str, Any]]:
        """
        Tìm chunk từ document cụ thể mà router đã chọn
        
        Args:
            documents: List các chunks từ vector search
            target_document_id: Document ID mà router chọn (VD: 'DOC_011')
        
        Returns:
            Chunk từ target document hoặc None
        """
        try:
            for doc in documents:
                # Check multiple possible locations for document ID
                doc_id = None
                
                # Method 1: Check metadata.source field
                if 'metadata' in doc and 'source' in doc['metadata']:
                    source = doc['metadata']['source']
                    if isinstance(source, dict) and 'file_path' in source:
                        file_path = source['file_path']
                        # Extract DOC_XXX from file path
                        import re
                        match = re.search(r'DOC_(\d+)', file_path)
                        if match:
                            doc_id = f"DOC_{match.group(1)}"
                
                # Method 2: Check direct metadata fields
                if not doc_id and 'metadata' in doc:
                    metadata = doc['metadata']
                    for key in ['document_id', 'doc_id', 'source_document']:
                        if key in metadata:
                            potential_id = metadata[key]
                            if target_document_id in str(potential_id):
                                doc_id = target_document_id
                                break
                
                # Method 3: Check source field directly
                if not doc_id and 'source' in doc:
                    source_str = str(doc['source'])
                    if target_document_id in source_str:
                        doc_id = target_document_id
                
                # If found matching document, return it
                if doc_id == target_document_id:
                    logger.info(f"✅ Found chunk from document {target_document_id}: {doc.get('id', 'Unknown ID')}")
                    return doc
            
            logger.warning(f"❌ No chunk found from document {target_document_id} in {len(documents)} available chunks")
            return None
            
        except Exception as e:
            logger.error(f"Error finding chunk from document {target_document_id}: {e}")
            return None

    def is_loaded(self) -> bool:
        """Kiểm tra xem model đã được load chưa"""
        return self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Lấy thông tin về model"""
        return {
            'model_name': self.model_name,
            'is_loaded': self.is_loaded(),
            'model_type': 'CrossEncoder' if self.model else None
        }
