
#!/usr/bin/env python3
"""fetch_cpa_pdfs.py

Crawl the Financial Supervisory Service (FSS) CPA exam board and download
every PDF attachment it finds.

1. Visit paginated list pages under:
     https://cpa.fss.or.kr/cpa/bbs/B0000368/list.do?menuNo=1200078&pageIndex=<N>
2. Extract each post URL (*/view.do?nttId=...*)
3. Visit the post, collect attachment links (*/fileDown.do*)
4. Keep only PDFs (HEAD check), stream‑download them into an output folder.

The code is defensive against HTML changes: it searches for “view.do” and
“fileDown.do” patterns, not fragile CSS classes.

Dependencies
------------
    pip install requests beautifulsoup4 tqdm

Quick start
-----------
    # Download first 3 pages of the board (usually 60 posts)
    python fetch_cpa_pdfs.py --pages 1-3

Command‑line options
--------------------
    --pages 1-5        # page ranges or single numbers, comma‑separated
    --dest downloads   # destination directory
    --max-sn 10        # probe up to this fileSn value per attachment
    --delay 0.5        # polite delay (sec) between HTTP requests

Limitations
-----------
* Requires outbound HTTPS access (not possible in this ChatGPT sandbox).
* The board occasionally uses javascript‑generated links; if so, use
  Selenium or copy the rendered HTML.

"""

import argparse
import itertools
import re
import time
from pathlib import Path
from typing import Iterable, List

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

BASE = "https://cpa.fss.or.kr"
LIST_URL = f"{BASE}/cpa/bbs/B0000368/list.do?menuNo=1200078"
VIEW_PATH = "/view.do"
FILE_PATH = "/fileDown.do"

def parse_page_ranges(expr: str) -> List[int]:
    """"1,2,4-6" -> [1,2,4,5,6]"""
    pages = set()
    for part in expr.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(part))
    return sorted(pages)

def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def iter_post_urls(page_idx: int) -> Iterable[str]:
    url = f"{LIST_URL}&pageIndex={page_idx}"
    soup = get_soup(url)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if VIEW_PATH in href:
            if href.startswith("http"):
                yield href
            else:
                yield BASE + href

def iter_attachment_urls(post_url: str) -> Iterable[str]:
    soup = get_soup(post_url)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if FILE_PATH in href:
            if href.startswith("http"):
                yield href
            else:
                yield BASE + href

def is_pdf(url: str) -> tuple[bool, str]:
    """HEAD request to verify and get server filename."""
    try:
        r = requests.head(url, allow_redirects=True, headers=HEADERS, timeout=10)
    except requests.RequestException:
        return False, ""
    ctype = r.headers.get("Content-Type", "").lower()
    disp = r.headers.get("Content-Disposition", "")
    fname_match = re.findall(r'filename[^;=]*=["\']?([^"\';]+)', disp)
    return "pdf" in ctype, (fname_match[0] if fname_match else "unknown.pdf")

def download(url: str, dest_dir: Path, delay: float = 0.0) -> bool:
    ok, fname = is_pdf(url)
    if not ok:
        return False
    dest = dest_dir / fname
    if dest.exists():
        return True
    with requests.get(url, stream=True, headers=HEADERS, timeout=30) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        with open(dest, "wb") as f, tqdm(
            total=total,
            unit="B",
            unit_scale=True,
            desc=fname,
            ascii=True,
        ) as bar:
            for chunk in r.iter_content(chunk_size=1 << 15):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))
    if delay:
        time.sleep(delay)
    return True

def main():
    ap = argparse.ArgumentParser(description="Crawl FSS CPA board for PDFs.")
    ap.add_argument(
        "--pages",
        default="1",
        help="Page numbers or ranges (e.g. '1-3,5'). Default: 1",
    )
    ap.add_argument(
        "--dest", "-o", default="downloads", help="Destination folder (default: downloads)"
    )
    ap.add_argument(
        "--max-sn",
        type=int,
        default=10,
        help="Max fileSn to probe; rarely needs change",
    )
    ap.add_argument("--delay", type=float, default=0.5, help="Delay between requests (sec)")
    args = ap.parse_args()

    dest_dir = Path(args.dest)
    dest_dir.mkdir(parents=True, exist_ok=True)

    pages = parse_page_ranges(args.pages)
    seen_urls = set()
    for p in pages:
        print(f"=== Page {p} ===")
        for post_url in iter_post_urls(p):
            print(f" Post: {post_url}")
            for att_url in iter_attachment_urls(post_url):
                if att_url in seen_urls:
                    continue
                seen_urls.add(att_url)
                # Append &fileSn=1..max_sn if not present so our PDF checker can iterate
                if "fileSn=" not in att_url:
                    att_url += "&fileSn=1"
                if download(att_url, dest_dir, args.delay):
                    print(f"  ✔ PDF saved from {att_url}")
                else:
                    # try other fileSn indices
                    base_no_sn = re.sub(r"fileSn=\d+", "fileSn={}", att_url)
                    for sn in range(2, args.max_sn + 1):
                        trial = base_no_sn.format(sn)
                        if download(trial, dest_dir, args.delay):
                            print(f"  ✔ PDF saved from {trial}")
                        else:
                            break

if __name__ == "__main__":
    main()
