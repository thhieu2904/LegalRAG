import logging
import os
import time
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
        # self._load_model()  # Comment out để load on-demand
    
    def _load_model(self):
        """Load model từ cache local hoặc download nếu cần - GPU for optimal performance"""
        if self.model_loaded:
            return
            
        try:
            logger.info(f"Loading reranker model: {self.model_name}")
            
            # Thử load từ local cache trước - sử dụng GPU với max_length=512
            local_model_path = self._get_local_model_path()
            if local_model_path and local_model_path.exists():
                logger.info(f"Found local model at: {local_model_path}")
                try:
                    # 🚀 PERFORMANCE OPTIMIZATION: Giới hạn max_length=512 để tăng tốc
                    self.model = CrossEncoder(str(local_model_path), device='cuda:0', max_length=512)
                    self.model_loaded = True
                    logger.info("✅ Reranker model loaded from local cache on GPU (max_length=512)")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load from local cache on GPU: {e}")
            
            # Fallback: load từ HuggingFace với max_length=512
            logger.info("Loading from HuggingFace (may download) on GPU with optimized settings")
            self.model = CrossEncoder(self.model_name, device='cuda:0', max_length=512)
            self.model_loaded = True
            logger.info("✅ Reranker model loaded from HuggingFace on GPU (max_length=512)")
            
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
                
                # 🚀 MINIMAL PROCESSING: Chỉ truncate và clean cơ bản
                # Để CrossEncoder tự xử lý với max_length=512 đã được set
                cleaned_content = content.replace("**", "").replace("*", "").replace("#", "")
                cleaned_content = " ".join(cleaned_content.split())  # Normalize whitespace
                
                # Truncate nếu quá dài (backup cho max_length limit)
                if len(cleaned_content) > 1000:  # Soft limit trước khi tokenization
                    cleaned_content = cleaned_content[:1000] + "..."
                
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
        top_k: int = 5,
        consensus_threshold: float = 0.6,  # 3/5 = 0.6
        min_rerank_score: float = -0.5  # LOWER for legal documents (cross-encoder can give negative scores)
    ) -> Optional[Dict[str, Any]]:
        """
        🎯 ENHANCED RERANKING: Tìm document dựa trên consensus của top-k chunks
        
        Thay vì chỉ lấy 1 chunk cao nhất (dễ sai lệch), method này:
        1. Lấy top-k chunks sau rerank (default: 5)
        2. Phân tích xem chunks nào thuộc document nào
        3. Tìm document có >= consensus_threshold chunks trong top-k
        4. Trả về document có consensus cao nhất
        5. Xử lý trường hợp "scattered chunks" (chunks từ các documents hoàn toàn khác nhau)
        
        Args:
            query: Câu hỏi cần tìm
            documents: Danh sách documents cần đánh giá
            top_k: Số chunks hàng đầu để phân tích consensus (default: 5)
            consensus_threshold: Tỷ lệ minimum chunks cùng document (default: 0.6 = 3/5)
            min_rerank_score: Score minimum để xem xét (đã điều chỉnh cho văn bản pháp luật)
        
        Returns:
            Document có consensus cao nhất hoặc None nếu không có consensus
        """
        if not documents:
            return None
            
        # Bước 1: Rerank tất cả documents và lấy top-k
        reranked = self.rerank_documents(query, documents, top_k=top_k)
        
        if not reranked:
            return None
            
        # Bước 2: Lọc ra những chunks có score đủ cao (điều chỉnh cho văn bản pháp luật)
        qualified_chunks = [
            doc for doc in reranked 
            if doc.get('rerank_score', -999) >= min_rerank_score
        ]
        
        if not qualified_chunks:
            logger.warning(f"No chunks meet minimum rerank score {min_rerank_score}")
            return reranked[0] if reranked else None  # Fallback to best chunk
            
        logger.info(f"🔍 CONSENSUS ANALYSIS: Analyzing {len(qualified_chunks)} qualified chunks (top_k={top_k})")
        
        # Bước 3: Phân tích document consensus
        document_analysis = self._analyze_document_consensus(qualified_chunks)
        
        # Bước 4: Tìm document có consensus cao nhất
        best_consensus = self._find_best_consensus(
            document_analysis, 
            consensus_threshold, 
            len(qualified_chunks)
        )
        
        if best_consensus:
            logger.info(f"✅ CONSENSUS FOUND: Document '{best_consensus['document_id']}' "
                       f"has {best_consensus['chunk_count']}/{len(qualified_chunks)} chunks "
                       f"(ratio: {best_consensus['consensus_ratio']:.2f})")
            return best_consensus['best_chunk']
        else:
            # 🔥 NEW LOGIC: Kiểm tra nếu các chunks thuộc các documents hoàn toàn khác nhau
            unique_documents = set(self._extract_document_id(chunk) for chunk in qualified_chunks)
            
            if len(unique_documents) == len(qualified_chunks):
                logger.warning(f"🚨 SCATTERED CHUNKS: {len(qualified_chunks)} chunks from {len(unique_documents)} different documents")
                logger.info("📋 Falling back to SINGLE BEST CHUNK strategy (traditional reranking)")
                return qualified_chunks[0]  # Return highest scored chunk
            else:
                logger.warning(f"❌ NO STRONG CONSENSUS: Falling back to traditional single best document "
                              f"(threshold: {consensus_threshold})")
                return qualified_chunks[0]  # Fallback to highest scored chunk

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
    
    def get_best_document(self, query: str, documents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Tìm document có độ liên quan cao nhất với query (Legacy method)
        
        ⚠️  DEPRECATED: Khuyến khích dùng get_consensus_document() để có kết quả chính xác hơn
        
        Args:
            query: Câu hỏi cần tìm
            documents: Danh sách documents cần đánh giá
        
        Returns:
            Document có điểm rerank cao nhất
        """
        reranked = self.rerank_documents(query, documents, top_k=1)
        return reranked[0] if reranked else None
    
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
