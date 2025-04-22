"""
SH 2025 CSV 클리너  ―  재공급·쉐어예비 전용
-----------------------------------------
* 단지명·주소 분리 → '주소' 칼럼 삽입 → 병합 공백 ffill → 덮어쓰기
"""

import pandas as pd
from pathlib import Path

ENCODING = "utf-8-sig"
FILES    = [
    "2025재공급.CSV",
    "2025쉐어예비.CSV",
]

def clean(path: Path) -> None:
    if not path.exists():
        print(f"❗  {path.name}  찾을 수 없음 — 건너뜁니다")
        return

    df = pd.read_csv(path, encoding=ENCODING, engine="python")

    # 1) '주소' 칼럼 처리
    if "주소" not in df.columns:
        df.insert(1, "주소", None)
    elif df.columns.get_loc("주소") != 1:
        cols = list(df.columns)
        cols.insert(1, cols.pop(cols.index("주소")))
        df = df[cols]

    # 2) 단지명·주소 분리
    mask = df.iloc[:, 0].astype(str).str.contains("\n")
    for idx in df.index[mask]:
        name, addr = (p.strip() for p in df.iat[idx, 0].split("\n", 1))
        df.iat[idx, 0] = name
        df.iat[idx, 1] = addr

    # 3) 헤더 이후부터 ffill
    if mask.any():
        first_data_idx = mask.idxmax()
        df.iloc[first_data_idx:, 0] = df.iloc[first_data_idx:, 0].ffill()
        df.iloc[first_data_idx:, 1] = df.iloc[first_data_idx:, 1].ffill()

    # 4) 저장
    df.to_csv(path, index=False, encoding=ENCODING)
    print(f"✅  {path.name}  정리 완료")

def main() -> None:
    base_dir = Path(__file__).resolve().parent
    for fname in FILES:
        clean(base_dir / fname)

if __name__ == "__main__":
    main()