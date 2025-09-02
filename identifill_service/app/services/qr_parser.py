import re
from typing import Optional
from app.models.schemas import CCCDData


class QRCodeParser:
    """Parser for CCCD QR code data"""
    
    @staticmethod
    def parse_qr_data(qr_string: str) -> Optional[CCCDData]:
        """
        Parse QR code string from CCCD
       
        Fields: citizen_id | old_id | full_name | date_of_birth | gender | address | issue_date
        """
        try:
            # Split by pipe separator
            parts = qr_string.strip().split('|')
            
            if len(parts) != 7:
                return None
                
            citizen_id, old_id, full_name, date_of_birth, gender, address, issue_date = parts
            
            # Validate citizen ID (12 digits)
            if not re.match(r'^\d{12}$', citizen_id.strip()):
                return None
                
            # Format date of birth (DDMMYYYY -> DD/MM/YYYY)
            dob_formatted = QRCodeParser._format_date(date_of_birth.strip())
            if not dob_formatted:
                return None
                
            # Format issue date (DDMMYYYY -> DD/MM/YYYY) 
            issue_date_formatted = QRCodeParser._format_date(issue_date.strip())
            if not issue_date_formatted:
                return None
            
            return CCCDData(
                citizen_id=citizen_id.strip(),
                old_id=old_id.strip() if old_id.strip() else None,
                full_name=full_name.strip(),
                date_of_birth=dob_formatted,
                gender=gender.strip(),
                address=address.strip(), 
                issue_date=issue_date_formatted
            )
            
        except Exception as e:
            print(f"Error parsing QR data: {e}")
            return None
    
    @staticmethod
    def _format_date(date_str: str) -> Optional[str]:
        """Format date from DDMMYYYY to DD/MM/YYYY"""
        try:
            if len(date_str) == 8 and date_str.isdigit():
                day = date_str[:2]
                month = date_str[2:4]
                year = date_str[4:8]
                
                # Basic validation
                if 1 <= int(day) <= 31 and 1 <= int(month) <= 12:
                    return f"{day}/{month}/{year}"
                    
            return None
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def validate_cccd_data(data: CCCDData) -> bool:
        """Validate extracted CCCD data"""
        try:
            # Check citizen ID format
            if not re.match(r'^\d{12}$', data.citizen_id):
                return False
                
            # Check name (contains letters and common Vietnamese characters)
            if not re.match(r'^[a-zA-ZÀ-ỹ\s]+$', data.full_name):
                return False
                
            # Check gender
            if data.gender.lower() not in ['nam', 'nữ', 'male', 'female']:
                return False
                
            # Check date format
            if not re.match(r'^\d{2}/\d{2}/\d{4}$', data.date_of_birth):
                return False
                
            if not re.match(r'^\d{2}/\d{2}/\d{4}$', data.issue_date):
                return False
                
            return True
            
        except Exception:
            return False
