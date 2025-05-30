import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_post_urls(menu_no='1200078', bbs_id='B0000368', max_pages=10):
    """
    CPA FSS 게시판(list.do)에서 게시글 view URL을 크롤링합니다.
    구조경로: /html/body/div[1]/div[1]/section/article/div[2]/div[2]
    """
    base_url = 'https://cpa.fss.or.kr/cpa/bbs/B0000368/list.do'
    post_urls = set()
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}

    for page in range(1, max_pages + 1):
        params = {'menuNo': menu_no, 'bbsId': bbs_id, 'pageIndex': page}
        resp = session.get(base_url, params=params, headers=headers)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'lxml')
        # 게시판 본문: section > article > div:nth-of-type(2) > div:nth-of-type(2)
        board_div = soup.select_one(
            'body > div:nth-of-type(1) > div:nth-of-type(1) '
            '> section > article > div:nth-of-type(2) > div:nth-of-type(2)'
        )
        if not board_div:
            break

        # ul.board-list-inner > li.board-item
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
    for url in get_post_urls(max_pages=5):
        print(url)
