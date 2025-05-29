#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import uuid
import logging
from datetime import datetime

import pdfplumber
import fitz               # PyMuPDF
import camelot           # camelot-py[cv]
from PIL import Image

# --- 설정 --------------------------------------------------

OCR_LANG      = 'kor'
OCR_DPI       = 300
PSM_OCR       = 3
COLUMN_RATIO  = 0.5   # 2단 분할 비율

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


# --- 본문 텍스트 추출 (pdfplumber only) -------------------

def extract_columns(page):
    # Always use the PDF's digital text layer
    w, h = page.width, page.height
    left = page.within_bbox((0, 0, w * COLUMN_RATIO, h)).extract_text() or ""
    right = page.within_bbox((w * COLUMN_RATIO, 0, w, h)).extract_text() or ""
    return left, right, True

# --- 테이블 추출 (Camelot stream) ----------------------------

def extract_tables(pdf_path, page_no):
    try:
        tables = camelot.read_pdf(pdf_path, pages=str(page_no), flavor='stream')
        out = []
        for idx, tbl in enumerate(tables, start=1):
            header = tbl.df.iloc[0].tolist()
            rows   = [row.tolist() for _, row in tbl.df.iloc[1:].iterrows()]
            bbox   = tuple(tbl._bbox)  # (x1, y1, x2, y2)
            out.append({
                "id":      f"T{page_no}_{idx}",
                "headers": header,
                "rows":    rows,
                "bbox":    bbox
            })
        return out
    except Exception as e:
        logger.warning(f"Page {page_no} table extract error: {e}")
        return []

# --- PDF 처리 메인 -------------------------------------------

def process_pdf(pdf_path, out_json):
    logger.info(f"→ Processing: {pdf_path}")
    # pdfplumber + PyMuPDF 오픈
    with pdfplumber.open(pdf_path) as pp:
        doc = fitz.open(pdf_path)
        pages_info = []
        tables_all = []

        for i, page in enumerate(pp.pages, start=1):
            left, right, is_text = extract_columns(page)
            pages_info.append({
                "page":       i,
                "text_layer": is_text,
                "columns":    [left, right]
            })
            for tbl in extract_tables(pdf_path, i):
                tables_all.append({"page": i, **tbl})

    # JSON 조립 (여기서 스키마에 맞게 필드명 조정 가능)
    result = {
        "document":          os.path.basename(pdf_path),
        "extracted_at_utc":  datetime.utcnow().isoformat() + "Z",
        "pages":             pages_info,
        "tables":            tables_all
    }
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"✔ Saved JSON → {out_json}")

if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), "pdfs")
    list_fp  = os.path.join(base_dir, "pdf_list.txt")
    names    = [l.strip() for l in open(list_fp, encoding='utf-8') if l.strip() and not l.startswith('#')]
    out_dir  = os.path.join(base_dir, "extracted_json_results")

    for name in names:
        inp = os.path.join(base_dir, name)
        out = os.path.join(out_dir, os.path.splitext(name)[0] + ".json")
        process_pdf(inp, out)
