import pandas as pd

# ✅ 1. CSV 파일 불러오기
file_path = '2025신규공급.CSV'  # 로컬에서 경로 수정 가능
df = pd.read_csv(file_path, encoding='utf-8-sig')

# ✅ 2. A열 줄바꿈 분리: 단지명 + 주소
for idx, val in df.iloc[:, 0].items():
    if isinstance(val, str) and '\n' in val:
        parts = val.split('\n')
        df.iloc[idx, 0] = parts[0].strip()  # 단지명
        df.insert(1, '주소', None)          # 주소 컬럼 삽입
        df.iloc[idx, 1] = parts[1].strip()  # 주소 입력
        break  # 첫 줄만 처리하면 전체 shift됨

# ✅ 3. 누락된 주소 및 단지명 채우기
df.iloc[:, 0] = df.iloc[:, 0].fillna(method='ffill')  # 단지명
df.iloc[:, 1] = df.iloc[:, 1].fillna(method='ffill')  # 주소

# ✅ 4. 저장
output_path = '신규공급_정리본.csv'
df.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"정리된 파일이 저장되었습니다: {output_path}")