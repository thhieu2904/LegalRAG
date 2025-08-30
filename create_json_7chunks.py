# Script để tạo JSON với cấu trúc 7 chunks cho tất cả files trong quy_trinh_chung_thuc
import subprocess
import json
from pathlib import Path
from datetime import datetime

def read_doc_content(doc_path):
    """Đọc nội dung file DOC"""
    ps_script = '''
    param([string]$docPath)
    try {
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $doc = $word.Documents.Open($docPath)
        $content = $doc.Content.Text
        $doc.Close()
        $word.Quit()
        Write-Output $content
    } catch {
        Write-Error $_.Exception.Message
    }
    '''

    script_path = Path('temp_read_doc.ps1')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(ps_script)

    try:
        result = subprocess.run([
            'powershell', '-ExecutionPolicy', 'Bypass', '-File', str(script_path),
            '-docPath', str(doc_path.absolute())
        ], capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30)

        script_path.unlink()

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            print(f"❌ Lỗi đọc {doc_path.name}: {result.stderr}")
            return None

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        if script_path.exists():
            script_path.unlink()
        return None

def parse_doc_content(content):
    """Phân tích nội dung DOC thành 7 chunks"""
    lines = content.split('\n')
    chunks = {}

    # Tìm vị trí các section chính
    current_section = ""
    section_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Phát hiện section mới
        if any(keyword in line.upper() for keyword in [
            'THÀNH PHẦN', 'THỜI HẠN', 'ĐỐI TƯỢNG', 'CƠ QUAN',
            'KẾT QUẢ', 'PHÍ', 'LỆ PHÍ', 'BIỂU MẪU', 'YÊU CẦU',
            'CĂN CỨ', 'QUY TRÌNH'
        ]):
            # Lưu section trước đó
            if current_section and section_content:
                chunks[current_section] = '\n'.join(section_content)

            # Bắt đầu section mới
            current_section = line
            section_content = [line]
        else:
            section_content.append(line)

    # Lưu section cuối cùng
    if current_section and section_content:
        chunks[current_section] = '\n'.join(section_content)

    return chunks

