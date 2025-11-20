"""
Vietnamese Reranker wrapper using sentence-transformers CrossEncoder.
"""
import os
import time
import logging
from typing import List, Tuple
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
    
    def get_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "max_length": self.max_length,
            "cache_dir": self.cache_dir,
            "cuda_available": torch.cuda.is_available(),
        }
