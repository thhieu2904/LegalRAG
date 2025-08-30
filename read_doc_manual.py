# Script đọc file DOC thủ công
import subprocess
from pathlib import Path

def read_doc_manual(doc_path):
    """Đọc file DOC thủ công"""
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

    script_path = Path('temp_read.ps1')
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(ps_script)

    try:
        result = subprocess.run([
            'powershell', '-ExecutionPolicy', 'Bypass', '-File', str(script_path),
            '-docPath', str(doc_path.absolute())
        ], capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30)

        if script_path.exists():
            script_path.unlink()

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            print(f'❌ Lỗi đọc: {result.stderr}')
            return None

    except Exception as e:
        print(f'❌ Lỗi: {e}')
        if script_path.exists():
            script_path.unlink()
        return None

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python read_doc_manual.py <doc_path> <output_path>")
        return
    
    doc_path_input = sys.argv[1]
    output_path = sys.argv[2]
    
    doc_path = Path(doc_path_input)
    
    # Extract filename for display
    filename = doc_path.stem
    doc_number = filename.split('.')[0] if '.' in filename else 'DOC'
    
    print(f'=== ĐỌC FILE {doc_number.upper()} THỦ CÔNG ===')

    content = read_doc_manual(doc_path)
    if content:
        print('✅ Đọc thành công!')
        print(f'Độ dài: {len(content)} ký tự')

        # Lưu nội dung để phân tích
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'\nĐã lưu nội dung vào: {output_path}')
        print('\nBây giờ tôi sẽ phân tích và tạo JSON thủ công...')

if __name__ == "__main__":
    main()
