import os
import re
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

def extract_meta_from_post(url, session, headers):
    """
    게시물 페이지의 제목에서 '2024 2차' 같은 연도/시험구분을 추출.
    """
    resp = session.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'lxml')

    # 예시: <h3 class="title">2024 2차 CPA 1교시 문제 및 답안</h3>
    title_tag = soup.select_one('h3.title') or soup.find('h3')
    title = title_tag.get_text(strip=True) if title_tag else ''

    m = re.search(r'(\d{4})\s*(1차|2차)', title)
    if m:
        year, phase = m.group(1), m.group(2)
    else:
        year, phase = 'unknown', 'unknown'
    return year, phase

def download_all(csv_path):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}
    meta_cache = {}

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('exists', '').lower() != 'true':
                continue

            post_url = row['post_url']
            file_url = row['url']

            # 1) 게시물 메타 정보 캐싱
            if post_url not in meta_cache:
                try:
                    year, phase = extract_meta_from_post(post_url, session, headers)
                except Exception:
                    year, phase = 'unknown', 'unknown'
                meta_cache[post_url] = (year, phase)
            year, phase = meta_cache[post_url]

            # 2) 파일 다운로드 준비
            print(f"▶ 다운로드: {file_url}")
            try:
                resp = session.get(file_url, headers=headers, stream=True)
                resp.raise_for_status()
            except Exception as e:
                print(f"   ✖ 요청 실패: {e}")
                continue

            # 3) 원본 파일명 추출
            cd = resp.headers.get('Content-Disposition', '')
            if 'filename=' in cd:
                filename = cd.split('filename=')[-1].strip('"; ')
            else:
                filename = os.path.basename(urlparse(file_url).path)
            filename = unquote(filename)

            # 4) 저장 경로 결정: script_dir/{year}_{phase}/
            script_dir = os.path.dirname(os.path.abspath(__file__))
            subdir = os.path.join(script_dir, f"{year}_{phase}")
            os.makedirs(subdir, exist_ok=True)

            save_name = f"{year}_{phase}_{filename}"
            save_path = os.path.join(subdir, save_name)

            # 5) 파일 쓰기
            try:
                with open(save_path, 'wb') as out:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            out.write(chunk)
                print(f"   ✔ 저장됨: {save_path}\n")
            except Exception as e:
                print(f"   ✖ 저장 실패: {e}\n")

if __name__ == '__main__':
    # 스크립트 위치 기준으로 2_file_urls.csv 사용
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path   = os.path.join(script_dir, '2_file_urls.csv')

    download_all(csv_path)
