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
        
        # Load the Cross-Encoder model
        try:
            self.model = CrossEncoder(
                model_name,
                max_length=max_length,
                device=self.device
            )
            
            # Manually set cache folder for model downloads if needed
            if cache_dir:
                os.environ['SENTENCE_TRANSFORMERS_HOME'] = cache_dir
                
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
    
    def rerank_with_document_filter(
        self,
        query: str,
        documents: List[str],
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        batch_size: int = 16,
        same_document_only: bool = True
    ) -> List[Tuple[int, str, float]]:
        """
        Rerank documents and identify best document to preserve full context.
        
        When same_document_only=True:
        1. Rerank ALL chunks (no filtering at this stage)
        2. Group chunks by document_id
        3. Calculate aggregate score for each document
        4. Pick document with majority of high-scoring chunks
        5. Return ALL chunks from that document (preserves full legal context)
        
        This prevents hallucination from mixed contexts while preserving
        complete legal document context.
        
        Args:
            query: Search query
            documents: List of candidate documents
            document_ids: List of document IDs (same length as documents)
            top_k: IGNORED - returns all chunks from best document
            batch_size: Batch size for inference
            same_document_only: If True, filter to single best document
        
        Returns:
            List of tuples (original_index, text, score) sorted by score descending
            Contains ALL chunks from the selected document
        """
        if not documents:
            return []
        
        # First, rerank all chunks
        all_results = self.rerank(
            query=query,
            documents=documents,
            top_k=len(documents),  # Get all scores first
            batch_size=batch_size
        )
        
        # If same_document_only is False OR no document_ids provided, return normal top_k
        if not same_document_only or not document_ids:
            return all_results[:top_k]
        
        # Validate document_ids length
        if len(document_ids) != len(documents):
            logger.warning(
                f"document_ids length ({len(document_ids)}) != documents length ({len(documents)}). "
                f"Falling back to normal reranking."
            )
            return all_results[:top_k]
        
        start_time = time.time()
        
        # Group chunks by document_id
        doc_groups = defaultdict(list)
        for idx, text, score in all_results:
            doc_id = document_ids[idx]
            doc_groups[doc_id].append((idx, text, score))
        
        logger.info(f"Grouped {len(documents)} chunks into {len(doc_groups)} documents")
        
        # Calculate aggregate score for each document
        # Strategy: Average of top-3 chunks per document
        doc_scores = {}
        for doc_id, chunks in doc_groups.items():
            # Sort chunks by score descending
            sorted_chunks = sorted(chunks, key=lambda x: x[2], reverse=True)
            # Take top-3 (or all if less than 3)
            top_3 = sorted_chunks[:3]
            # Calculate average score
            avg_score = sum(c[2] for c in top_3) / len(top_3)
            doc_scores[doc_id] = avg_score
            logger.debug(f"Document {doc_id}: {len(chunks)} chunks, avg_top3_score={avg_score:.4f}")
        
        # Pick best document (document with highest aggregate score)
        best_doc_id = max(doc_scores.items(), key=lambda x: x[1])[0]
        best_doc_score = doc_scores[best_doc_id]
        best_chunks = doc_groups[best_doc_id]
        
        logger.info(
            f"Selected document {best_doc_id} (score={best_doc_score:.4f}) "
            f"with {len(best_chunks)} chunks from {len(doc_groups)} candidates"
        )
        
        # Sort chunks from best document by score and return ALL of them
        # (No top_k filtering - preserve full legal context)
        best_chunks_sorted = sorted(best_chunks, key=lambda x: x[2], reverse=True)
        final_results = best_chunks_sorted  # Return ALL chunks
        
        elapsed = time.time() - start_time
        logger.info(
            f"Document-first reranking completed in {elapsed:.3f}s: "
            f"{len(documents)} input chunks → {len(doc_groups)} documents → "
            f"Selected 1 document → Returning ALL {len(final_results)} chunks (full context preserved)"
        )
        
        return final_results
    
    def get_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "max_length": self.max_length,
            "cache_dir": self.cache_dir,
            "cuda_available": torch.cuda.is_available(),
        }
