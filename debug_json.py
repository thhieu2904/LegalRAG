import json

# Debug script để kiểm tra cấu trúc JSON
json_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents\DOC_028\28. Ghi vào Sổ hộ tịch việc ly hôn, hủy việc kết hôn của công dân Việt Nam đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài.json"

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== DEBUG JSON STRUCTURE ===")
print(f"Keys in data: {list(data.keys())}")

metadata = data.get('metadata', {})
print(f"\nMetadata keys: {list(metadata.keys())}")

fee_structure = data.get('fee_structure', {})
print(f"\nFee structure keys: {list(fee_structure.keys())}")
print(f"Fee structure type: {type(fee_structure)}")

if fee_structure:
    main_fee = fee_structure.get('main_fee', {})
    print(f"\nMain fee: {main_fee}")
    print(f"Main fee type: {type(main_fee)}")

    regional_fees = fee_structure.get('regional_fees', [])
    print(f"\nRegional fees: {regional_fees}")
    print(f"Regional fees type: {type(regional_fees)}")

    exemptions = fee_structure.get('exemptions', [])
    print(f"\nExemptions: {exemptions}")
    print(f"Exemptions type: {type(exemptions)}")

    additional_fees = fee_structure.get('additional_fees', {})
    print(f"\nAdditional fees: {additional_fees}")
    print(f"Additional fees type: {type(additional_fees)}")

print("\n=== TESTING FEE STRUCTURE ACCESS ===")
if isinstance(fee_structure, dict):
    print("Fee structure is dict - OK")
    main_fee = fee_structure.get('main_fee', {})
    if isinstance(main_fee, dict):
        print("Main fee is dict - OK")
        print(f"Direct fee: {main_fee.get('direct', 'N/A')}")
        print(f"Online fee: {main_fee.get('online', 'N/A')}")
    else:
        print(f"Main fee is not dict: {type(main_fee)}")

    regional_fees = fee_structure.get('regional_fees', [])
    if isinstance(regional_fees, list):
        print("Regional fees is list - OK")
        for i, fee in enumerate(regional_fees):
            print(f"Regional fee {i}: {fee}")
    else:
        print(f"Regional fees is not list: {type(regional_fees)}")
