"""
Auto-fill Service - Fill forms với CCCD data
Mapping CCCD fields to form placeholders
"""

import logging
import re
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class AutoFillService:
    """
    Service để tự động điền form với dữ liệu từ CCCD
    Sử dụng mapping configuration để match fields
    """
    
    def __init__(self):
        # Load mapping configuration
        self.field_mapping = self._load_default_mapping()
        logger.info("AutoFillService initialized with default mapping")
    
    def _load_default_mapping(self) -> Dict[str, List[str]]:
        """
        Default mapping từ CCCD fields đến form placeholders
        """
        return {
            # CCCD field -> List of possible form field names
            "full_name": [
                "ho_ten_nguoi_yeu_cau", "ho_ten", "ho_va_ten", 
                "ho_ten_cha", "ho_ten_me", "nguoi_yeu_cau"
            ],
            "citizen_id": [
                "so_cccd", "cccd", "so_cmt", "so_cmnd", 
                "so_giay_to_tuy_than", "can_cuoc_cong_dan"
            ],
            "date_of_birth": [
                "ngay_sinh", "ngay_thang_nam_sinh", "nam_sinh"
            ],
            "gender": [
                "gioi_tinh", "phai"
            ],
            "address": [
                "dia_chi", "noi_cu_tru", "cho_o_hien_tai", "que_quan"
            ],
            "issue_date": [
                "ngay_cap", "ngay_cap_cccd"
            ],
            "issue_place": [
                "noi_cap", "co_quan_cap"
            ]
        }
    
    def auto_fill_form_html(self, html_content: str, cccd_data: Dict[str, Any], placeholders: List[Dict[str, str]]) -> str:
        """
        Auto-fill HTML form với CCCD data
        
        Args:
            html_content: Original HTML content
            cccd_data: Data từ CCCD QR scan
            placeholders: List placeholders từ form
            
        Returns:
            HTML content với filled values
        """
        try:
            filled_html = html_content
            fill_log = []
            
            # Process each placeholder
            for placeholder in placeholders:
                placeholder_name = placeholder["name"]
                placeholder_pattern = placeholder["pattern"]
                field_type = placeholder["field_type"]
                
                # Find matching CCCD field
                cccd_value = self._find_matching_cccd_value(placeholder_name, cccd_data)
                
                if cccd_value:
                    # Create input field based on type
                    input_field = self._create_input_field(
                        field_name=placeholder_name,
                        field_type=field_type,
                        field_value=cccd_value
                    )
                    
                    # Replace placeholder with input field
                    filled_html = filled_html.replace(placeholder_pattern, input_field)
                    
                    fill_log.append({
                        "placeholder": placeholder_name,
                        "cccd_field": self._get_cccd_field_name(placeholder_name, cccd_data),
                        "value": cccd_value
                    })
                else:
                    # Create empty input field
                    input_field = self._create_input_field(
                        field_name=placeholder_name,
                        field_type=field_type,
                        field_value=""
                    )
                    filled_html = filled_html.replace(placeholder_pattern, input_field)
            
            logger.info(f"✅ Auto-filled {len(fill_log)} fields")
            for log_entry in fill_log:
                logger.info(f"   - {log_entry['placeholder']} = {log_entry['value']}")
            
            return filled_html
            
        except Exception as e:
            logger.error(f"Error auto-filling form: {e}")
            return html_content  # Return original on error
    
    def _find_matching_cccd_value(self, placeholder_name: str, cccd_data: Dict[str, Any]) -> Optional[str]:
        """
        Find matching CCCD value cho placeholder
        """
        placeholder_lower = placeholder_name.lower()
        
        # Check exact mapping first
        for cccd_field, form_fields in self.field_mapping.items():
            if placeholder_lower in [field.lower() for field in form_fields]:
                cccd_value = cccd_data.get(cccd_field)
                if cccd_value:
                    return str(cccd_value)
        
        # Check fuzzy matching
        for cccd_field, cccd_value in cccd_data.items():
            if cccd_value and self._is_field_match(placeholder_lower, cccd_field):
                return str(cccd_value)
        
        return None
    
    def _get_cccd_field_name(self, placeholder_name: str, cccd_data: Dict[str, Any]) -> Optional[str]:
        """
        Get CCCD field name that was matched
        """
        placeholder_lower = placeholder_name.lower()
        
        for cccd_field, form_fields in self.field_mapping.items():
            if placeholder_lower in [field.lower() for field in form_fields]:
                return cccd_field
        
        return None
    
    def _is_field_match(self, placeholder_name: str, cccd_field: str) -> bool:
        """
        Check fuzzy matching between placeholder and CCCD field
        """
        keywords_map = {
            "full_name": ["ho", "ten", "name"],
            "citizen_id": ["cccd", "cmt", "cmnd", "id"],
            "date_of_birth": ["sinh", "birth", "ngay"],
            "gender": ["gioi", "tinh", "phai", "sex"],
            "address": ["dia", "chi", "address", "cu", "tru"],
            "issue_date": ["cap", "issue"],
        }
        
        if cccd_field in keywords_map:
            keywords = keywords_map[cccd_field]
            return any(keyword in placeholder_name for keyword in keywords)
        
        return False
    
    def _create_input_field(self, field_name: str, field_type: str, field_value: str) -> str:
        """
        Create HTML input field based on type
        """
        common_attrs = f'name="{field_name}" id="{field_name}" class="form-field" value="{field_value}"'
        
        if field_type == "date":
            return f'<input type="date" {common_attrs} />'
        elif field_type == "email":
            return f'<input type="email" {common_attrs} />'
        elif field_type == "number":
            return f'<input type="text" {common_attrs} pattern="[0-9]*" />'
        elif field_type == "select" and "gioi_tinh" in field_name.lower():
            selected_male = 'selected' if field_value.lower() in ['nam', 'male', 'm'] else ''
            selected_female = 'selected' if field_value.lower() in ['nữ', 'nu', 'female', 'f'] else ''
            return f'''
            <select name="{field_name}" id="{field_name}" class="form-field">
                <option value="">Chọn giới tính</option>
                <option value="Nam" {selected_male}>Nam</option>
                <option value="Nữ" {selected_female}>Nữ</option>
            </select>
            '''
        else:
            return f'<input type="text" {common_attrs} />'
    
    def get_fill_preview(self, placeholders: List[Dict[str, str]], cccd_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preview what fields sẽ được auto-filled
        """
        preview = {
            "total_placeholders": len(placeholders),
            "fillable_fields": [],
            "unfillable_fields": []
        }
        
        for placeholder in placeholders:
            placeholder_name = placeholder["name"]
            cccd_value = self._find_matching_cccd_value(placeholder_name, cccd_data)
            
            if cccd_value:
                preview["fillable_fields"].append({
                    "field_name": placeholder_name,
                    "field_type": placeholder["field_type"],
                    "cccd_value": cccd_value,
                    "cccd_source": self._get_cccd_field_name(placeholder_name, cccd_data)
                })
            else:
                preview["unfillable_fields"].append({
                    "field_name": placeholder_name,
                    "field_type": placeholder["field_type"],
                    "reason": "No matching CCCD field"
                })
        
        preview["fill_rate"] = len(preview["fillable_fields"]) / len(placeholders) * 100 if placeholders else 0
        
        return preview
