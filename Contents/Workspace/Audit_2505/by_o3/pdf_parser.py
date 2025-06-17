#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import io
import re
import json
import uuid
import logging
from datetime import datetime, timezone
from PIL import Image
import pytesseract
import cv2
import numpy as np

# 환경 확인
print("Using Python:", sys.executable)
print("sys.path:", sys.path)

# 1) PyMuPDF import
try:
    import fitz  # PyMuPDF
except ModuleNotFoundError:
    raise ImportError(
        "PyMuPDF 모듈을 찾을 수 없습니다. 'pip install PyMuPDF' 를 실행해주세요."
    )

# 2) Camelot import
try:
    import camelot  # camelot-py[cv] 로 설치해야 합니다
except ModuleNotFoundError:
    raise ImportError(
        "Camelot 모듈을 찾을 수 없습니다. "
        "'pip install \"camelot-py[cv]\"' 또는 "
        "'conda install -c conda-forge camelot-py' 를 실행해주세요."
    )

# --- 로깅 설정 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- 0. 설정 불러오기 (config.json 대신 기본값) ---
# 이 예제에서는 CONFIG 없이 기본 상수를 사용하도록 간소화합니다.

OCR_LANG = 'kor'
OCR_DPI = 300
HEADER_HEIGHT_PT = 60.0
FOOTER_HEIGHT_PT = 40.0
COLUMN_GAP_RATIO = 0.5
EMPTY_VALUE = None

# --- 헬퍼 함수 ---

def get_current_timestamp_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()

def generate_unique_id(prefix=""):
    return f"{prefix.upper()}_{uuid.uuid4().hex[:6].upper()}"

def ocr_image_region(pil_img, lang=OCR_LANG, psm=6):
    """PIL 이미지 영역 OCR + confidence 반환"""
    # --- pre-process for clean horizontal Korean text ---
    # convert PIL to OpenCV image
    open_cv_image = np.array(pil_img.convert('RGB'))[:, :, ::-1]
    # grayscale
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    # Otsu threshold
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # convert back to PIL
    pil_img = Image.fromarray(binary)

    if pil_img.width < 5 or pil_img.height < 5:
        return "", 0.0
    try:
        whitelist = '가-힣A-Za-z0-9\\s\\./\\(\\)\\-'
        config = f'--oem 3 --psm {psm} -c tessedit_char_whitelist={whitelist}'
        data = pytesseract.image_to_data(
            pil_img, lang=lang, config=config,
            output_type=pytesseract.Output.DICT
        )
        words, confs = [], []
        for i, txt in enumerate(data['text']):
            conf = int(data['conf'][i])
            if data['level'][i] == 5 and conf > -1 and txt.strip():
                words.append(txt.strip())
                confs.append(conf)
        text = " ".join(words)
        avg_conf = (sum(confs)/len(confs)/100) if confs else 0.0
        return text, round(avg_conf, 2)
    except Exception as e:
        logger.error(f"OCR 실패: {e}")
        return "", 0.0

def convert_pdf_date_to_iso(pdf_date_str):
    if not pdf_date_str or not pdf_date_str.startswith("D:"):
        return None
    try:
        dt = datetime.strptime(pdf_date_str[2:16], "%Y%m%d%H%M%S")
        return dt.isoformat() + "Z"
    except ValueError:
        return pdf_date_str

# --- PDF 메타데이터 추출 ---

def get_pdf_document_info_from_meta(doc, pdf_path):
    meta = doc.metadata
    first = doc[0] if doc.page_count else None
    return {
        "source_file_name": os.path.basename(pdf_path),
        "title": meta.get("title") or os.path.splitext(os.path.basename(pdf_path))[0],
        "author": meta.get("author", EMPTY_VALUE),
        "creation_date_pdf": convert_pdf_date_to_iso(meta.get("creationDate")),
        "extraction_details": {
            "timestamp": get_current_timestamp_iso(),
            "tool_chain": "PyMuPDF->Pillow->Pytesseract->Camelot->CustomParser",
            "tool_versions": {
                "PyMuPDF": fitz.__doc__.split("Version ")[1].split()[0] if fitz.__doc__ and "Version" in fitz.__doc__ else "N/A",
                "Pillow": Image.__version__ if hasattr(Image, "__version__") else "N/A",
                "Pytesseract": str(pytesseract.get_tesseract_version()) if hasattr(pytesseract, "get_tesseract_version") else "N/A",
                "Camelot": camelot.__version__ if hasattr(camelot, "__version__") else "N/A",
                "CustomParser": "1.0"
            }
        },
        "physical_layout_defaults": {
            "total_pages_in_pdf": doc.page_count,
            "page_width_pt": first.rect.width if first else 595.0,
            "page_height_pt": first.rect.height if first else 842.0,
            "columns_per_page": 2,
            "estimated_header_height_pt": HEADER_HEIGHT_PT,
            "estimated_footer_height_pt": FOOTER_HEIGHT_PT
        },
        "data_conventions": {
            "coordinate_system": "PDF points (origin bottom-left for PyMuPDF)",
            "empty_value_representation": EMPTY_VALUE,
            "confidence_score_scale": "0.0–1.0"
        }
    }

