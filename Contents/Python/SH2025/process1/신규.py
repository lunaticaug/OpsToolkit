"""
신규 공급 CSV(2025신규공급.CSV) ‑ 단지명·주소 분리 & 셀 병합 공백 채우기
------------------------------------------------------------------------
* A열(0번째 열)에 '단지명\n주소'가 들어가 있는 행을 찾아
  └ 단지명  → A열 그대로
  └ 주소    → 새로 만든 B열(1번째 열, 이름: '주소')에 이동
* 이후 빈 셀(셀 병합 풀리며 생긴 공백) → 바로 위 값으로 채움(ffill)
* 같은 파일을 **그대로 덮어쓰기**.  재실행해도 안전합니다.
"""

import pandas as pd
from pathlib import Path

# === 설정 === #
FILE_PATH = Path("2025신규공급.CSV")   # 스크립트와 같은 폴더에 있다고 가정
ENCODING  = "utf-8-sig"               # 한글 CSV용 인코딩

def main() -> None:
    # 1) CSV 로드 ---------------------------------------------------------
    df = pd.read_csv(FILE_PATH, encoding=ENCODING, engine="python")

    # 2) '주소' 칼럼 없으면 삽입, 있으면 위치를 2번째로 고정 ------------------
    if "주소" not in df.columns:
        df.insert(1, "주소", None)
    elif df.columns.get_loc("주소") != 1:
        cols = list(df.columns)
        cols.insert(1, cols.pop(cols.index("주소")))
        df = df[cols]

    # 3) 단지명·주소 분리 ---------------------------------------------------
    for idx, val in df.iloc[:, 0].items():                   # 0번째 열 순회
        if isinstance(val, str) and "\n" in val:
            name, address = [p.strip() for p in val.split("\n", 1)]
            df.iat[idx, 0] = name        # 단지명
            df.iat[idx, 1] = address     # 주소

    # 4) 셀 병합 공백 채우기 ----------------------------------------------
    df.iloc[:, 0] = df.iloc[:, 0].ffill()   # 단지명 앞행 값 복사
    df.iloc[:, 1] = df.iloc[:, 1].ffill()   # 주소    앞행 값 복사

    # 5) 저장(덮어쓰기) ----------------------------------------------------
    df.to_csv(FILE_PATH, index=False, encoding=ENCODING)
    print(f"✅ 정리 완료 → {FILE_PATH.resolve()}")

if __name__ == "__main__":
    main()