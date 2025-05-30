import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv

def get_post_urls(menu_no='1200078', bbs_id='B0000368', max_pages=10):
    base_url = 'https://cpa.fss.or.kr/cpa/bbs/B0000368/list.do'
    post_urls = set()
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}

    for page in range(1, max_pages + 1):
        params = {'menuNo': menu_no, 'bbsId': bbs_id, 'pageIndex': page}
        resp = session.get(base_url, params=params, headers=headers)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'lxml')
        board_div = soup.select_one(
            'body > div:nth-of-type(1) > div:nth-of-type(1) '
            '> section > article > div:nth-of-type(2) > div:nth-of-type(2)'
        )
        if not board_div:
            break

        items = board_div.select('ul.board-list-inner > li.board-item')
        if not items:
            break

        for li in items:
            a = li.select_one('p.subject a[href]')
            if a:
                full_url = urljoin(resp.url, a['href'])
                post_urls.add(full_url)

    return sorted(post_urls)

if __name__ == '__main__':
    urls = get_post_urls(max_pages=5)

    # CSV로 저장
    output_file = 'post_urls.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['url'])         # 헤더
        for url in urls:
            writer.writerow([url])

    print(f"총 {len(urls)}개의 URL을 '{output_file}'에 저장했습니다.")
