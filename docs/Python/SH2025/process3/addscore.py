# ── 0. 준비 ──────────────────────────────────────────────
import pandas as pd, numpy as np

SRC  = "site_station_map.csv"          # 원본
DEST = "site_station_map_scored.csv"   # 결과

# ① 가중치 / ② 시간→점수 커브 / ③ 총점→최종판정 cut‑off

WEIGHTS = {"친숙도":0.25, "생활편의점수":0.20, "통근점수":0.55}

# ── 사용자 정의 점수 매핑 ─────────────────────────────
# 1) 지하철역 → 익숙도(친숙도) 점수 매핑
station_fam = {
    # Gangnam Core
    "언주역":4,"선정릉역":4,"도곡역":4,"선릉역":4,"교대역":4,"남부터미널역":4,
    # CBD / 용산축
    "서울역":5,"용산역":5,"남영역":5,"효창공원앞역":5,"충정로역":5,
    # Line6 서부
    "상수역":4,"홍대입구역":4,"가좌역":4,"구산역":3,"역촌역":3,
    # 동부 5·7·8
    "길동역":3,"천호역":3,"구의역":3,"군자역":3,"중곡역":3,"장한평역":3,"마장역":3,"용답역":3,
    # 북부 외곽
    "공릉역":2,"태릉입구역":2,"상계역":2,"광운대역":2,"상봉역":2,"회기역":2,
    # 기타
    "신림역":3,"서울대입구역":3,"신대방역":3,"개봉역":2,"화곡역":2,"당산역":4,"신길역":4,"신도림역":4,
    "노량진역":5,"문정역":4,"잠실역":4,"잠실새내역":4,"동묘앞역":3
}

# 1‑a) 역 → 클러스터 매핑 (통근·생활 기본값용)
station_cluster = {
    # Gangnam Core
    "언주역":"Gangnam Core","선정릉역":"Gangnam Core","도곡역":"Gangnam Core","선릉역":"Gangnam Core",
    "교대역":"Gangnam Core","남부터미널역":"Gangnam Core","잠실역":"Gangnam Core",
    "잠실새내역":"Gangnam Core","문정역":"Gangnam Core",

    # Yeouido Adjacent
    "노량진역":"Yeouido Adjacent","신길역":"Yeouido Adjacent","당산역":"Yeouido Adjacent",
    "신도림역":"Yeouido Adjacent","남영역":"Yeouido Adjacent",

    # CBD Central
    "서울역":"CBD Central","효창공원앞역":"CBD Central","용산역":"CBD Central","충정로역":"CBD Central",

    # Line6 Northwest
    "상수역":"Line6 NW","홍대입구역":"Line6 NW","가좌역":"Line6 NW","구산역":"Line6 NW","역촌역":"Line6 NW",

    # East 5/7/8
    "길동역":"East 5/7/8","천호역":"East 5/7/8","구의역":"East 5/7/8","군자역":"East 5/7/8",
    "중곡역":"East 5/7/8","장한평역":"East 5/7/8","마장역":"East 5/7/8","용답역":"East 5/7/8",

    # Northern
    "공릉역":"Northern","태릉입구역":"Northern","상계역":"Northern","광운대역":"Northern",
    "상봉역":"Northern","회기역":"Northern",

    # Southwest Line2
    "신림역":"SW Line2","서울대입구역":"SW Line2","신대방역":"SW Line2","개봉역":"SW Line2","화곡역":"SW Line2",

    # Eastern/Central Line6
    "동묘앞역":"E/C Line6"
}

# 클러스터별 기본 통근·생활 점수
cluster_commute_default = {
    "CBD Central":5, "Yeouido Adjacent":5,
    "Gangnam Core":4, "Line6 NW":4,
    "SW Line2":3, "East 5/7/8":3,
    "E/C Line6":3, "Northern":2
}
cluster_life_default = {
    "CBD Central":4, "Yeouido Adjacent":4, "Gangnam Core":4,
    "Line6 NW":3, "SW Line2":3, "East 5/7/8":3, "E/C Line6":3,
    "Northern":2
}

