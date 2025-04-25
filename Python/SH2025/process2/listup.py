import pandas as pd

df = pd.read_csv("2025청안주LIST.csv", encoding="utf-8-sig")

unique_sites = (
    df[["단지명", "주소"]]
    .drop_duplicates()              # 중복 제거
    .sort_values(["주소", "단지명"]) # 보기 좋게 정렬
)

unique_sites["지하철역"] = ""        # 빈 열 만들어 두기
unique_sites.to_csv("site_station_map.csv", index=False, encoding="utf-8-sig")

print("👉  site_station_map.csv  생성 — 여기서 지하철역 열을 입력하세요")