# --- 페이지 처리 ---

def process_single_page_details(page, layout_defaults, pdf_path, page_num):
    """페이지 물리 정보 + OCR 추출 + 테이블 위치 식별"""
    # 이미지 렌더링
    factor = OCR_DPI / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(factor, factor), alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes()))

    w_px, h_px = img.size
    header_h = int(layout_defaults["estimated_header_height_pt"] * factor)
    footer_h = int(layout_defaults["estimated_footer_height_pt"] * factor)

    # 헤더/풋터 OCR
    header_img = img.crop((0, 0, w_px, header_h))
    header_text, header_conf = ocr_image_region(header_img, psm=6)
    footer_img = img.crop((0, h_px - footer_h, w_px, h_px))
    footer_text, footer_conf = ocr_image_region(footer_img, psm=6)

    # 본문 -> 컬럼 분리
    body = img.crop((0, header_h, w_px, h_px - footer_h))
    mid = int(body.width * COLUMN_GAP_RATIO)
    left_img, right_img = body.crop((0,0,mid,body.height)), body.crop((mid,0,body.width,body.height))
    left_text, left_conf = ocr_image_region(left_img)
    right_text, right_conf = ocr_image_region(right_img)

    # PDF 좌표 bbox 계산
    pw, ph = page.rect.width, page.rect.height
    start_y, end_y = layout_defaults["estimated_header_height_pt"], ph - layout_defaults["estimated_footer_height_pt"]
    split_x = pw * COLUMN_GAP_RATIO
    left_bbox = [0.0, start_y, split_x, end_y]
    right_bbox = [split_x, start_y, pw, end_y]

    # 테이블 위치 식별 (Camelot)
    elements = []
    try:
        tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='stream')
        for idx, tbl in enumerate(tables, 1):
            eid = generate_unique_id(f"T{page_num}_{idx}")
            x1,y1,x2,y2 = tbl._bbox  # use private _bbox attribute
            # PyMuPDF 좌하단 원점 변환
            fitz_bbox = [x1, ph - y2, x2, ph - y1]
            col_idx = 0 if ((fitz_bbox[0]+fitz_bbox[2])/2) < split_x else 1
            elements.append({
                "element_id": eid,
                "type": "data_table",
                "bbox_pt": fitz_bbox,
                "column_index_assignment": col_idx,
                "estimated_confidence": round(tbl.parsing_report.get('accuracy',0)/100, 2)
            })
    except Exception as e:
        logger.warning(f"페이지 {page_num} Camelot 테이블 오류: {e}")

    return {
        "page_number_in_pdf": page_num,
        "display_page_label": footer_text or f"{page_num}/{layout_defaults['total_pages_in_pdf']}",
        "dimensions_pt": {"width": pw, "height": ph},
        "detected_header_text": header_text,
        "detected_footer_text": footer_text,
        "columns_content": [
            {"column_index": 0, "bbox_pt": left_bbox, "raw_ocr_text": left_text, "estimated_confidence": left_conf},
            {"column_index": 1, "bbox_pt": right_bbox, "raw_ocr_text": right_text, "estimated_confidence": right_conf}
        ],
        "identified_structural_elements_locations": elements
    }

# --- 구조화된 요소 파싱 ---

