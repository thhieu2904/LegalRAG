"""
Vietnamese Reranker wrapper using sentence-transformers CrossEncoder.
"""
import os
import time
import logging
from typing import List, Tuple, Optional
from collections import defaultdict
from sentence_transformers import CrossEncoder
import torch

logger = logging.getLogger(__name__)


class VietnameseReranker:
    """
    Wrapper for Vietnamese document reranking using Cross-Encoder.
    
    Uses AITeamVN/Vietnamese_Reranker model to compute relevance scores
    for query-document pairs.
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        device: str = "cpu",
        max_length: int = 1024,
        cache_dir: str = "/app/models"
    ):
        """
        Initialize the Vietnamese Reranker.
        
        Args:
            model_name: HuggingFace model identifier (default: BAAI/bge-reranker-v2-m3)
            device: Device to use ('cpu' or 'cuda')
            max_length: Maximum sequence length
            cache_dir: Directory to cache downloaded models
        """
        self.model_name = model_name
        self.device = device
        self.max_length = max_length
        self.cache_dir = cache_dir
        
        logger.info(f"Initializing Vietnamese Reranker: {model_name}")
        logger.info(f"Device: {device}, Max Length: {max_length}")
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Check GPU availability
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, falling back to CPU")
            self.device = "cpu"
        
        # Set cache folder BEFORE loading model
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = cache_dir
            os.environ['HF_HOME'] = cache_dir
            os.environ['TRANSFORMERS_CACHE'] = cache_dir
            logger.info(f"Model cache directory: {cache_dir}")
        
        # Load the Cross-Encoder model
        try:
            self.model = CrossEncoder(
                model_name,
                max_length=max_length,
                device=self.device
            )
                
            logger.info(f"✓ Model loaded successfully on {self.device}")
            
            # Log GPU info if available
            if self.device == "cuda":
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                logger.info(f"GPU: {gpu_name}, Memory: {gpu_memory:.2f} GB")
                
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
        batch_size: int = 16
    ) -> List[Tuple[int, str, float]]:
        """
        Rerank documents based on relevance to query.
        
        Args:
            query: Search query
            documents: List of candidate documents
            top_k: Number of top results to return
            batch_size: Batch size for inference
        
        Returns:
            List of tuples (original_index, text, score) sorted by score descending
        """
        if not documents:
            return []
        
        start_time = time.time()
        
        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]
        
        # Compute relevance scores
        try:
            scores = self.model.predict(
                pairs,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            raise
        
        # Combine with original indices
        results = [
            (idx, doc, float(score))
            for idx, (doc, score) in enumerate(zip(documents, scores))
        ]
        
        # Sort by score descending and take top-k
        results.sort(key=lambda x: x[2], reverse=True)
        top_results = results[:top_k]
        
        elapsed = time.time() - start_time
        logger.info(
            f"Reranked {len(documents)} documents in {elapsed:.3f}s "
            f"(batch_size={batch_size}, device={self.device})"
        )
        
        return top_results
    
    def rerank_with_scores(
        self,
        query: str,
        documents: List[str],
        document_ids: Optional[List[str]] = None,
        document_titles: Optional[List[str]] = None,
        top_k: int = 5,
        batch_size: int = 16,
        include_document_scores: bool = True
    ) -> Tuple[List[Tuple[int, str, float]], Optional[List[dict]]]:
        """
        Rerank documents and return top-K chunks WITH document-level scores.
        
        This is the hybrid approach:
        1. Rerank ALL chunks with title-aware scoring
        2. Return top-K chunks (from potentially multiple documents)
        3. Also return aggregated document scores for query-service to decide clarification
        
        Query-service uses document_scores to:
        - If score_gap between top-1 and top-2 doc is large → answer directly
        - If score_gap is small → trigger clarification (ambiguous query)
        
        Args:
            query: Search query
            documents: List of candidate documents
            document_ids: List of document IDs (same length as documents)
            document_titles: List of document titles for title-aware reranking
            top_k: Number of top chunks to return
            batch_size: Batch size for inference
            include_document_scores: If True, calculate and return document scores
        
        Returns:
            Tuple of:
            - List of tuples (original_index, text, score) sorted by score descending
            - List of document score dicts (if include_document_scores=True)
        """
        if not documents:
            return [], None
        
        # Prepend document titles to content for title-aware reranking
        docs_for_rerank = documents
        if document_titles and len(document_titles) == len(documents):
            docs_for_rerank = [
                f"[{title}] {content}" if title else content
                for title, content in zip(document_titles, documents)
            ]
            logger.info(f"Title-aware reranking enabled for {len(documents)} chunks")
        
        # Rerank all chunks
        all_results = self.rerank(
            query=query,
            documents=docs_for_rerank,
            top_k=len(documents),  # Get all scores first
            batch_size=batch_size
        )
        
        # Map back to original documents (without title prefix)
        all_results = [
            (idx, documents[idx], score)
            for idx, _, score in all_results
        ]
        
        # Calculate document scores if requested and document_ids provided
        document_scores = None
        if include_document_scores and document_ids and len(document_ids) == len(documents):
            start_time = time.time()
            
            # Group chunks by document_id
            doc_groups = defaultdict(list)
            for idx, text, score in all_results:
                doc_id = document_ids[idx]
                doc_groups[doc_id].append((idx, text, score))
            
            logger.info(f"Grouped {len(documents)} chunks into {len(doc_groups)} documents")
            
            # Calculate aggregate scores for each document
            document_scores = []
            for doc_id, chunks in doc_groups.items():
                sorted_chunks = sorted(chunks, key=lambda x: x[2], reverse=True)
                top_3 = sorted_chunks[:3]
                avg_score = sum(c[2] for c in top_3) / len(top_3)
                max_score = sorted_chunks[0][2]
                
                document_scores.append({
                    'document_id': doc_id,
                    'avg_score': avg_score,
                    'max_score': max_score,
                    'chunk_count': len(chunks)
                })
            
            # Sort by avg_score descending
            document_scores.sort(key=lambda x: x['avg_score'], reverse=True)
            
            elapsed = time.time() - start_time
            logger.info(
                f"Calculated scores for {len(document_scores)} documents in {elapsed:.3f}s. "
                f"Top doc: {document_scores[0]['document_id'][:8]}... (avg={document_scores[0]['avg_score']:.4f})"
            )
        
        # Return top-K chunks (from any documents) + document scores
        return all_results[:top_k], document_scores
    
    # Keep old method for backward compatibility but mark as deprecated
    def rerank_with_document_filter(
        self,
        query: str,
        documents: List[str],
        document_ids: Optional[List[str]] = None,
        document_titles: Optional[List[str]] = None,
        top_k: int = 5,
        batch_size: int = 16,
        same_document_only: bool = True
    ) -> List[Tuple[int, str, float]]:
        """
        DEPRECATED: Use rerank_with_scores instead.
        Kept for backward compatibility.
        """
        logger.warning("rerank_with_document_filter is deprecated. Use rerank_with_scores instead.")
        results, _ = self.rerank_with_scores(
            query=query,
            documents=documents,
            document_ids=document_ids,
            document_titles=document_titles,
            top_k=top_k,
            batch_size=batch_size,
            include_document_scores=False
        )
        return results
    
    def get_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "max_length": self.max_length,
            "cache_dir": self.cache_dir,
            "cuda_available": torch.cuda.is_available(),
        }
