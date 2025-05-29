import pandas as pd

# 1. 파일 로드
all_df  = pd.read_csv("All_Scored_Sites.csv", dtype=str)
site_df = pd.read_csv("site_station_map_scored.csv", dtype=str)

# 2. 덮어쓸 컬럼 리스트 (All에서는 C열부터)
cols_to_copy = all_df.columns[2:]  
# → ['Cluster','친숙도','생활편의점수','통근점수','총점','우선검토']

# 3. 두 키로 merge
merged = pd.merge(
    site_df,
    all_df[ ["단지명","지하철역"] + list(cols_to_copy) ],
    on=["단지명","지하철역"],
    how="left",
    suffixes=("","_new")
)

# 4. site_df의 D열~에 All_df 값을 덮어쓰기
for col in cols_to_copy:
    merged[col] = merged[f"{col}_new"]
    merged.drop(columns=[f"{col}_new"], inplace=True)

# 5. 원래 순서대로 컬럼 정렬 (필요시)
cols = site_df.columns.tolist()
# 만약 site_df에 없는 새 컬럼이 있다면, cols_to_copy에 맞게 조정하세요.
merged = merged[cols]

# 6. 결과 저장
merged.to_csv("site_station_map_scored.csv", index=False)