# 2) 생활편의 점수 함수 : 대형마트 도보시간 기반 (없으면 기본 3)
def life_score(t):
    try:
        t=float(t)
    except (ValueError,TypeError):
        return 3
    if   t<=10: return 5
    elif t<=15: return 4
    elif t<=20: return 3
    elif t<=25: return 2
    else:       return 1

def commute_grade(t):
    """평균 통근시간(분)을 1~5점 범위로 환산"""
    if   t <= 30: return 5
    elif t <= 40: return 4
    elif t <= 50: return 3
    elif t <= 60: return 2
    else:         return 1

def final_mark(score):
    if score >= 4.0: return "◎"     # 적극   (Good)
    elif score >= 3.0: return "○"   # 조건부 (Acceptable)
    else:              return "△"   # 보류   (Risky)

# ── 1. 로드 & 전처리 ────────────────────────────────────
df = pd.read_csv(SRC)
df.columns = df.columns.str.strip()

# 클러스터 열 생성
if "Cluster" not in df.columns:
    df["Cluster"] = df["지하철역"].map(station_cluster).fillna("Unknown")

# ── 1.1. 친숙도 자동 생성 ─────────────────────────────
if "친숙도" not in df.columns:
    df["친숙도"] = df["지하철역"].map(station_fam).fillna(1).astype(int)

# ── 1.2. 생활편의점수 자동 생성 (대형마트_도보_분 열 필요) ─────────
if "생활편의점수" not in df.columns:
    if "대형마트_도보_분" not in df.columns:
        df["대형마트_도보_분"] = np.nan
    df["생활편의점수"] = df["대형마트_도보_분"].apply(life_score).astype(int)

# 통근시간(지하철 + 버스) 평균 → ‘통근점수’ 자동 산출
sub_cols = ["여의도_지하철_분", "용산_지하철_분", "역삼_지하철_분"]
bus_cols = ["여의도_버스_분", "용산_버스_분", "역삼_버스_분"]
time_cols = sub_cols + bus_cols

avail_cols = [c for c in time_cols if c in df.columns]
if avail_cols:
    # 행별: NaN 제외하고 평균
    df["통근평균"] = df[avail_cols].mean(axis=1, skipna=True)
    df["통근점수"] = df["통근평균"].apply(commute_grade)
else:
    print("[경고] 통근시간 관련 컬럼이 없습니다. 기본 3점으로 설정합니다.")
    df["통근평균"] = np.nan
    df["통근점수"] = 3


# ── 통근·생활 점수 결측 → 클러스터 기본값으로 보완 ──────────
df["통근점수"] = pd.to_numeric(df.get("통근점수", np.nan), errors="coerce")
df["통근점수"] = df["통근점수"].fillna(df["Cluster"].map(cluster_commute_default))

df["생활편의점수"] = pd.to_numeric(df.get("생활편의점수", np.nan), errors="coerce")
# life_score 가 NaN→1 처리했을 때 보정
df["생활편의점수"] = df["생활편의점수"].where(
    df["생활편의점수"] > 1,
    df["Cluster"].map(cluster_life_default)
)


# ── 1.5. 결측치 및 컬럼 기본값 처리 ─────────────────────────────
# 필요한 점수 컬럼이 없으면 0으로 초기화
for col in ["친숙도", "생활편의점수", "통근점수"]:
    if col not in df.columns:
        df[col] = 0
# 숫자형으로 변환 및 NaN은 0으로 대체
for col in ["친숙도", "생활편의점수", "통근점수"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ── 2. 총점 & 최종판정 계산 ─────────────────────────────
df["총점"] = (df[list(WEIGHTS)]
              .mul(pd.Series(WEIGHTS))
              .sum(axis=1)
              .round(2))

df["최종판정"] = df["총점"]      # 가중평균 점수를 그대로 기록

# ── 3. 플래그 기본값(필터용) ─────────────────────────────
df["우선검토"] = df["총점"] >= 3.0
df["청약제출"] = False            # 이후 수동 갱신

# ── 4. 저장 ────────────────────────────────────────────
df.to_csv(DEST, index=False)
print(f"[+] 저장 완료 → {DEST}")