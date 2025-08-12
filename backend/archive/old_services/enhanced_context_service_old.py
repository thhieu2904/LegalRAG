"""
Enhanced Context Service - Chiến lược Truy xuất Linh hoạt (Hybrid Retrieval)
Tối ưu hóa ngữ cảnh gửi đến LLM bằng cách:
1. Phân tích mẫu phân bố của top chunks
2. Quyết định gửi toàn bộ file hay chỉ top chunks
3. Tạo ngữ cảnh mạch lạc và đầy đủ
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class EnhancedContextService:
    """
    Service tối ưu context cho LLM với chiến lược hybrid retrieval
    """
    
    def __init__(self, vectordb_service, document_processor):
        self.vectordb_service = vectordb_service
        self.document_processor = document_processor
        
        # Thresholds để quyết định chiến lược
        self.single_file_threshold = 0.4  # 40% chunks từ cùng 1 file (giảm từ 60%)
        self.file_context_max_chunks = 50  # Tối đa số chunks trong 1 file
        self.hybrid_top_k = 8  # Số chunks top khi dùng hybrid mode
        self.min_chunks_for_single_file = 2  # Tối thiểu 2 chunks để xem xét single file
        
    def analyze_chunk_distribution(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phân tích phân bố của chunks theo file/document
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'unique_files': 0,
                'file_distribution': {},
                'dominant_file': None,
                'dominant_file_ratio': 0.0,
                'strategy_recommendation': 'empty'
            }
        
        # Thu thập thông tin file từ chunks
        file_counts = defaultdict(int)
        file_chunks = defaultdict(list)
        
        for chunk in chunks:
            source = chunk.get('source', {})
            file_key = source.get('file_path', source.get('document_title', 'unknown'))
            file_counts[file_key] += 1
            file_chunks[file_key].append(chunk)
        
        # Tìm file chiếm ưu thế
        total_chunks = len(chunks)
        dominant_file = max(file_counts.items(), key=lambda x: x[1]) if file_counts else (None, 0)
        dominant_file_name, dominant_count = dominant_file
        dominant_ratio = dominant_count / total_chunks if total_chunks > 0 else 0
        
        # Quyết định strategy với logic cải tiến
        if dominant_ratio >= self.single_file_threshold and dominant_count >= self.min_chunks_for_single_file:
            strategy = 'single_file'
        elif len(file_counts) <= 2 and dominant_count >= 2:
            strategy = 'dual_file'  
        else:
            strategy = 'multi_file'
        
        # Log để debug
        logger.info(f"Chunk analysis: {total_chunks} chunks, {len(file_counts)} files, "
                   f"dominant: {dominant_file_name} ({dominant_ratio:.2f}), strategy: {strategy}")
        
        return {
            'total_chunks': total_chunks,
            'unique_files': len(file_counts),
            'file_distribution': dict(file_counts),
            'file_chunks': dict(file_chunks),
            'dominant_file': dominant_file_name,
            'dominant_file_ratio': dominant_ratio,
            'strategy_recommendation': strategy
        }

    def get_full_document_context(self, file_path: str, collection_name: str) -> Optional[str]:
        """
        Lấy toàn bộ nội dung document từ file_path
        """
        try:
            # Tìm tất cả chunks của file trong collection
            all_chunks = self.vectordb_service.get_chunks_by_source(
                collection_name=collection_name,
                file_path=file_path
            )
            
            if not all_chunks:
                logger.warning(f"No chunks found for file: {file_path}")
                return None
            
            # Sắp xếp chunks theo chunk_index
            sorted_chunks = sorted(
                all_chunks,
                key=lambda x: x.get('metadata', {}).get('chunk_index', 0)
            )
            
            # Giới hạn số lượng chunks để tránh context quá dài
            if len(sorted_chunks) > self.file_context_max_chunks:
                logger.warning(f"File {file_path} has {len(sorted_chunks)} chunks, truncating to {self.file_context_max_chunks}")
                sorted_chunks = sorted_chunks[:self.file_context_max_chunks]
            
            # Kết hợp content
            full_content = []
            prev_chunk_idx = -1
            
            for chunk in sorted_chunks:
                chunk_idx = chunk.get('metadata', {}).get('chunk_index', 0)
                content = chunk.get('content', '').strip()
                
                if not content:
                    continue
                
                # Thêm separator nếu có khoảng trống giữa chunks
                if chunk_idx > prev_chunk_idx + 1 and prev_chunk_idx >= 0:
                    full_content.append("\n[...]\n")
                
                full_content.append(content)
                prev_chunk_idx = chunk_idx
            
            result = '\n\n'.join(full_content)
            logger.info(f"Retrieved full document context: {len(sorted_chunks)} chunks, {len(result)} chars")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting full document context for {file_path}: {e}")
            return None

    def create_hybrid_context(
        self, 
        chunks: List[Dict[str, Any]], 
        query: str,
        max_context_length: int = 3000
    ) -> Dict[str, Any]:
        """
        Tạo context tối ưu bằng hybrid strategy
        """
        try:
            analysis = self.analyze_chunk_distribution(chunks)
            
            if analysis['total_chunks'] == 0:
                return {
                    'context': "",
                    'strategy_used': 'empty',
                    'chunks_included': 0,
                    'files_included': 0,
                    'analysis': analysis
                }
            
            strategy = analysis['strategy_recommendation']
            logger.info(f"Using strategy: {strategy} (dominant_file_ratio: {analysis['dominant_file_ratio']:.2f})")
            
            if strategy == 'single_file':
                return self._create_single_file_context(analysis, max_context_length)
            elif strategy == 'dual_file':
                return self._create_dual_file_context(analysis, max_context_length)
            else:
                return self._create_multi_chunk_context(chunks, max_context_length, analysis)
                
        except Exception as e:
            logger.error(f"Error creating hybrid context: {e}")
            # Fallback to simple chunk concatenation
            return self._create_fallback_context(chunks, max_context_length)

    def _create_single_file_context(self, analysis: Dict[str, Any], max_length: int) -> Dict[str, Any]:
        """Tạo context từ toàn bộ file dominanting"""
        dominant_file = analysis['dominant_file']
        file_chunks = analysis['file_chunks'][dominant_file]
        
        # Lấy collection từ chunk đầu tiên
        collection = file_chunks[0].get('collection', 'legal_documents')
        
        # Thử lấy full document
        full_context = self.get_full_document_context(dominant_file, collection)
        
        if full_context and len(full_context) <= max_length:
            return {
                'context': full_context,
                'strategy_used': 'single_file_full',
                'chunks_included': len(file_chunks),
                'files_included': 1,
                'analysis': analysis,
                'source_file': dominant_file
            }
        else:
            # Fallback: sử dụng top chunks từ file đó
            sorted_chunks = sorted(file_chunks, key=lambda x: x.get('similarity', 0), reverse=True)
            top_chunks = sorted_chunks[:self.hybrid_top_k]
            
            context_parts = []
            current_length = 0
            chunks_used = 0
            
            for chunk in top_chunks:
                content = chunk.get('content', '').strip()
                if current_length + len(content) <= max_length:
                    context_parts.append(content)
                    current_length += len(content) + 2  # +2 for \n\n
                    chunks_used += 1
                else:
                    break
            
            return {
                'context': '\n\n'.join(context_parts),
                'strategy_used': 'single_file_chunks',
                'chunks_included': chunks_used,
                'files_included': 1,
                'analysis': analysis,
                'source_file': dominant_file
            }

    def _create_dual_file_context(self, analysis: Dict[str, Any], max_length: int) -> Dict[str, Any]:
        """Tạo context từ 2 files chính"""
        file_chunks = analysis['file_chunks']
        
        # Sắp xếp files theo số lượng chunks
        sorted_files = sorted(file_chunks.items(), key=lambda x: len(x[1]), reverse=True)
        top_2_files = sorted_files[:2]
        
        context_parts = []
        current_length = 0
        total_chunks = 0
        files_used = []
        
        for file_name, chunks in top_2_files:
            # Sort chunks theo similarity
            sorted_chunks = sorted(chunks, key=lambda x: x.get('similarity', 0), reverse=True)
            
            # Add file header
            if context_parts:
                file_header = f"\n--- {file_name} ---\n"
                if current_length + len(file_header) <= max_length:
                    context_parts.append(file_header)
                    current_length += len(file_header)
            
            # Add chunks from this file
            chunks_from_file = 0
            for chunk in sorted_chunks[:4]:  # Max 4 chunks per file
                content = chunk.get('content', '').strip()
                if current_length + len(content) <= max_length:
                    context_parts.append(content)
                    current_length += len(content) + 2
                    chunks_from_file += 1
                    total_chunks += 1
                else:
                    break
            
            if chunks_from_file > 0:
                files_used.append(file_name)
        
        return {
            'context': '\n\n'.join(context_parts),
            'strategy_used': 'dual_file',
            'chunks_included': total_chunks,
            'files_included': len(files_used),
            'analysis': analysis,
            'source_files': files_used
        }

    def _create_multi_chunk_context(self, chunks: List[Dict[str, Any]], max_length: int, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo context từ top chunks nhiều files khác nhau"""
        # Sort theo similarity score
        sorted_chunks = sorted(chunks, key=lambda x: x.get('rerank_score', x.get('similarity', 0)), reverse=True)
        
        context_parts = []
        current_length = 0
        chunks_used = 0
        files_used = set()
        
        for chunk in sorted_chunks[:self.hybrid_top_k]:
            content = chunk.get('content', '').strip()
            source = chunk.get('source', {})
            file_name = source.get('document_title', source.get('file_path', 'unknown'))
            
            # Add file separator khi chuyển sang file mới
            if file_name not in files_used and files_used:
                separator = f"\n--- {file_name} ---\n"
                if current_length + len(separator) <= max_length:
                    context_parts.append(separator)
                    current_length += len(separator)
            
            if current_length + len(content) <= max_length:
                context_parts.append(content)
                current_length += len(content) + 2
                chunks_used += 1
                files_used.add(file_name)
            else:
                break
        
        return {
            'context': '\n\n'.join(context_parts),
            'strategy_used': 'multi_chunk',
            'chunks_included': chunks_used,
            'files_included': len(files_used),
            'analysis': analysis,
            'source_files': list(files_used)
        }

    def _create_fallback_context(self, chunks: List[Dict[str, Any]], max_length: int) -> Dict[str, Any]:
        """Fallback context creation khi có lỗi"""
        context_parts = []
        current_length = 0
        
        for chunk in chunks[:5]:  # Chỉ lấy 5 chunks đầu
            content = chunk.get('content', '').strip()
            if content and current_length + len(content) <= max_length:
                context_parts.append(content)
                current_length += len(content) + 2
            else:
                break
        
        return {
            'context': '\n\n'.join(context_parts),
            'strategy_used': 'fallback',
            'chunks_included': len(context_parts),
            'files_included': 1,  # Unknown
            'analysis': {'error': 'fallback_used'}
        }

    def optimize_context_for_query(
        self, 
        chunks: List[Dict[str, Any]], 
        query: str,
        target_length: int = 2500
    ) -> Dict[str, Any]:
        """
        Main method để tạo context tối ưu cho query
        """
        start_time = time.time()
        
        if not chunks:
            return {
                'context': "",
                'metadata': {
                    'strategy_used': 'empty',
                    'chunks_included': 0,
                    'files_included': 0,
                    'processing_time': time.time() - start_time
                }
            }
        
        # Tạo hybrid context
        result = self.create_hybrid_context(chunks, query, target_length)
        
        # Add metadata
        result['metadata'] = {
            'strategy_used': result.get('strategy_used', 'unknown'),
            'chunks_included': result.get('chunks_included', 0),
            'files_included': result.get('files_included', 0),
            'context_length': len(result.get('context', '')),
            'processing_time': time.time() - start_time,
            'query_length': len(query),
            'target_length': target_length
        }
        
        logger.info(f"Context optimized: {result['metadata']['strategy_used']} strategy, "
                   f"{result['metadata']['chunks_included']} chunks, "
                   f"{result['metadata']['context_length']} chars in "
                   f"{result['metadata']['processing_time']:.2f}s")
        
        return result
