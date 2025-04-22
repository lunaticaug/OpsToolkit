#!/usr/bin/env python3
"""
fill_data.py
────────────────────────────────────────────────────────
1. CSV 인코딩 자동 감지(UTF‑8‑SIG ↔ CP949)
2. (단지명 + 주소) 정규화 매칭 → 지하철역 채우기
3. 지하철역 컬럼을 D열(4번째)로 위치 고정
4. SupplyCategory에 '신혼부부' 포함 행 → 선택 = 'X'
5. 결과를 원본 2025청안주LIST.csv에 덮어쓰기 저장
────────────────────────────────────────────────────────
"""
import pandas as pd
import re
import chardet

# ────────────────────────────────────────────────── #
# 0. 안전한 CSV 읽기
# ────────────────────────────────────────────────── #
def read_csv_smart(path: str) -> pd.DataFrame:
    """Try UTF‑8 first, fall back to CP949 if needed."""
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        with open(path, "rb") as f:
            enc = chardet.detect(f.read(20_000))["encoding"] or "cp949"
        return pd.read_csv(path, encoding=enc)

# ────────────────────────────────────────────────── #
# 1. 데이터 로드
# ────────────────────────────────────────────────── #
df    = read_csv_smart("2025청안주LIST.csv")
mapdf = read_csv_smart("site_station_map.csv")

# ────────────────────────────────────────────────── #
# 2. 단지명+주소 정규화 키 생성
# ────────────────────────────────────────────────── #
def norm(txt: str) -> str:
    if pd.isna(txt):
        return ""
    txt = re.sub(r"\([^)]*\)", "", txt)   # 괄호 내용 삭제
    txt = re.sub(r"\s+", "", txt)         # 모든 공백 삭제
    return txt.lower()

for frame in (df, mapdf):
    frame["키"] = (frame["단지명"].astype(str) + frame["주소"].astype(str)).apply(norm)

# ────────────────────────────────────────────────── #
# 3. 지하철역 매핑
# ────────────────────────────────────────────────── #
station_dict = mapdf.set_index("키")["지하철역"].to_dict()

# 잔여 접미사 열(*_x/_y/_map 등) 제거
df = df.drop(columns=[c for c in df.columns if re.match(r"지하철역_.*", c)], errors="ignore")

# 지하철역 컬럼 없으면 생성
if "지하철역" not in df.columns:
    df.insert(3, "지하철역", pd.NA)

# 빈 칸만 채움
df["지하철역"] = df.apply(
    lambda r: station_dict.get(r["키"], r["지하철역"])
    if pd.isna(r["지하철역"]) or str(r["지하철역"]).strip() == ""
    else r["지하철역"],
    axis=1,
)

# D열(인덱스 3) 위치 보정
if df.columns.get_loc("지하철역") != 3:
    col = df.pop("지하철역")
    df.insert(3, "지하철역", col)

# ────────────────────────────────────────────────── #
# 4. '신혼부부' 행 → 선택 = 'X'
# ────────────────────────────────────────────────── #
if "선택" not in df.columns:
    df["선택"] = pd.NA

mask = df["SupplyCategory"].astype(str).str.contains("신혼부부", na=False)
df.loc[mask, "선택"] = "X"

# ────────────────────────────────────────────────── #
# 5. 저장
# ────────────────────────────────────────────────── #
df.drop(columns=["키"]).to_csv("2025청안주LIST.csv", index=False, encoding="utf-8-sig")
print("✅ 지하철역 채우기 및 '신혼부부' 선택 표시 완료")