def parse_structured_elements_data(page_details, pdf_path, doc):
    all_elems = {}
    for pd in page_details:
        pn = pd["page_number_in_pdf"]
        ph = doc[pn-1].rect.height
        for loc in pd["identified_structural_elements_locations"]:
            eid, etype, bbox = loc["element_id"], loc["type"], loc["bbox_pt"]
            if etype == "data_table":
                # Camelot 다시 호출하여 데이터 확보
                area = f"{bbox[0]},{ph-bbox[3]},{bbox[2]},{ph-bbox[1]}"
                try:
                    tables = camelot.read_pdf(
                        pdf_path,
                        pages=str(pn),
                        flavor='stream',
                        table_areas=[area]
                    )
                    df = tables[0].df if tables else None
                    headers = df.iloc[0].tolist() if df is not None and len(df) > 0 else []
                    rows = []
                    if df is not None and len(df)>1:
                        for _, row in df.iloc[1:].iterrows():
                            rows.append({h: str(row[i]).strip() if row[i] is not None else EMPTY_VALUE
                                         for i,h in enumerate(headers)})
                    raw_txt = df.to_string(index=False) if df is not None else ""
                    all_elems[eid] = {
                        "type": "data_table",
                        "source_page_number": pn,
                        "primary_column_assignment": loc["column_index_assignment"],
                        "caption_or_title_text": None,
                        "table_headers": headers,
                        "table_rows_data": rows,
                        "parsing_details": {
                            "parsing_confidence": loc["estimated_confidence"],
                            "parsing_method": "Camelot:stream"
                        },
                        "raw_element_ocr_text": raw_txt
                    }
                except Exception as e:
                    logger.error(f"테이블 파싱 실패 {eid}: {e}")
    return all_elems

# --- 논리 구조 파싱 (간략화) ---

def parse_document_logical_content(pages_texts, page_details, structured_map):
    # TODO: 실제 문서 분석에 맞춰 개발 필요
    return {"problems": []}

# --- 서문·부록 추출 ---

def extract_preamble_and_appendices_content(pages_texts):
    # TODO: 키워드 기반 구현
    return [], []

# --- 메인 파이프라인 ---

def main_processing_pipeline(pdf_path, out_json):
    doc = fitz.open(pdf_path)
    info = get_pdf_document_info_from_meta(doc, pdf_path)
    layout = info["physical_layout_defaults"]

    page_details = []
    pages_texts = []
    for i in range(doc.page_count):
        pd = process_single_page_details(doc[i], layout, pdf_path, i+1)
        page_details.append(pd)
        pages_texts.append({
            "page": i+1,
            "left_text": pd["columns_content"][0]["raw_ocr_text"],
            "right_text": pd["columns_content"][1]["raw_ocr_text"]
        })

    structured = parse_structured_elements_data(page_details, pdf_path, doc)
    preamble, appendices = extract_preamble_and_appendices_content(pages_texts)
    logical = parse_document_logical_content(pages_texts, page_details, structured)

    final = {
        "schema_version": "1.1",
        "document_info": info,
        "preamble_content": preamble,
        "page_details": page_details,
        "logical_content_structure": logical,
        "structured_data_elements": structured,
        "appendices_content": appendices
    }
    doc.close()

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved JSON to {out_json}")

# --- 실행부 ---

if __name__ == "__main__":
    # pdfs 폴더 및 리스트 파일 경로
    base_dir = os.path.join(os.path.dirname(__file__), "pdfs")
    list_file = os.path.join(base_dir, "pdf_list.txt")
    if not os.path.exists(list_file):
        logger.error(f"목록 파일이 없습니다: {list_file}")
        sys.exit(1)

    # try UTF-8 first, then fall back to CP949 if it fails
    try:
        with open(list_file, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
    except UnicodeDecodeError:
        with open(list_file, 'r', encoding='cp949') as f:
            lines = f.read().splitlines()
    pdfs_to_process = [
        ln.strip() for ln in lines
        if ln.strip() and not ln.startswith('#')
    ]

    output_root = os.path.join(base_dir, "extracted_json_results")
    os.makedirs(output_root, exist_ok=True)

    for name in pdfs_to_process:
        pdf_path = os.path.join(base_dir, name)
        if not os.path.exists(pdf_path):
            logger.warning(f"파일 없음, 건너뜀: {pdf_path}")
            continue
        out_path = os.path.join(output_root, os.path.splitext(name)[0] + "_extracted.json")
        main_processing_pipeline(pdf_path, out_path)
