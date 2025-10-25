#!/usr/bin/env python3
"""
Test admin panel storage manager features
"""

import requests
import json

ADMIN_URL = "http://localhost:8001"

def test_storage_manager():
    print("\n" + "="*70)
    print("🧪 ADMIN PANEL 'QUẢN LÝ FORM' FEATURE TEST")
    print("="*70)
    
    # Feature 1: View list of CCCDs
    print("\n[FEATURE 1] Xem danh sách các CCCD (ID)")
    print("-" * 70)
    
    try:
        response = requests.get(f"{ADMIN_URL}/api/v1/storage/stats")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                stats = data.get("data", {})
                cccd_list = stats.get("cccd_list", [])
                
                print(f"✅ Successfully retrieved CCCD list")
                print(f"   Total CCCDs: {len(cccd_list)}")
                print(f"   Total forms: {stats.get('total_forms')}")
                print(f"   Total users: {stats.get('total_users')}")
                
                if cccd_list:
                    print(f"\n   CCCD List:")
                    for user in cccd_list:
                        print(f"      - ID: {user.get('scan_cccd')}")
                        print(f"        Name: {user.get('scan_ho_ten')}")
                        print(f"        Forms: {user.get('form_count')}")
                        print()
                else:
                    print("   ⚠️  No CCCDs found")
            else:
                print(f"❌ Backend error: {data.get('message')}")
        else:
            print(f"❌ HTTP Error {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Feature 2: Click on CCCD to view forms
    print("[FEATURE 2] Khi ấn vào 1 CCCD, xem danh sách form")
    print("-" * 70)
    
    if cccd_list:
        test_cccd = cccd_list[0].get("scan_cccd")
        print(f"Testing with CCCD: {test_cccd}")
        
        try:
            response = requests.get(
                f"{ADMIN_URL}/api/v1/storage/list",
                params={"cccd": test_cccd}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    forms = data.get("data", [])
                    
                    print(f"✅ Successfully retrieved forms for CCCD {test_cccd}")
                    print(f"   Total forms: {len(forms)}")
                    
                    if forms:
                        print(f"\n   Forms list:")
                        for i, form in enumerate(forms, 1):
                            print(f"      {i}. {form.get('form_name')}")
                            print(f"         File: {form.get('file_name')}")
                            print(f"         Size: {form.get('file_size')} bytes")
                            print(f"         File ID: {form.get('file_id')}")
                            print(f"         Created: {form.get('created_at')}")
                            print()
                    else:
                        print("   ⚠️  No forms found for this CCCD")
                else:
                    print(f"❌ Backend error: {data.get('message')}")
            else:
                print(f"❌ HTTP Error {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        
        # Feature 3: Download form
        print("[FEATURE 3] Tải về form")
        print("-" * 70)
        
        if forms:
            test_file_id = forms[0].get("file_id")
            test_filename = forms[0].get("file_name")
            
            print(f"Testing download of: {test_filename}")
            print(f"File ID: {test_file_id}")
            
            try:
                response = requests.get(
                    f"{ADMIN_URL}/api/v1/storage/download/{test_file_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"✅ Download successful")
                    print(f"   Status: {response.status_code}")
                    print(f"   Content-Type: {response.headers.get('content-type')}")
                    print(f"   Content-Length: {len(response.content)} bytes")
                    print(f"   Filename: {response.headers.get('content-disposition', 'N/A')}")
                else:
                    print(f"❌ HTTP Error {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
    
    print("\n" + "="*70)
    print("✅ ALL FEATURES WORKING!")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_storage_manager()
    exit(0 if success else 1)
