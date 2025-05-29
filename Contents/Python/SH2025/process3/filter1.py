#!/usr/bin/env python3
# mark_shin.py ─ D열(SupplyCategory)에서 '신혼부부' 찾으면 선택='X'
import pandas as pd

FILE = "2025청안주LIST.csv"

# 1. CSV 읽기
df = pd.read_csv(FILE, encoding="utf-8-sig")

# 2. '선택' 컬럼 없으면 추가
if "선택" not in df.columns:
    df["선택"] = pd.NA         # 빈 열 생성

# 3. 'SupplyCategory' 열에 '신혼부부' 포함된 행 표시
mask = df["SupplyCategory"].astype(str).str.contains("신혼부부", na=False)
df.loc[mask, "선택"] = "❌"

# 4. 저장(덮어쓰기)
df.to_csv(FILE, index=False, encoding="utf-8-sig")
print("✅ '신혼부부' 행 → 선택 = 'X' 처리 완료")