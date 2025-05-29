import pandas as pd
import re

########################################
# 1. CSV 읽기
########################################
df1 = pd.read_csv("2025청안주LIST.csv", encoding="utf-8-sig")   # 1번
df2 = pd.read_csv("merged_2025.csv",   encoding="utf-8-sig")   # 2번

########################################
# 2. 단지명 정규화 함수
########################################
def normalize(name: str) -> str:
    if pd.isna(name):
        return ""
    # (1) 괄호 안 제거  (2) 공백·탭 제거  (3) 전각/반각 공백 정리  (4) 소문자 변환
    name = re.sub(r"\([^)]*\)", "", name)   # (…) 삭제
    name = re.sub(r"\s+", "", name)         # 모든 공백 삭제
    return name.lower()

df1["단지명_정규"] = df1["단지명"].apply(normalize)
df2["단지명_정규"] = df2["단지명"].apply(normalize)

########################################
# 3. 필요한 열만 추려서 매핑 테이블 구성
########################################
lookup = (
    df2[["단지명_정규", "공급유형", "주소"]]
    .drop_duplicates(subset="단지명_정규")
)

########################################
# 4. 왼쪽 조인으로 값 채우기
########################################
df_merged = df1.merge(lookup, on="단지명_정규", how="left", suffixes=("", "_src"))

# 4‑1. 공급유형(A열) 채우기 ― 이미 값이 있으면 보존
df_merged["공급유형"] = df_merged["공급유형"].fillna(df_merged["공급유형_src"])

# 4‑2. 주소(C열) 채우기 ― 비어 있을 때만 입력
df_merged["주소"] = df_merged["주소"].fillna(df_merged["주소_src"])

########################################
# 5. 작업용 열 제거 → 원본 파일로 덮어쓰기
########################################
(
    df_merged
    .drop(columns=["단지명_정규", "공급유형_src", "주소_src"])
    .to_csv("2025청안주LIST.csv",  # ★ 기존 파일 그대로 덮어씀
            index=False,
            encoding="utf-8-sig")
)

print("✅ 공급유형·주소 보완 완료 → 2025청안주LIST.csv 에 덮어쓰기 저장")