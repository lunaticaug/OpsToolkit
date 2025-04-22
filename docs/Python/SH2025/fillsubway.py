# fillsubway.py  (최종·간단 버전)
import pandas as pd

df    = pd.read_csv("2025청안주LIST.csv",    encoding="utf-8-sig")
mapdf = pd.read_csv("site_station_map.csv", encoding="utf-8-sig")

# 1) 단지명·주소 기준 병합 → mapdf 쪽 역명은 지하철역_src 로 붙음
df = df.merge(mapdf, on=["단지명", "주소"], how="left", suffixes=("", "_src"))

# 2) 원본 지하철역이 비어 있으면 _src 값으로 채우기
if "지하철역_src" in df.columns:                # merge 성공 여부 확인
    df["지하철역"] = df["지하철역"].combine_first(df["지하철역_src"])
    df = df.drop(columns=["지하철역_src"])      # 처리 끝났으면 제거

# 3) 덮어쓰기 저장
df.to_csv("2025청안주LIST.csv", index=False, encoding="utf-8-sig")
print("✅ 지하철역 병합 완료")