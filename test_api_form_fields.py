#!/usr/bin/env python3
"""
Test Dynamic Form Fields API
"""

import requests
import json
from pathlib import Path

def test_form_fields_api():
    """
    Test GET /forms/{collection_id}/{doc_id}/{form_name}/fields
    """
    
    # API endpoint
    base_url = "http://localhost:8002"
    endpoint = "/forms/quy_trinh_cap_ho_tich_cap_xa/DOC_001/Khai_sinh.docx/fields"
    
    url = f"{base_url}{endpoint}"
    
    print("🧪 Testing Dynamic Form Fields API")
    print("=" * 50)
    print(f"📡 URL: {url}")
    print()
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API Request Successful!")
            print(f"📊 Response Status: {response.status_code}")
            print()
            
            # Pretty print key information
            if data.get("success"):
                fields = data.get("fields", {})
                form_info = data.get("form_info", {})
                
                print("📋 Form Information:")
                print(f"  • Collection: {form_info.get('collection_id')}")
                print(f"  • Document: {form_info.get('doc_id')}")
                print(f"  • Form Name: {form_info.get('form_name')}")
                print()
                
                print("📊 Field Statistics:")
                print(f"  • Total Fields: {fields.get('total_fields', 0)}")
                print(f"  • CCCD Fields (scan_*): {len(fields.get('scan_fields', []))}")
                print(f"  • User Input Fields (form_*): {len(fields.get('form_fields', []))}")
                print(f"  • Other Fields: {len(fields.get('other_fields', []))}")
                print()
                
                print("🎯 CCCD Fields (Auto-filled):")
                scan_fields = fields.get('scan_fields', [])
                field_metadata = fields.get('field_metadata', {})
                
                for field in scan_fields[:5]:  # Show first 5
                    meta = field_metadata.get(field, {})
                    print(f"  • {field} → {meta.get('display_label', field)} ({meta.get('field_type', 'text')})")
                
                if len(scan_fields) > 5:
                    print(f"  ... and {len(scan_fields) - 5} more")
                print()
                
                print("📝 User Input Fields (Need manual input):")
                form_fields = fields.get('form_fields', [])
                
                for field in form_fields[:10]:  # Show first 10
                    meta = field_metadata.get(field, {})
                    print(f"  • {field} → {meta.get('display_label', field)} ({meta.get('field_type', 'text')})")
                
                if len(form_fields) > 10:
                    print(f"  ... and {len(form_fields) - 10} more")
                
                # Save full response to file
                output_file = Path("api_test_form_fields_response.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"\n💾 Full response saved to: {output_file}")
                
            else:
                print("❌ API returned success=false")
                print(json.dumps(data, indent=2, ensure_ascii=False))
        
        else:
            print(f"❌ API Request Failed!")
            print(f"📊 Status Code: {response.status_code}")
            print(f"📄 Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("💡 Make sure identifill_service is running on port 8002")
        print("   Run: conda activate identifill_env && uvicorn main:app --reload --port 8002")
    
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


def test_multiple_forms():
    """
    Test API với multiple form files
    """
    
    base_url = "http://localhost:8002"
    
    # Test với các form files khác nhau
    test_forms = [
        "Khai_sinh.docx",
        "Khai_sinh_old.docx", 
        "original.docx"
    ]
    
    print("\n🔄 Testing Multiple Forms")
    print("=" * 50)
    
    for form_name in test_forms:
        endpoint = f"/forms/quy_trinh_cap_ho_tich_cap_xa/DOC_001/{form_name}/fields"
        url = f"{base_url}{endpoint}"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                fields = data.get("fields", {})
                print(f"✅ {form_name}: {fields.get('total_fields', 0)} fields")
            else:
                print(f"❌ {form_name}: Status {response.status_code}")
        
        except Exception as e:
            print(f"❌ {form_name}: Error - {e}")


if __name__ == "__main__":
    test_form_fields_api()
    test_multiple_forms()
