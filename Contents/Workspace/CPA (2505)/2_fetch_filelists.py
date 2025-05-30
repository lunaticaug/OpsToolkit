"""
Process 2 : 게시물별 첨부파일 URL 리스트(csv) 생성
-------------------------------------------------
입력 : 1_post_urls.csv  (Process 1 결과)
출력 : 2_file_urls.csv  (모든 첨부파일 정보)
       2_pdf_urls.csv   (PDF만 따로, 선택 사항)

* 스크립트와 같은 폴더에 CSV를 읽고 씁니다.
"""

import os
import re
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# --------------------------- 유틸 --------------------------- #
def load_post_urls(csv_path: str) -> list[str]:
    """1_post_urls.csv 에서 게시물 URL 리스트를 읽어 반환"""
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [row["url"] for row in reader]

def extract_meta(soup: BeautifulSoup) -> tuple[str, str]:
    """
    게시물 제목에서
      · year  : 20XX (없으면 'unknown')
      · phase : 1차 / 2차 (다양한 표기 허용, 없으면 'unknown')
    를 추출해 (year, phase) 로 반환
    """
    # 제목 위치: <div class="board-title"><div class="subject"><h3>...</h3></div></div>
    title_tag = soup.select_one("div.board-title div.subject h3")
    text = title_tag.get_text(strip=True) if title_tag else ""

    # 연도: 2000~2099
    m_year = re.search(r"(20\d{2})", text)
    year = m_year.group(1) if m_year else "unknown"

    # 시험구분: 1차·2차 / 제1차·제2차 / 제1시험·제2시험
    m_phase = re.search(r"(?:제)?\s*(1차|2차|1시험|2시험)", text)
    if m_phase:
        raw = m_phase.group(1)
        phase = "1차" if raw.startswith("1") else "2차"
    else:
        phase = "unknown"

    return year, phase

def build_file_url(atch_id: str, bbs_id: str, file_sn: int) -> str:
    """첨부파일 download URL 규칙화"""
    return (
        "https://cpa.fss.or.kr/cpa/cmmn/file/fileDown.do"
        f"?menuNo=&atchFileId={atch_id}&fileSn={file_sn}&bbsId={bbs_id}"
    )

# ------------------------- 메인 로직 ------------------------ #
def get_file_urls(post_urls: list[str], max_filesn: int = 10):
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    all_records = []
    pdf_urls = []

    for post_url in post_urls:
        print(f"▶ 게시물 파싱: {post_url}")
        try:
            resp = session.get(post_url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"   ✖ 요청 실패: {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # (1) 메타정보
        year, phase = extract_meta(soup)

        # (2) 첫 번째 첨부파일 링크에서 atchFileId / bbsId 확보
        a_file = soup.find("a", href=lambda h: h and "fileDown.do" in h)
        if not a_file:
            print("   • 첨부파일 없음")
            continue
        qs = parse_qs(urlparse(a_file["href"]).query)
        atch_id = qs.get("atchFileId", [""])[0]
        bbs_id = qs.get("bbsId", [""])[0]

        # (3) fileSn 1 ~ max_filesn 순회
        for file_sn in range(1, max_filesn + 1):
            f_url = build_file_url(atch_id, bbs_id, file_sn)
            head = session.head(f_url, allow_redirects=True, timeout=5)
            exists = head.status_code == 200
            is_pdf = False
            if exists:
                cd = head.headers.get("Content-Disposition", "").lower()
                ct = head.headers.get("Content-Type", "").lower()
                if "pdf" in cd or "pdf" in ct:
                    is_pdf = True
                    pdf_urls.append(f_url)

            all_records.append(
                {
                    "post_url": post_url,
                    "year": year,
                    "phase": phase,
                    "atchFileId": atch_id,
                    "bbsId": bbs_id,
                    "file_sn": file_sn,
                    "url": f_url,
                    "exists": exists,
                    "is_pdf": is_pdf,
                }
            )

    return all_records, pdf_urls

# ------------------------- 실행부 -------------------------- #
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    posts_csv = os.path.join(script_dir, "1_post_urls.csv")
    files_csv = os.path.join(script_dir, "2_file_urls.csv")
    pdfs_csv = os.path.join(script_dir, "2_pdf_urls.csv")

    post_urls = load_post_urls(posts_csv)
    records, pdf_urls = get_file_urls(post_urls, max_filesn=10)

    # (A) 전체 첨부파일 정보 저장
    with open(files_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "post_url",
            "year",
            "phase",
            "atchFileId",
            "bbsId",
            "file_sn",
            "url",
            "exists",
            "is_pdf",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # (B) PDF 전용 리스트(선택)
    with open(pdfs_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url"])
        for u in pdf_urls:
            writer.writerow([u])

    print(
        f"\n완료: {len(records)}개 파일 → '{files_csv}', "
        f"{len(pdf_urls)}개 PDF → '{pdfs_csv}' 저장"
    )
