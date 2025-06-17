import os
import re
import fitz  # PyMuPDF

def count_hangul_chars(text):
    """문자열에서 한글 음절(U+AC00–U+D7AF)만 골라 개수 반환"""
    return len(re.findall(r'[\uac00-\ud7af]', text))

def has_text_layer_by_hangul(pdf_path, min_hangul_per_page=50):
    """
    1) PyMuPDF로 텍스트 추출
    2) 전체 한글 문자 개수 ≥ pages * min_hangul_per_page 이면 True 반환
    """
    try:
        doc = fitz.open(pdf_path)
        total_hangul = 0
        for page in doc:
            txt = page.get_text() or ""
            total_hangul += count_hangul_chars(txt)
        page_count = doc.page_count
        # 임계값 계산
        required = page_count * min_hangul_per_page
        return total_hangul >= required
    except Exception as e:
        print(f"[ERROR] {pdf_path} 처리 중 오류: {e}")
        return False

def process_pdfs(folder_path, min_hangul_per_page=50):
    """
    스크립트 위치 기준 폴더 스캔:
      - 조건 만족(pdf당 한글 수 충분) → [OK]
      - 그렇지 않으면 '_noOCR' 붙여 리네임
    """
    for fn in os.listdir(folder_path):
        if not fn.lower().endswith('.pdf'):
            continue
        name, ext = os.path.splitext(fn)
        if name.endswith('_noOCR'):
            continue

        full = os.path.join(folder_path, fn)
        if has_text_layer_by_hangul(full, min_hangul_per_page):
            print(f"[OK] 충분한 한글 탐지: {fn}")
        else:
            new = f"{name}_noOCR{ext}"
            try:
                os.rename(full, os.path.join(folder_path, new))
                print(f"[RENAMED] 한글 부족: {fn} → {new}")
            except Exception as e:
                print(f"[ERROR] 리네임 실패: {fn} ({e})")

if __name__ == "__main__":
    import os
    # 1) 스크립트가 있는 폴더 기준
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # 2) 페이지당 최소 한글 50자 기준 (원하는 값으로 조정 가능)
    process_pdfs(script_dir, min_hangul_per_page=100)
