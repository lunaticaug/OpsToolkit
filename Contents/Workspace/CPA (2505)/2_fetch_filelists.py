import os
import re
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

def load_post_urls(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [row['url'] for row in reader]

def extract_meta(soup):
    """
    게시물 제목(<h3 class="title">…)에서 '2024 2차' 패턴을 찾아서
    (year, phase) 튜플로 반환. 못 찾으면 ('unknown','unknown').
    """
    title_tag = soup.select_one('h3.title') or soup.find('h3')
    if title_tag:
        text = title_tag.get_text(strip=True)
        m = re.search(r'(\d{4})\s*(1차|2차)', text)
        if m:
            return m.group(1), m.group(2)
    return 'unknown', 'unknown'

def get_file_urls(post_urls, max_filesn=10):
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    all_records = []
    pdf_urls = []

    for post_url in post_urls:
        print(f"▶ 처리 중: {post_url}")
        resp = session.get(post_url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        # 메타 추출
        year, phase = extract_meta(soup)

        # 첨부파일 링크 기준 정보 추출
        link = soup.find('a', href=lambda h: h and 'fileDown.do' in h)
        if not link:
            print("   • 첨부파일 없음")
            continue

        qs = parse_qs(urlparse(link['href']).query)
        atchFileId = qs.get('atchFileId', [''])[0]
        bbsId      = qs.get('bbsId', [''])[0]

        for file_sn in range(1, max_filesn + 1):
            file_url = (
                'https://cpa.fss.or.kr/cpa/cmmn/file/fileDown.do'
                f'?menuNo=&atchFileId={atchFileId}&fileSn={file_sn}&bbsId={bbsId}'
            )
            head = session.head(file_url, allow_redirects=True)
            exists = (head.status_code == 200)
            is_pdf = False
            if exists:
                cd = head.headers.get('Content-Disposition', '').lower()
                ct = head.headers.get('Content-Type', '').lower()
                if 'pdf' in ct or 'pdf' in cd:
                    is_pdf = True
                    pdf_urls.append(file_url)

            all_records.append({
                'post_url':    post_url,
                'year':        year,
                'phase':       phase,
                'atchFileId':  atchFileId,
                'bbsId':       bbsId,
                'file_sn':     file_sn,
                'url':         file_url,
                'exists':      exists,
                'is_pdf':      is_pdf
            })

    return all_records, pdf_urls

if __name__ == '__main__':
    script_dir     = os.path.dirname(os.path.abspath(__file__))
    posts_csv_path = os.path.join(script_dir, '1_post_urls.csv')
    files_csv_path = os.path.join(script_dir, '2_file_urls.csv')
    pdfs_csv_path  = os.path.join(script_dir, '2_pdf_urls.csv')

    post_urls = load_post_urls(posts_csv_path)
    records, pdf_urls = get_file_urls(post_urls, max_filesn=10)

    # 전체 파일 리스트에 year, phase 포함
    with open(files_csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'post_url','year','phase',
            'atchFileId','bbsId','file_sn',
            'url','exists','is_pdf'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # PDF URL만 별도 저장 (필요 시)
    with open(pdfs_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['url'])
        for u in pdf_urls:
            writer.writerow([u])

    print(f"\n완료: {len(records)}개 파일 URL → '{files_csv_path}', '{pdfs_csv_path}' 생성")