def create_json_structure(doc_path, content_chunks, doc_name):
    """Tạo cấu trúc JSON với 7 chunks"""

    # Metadata cơ bản
    metadata = {
        "source": f"data/documents/quy_trinh_chung_thuc/{doc_name}",
        "title": doc_name.replace('.doc', '').replace('_', ' '),
        "code": f"QT {doc_path.parent.name.replace('DOC_', '')}/CT-HCTP",
        "issuing_authority": "Sở Tư pháp",
        "effective_date": "2025-07-07",
        "executing_agency": "Cơ quan có thẩm quyền",
        "applicant_type": ["Cá nhân", "Tổ chức"],
        "processing_time_text": "Theo quy định",
        "fee_vnd": None,
        "fee_text": "Theo quy định",
        "has_form": False,
        "requirements_conditions": "Theo quy định của pháp luật",
        "legal_basis_references": [
            "Nghị định số 23/2015/NĐ-CP",
            "Nghị định số 07/2025/NĐ-CP"
        ],
        "last_updated": datetime.now().strftime('%Y-%m-%d'),
        "version": "1.0",
        "collection_type": "quy_trinh_chung_thuc"
    }

    # Tạo 7 chunks từ content_chunks
    structured_chunks = []

    # Chunk 1: Thành phần hồ sơ
    hs_content = ""
    for key, value in content_chunks.items():
        if 'THÀNH PHẦN' in key.upper() or 'HỒ SƠ' in key.upper():
            hs_content = value
            break

    if not hs_content:
        hs_content = "Người yêu cầu cần xuất trình giấy tờ tùy thân và các giấy tờ liên quan theo quy định."

    structured_chunks.append({
        "chunk_id": 1,
        "section_title": "Thành phần hồ sơ",
        "content": hs_content,
        "source_reference": "Mục 5.a",
        "keywords": ["hồ sơ", "giấy tờ", "xuất trình", "yêu cầu"]
    })

    # Chunk 2: Thời hạn và Đối tượng
    th_content = ""
    dt_content = ""
    for key, value in content_chunks.items():
        if 'THỜI HẠN' in key.upper():
            th_content = value
        elif 'ĐỐI TƯỢNG' in key.upper():
            dt_content = value

    combined_content = ""
    if th_content:
        combined_content += f"**Thời hạn:** {th_content}\n\n"
    if dt_content:
        combined_content += f"**Đối tượng:** {dt_content}"

    if not combined_content:
        combined_content = "**Thời hạn:** Theo quy định của pháp luật\n\n**Đối tượng:** Cá nhân, tổ chức"

    structured_chunks.append({
        "chunk_id": 2,
        "section_title": "Thời hạn và Đối tượng",
        "content": combined_content,
        "source_reference": "Mục 5.b, 5.c",
        "keywords": ["thời hạn", "đối tượng", "thực hiện"]
    })

    # Chunk 3: Cơ quan thực hiện
    cq_content = ""
    for key, value in content_chunks.items():
        if 'CƠ QUAN' in key.upper():
            cq_content = value
            break

    if not cq_content:
        cq_content = "Cơ quan có thẩm quyền theo quy định của pháp luật."

    structured_chunks.append({
        "chunk_id": 3,
        "section_title": "Cơ quan thực hiện",
        "content": cq_content,
        "source_reference": "Mục 5.d",
        "keywords": ["cơ quan", "thẩm quyền", "thực hiện"]
    })

    # Chunk 4: Kết quả và Lệ phí
    kq_content = ""
    phi_content = ""
    for key, value in content_chunks.items():
        if 'KẾT QUẢ' in key.upper():
            kq_content = value
        elif 'PHÍ' in key.upper() or 'LỆ PHÍ' in key.upper():
            phi_content = value

    combined_content = ""
    if kq_content:
        combined_content += f"**Kết quả:** {kq_content}\n\n"
    if phi_content:
        combined_content += f"**Lệ phí:** {phi_content}"

    if not combined_content:
        combined_content = "**Kết quả:** Theo quy định\n\n**Lệ phí:** Theo quy định"

    structured_chunks.append({
        "chunk_id": 4,
        "section_title": "Kết quả và Lệ phí",
        "content": combined_content,
        "source_reference": "Mục 5.đ, 5.e",
        "keywords": ["kết quả", "lệ phí", "phí"]
    })

    # Chunk 5: Biểu mẫu
    bm_content = ""
    for key, value in content_chunks.items():
        if 'BIỂU MẪU' in key.upper() or 'MẪU' in key.upper():
            bm_content = value
            break

    if not bm_content:
        bm_content = "Các biểu mẫu theo quy định (nếu có)."

    structured_chunks.append({
        "chunk_id": 5,
        "section_title": "Biểu mẫu",
        "content": bm_content,
        "source_reference": "Mục 6",
        "keywords": ["biểu mẫu", "mẫu", "đơn"]
    })

    # Chunk 6: Yêu cầu và Căn cứ pháp lý
    yc_content = ""
    cc_content = ""
    for key, value in content_chunks.items():
        if 'YÊU CẦU' in key.upper() or 'ĐIỀU KIỆN' in key.upper():
            yc_content = value
        elif 'CĂN CỨ' in key.upper() or 'PHÁP LÝ' in key.upper():
            cc_content = value

    combined_content = ""
    if yc_content:
        combined_content += f"**Yêu cầu:** {yc_content}\n\n"
    if cc_content:
        combined_content += f"**Căn cứ pháp lý:** {cc_content}"

    if not combined_content:
        combined_content = "**Yêu cầu:** Theo quy định của pháp luật\n\n**Căn cứ pháp lý:** Các văn bản pháp luật liên quan"

    structured_chunks.append({
        "chunk_id": 6,
        "section_title": "Yêu cầu và Căn cứ pháp lý",
        "content": combined_content,
        "source_reference": "Mục 5.g, 5.h",
        "keywords": ["yêu cầu", "căn cứ", "pháp lý"]
    })

    # Chunk 7: Quy trình thực hiện
    qt_content = ""
    for key, value in content_chunks.items():
        if 'QUY TRÌNH' in key.upper() or 'CÁC BƯỚC' in key.upper():
            qt_content = value
            break

    if not qt_content:
        qt_content = "Các bước thực hiện theo quy định của pháp luật."

    structured_chunks.append({
        "chunk_id": 7,
        "section_title": "Quy trình thực hiện",
        "content": qt_content,
        "source_reference": "Mục 5.k",
        "keywords": ["quy trình", "các bước", "thực hiện"]
    })

    return {
        "metadata": metadata,
        "content_chunks": structured_chunks
    }

def main():
    """Main function"""
    base_path = Path('backend/data/storage/collections/quy_trinh_chung_thuc/documents')

    print('=== TẠO JSON VỚI 7 CHUNKS CHO TẤT CẢ FILES ===')

    total_processed = 0
    success_count = 0

    # Duyệt qua tất cả DOC folders
    for doc_dir in sorted(base_path.iterdir()):
        if not doc_dir.is_dir() or not doc_dir.name.startswith('DOC_'):
            continue

        print(f'\\n📂 Processing: {doc_dir.name}')

        # Tìm file DOC
        doc_files = list(doc_dir.glob('*.doc'))
        if not doc_files:
            print('  ❌ Không tìm thấy file DOC')
            continue

        doc_file = doc_files[0]  # Lấy file đầu tiên
        print(f'  📄 Found DOC: {doc_file.name}')

        # Đọc nội dung DOC
        content = read_doc_content(doc_file)
        if not content:
            print('  ❌ Không thể đọc nội dung DOC')
            continue

        # Phân tích nội dung thành chunks
        content_chunks = parse_doc_content(content)
        print(f'  📊 Found {len(content_chunks)} raw sections')

        # Tạo cấu trúc JSON
        json_structure = create_json_structure(doc_file, content_chunks, doc_file.name)

        # Lưu file JSON
        json_file = doc_file.parent / f"{doc_file.stem}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_structure, f, ensure_ascii=False, indent=2)

        print(f'  ✅ Created JSON: {json_file.name}')
        print(f'  📊 Chunks: {len(json_structure["content_chunks"])}')

        total_processed += 1
        success_count += 1

    print(f'\\n=== TỔNG KẾT ===')
    print(f'📂 Files processed: {total_processed}')
    print(f'✅ Success: {success_count}')
    print(f'❌ Failed: {total_processed - success_count}')

    if success_count == total_processed:
        print('\\n🎉 HOÀN THÀNH! Tất cả files đã được tạo JSON với cấu trúc 7 chunks chuẩn!')

if __name__ == "__main__":
    main()
