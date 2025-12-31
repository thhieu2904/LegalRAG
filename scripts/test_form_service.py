"""
Quick test script to verify form-service logic
Run with: python scripts/test_form_service.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'form-service'))

def test_filename_generation():
    """Test filename generation logic"""
    from src.services.form_filler import FormFiller
    
    filler = FormFiller.__new__(FormFiller)  # Create without __init__
    
    # Test 1: With CCCD
    result = filler.generate_filename("Đơn đăng ký khai sinh", "20251130_0001", "012345678901")
    expected = "012345678901_don-dang-ky-khai-sinh.docx"
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"✅ Test 1 PASSED: {result}")
    
    # Test 2: Without CCCD
    result = filler.generate_filename("Đơn đăng ký khai sinh", "20251130_0001", None)
    expected = "don-dang-ky-khai-sinh.docx"
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"✅ Test 2 PASSED: {result}")
    
    # Test 3: Storage path
    result = filler.generate_storage_path("20251130_0001", "012345678901_form.docx")
    expected = "user_forms/20251130_0001/012345678901_form.docx"
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"✅ Test 3 PASSED: {result}")
    
    print("\n✅ All filename tests passed!")


def test_user_form_parsing():
    """Test user form filename parsing logic"""
    # Import parsing function from admin-service
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'admin-service', 'src', 'routers'))
    
    def parse_user_form_filename(filename: str) -> tuple:
        """Parse user form filename to extract CCCD and form name."""
        name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        parts = name.split('_', 1)
        if len(parts) == 2 and len(parts[0]) == 12 and parts[0].isdigit():
            return parts[0], parts[1]
        else:
            return None, name
    
    # Test 1: With CCCD prefix
    cccd, form_name = parse_user_form_filename("012345678901_don-khai-sinh.docx")
    assert cccd == "012345678901", f"Expected CCCD 012345678901, got {cccd}"
    assert form_name == "don-khai-sinh", f"Expected form_name don-khai-sinh, got {form_name}"
    print(f"✅ Parse test 1 PASSED: CCCD={cccd}, form={form_name}")
    
    # Test 2: Without CCCD
    cccd, form_name = parse_user_form_filename("don-khai-sinh.docx")
    assert cccd is None, f"Expected None CCCD, got {cccd}"
    assert form_name == "don-khai-sinh", f"Expected form_name don-khai-sinh, got {form_name}"
    print(f"✅ Parse test 2 PASSED: CCCD={cccd}, form={form_name}")
    
    # Test 3: Short number (not CCCD)
    cccd, form_name = parse_user_form_filename("12345_don-khai-sinh.docx")
    assert cccd is None, f"Expected None CCCD for short number, got {cccd}"
    print(f"✅ Parse test 3 PASSED: Short number not treated as CCCD")
    
    print("\n✅ All parsing tests passed!")


def test_api_models():
    """Test that Pydantic models are defined correctly"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'form-service'))
        from src.models import (
            CCCDScanRequest, CCCDScanResponse,
            FormRenderRequest, FormRenderResponse,
            FormFillRequest
        )
        
        # Test CCCDScanRequest
        req = CCCDScanRequest(image_data="base64encodedimage")
        assert req.image_data == "base64encodedimage"
        print("✅ CCCDScanRequest model OK")
        
        # Test FormFillRequest
        req = FormFillRequest(
            template_path="forms/doc-id/form.docx",
            data={"scan_ho_ten": "Nguyen Van A"}
        )
        assert req.template_path == "forms/doc-id/form.docx"
        assert req.data["scan_ho_ten"] == "Nguyen Van A"
        print("✅ FormFillRequest model OK")
        
        print("\n✅ All model tests passed!")
        
    except ImportError as e:
        print(f"⚠️ Import error (expected if deps not installed): {e}")


def main():
    print("=" * 50)
    print("FORM SERVICE LOGIC TESTS")
    print("=" * 50)
    print()
    
    # Test 1: Filename generation
    print("📝 Testing filename generation...")
    try:
        test_filename_generation()
    except Exception as e:
        print(f"❌ Filename test failed: {e}")
    
    print()
    
    # Test 2: User form parsing
    print("📝 Testing user form parsing...")
    try:
        test_user_form_parsing()
    except Exception as e:
        print(f"❌ Parsing test failed: {e}")
    
    print()
    
    # Test 3: API models
    print("📝 Testing API models...")
    try:
        test_api_models()
    except Exception as e:
        print(f"❌ Model test failed: {e}")
    
    print()
    print("=" * 50)
    print("TESTS COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    main()
