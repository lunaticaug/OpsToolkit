"""
Process 3 : 첨부파일 일괄 다운로드 (download 폴더)
------------------------------------------------
입력 : 2_file_urls.csv
저장 : <script_dir>/download/
          {year}_{phase}_{원본파일명}.*
"""

import os
import csv
import requests
from urllib.parse import urlparse, unquote

CSV_NAME   = "2_file_urls.csv"   # Process 2 결과
TIMEOUT    = 15                  # HTTP 타임아웃(sec)
CHUNK_SIZE = 8192                # 스트리밍 chunk 크기

def download_all(csv_path: str, download_dir: str):
    os.makedirs(download_dir, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("exists", "").lower() != "true":
                continue

            year  = row["year"]  or "unknown"
            phase = row["phase"] or "unknown"
            url   = row["url"]

            # 요청
            try:
                resp = session.get(url, stream=True, timeout=TIMEOUT)
                resp.raise_for_status()
            except Exception as err:
                print(f"[FAIL] {url} ▶ {err}")
                continue

            # 원본 파일명
            cd = resp.headers.get("Content-Disposition", "")
            if "filename=" in cd:
                fname = cd.split("filename=")[-1].strip('"; ')
            else:
                fname = os.path.basename(urlparse(url).path)
            fname = unquote(fname)

            # 최종 파일명 & 경로  → download 폴더
            save_name = f"{year}_{phase}_{fname}"
            save_path = os.path.join(download_dir, save_name)

            if os.path.exists(save_path):
                print(f"[SKIP] 이미 존재: {save_name}")
                continue

            # 저장
            try:
                with open(save_path, "wb") as out:
                    for chunk in resp.iter_content(CHUNK_SIZE):
                        if chunk:
                            out.write(chunk)
                print(f"[OK]   {save_name}")
            except Exception as err:
                print(f"[FAIL] 저장 오류 {save_name} ▶ {err}")

if __name__ == "__main__":
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    csv_path     = os.path.join(script_dir, CSV_NAME)
    download_dir = os.path.join(script_dir, "download")   # ★ 저장 폴더

    if not os.path.isfile(csv_path):
        print(f"'{CSV_NAME}'가 없습니다. 먼저 Process 2를 실행하세요.")
    else:
        download_all(csv_path, download_dir)
