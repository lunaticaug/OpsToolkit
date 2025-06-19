# hwp2docx_batch.py  (최종 수정본)
import pathlib, sys
import win32com.client as win32

def list_file_converters(word):
    print("\n[Word FileConverters 목록]")
    print("No  FormatName                    Extensions")
    print("──  ───────────────────────────── ──────────")
    for n, fc in enumerate(word.FileConverters, start=1):
        fmt = getattr(fc, "FormatName", "(unknown)")
        ext = getattr(fc, "Extensions", "-")
        print(f"{n:>2}  {fmt:<28} {ext}")
    print("─" * 50)

def find_hwp_converter(word):
    """FormatName · Extensions 둘 다 검사해 첫 번째 HWP 변환기를 반환"""
    for fc in word.FileConverters:
        fmt = getattr(fc, "FormatName", "").upper()
        ext = getattr(fc, "Extensions", "").upper()
        if "HWP" in fmt or "HWP" in ext:
            return fc
    return None

def main():
    script_dir = pathlib.Path(__file__).resolve().parent
    src_dir    = script_dir
    dest_dir   = script_dir / "docx"
    dest_dir.mkdir(exist_ok=True)

    print(f"Source : {src_dir}")
    print(f"Output : {dest_dir}")

    word = win32.Dispatch("Word.Application")
    word.DisplayAlerts = 0

    list_file_converters(word)
    hwp_conv = find_hwp_converter(word)

    if hwp_conv is None:
        print("\n⚠️  HWP 변환기가 Word에 등록되지 않았습니다.")
        print("   · Word 비트 수와 같은 Hanword 변환기 설치 여부 확인")
        word.Quit()
        sys.exit(1)

    print(f"\n✅ HWP 변환기 발견: {hwp_conv.FormatName} ({hwp_conv.Extensions})\n")
    wd_format_docx = 16  # DOCX

    hwp_files = list(src_dir.glob("*.hwp"))
    if not hwp_files:
        print("⚠️  변환할 .hwp 파일이 없습니다.")
        word.Quit()
        return

    for hwp in hwp_files:
        try:
            print(f"▶ {hwp.name}")
            doc = word.Documents.Open(
                str(hwp),
                ConfirmConversions=False,
                ReadOnly=True,
                Format=hwp_conv.OpenFormat
            )
            out = dest_dir / f"{hwp.stem}.docx"
            doc.SaveAs(str(out), FileFormat=wd_format_docx)
            doc.Close(False)
            print(f"   ✔ 저장 → {out.name}")
        except Exception as e:
            print(f"   ✖ 오류 : {e}")

    word.Quit()
    print("\n🎉 모든 변환 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()
