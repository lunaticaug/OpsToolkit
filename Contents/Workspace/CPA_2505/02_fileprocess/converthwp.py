"""
구형 HWP(조합형 포함) → DOCX 일괄 변환
------------------------------------
· 스크립트가 놓인 폴더의 *.hwp 를 ./docx 폴더에 저장
· Word 32-/64-bit + Hanword HWP Document Converter가 설치돼 있어야 함
"""

import pathlib, win32com.client as win32

# ───── 경로 ─────────────────────────────────────
here      = pathlib.Path(__file__).resolve().parent
src_dir   = here            # HWP들이 있는 곳
dest_dir  = here / "docx"   # 결과 폴더
dest_dir.mkdir(exist_ok=True)

# ───── Word 열기 ────────────────────────────────
word = win32.Dispatch("Word.Application")
word.DisplayAlerts = 0            # 팝업 억제

# ① “HWP Text Converter” 필터 ID 가져오기
hwp_conv = None
for fc in word.FileConverters:
    if "HWP" in fc.FormatName.upper():
        hwp_conv = fc
        break
if hwp_conv is None:
    raise RuntimeError("HWP 변환기가 Word에 등록되지 않았습니다.")

wdFormatDocx = 16                 # DOCX 저장 포맷 코드

# ───── 변환 루프 ────────────────────────────────
for hwp_path in src_dir.glob("*.hwp"):
    try:
        print("▶", hwp_path.name)
        doc = word.Documents.Open(
            str(hwp_path),
            ConfirmConversions=False,
            ReadOnly=True,
            Format=hwp_conv.OpenFormat  # ★ 필터 강제 지정 ★
        )
        out_path = dest_dir / f"{hwp_path.stem}.docx"
        doc.SaveAs(str(out_path), FileFormat=wdFormatDocx)
        doc.Close(False)
        print("   ✔", out_path.name)
    except Exception as e:
        print("   ✖ 문제 발생:", e)

word.Quit()
print("\n완료! DOCX →", dest_dir)
