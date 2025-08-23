"""
FilterEngine Service - Business Logic Separation

Derives smart filters và business rules từ document metadata
instead of hardcoding trong JSON files (god object elimination)
"""

from typing import Dict, List, Any, Optional
import re

class FilterEngine:
    """
    Centralized business logic để derive filters từ metadata
    Eliminates need to store business logic trong JSON files
    """
    
    @staticmethod
    def derive_smart_filters(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Derive comprehensive smart filters từ document metadata
        
        Args:
            metadata: Document metadata từ document.json
            
        Returns:
            Dict containing derived smart filters
        """
        if not metadata:
            return {}
        
        filters = {
            "exact_title": FilterEngine._get_exact_title_filters(metadata),
            "procedure_code": FilterEngine._get_procedure_code_filters(metadata),
            "agency": FilterEngine._get_agency_filters(metadata),
            "cost_range": FilterEngine._get_cost_range(metadata),
            "processing_category": FilterEngine._get_processing_category(metadata),
            "subject_matter": FilterEngine._get_subject_matter(metadata),
            "urgency_level": FilterEngine._get_urgency_level(metadata)
        }
        
        # Remove empty filters
        return {k: v for k, v in filters.items() if v}
    
    @staticmethod
    def _get_exact_title_filters(metadata: Dict[str, Any]) -> List[str]:
        """Extract title-based filters"""
        title = metadata.get("title", "")
        if not title:
            return []
        
        filters = [title]
        
        # Add variations
        if "đăng ký" in title.lower():
            filters.append("thủ tục đăng ký")
        if "cấp" in title.lower():
            filters.append("thủ tục cấp giấy tờ")
        if "chứng thực" in title.lower():
            filters.append("chứng thực hồ sơ")
            
        return filters
    
    @staticmethod
    def _get_procedure_code_filters(metadata: Dict[str, Any]) -> List[str]:
        """Extract procedure code filters"""
        code = metadata.get("code", "")
        if not code:
            return []
        
        filters = [code]
        
        # Extract pattern-based codes
        if "QT" in code:
            filters.append("quy trình cấp xã")
        if "CX" in code:
            filters.append("cấp xã")
        if "HCTP" in code:
            filters.append("hộ tịch")
            
        return filters
    
    @staticmethod  
    def _get_agency_filters(metadata: Dict[str, Any]) -> List[str]:
        """Extract executing agency filters"""
        agency = metadata.get("executing_agency", "")
        if not agency:
            return []
        
        filters = [agency]
        
        # Normalize agency names
        if "cấp xã" in agency.lower():
            filters.extend(["UBND xã", "ủy ban xã", "chính quyền cơ sở"])
        if "cấp huyện" in agency.lower():
            filters.extend(["UBND huyện", "ủy ban huyện"])
        if "cấp tỉnh" in agency.lower():
            filters.extend(["UBND tỉnh", "ủy ban tỉnh"])
            
        return filters
    
    @staticmethod
    def _get_cost_range(metadata: Dict[str, Any]) -> str:
        """Determine cost category"""
        fee = metadata.get("fee_vnd")
        
        if fee is None or fee == 0:
            return "free"
        elif fee < 50000:
            return "very_low"
        elif fee < 100000:
            return "low"
        elif fee < 300000:
            return "medium"
        elif fee < 500000:
            return "high"
        else:
            return "very_high"
    
    @staticmethod
    def _get_processing_category(metadata: Dict[str, Any]) -> str:
        """Determine processing time category"""
        processing_time = metadata.get("processing_time", "")
        
        if not processing_time:
            return "unknown"
        
        # Extract số ngày
        if "ngày" in processing_time.lower():
            try:
                days = int(re.search(r'(\d+)', processing_time).group(1))
                if days <= 1:
                    return "instant"
                elif days <= 3:
                    return "fast"  
                elif days <= 7:
                    return "normal"
                elif days <= 15:
                    return "slow"
                else:
                    return "very_slow"
            except:
                pass
        
        if "tức thì" in processing_time.lower():
            return "instant"
        if "nhanh" in processing_time.lower():
            return "fast"
            
        return "normal"
    
    @staticmethod
    def _get_subject_matter(metadata: Dict[str, Any]) -> List[str]:
        """Extract thematic subject matter"""
        title = metadata.get("title", "").lower()
        subjects = []
        
        # Thematic categorization
        if any(word in title for word in ["khai sinh", "hộ tịch", "sinh"]):
            subjects.append("birth_registration")
        if any(word in title for word in ["kết hôn", "hôn nhân"]):
            subjects.append("marriage")
        if any(word in title for word in ["chứng thực", "công chứng"]):
            subjects.append("notarization")
        if any(word in title for word in ["giấy phép", "cấp phép"]):
            subjects.append("licensing")
        if any(word in title for word in ["thuế", "tài chính"]):
            subjects.append("taxation")
            
        return subjects
    
    @staticmethod
    def _get_urgency_level(metadata: Dict[str, Any]) -> str:
        """Determine urgency based on processing time và cost"""
        processing_time = metadata.get("processing_time", "")
        fee = metadata.get("fee_vnd", 0)
        
        # Instant procedures = high urgency
        if "tức thì" in processing_time.lower():
            return "high"
        
        # Free procedures = often urgent public services    
        if fee == 0:
            return "medium"
        
        # Quick + low cost = standard urgency
        if "ngày" in processing_time.lower():
            try:
                days = int(re.search(r'(\d+)', processing_time).group(1))
                if days <= 3:
                    return "medium"
                elif days > 10:
                    return "low"
            except:
                pass
                
        return "normal"
    
    @staticmethod
    def get_collection_mapping(metadata: Dict[str, Any]) -> str:
        """
        Determine appropriate collection based on metadata
        Replaces hardcoded expected_collection trong router_questions.json
        """
        title = metadata.get("title", "").lower()
        agency = metadata.get("executing_agency", "").lower()
        
        # Collection mapping logic
        if "hộ tịch" in title or "khai sinh" in title:
            return "quy_trinh_cap_ho_tich_cap_xa"
        elif "chứng thực" in title or "công chứng" in title:
            return "quy_trinh_chung_thuc"
        elif "cấp xã" in agency:
            return "quy_trinh_cap_xa_tong_hop"
        elif "cấp huyện" in agency:
            return "quy_trinh_cap_huyen"
        else:
            return "quy_trinh_tong_hop"
