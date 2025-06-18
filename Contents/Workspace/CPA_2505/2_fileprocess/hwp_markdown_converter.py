# hwp_to_markdown_batch.py
# ----------------------------------------------------------
# ▸ 동작: fulldata/hwp 폴더의 *.hwp 를 docx 거쳐 markdown으로 변환
# ▸ 경로: OpsToolkit/Contents/Workspace/CPA_2505/ 에서 실행
# ▸ 요구: Windows + Microsoft Word + pywin32
# ----------------------------------------------------------

import pathlib
import win32com.client as win32
import re

def setup_paths():
    """경로 설정"""
    script_dir = pathlib.Path(__file__).resolve().parent
    
    # 스크립트가 hwp 폴더에 있다면 현재 폴더가 hwp_dir
    if script_dir.name == "hwp":
        hwp_dir = script_dir
        output_base = script_dir.parent / "output"
    else:
        # 스크립트가 다른 곳에 있다면 fulldata/hwp 찾기
        hwp_dir = script_dir / "fulldata" / "hwp"
        output_base = script_dir / "output"
    
    docx_dir = output_base / "docx"
    md_dir = output_base / "markdown"
    
    # 출력 폴더 생성
    docx_dir.mkdir(parents=True, exist_ok=True)
    md_dir.mkdir(parents=True, exist_ok=True)
    
    return hwp_dir, docx_dir, md_dir

def hwp_to_docx(hwp_dir, docx_dir):
    """HWP → DOCX 변환 (다른 확장자는 무시)"""
    print("=" * 50)
    print("1단계: HWP → DOCX 변환")
    print("=" * 50)
    
    # HWP 파일만 찾기
    hwp_files = list(hwp_dir.glob("*.hwp"))
    if not hwp_files:
        print("⚠️  변환할 .hwp 파일이 없습니다.")
        return []
    
    print(f"총 {len(hwp_files)}개의 HWP 파일 발견")
    
    # Word COM 초기화
    word = win32.Dispatch("Word.Application")
    word.DisplayAlerts = 0
    word.Visible = False
    
    converted_files = []
    
    for i, hwp_path in enumerate(hwp_files, 1):
        try:
            print(f"▶ [{i}/{len(hwp_files)}] 변환 중: {hwp_path.name}")
            
            # HWP 파일 열기
            doc = word.Documents.Open(
                str(hwp_path),
                ConfirmConversions=False,
                ReadOnly=True
            )
            
            # DOCX로 저장
            docx_path = docx_dir / f"{hwp_path.stem}.docx"
            doc.SaveAs2(str(docx_path), FileFormat=16)  # 16 = docx
            doc.Close(False)
            
            converted_files.append(docx_path)
            print(f"   ✔ 완료: {docx_path.name}")
            
        except Exception as err:
            print(f"   ✖ 오류: {hwp_path.name} - {err}")
    
    word.Quit()
    return converted_files

def format_to_markdown(text):
    """텍스트를 마크다운으로 기본 포맷팅"""
    if not text:
        return ""
    
    # 연속된 공백/줄바꿈 정리
    text = re.sub(r'\r\n', '\n', text)  # Windows 줄바꿈 통일
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # 3개 이상 줄바꿈을 2개로
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)  # 각 줄 앞뒤 공백 제거
    
    # 기본적인 제목 감지 (단순한 패턴)
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
            
        # 간단한 제목 감지 (숫자로 시작하는 짧은 줄)
        if (len(line) < 50 and 
            (re.match(r'^\d+\.', line) or  # "1. 제목" 형태
             re.match(r'^제\s*\d+', line) or  # "제1장" 형태
             line.isupper())):  # 모두 대문자
            formatted_lines.append(f"## {line}")
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def docx_to_markdown(docx_files, md_dir):
    """DOCX → Markdown 변환"""
    print("\n" + "=" * 50)
    print("2단계: DOCX → Markdown 변환")
    print("=" * 50)
    
    if not docx_files:
        print("변환할 DOCX 파일이 없습니다.")
        return
    
    word = win32.Dispatch("Word.Application")
    word.DisplayAlerts = 0
    word.Visible = False
    
    for i, docx_path in enumerate(docx_files, 1):
        try:
            print(f"▶ [{i}/{len(docx_files)}] 처리 중: {docx_path.name}")
            
            # DOCX 파일 열기
            doc = word.Documents.Open(str(docx_path))
            
            # 텍스트 추출
            text = doc.Content.Text
            
            # 마크다운 포맷팅
            markdown_text = format_to_markdown(text)
            
            # 마크다운 파일로 저장
            md_path = md_dir / f"{docx_path.stem}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {docx_path.stem}\n\n")  # 파일명을 제목으로
                f.write(markdown_text)
            
            doc.Close()
            print(f"   ✔ 완료: {md_path.name}")
            
        except Exception as e:
            print(f"   ✖ 오류: {docx_path.name} - {e}")
    
    word.Quit()

def main():
    """메인 실행 함수"""
    print("HWP → Markdown 일괄 변환기")
    print("대상 경로: fulldata/hwp/*.hwp")
    
    # 경로 설정
    hwp_dir, docx_dir, md_dir = setup_paths()
    
    print(f"\n📁 HWP 폴더: {hwp_dir}")
    print(f"📁 DOCX 출력: {docx_dir}")
    print(f"📁 Markdown 출력: {md_dir}")
    
    # 1단계: HWP → DOCX
    converted_files = hwp_to_docx(hwp_dir, docx_dir)
    
    # 2단계: DOCX → Markdown
    docx_to_markdown(converted_files, md_dir)
    
    print("\n" + "=" * 50)
    print("🎉 모든 변환 작업이 완료되었습니다!")
    print(f"📄 변환된 파일: {len(converted_files)}개")
    print(f"📂 결과 위치: {md_dir}")
    print("=" * 50)

if __name__ == "__main__":
    main()