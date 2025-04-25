import pandas as pd

# 1) 원본 불러오기
site_df = pd.read_csv("site_station_map_scored.csv", dtype=str)
list_df = pd.read_csv("2025청안주LIST.csv", dtype=str)

# 2) site_df에서 key 및 값 가져오기
key_cols = ["단지명","지하철역"]
site_sub = site_df[key_cols + ["우선검토","총점"]].copy()
# bool 타입 변환
site_sub["우선검토"] = site_sub["우선검토"].map({"True": True, "False": False})

# 3) list_df에 merge
merged = pd.merge(
    list_df,
    site_sub,
    on=key_cols,
    how="left"
)

# 4) 선택 컬럼 업데이트 (우선검토=False → 선택="✅")
merged["선택"] = merged.apply(
    lambda r: "✅" if r["우선검토"] is False else r["선택"],
    axis=1
)

# 5) 최종판정 컬럼을 site_df의 총점으로 무조건 대체
# 신규 최종판정: site_df의 총점으로 무조건 대체
merged["최종판정"] = merged["총점"]

# 6) 불필요 컬럼 정리 및 순서 복원 (원본 '최종판정' 교체)
out_cols = [col for col in list_df.columns if col != "최종판정"] + ["최종판정"]
out_df = merged[out_cols]

# 7) 덮어쓰기 저장
out_df.to_csv("2025청안주LIST.csv", index=False, encoding="utf-8-sig")

print("✅ 2025리스트 파일이 업데이트되었습니다.")