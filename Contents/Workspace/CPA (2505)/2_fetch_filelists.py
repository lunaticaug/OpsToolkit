import os
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

def load_post_urls(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [row['url'] for row in reader]

def get_file_urls(post_urls, max_filesn=10):
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}

    all_records = []
    pdf_urls = []

    for post_url in post_urls:
        print(f"▶ 처리 중: {post_url}")
        resp = session.get(post_url, headers=headers)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'lxml')
        # 첨부파일 download 링크 중 첫 번째에서 atchFileId, bbsId 추출
        link = soup.find('a', href=lambda h: h and 'fileDown.do' in h)
        if not link:
            print("   • 첨부가 없습니다.")
            continue

        qs = parse_qs(urlparse(link['href']).query)
        atchFileId = qs.get('atchFileId', [''])[0]
        bbsId       = qs.get('bbsId', [''])[0]

        for file_sn in range(1, max_filesn + 1):
            file_url = (
                'https://cpa.fss.or.kr/cpa/cmmn/file/fileDown.do'
                f'?menuNo=&atchFileId={atchFileId}&fileSn={file_sn}&bbsId={bbsId}'
            )
            # HEAD 요청으로 존재 여부 및 파일 타입 확인
            head = session.head(file_url, allow_redirects=True, headers=headers)
            exists = (head.status_code == 200)
            is_pdf = False
            if exists:
                cd = head.headers.get('Content-Disposition', '').lower()
                ct = head.headers.get('Content-Type', '').lower()
                if 'pdf' in ct or 'pdf' in cd:
                    is_pdf = True
                    pdf_urls.append(file_url)

            all_records.append({
                'post_url': post_url,
                'atchFileId': atchFileId,
                'bbsId': bbsId,
                'file_sn': file_sn,
                'url': file_url,
                'exists': exists,
                'is_pdf': is_pdf
            })

    return all_records, pdf_urls

if __name__ == '__main__':
    # 1) 스크립트 위치 기준으로 파일 경로 설정
    script_dir      = os.path.dirname(os.path.abspath(__file__))
    posts_csv_path  = os.path.join(script_dir, 'post_urls.csv')
    files_csv_path  = os.path.join(script_dir, 'file_urls.csv')
    pdfs_csv_path   = os.path.join(script_dir, 'pdf_urls.csv')

    # 2) post_urls.csv 읽기
    post_urls = load_post_urls(posts_csv_path)

    # 3) 파일 URL 리스트 생성
    records, pdf_urls = get_file_urls(post_urls, max_filesn=10)

    # 4) 전체 파일 상태 기록
    with open(files_csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['post_url','atchFileId','bbsId','file_sn','url','exists','is_pdf']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # 5) PDF URL만 별도 저장
    with open(pdfs_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['url'])
        for u in pdf_urls:
            writer.writerow([u])

    print(f"\n완료: {len(post_urls)}개 게시물 → '{files_csv_path}', '{pdfs_csv_path}' 생성")    
