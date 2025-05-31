import os
from PyPDF2 import PdfReader

def has_text_layer(pdf_path):
    """
    PDF에 텍스트 레이어가 있는지 확인합니다.
    텍스트가 하나라도 추출되면 True, 없으면 False 반환.
    """
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                return True
        return False
    except Exception as e:
        print(f"[ERROR] {pdf_path} 읽기 실패: {e}")
        return False

def process_pdfs_in_folder(folder_path):
    """
    폴더 내 PDF를 검사하여,
    - 텍스트 레이어 있으면 메시지 출력
    - 없으면 '_noOCR'를 붙여 리네임
    이미 '_noOCR'가 붙은 파일은 건너뜁니다.
    """
    for filename in os.listdir(folder_path):
        if not filename.lower().endswith('.pdf'):
            continue

        name, ext = os.path.splitext(filename)
        if name.endswith('_noOCR'):
            continue

        full_path = os.path.join(folder_path, filename)
        if has_text_layer(full_path):
            print(f"[OK] 텍스트 레이어 있음: {filename}")
        else:
            new_name = f"{name}_noOCR{ext}"
            new_path = os.path.join(folder_path, new_name)
            try:
                os.rename(full_path, new_path)
                print(f"[RENAMED] 텍스트 레이어 없음: {filename} → {new_name}")
            except Exception as e:
                print(f"[ERROR] 리네임 실패: {filename} ({e})")

if __name__ == "__main__":
    # 1) __file__로 스크립트 위치 얻기
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # 2) 스크립트가 있는 폴더를 스캔
    process_pdfs_in_folder(script_dir)
