# convert_hwp_to_docx.py
# ----------------------------------------------------------
# ▸ 동작:  이 파이썬 파일이 놓인 폴더(=script_dir)에 있는 *.hwp 를
#          같은 위치의 ./docx 하위 폴더에 *.docx 로 일괄 저장
# ▸ 요구:  Windows + Microsoft Word(32/64-bit) + pywin32
# ----------------------------------------------------------

import pathlib
import win32com.client as win32

# 1) 경로 설정 ------------------------------------------------
script_dir = pathlib.Path(__file__).resolve().parent     # 스크립트 위치
src_dir    = script_dir                                  # HWP 원본 폴더
dest_dir   = script_dir / "docx"                         # DOCX 저장 폴더
dest_dir.mkdir(exist_ok=True)

print(f"Source folder : {src_dir}")
print(f"Output folder : {dest_dir}\n")

# 2) Word COM 초기화 -----------------------------------------
wd_format_docx = 16               # FileFormat 값 (docx)
word = win32.Dispatch("Word.Application")
word.DisplayAlerts = 0            # 팝업 억제

# 3) 변환 루프 -----------------------------------------------
hwp_files = list(src_dir.glob("*.hwp"))
if not hwp_files:
    print("⚠️  변환할 .hwp 파일이 없습니다.")
else:
    for hwp_path in hwp_files:
        try:
            print(f"▶ 변환 중: {hwp_path.name}")
            doc = word.Documents.Open(
                str(hwp_path),
                ConfirmConversions=False,   # 변환기 대화상자 OFF
                ReadOnly=True
            )
            out_path = dest_dir / f"{hwp_path.stem}.docx"
            doc.SaveAs(str(out_path), FileFormat=wd_format_docx)
            doc.Close(False)
            print(f"   ✔ 저장 완료 → {out_path.name}")
        except Exception as err:
            print(f"   ✖ 오류    → {err}")

# 4) 종료 -----------------------------------------------------
word.Quit()
print("\n모든 변환 작업이 완료되었습니다.")
