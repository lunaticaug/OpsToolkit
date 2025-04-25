"""
fillsubway.py
--------------------------------------------------
✓ 인코딩 자동 감지 (UTF‑8‑SIG ↔ CP949)
✓ 단지명·주소 정규화 후 매칭 – 괄호·공백·대소문자 무시
✓ 지하철역을 D열(4번째)로 삽입 (기존 값은 유지하며 빈 칸만 채움)
--------------------------------------------------
"""
import pandas as pd
import re
import chardet

# ---------- 0. 유틸 : 안전한 CSV 로드 -------------------------------------- #
def read_csv_smart(path: str) -> pd.DataFrame:
    """UTF‑8 → 실패 시 CP949 로 재시도"""
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        # 파일 앞부분만 읽어 인코딩 감지
        with open(path, "rb") as f:
            enc = chardet.detect(f.read(20_000))["encoding"] or "cp949"
        return pd.read_csv(path, encoding=enc)

# ---------- 1. 데이터 로드 -------------------------------------------------- #
df    = read_csv_smart("2025청안주LIST.csv")
mapdf = read_csv_smart("site_station_map.csv")

# ---------- 2. 단지명·주소 정규화 ----------------------------------------- #
def norm(text: str) -> str:
    if pd.isna(text):
        return ""
    # 괄호 내용 제거 → 공백 제거 → 소문자
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\s+", "", text)
    return text.lower()

for frame in (df, mapdf):
    frame["키"] = (frame["단지명"].astype(str) + frame["주소"].astype(str)).apply(norm)

# ---------- 3. 매핑 테이블(dict) 생성 -------------------------------------- #
station_dict = mapdf.set_index("키")["지하철역"].to_dict()

# ---------- 4. 지하철역 채우기 -------------------------------------------- #
if "지하철역" not in df.columns:
    df.insert(3, "지하철역", pd.NA)

# 빈 셀만 채움
df["지하철역"] = df.apply(
    lambda row: station_dict.get(row["키"], row["지하철역"])
    if pd.isna(row["지하철역"]) or str(row["지하철역"]).strip() == ""
    else row["지하철역"],
    axis=1,
)

# ---------- 5. D열 위치 보정(인덱스 3) ------------------------------------ #
if df.columns.get_loc("지하철역") != 3:
    col = df.pop("지하철역")
    df.insert(3, "지하철역", col)

# ---------- 6. 저장 ------------------------------------------------------- #
df.drop(columns=["키"]).to_csv("2025청안주LIST.csv", index=False, encoding="utf-8-sig")
print("✅ 지하철역 입력(느슨한 매칭) 완료 – 2025청안주LIST.csv 덮어쓰기")