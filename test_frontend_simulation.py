#!/usr/bin/env python3
"""
🧪 Frontend Storage Manager Simulation Test
Simulates the exact flow that happens in StorageManager.tsx
"""

import requests
import json
from typing import Any

ADMIN_URL = "http://localhost:8001"

class FrontendSimulator:
    """Simulates frontend API calls"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def fetch_storage_stats(self) -> dict:
        """Simulate: const data = await adminApi.fetchStorageStats()"""
        print("\n📊 Calling: fetchStorageStats()")
        print("   └─ GET /api/v1/storage/stats")
        
        try:
            response = self.session.get(f"{ADMIN_URL}/api/v1/storage/stats")
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Simulate frontend check: if (!response.data.success)
            if not data.get("success"):
                raise Exception(f"Backend error: {data.get('message')}")
            
            # Extract actual data
            stats = data.get("data")
            print(f"   ✅ Success! Retrieved {stats.get('total_forms')} forms from {stats.get('total_users')} users")
            print(f"   ✅ CCCD list: {len(stats.get('cccd_list', []))} users")
            
            return stats
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            raise
    
    def fetch_forms_by_cccd(self, cccd: str) -> list:
        """Simulate: const data = await adminApi.fetchFormsByCCCD(cccd)"""
        print(f"\n📋 Calling: fetchFormsByCCCD('{cccd}')")
        print(f"   └─ GET /api/v1/storage/list?cccd={cccd}")
        
        try:
            response = self.session.get(
                f"{ADMIN_URL}/api/v1/storage/list",
                params={"cccd": cccd}
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Simulate frontend check: if (!response.data.success)
            if not data.get("success"):
                raise Exception(f"Backend error: {data.get('message')}")
            
            forms = data.get("data")
            print(f"   ✅ Success! Retrieved {len(forms)} forms")
            for form in forms:
                print(f"      - {form.get('form_name')} ({form.get('file_name')})")
            
            return forms
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            raise

def main():
    print("="*70)
    print("🧪 FRONTEND STORAGE MANAGER SIMULATION TEST")
    print("="*70)
    print("\nSimulating: StorageManager.tsx -> loadStats() flow")
    
    simulator = FrontendSimulator()
    
    try:
        # Step 1: Load stats (same as StorageManager line 55-60)
        print("\n[STEP 1] StorageManager mounts → calls loadStats()")
        stats = simulator.fetch_storage_stats()
        
        # Step 2: Get first user
        if stats.get('cccd_list'):
            first_user = stats['cccd_list'][0]
            print(f"\n[STEP 2] User clicks on first user in list")
            print(f"         CCCD: {first_user.get('scan_cccd')}")
            print(f"         Name: {first_user.get('scan_ho_ten')}")
            print(f"         Forms: {first_user.get('form_count')}")
            
            # Step 3: Load forms for this user (same as StorageManager line 74-80)
            print(f"\n[STEP 3] StorageManager calls loadUserForms()")
            forms = simulator.fetch_forms_by_cccd(first_user['scan_cccd'])
            
            if forms:
                print(f"\n[RESULT] ✅ SUCCESS!")
                print(f"  - Admin panel can load stats")
                print(f"  - Admin panel can load user's forms")
                print(f"  - All API responses are properly wrapped")
        else:
            print("\n⚠️  No users with forms in storage")
            
    except Exception as e:
        print(f"\n[RESULT] ❌ FAILURE!")
        print(f"  Error: {e}")
        print(f"\nThis is what frontend gets:")
        print(f"  - Frontend tries to access response.data.success")
        print(f"  - If success field is missing → throws 'Failed to fetch storage stats'")
        return False
    
    print("\n" + "="*70)
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
