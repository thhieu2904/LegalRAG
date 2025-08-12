import logging
from typing import List, Dict, Any, Optional, Tuple
import re
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from ..core.config import settings

logger = logging.getLogger(__name__)

class QueryRouter:
    """Bộ định tuyến thông minh để xác định collection phù hợp nhất cho câu hỏi"""
    
    def __init__(self, embedding_model: Optional[SentenceTransformer] = None):
        self.embedding_model = embedding_model
        
        # Định nghĩa các collection với từ khóa và mẫu câu hỏi
        self.collections_config = {
            'ho_tich_cap_xa': {
                'name': 'Hộ tịch cấp xã',
                'keywords': 'hộ tịch, cấp xã, khai sinh, kết hôn, khai tử, giám hộ, trích lục, bản sao, đăng ký lại, yếu tố nước ngoài, lưu động, tình trạng hôn nhân, giấy khai sinh, xác nhận hộ tịch, nhận cha mẹ con, cải chính, bổ sung, thay đổi thông tin, dân tộc, chấm dứt giám hộ, giám sát giám hộ',
                'sample_queries': [
                    'làm thế nào để đăng ký khai sinh',
                    'thủ tục kết hôn cần gì',
                    'cách cấp trích lục hộ tịch',
                    'đăng ký khai tử như thế nào',
                    'thủ tục giám hộ trẻ em'
                ]
            },
            
            'chung_thuc': {
                'name': 'Chứng thực',  
                'keywords': 'chứng thực, hợp đồng, giao dịch, di chúc, bản sao, chữ ký, di sản, sửa đổi, bổ sung, hủy bỏ, người dịch, tài sản, động sản, quyền sử dụng đất, nhà ở, từ chối nhận di sản, thỏa thuận phân chia, khai nhận di sản, cộng tác viên dịch thuật, sai sót trong hợp đồng',
                'sample_queries': [
                    'chứng thực hợp đồng mua bán',
                    'làm di chúc cần chứng thực gì',
                    'chứng thực bản sao giấy tờ',
                    'thủ tục chứng thực chữ ký',
                    'sửa lỗi trong hợp đồng đã chứng thực'
                ]
            },
            
            'nuoi_con_nuoi': {
                'name': 'Nuôi con nuôi',
                'keywords': 'nuôi con nuôi, đăng ký, STP, yếu tố nước ngoài, trẻ em, cơ sở nuôi dưỡng, cha dượng, mẹ kế, xác nhận, nhận con riêng, cô cậu dì chú bác ruột, nhận cháu làm con nuôi, người nước ngoài thường trú, công dân việt nam, đủ điều kiện',
                'sample_queries': [
                    'thủ tục nhận con nuôi trong nước',
                    'người nước ngoài nhận con nuôi việt nam',
                    'cha dượng nhận con riêng của vợ',
                    'cô ruột nhận cháu làm con nuôi',
                    'đăng ký lại việc nuôi con nuôi'
                ]
            }
        }
    
    def normalize_text(self, text: str) -> str:
        """Chuẩn hóa text để so sánh"""
        # Chuyển về lowercase
        text = text.lower()
        
        # Loại bỏ dấu câu và ký tự đặc biệt
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Loại bỏ khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def calculate_keyword_similarity(self, query: str, collection_name: str) -> float:
        """Tính độ tương đồng dựa trên từ khóa"""
        normalized_query = self.normalize_text(query)
        keywords_string = self.collections_config[collection_name]['keywords']
        keywords = [kw.strip() for kw in keywords_string.split(',')]
        
        # Đếm số từ khóa xuất hiện
        matched_keywords = 0
        for keyword in keywords:
            if self.normalize_text(keyword) in normalized_query:
                matched_keywords += 1
        
        # Tính tỷ lệ
        similarity = matched_keywords / len(keywords) if keywords else 0
        return similarity
    
    def calculate_semantic_similarity(self, query: str, collection_name: str) -> float:
        """Tính độ tương đồng ngữ nghĩa sử dụng embedding"""
        if not self.embedding_model:
            return 0.0
            
        try:
            # Embedding cho query
            query_embedding = self.embedding_model.encode([query], convert_to_tensor=False)
            
            # Embedding cho sample queries của collection
            sample_queries = self.collections_config[collection_name]['sample_queries']
            sample_embeddings = self.embedding_model.encode(sample_queries, convert_to_tensor=False)
            
            # Ensure we have numpy arrays
            query_embedding = np.array(query_embedding)
            sample_embeddings = np.array(sample_embeddings)
            
            # Tính cosine similarity
            similarities = cosine_similarity(query_embedding, sample_embeddings)[0]
            
            # Lấy similarity cao nhất
            max_similarity = np.max(similarities)
            return float(max_similarity)
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def route_query(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Định tuyến query đến collection phù hợp nhất - sử dụng config defaults
        Returns: List[(collection_name, confidence_score)]
        """
        if top_k is None:
            top_k = settings.query_router_top_k
        scores = {}
        
        for collection_name in self.collections_config.keys():
            # Tính keyword similarity (trọng số 0.4)
            keyword_score = self.calculate_keyword_similarity(query, collection_name)
            
            # Tính semantic similarity (trọng số 0.6)
            semantic_score = self.calculate_semantic_similarity(query, collection_name)
            
            # Tổng hợp score
            total_score = keyword_score * 0.4 + semantic_score * 0.6
            scores[collection_name] = total_score
            
            logger.debug(f"Collection {collection_name}: keyword={keyword_score:.3f}, semantic={semantic_score:.3f}, total={total_score:.3f}")
        
        # Sắp xếp theo score giảm dần
        sorted_collections = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Lọc những collection có score > threshold
        threshold = 0.1
        relevant_collections = [(name, score) for name, score in sorted_collections if score > threshold]
        
        # Nếu không có collection nào đạt threshold, trả về top 1
        if not relevant_collections:
            relevant_collections = [sorted_collections[0]]
        
        return relevant_collections[:top_k]
    
    def get_best_collection(self, query: str, confidence_threshold: Optional[float] = None) -> Optional[str]:
        """Lấy collection tốt nhất cho query - sử dụng config defaults"""
        if confidence_threshold is None:
            confidence_threshold = settings.default_similarity_threshold
            
        routes = self.route_query(query, top_k=settings.best_collection_top_k)
        
        if routes and routes[0][1] >= confidence_threshold:
            return routes[0][0]
        
        # Fallback: tìm collection có nhiều từ khóa match nhất
        best_collection = None
        max_matches = 0
        
        normalized_query = self.normalize_text(query)
        
        for collection_name, config in self.collections_config.items():
            # Chuyển keywords từ string thành list
            keywords_list = [kw.strip() for kw in config['keywords'].split(',')]
            matches = sum(1 for keyword in keywords_list 
                         if self.normalize_text(keyword) in normalized_query)
            
            if matches > max_matches:
                max_matches = matches
                best_collection = collection_name
        
        return best_collection
    
    def explain_routing(self, query: str) -> Dict[str, Any]:
        """Giải thích tại sao chọn collection này - sử dụng config defaults"""
        routes = self.route_query(query, top_k=settings.collections_top_k)
        
        explanation = {
            'query': query,
            'recommended_collections': routes,
            'reasoning': []
        }
        
        normalized_query = self.normalize_text(query)
        
        for collection_name, score in routes:
            config = self.collections_config[collection_name]
            
            # Chuyển keywords từ string thành list
            keywords_list = [kw.strip() for kw in config['keywords'].split(',')]
            
            # Tìm từ khóa matched
            matched_keywords = [
                keyword for keyword in keywords_list
                if self.normalize_text(keyword) in normalized_query
            ]
            
            explanation['reasoning'].append({
                'collection': collection_name,
                'collection_name': config['name'],
                'confidence': score,
                'matched_keywords': matched_keywords,
                'keyword_count': len(matched_keywords)
            })
        
        return explanation
