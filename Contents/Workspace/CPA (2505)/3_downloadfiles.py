"""
Process 3 : 첨부파일 일괄 다운로드
--------------------------------
입력 : 2_file_urls.csv (Process 2 결과)
출력 : <script_dir>/{year}_{phase}/
          {year}_{phase}_{원본파일명}.*
"""

import os
import csv
import requests
from urllib.parse import urlparse, unquote

# ------------------ 설정 ------------------ #
CSV_NAME   = "2_file_urls.csv"   # Process 2 결과
TIMEOUT    = 15                  # 요청 타임아웃(sec)
CHUNK_SIZE = 8192               # 다운로드 chunk

# ------------ 다운로드 함수 -------------- #
def download_all(csv_path: str):
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # ① 존재하지 않는 파일(skip)
            if row.get("exists", "").lower() != "true":
                continue

            year  = row["year"]   or "unknown"
            phase = row["phase"]  or "unknown"
            url   = row["url"]

            # ② HTTP GET
            try:
                resp = session.get(url, stream=True, timeout=TIMEOUT)
                resp.raise_for_status()
            except Exception as err:
                print(f"[FAIL] {url}  ▶ {err}")
                continue

            # ③ 원본 파일명 추출
            cd = resp.headers.get("Content-Disposition", "")
            if "filename=" in cd:
                fname = cd.split("filename=")[-1].strip('"; ')
            else:
                fname = os.path.basename(urlparse(url).path)
            fname = unquote(fname)

            # ④ 저장 경로 (year_phase 폴더 → year_phase_prefix)
            subdir   = os.path.join(os.path.dirname(csv_path), f"{year}_{phase}")
            os.makedirs(subdir, exist_ok=True)

            save_name = f"{year}_{phase}_{fname}"
            save_path = os.path.join(subdir, save_name)

            # 중복 다운로드 방지
            if os.path.exists(save_path):
                print(f"[SKIP] 이미 존재: {save_name}")
                continue

            # ⑤ 스트리밍 저장
            try:
                with open(save_path, "wb") as out:
                    for chunk in resp.iter_content(CHUNK_SIZE):
                        if chunk:
                            out.write(chunk)
                print(f"[OK]   {save_name}")
            except Exception as err:
                print(f"[FAIL] 저장 오류 {save_name} ▶ {err}")

# ---------------- 실행부 ----------------- #
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path   = os.path.join(script_dir, CSV_NAME)

    if not os.path.isfile(csv_path):
        print(f"'{CSV_NAME}'가 없습니다. 먼저 Process 2를 실행하세요.")
    else:
        download_all(csv_path)
