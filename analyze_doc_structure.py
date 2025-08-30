# Script để phân tích cấu trúc DOC files
import subprocess
import json
from pathlib import Path

base_path = Path('backend/data/storage/collections/quy_trinh_chung_thuc/documents')

print('=== PHÂN TÍCH CẤU TRÚC 3 FILE DOC ĐẦU TIÊN ===')

# Tạo script PowerShell để đọc DOC
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

script_path = Path('read_doc.ps1')
with open(script_path, 'w', encoding='utf-8') as f:
    f.write(ps_script)

# Đọc 3 file đầu tiên
doc_files = ['DOC_001/1_Cap_ban_sao_tu_so_goc.doc',
             'DOC_002/2.Thủ tục chứng thực bản sao từ bản chính giấy tờ, văn bản.doc',
             'DOC_003/3. Thủ tục chứng thực chữ ký trong các giấy tờ, văn bản.doc']

for i, doc_file in enumerate(doc_files, 1):
    doc_path = base_path / doc_file
    print(f'\n=== FILE {i}: {doc_file} ===')

    if doc_path.exists():
        try:
            result = subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-File', str(script_path),
                '-docPath', str(doc_path.absolute())
            ], capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30)

            if result.returncode == 0 and result.stdout.strip():
                content = result.stdout.strip()
                print(f'✅ Đọc thành công - {len(content)} ký tự')

                # Phân tích cấu trúc nội dung
                lines = content.split('\n')
                print(f'Số dòng: {len(lines)}')

                # Tìm các section chính
                sections = []
                current_section = []

                for line in lines:
                    line = line.strip()
                    if line and len(line) > 5:
                        # Phát hiện tiêu đề (viết hoa, có dấu chấm, v.v.)
                        if (line.isupper() or
                            line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or
                            any(keyword in line.upper() for keyword in ['THÀNH PHẦN', 'THỜI HẠN', 'ĐỐI TƯỢNG', 'KẾT QUẢ', 'QUY TRÌNH', 'LỆ PHÍ'])):
                            if current_section:
                                sections.append('\n'.join(current_section))
                            current_section = [line]
                        else:
                            current_section.append(line)

                if current_section:
                    sections.append('\n'.join(current_section))

                print(f'Số sections tiềm năng: {len(sections)}')
                for j, section in enumerate(sections[:6]):  # Hiển thị 6 section đầu
                    first_line = section.split('\n')[0][:80]
                    print(f'  Section {j+1}: {first_line}...')

                # Lưu nội dung để phân tích thêm
                content_file = Path(f'doc_content_{i}.txt')
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'  Đã lưu: {content_file}')

            else:
                print(f'❌ Lỗi đọc: {result.stderr}')

        except Exception as e:
            print(f'❌ Lỗi: {e}')
    else:
        print(f'❌ File không tồn tại: {doc_path}')

# Dọn dẹp
if script_path.exists():
    script_path.unlink()

print('\n=== TỔNG KẾT PHÂN TÍCH ===')
print('Đã phân tích 3 file DOC đầu tiên')
print('Dựa trên kết quả, tôi sẽ đề xuất số chunks phù hợp')
