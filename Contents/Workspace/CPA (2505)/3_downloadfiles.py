import os
import csv
import requests
from urllib.parse import urlparse, unquote

def download_pdfs(csv_path, prefix='3_'):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row['url']
            try:
                print(f"▶ 다운로드 중: {url}")
                resp = session.get(url, headers=headers, stream=True)
                resp.raise_for_status()

                # Content-Disposition 헤더에서 원본 파일명 추출
                cd = resp.headers.get('Content-Disposition', '')
                if 'filename=' in cd:
                    filename = cd.split('filename=')[-1].strip('"; ')
                else:
                    # URL 경로에서 파일명 추출
                    filename = os.path.basename(urlparse(url).path)

                filename = unquote(filename)
                save_name = prefix + filename
                save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), save_name)

                # 파일 스트리밍으로 저장
                with open(save_path, 'wb') as out:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            out.write(chunk)

                print(f"   ✔ 저장됨: {save_name}\n")
            except Exception as e:
                print(f"   ✖ 실패: {e}\n")

if __name__ == '__main__':
    # 스크립트 위치 기준으로 2_pdf_urls.csv 읽기
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    csv_path    = os.path.join(script_dir, '2_pdf_urls.csv')

    download_pdfs(csv_path)
