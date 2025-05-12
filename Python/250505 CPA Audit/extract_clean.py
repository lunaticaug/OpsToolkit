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
import pytesseract
from PIL import Image
import numpy as np
import cv2

# --- 설정 --------------------------------------------------

OCR_LANG      = 'kor'
OCR_DPI       = 300
PSM_OCR       = 3
COLUMN_RATIO  = 0.5   # 2단 분할 비율

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# --- 헬퍼: 이미지 전처리 + OCR --------------------------------

def ocr_image(pil_img):
    arr  = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    blur = cv2.medianBlur(gray, 3)
    proc = Image.fromarray(blur)
    data = pytesseract.image_to_data(
        proc, lang=OCR_LANG,
        config=f'--oem 3 --psm {PSM_OCR}',
        output_type=pytesseract.Output.DICT
    )
    words, confs = [], []
    for i, txt in enumerate(data['text']):
        try:
            conf = float(data['conf'][i])
        except:
            continue
        if data['level'][i] == 5 and txt.strip() and conf >= 0:
            words.append(txt.strip())
            confs.append(conf)
    text = " ".join(words)
    conf = (sum(confs)/len(confs)/100) if confs else 0.0
    return text, round(conf, 2)

# --- 본문 텍스트 추출 (pdfplumber or OCR) -------------------

def extract_columns(page):
    # 1) 텍스트 레이어가 있으면 pdfplumber로 바로 추출
    txt = page.extract_text(layout=True)
    if txt:
        w, h = page.width, page.height
        left  = page.within_bbox((0, 0, w*COLUMN_RATIO, h)).extract_text() or ""
        right = page.within_bbox((w*COLUMN_RATIO, 0, w, h)).extract_text() or ""
        return left, right, True

    # 2) 없으면 스캔본 => OCR
    img = page.to_image(resolution=OCR_DPI).original
    w_px, h_px = img.size
    split = int(w_px * COLUMN_RATIO)
    l_img = img.crop((0, 0, split, h_px))
    r_img = img.crop((split, 0, w_px, h_px))
    lt, lc = ocr_image(l_img)
    rt, rc = ocr_image(r_img)
    return lt, rt, False

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
