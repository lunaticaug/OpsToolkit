#!/usr/bin/env python3
"""
세 CSV(신규·재공급·쉐어예비) 통합 ‑ 공급유형 열(A열) 추가
-------------------------------------------------------
* 각 파일을 읽어 첫 열(0번째)에 '공급유형' 칼럼을 삽입
* 값은 파일별 레이블:  신��공급 / 재공급 / 쉐어예비
* 열 이름·개수는 파일에 있는 그대로 유지
* 모두 이어붙여  merged_2025.csv 로 저장
"""
#!/usr/bin/env python3
"""
세 CSV(신규·재공급·쉐어예비) 통합 – 공급유형 열(A열) 추가
-------------------------------------------------------
* CSV 원본은 절대 수정하지 않고, 읽은 뒤 메모리에서만 가공합니다.
* 쉐어예비 파일의 헤더 '금회공급'을 '공급호수(실)'로 이름만 통일.
* 맨 앞에 '공급유형' 열을 삽입해 파일별 레이블(신규공급/재공급/쉐어예비)을 기록.
* 모든 데이터를 이어붙여 merged_2025.csv 로 저장합니다.
"""

import pandas as pd
from pathlib import Path

ENCODING = "utf-8-sig"

FILES = [
    ("2025신규공급.CSV", "신규공급"),
    ("2025재공급.CSV", "재공급"),
    ("2025쉐어예비.CSV", "쉐어예비"),
]


def load_and_annotate(path: Path, label: str) -> pd.DataFrame:
    """CSV 하나를 읽어 레이블을 추가하고 헤더를 통일한 DataFrame 반환."""
    df = pd.read_csv(path, encoding=ENCODING, engine="python")

    # 쉐어예비 전용 헤더 보정: '금회공급' → '공급호수(실)'
    if "금회공급" in df.columns and "공급호수(실)" not in df.columns:
        df.rename(columns={"금회공급": "공급호수(실)"}, inplace=True)

    # A열에 공급유형 삽입
    df.insert(0, "공급유형", label)

    return df


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    frames = []

    for fname, label in FILES:
        fpath = base_dir / fname
        if not fpath.exists():
            print(f"❗ {fname} 파일을 찾을 수 없어 건너뜁니다.")
            continue
        frames.append(load_and_annotate(fpath, label))

    if not frames:
        print("⚠️  통합할 데이터가 없습니다.")
        return

    merged = pd.concat(frames, ignore_index=True)
    out_path = base_dir / "merged_2025.csv"
    merged.to_csv(out_path, index=False, encoding=ENCODING)
    print(f"✅ 통합 완료 → {out_path}")


if __name__ == "__main__":
    main()