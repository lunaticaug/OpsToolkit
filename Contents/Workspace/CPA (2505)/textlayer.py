import os
from PyPDF2 import PdfReader

def has_text_layer(pdf_path):
    """
    1) PyPDF2로 텍스트 추출 시도
    2) 실패 시, PDF 내부 바이트에서 '/Font' 또는 텍스트 오퍼레이터 존재 여부 확인
    """
    try:
        reader = PdfReader(pdf_path)
        # 1) extract_text로 확인
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                return True
        # 2) 폴백: raw bytes에서 텍스트 관련 키워드 검색
        with open(pdf_path, 'rb') as f:
            head = f.read(1024 * 1024)  # 앞 1MB만 읽어도 충분
        keywords = [b'/Font', b'Tj', b'TJ', b'BT', b'ET']
        if any(kw in head for kw in keywords):
            return True
        return False
    except Exception as e:
        print(f"[ERROR] {pdf_path} 읽기 실패: {e}")
        return False

def process_pdfs_in_folder(folder_path):
    """
    스크립트 위치 기준 폴더 스캔:
    - 텍스트 레이어 있으면 [OK] 메시지
    - 없으면 '_noOCR' 붙여 리네임
    """
    for filename in os.listdir(folder_path):
        if not filename.lower().endswith('.pdf'):
            continue
        name, ext = os.path.splitext(filename)
        if name.endswith('_noOCR'):
            continue

        full = os.path.join(folder_path, filename)
        if has_text_layer(full):
            print(f"[OK] 텍스트 레이어 있음: {filename}")
        else:
            new_name = f"{name}_noOCR{ext}"
            new_path = os.path.join(folder_path, new_name)
            try:
                os.rename(full, new_path)
                print(f"[RENAMED] 텍스트 레이어 없음: {filename} → {new_name}")
            except Exception as e:
                print(f"[ERROR] 리네임 실패: {filename} ({e})")

if __name__ == "__main__":
    # 스크립트가 있는 폴더를 기준으로 자동 스캔
    script_dir = os.path.dirname(os.path.realpath(__file__))
    process_pdfs_in_folder(script_dir)
