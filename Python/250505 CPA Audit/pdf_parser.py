# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageDraw
import io
import re
import json
import camelot # 테이블 추출용
import os
import sys
from datetime import datetime, timezone
import uuid
import logging

# --- 0. 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 1. 설정 로드 및 상수 ---
CONFIG = {}

def load_config(config_path="config.json"):
    global CONFIG
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG = json.load(f)
        logger.info(f"설정 파일 로드 성공: {config_path}")
    except FileNotFoundError:
        logger.error(f"오류: 설정 파일({config_path})을 찾을 수 없습니다. 기본값으로 실행 불가능. 스크립트를 종료합니다.")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"오류: 설정 파일({config_path})이 올바른 JSON 형식이 아닙니다. 스크립트를 종료합니다.")
        sys.exit(1)

# Tesseract 경로 설정 (필요시 주석 해제 및 실제 경로로 수정)
# TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Windows 예시
# if TESSERACT_PATH and os.path.exists(TESSERACT_PATH):
#     pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
# else:
#     logger.warning("Tesseract 경로가 설정되지 않았거나 유효하지 않습니다. 시스템 PATH에 의존합니다.")


# --- 2. 유틸리티 함수 ---
def get_current_timestamp_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()

def generate_unique_id(prefix=""):
    return f"{prefix.upper()}_{uuid.uuid4().hex[:8].upper()}"

def convert_pdf_date_to_iso(pdf_date_str):
    if not pdf_date_str: return CONFIG["schema_details"].get("empty_value_representation_is_null", True) and None or ""
    if pdf_date_str.startswith("D:"):
        dt_str = pdf_date_str[2:16]
        try:
            dt_obj = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
            offset_str = pdf_date_str[16:].replace("'", "")
            # TODO: 실제 PDF 시간대 오프셋 파싱 및 적용 (현재는 UTC로 가정)
            return dt_obj.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            logger.warning(f"PDF 날짜 형식 변환 실패: {pdf_date_str}")
    return pdf_date_str

def ocr_image_region(pil_image, lang=None, psm=None):
    lang = lang or CONFIG["ocr_engine_options"]["lang"]
    psm = psm or CONFIG["ocr_engine_options"]["default_psm"]
    if pil_image.width < 5 or pil_image.height < 5:
        return "", 0.0
    try:
        custom_config = f'--oem 3 --psm {psm}'
        ocr_data = pytesseract.image_to_data(pil_image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)
        text_segments, confidences = [], []
        for i in range(len(ocr_data['text'])):
            if ocr_data['level'][i] == 5 and int(ocr_data['conf'][i]) > -1:
                word_text = ocr_data['text'][i].strip()
                if word_text:
                    text_segments.append(word_text)
                    confidences.append(int(ocr_data['conf'][i]))
        full_text = " ".join(text_segments)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return full_text.strip(), round(avg_confidence / 100.0, 3)
    except Exception as e:
        logger.error(f"OCR 중 오류 발생 (이미지 크기: {pil_image.size}): {e}", exc_info=False) # exc_info=True로 스택 트레이스 확인 가능
        return "", 0.0

def get_pdf_document_info_from_meta(doc_fitz, pdf_file_path):
    meta = doc_fitz.metadata
    page_one = doc_fitz[0] if len(doc_fitz) > 0 else None
    
    pymupdf_version = "N/A"
    if hasattr(fitz, '__doc__') and fitz.__doc__:
      version_match = re.search(r'Version\s*([\d\.]+)', fitz.__doc__)
      if version_match: pymupdf_version = version_match.group(1)

    tool_versions = {
        "PyMuPDF": pymupdf_version,
        "Pillow": Image.__version__ if hasattr(Image, '__version__') else "N/A",
        "Pytesseract": str(pytesseract.get_tesseract_version()).strip() if hasattr(pytesseract, 'get_tesseract_version') else "N/A",
        "Camelot": camelot.__version__ if hasattr(camelot, '__version__') else "N/A",
        "CustomParser": CONFIG["schema_details"]["version"] # 이 스크립트의 스키마 버전과 동일하게
    }
    
    empty_repr = None if CONFIG["schema_details"]["empty_value_representation_is_null"] else ""

    return {
        "source_file_name": os.path.basename(pdf_file_path),
        "title": meta.get("title") or os.path.splitext(os.path.basename(pdf_file_path))[0],
        "author": meta.get("author", empty_repr),
        "creation_date_pdf": convert_pdf_date_to_iso(meta.get("creationDate")),
        "extraction_details": {
            "timestamp": get_current_timestamp_iso(),
            "tool_chain": "PyMuPDF -> Pillow -> Pytesseract -> Camelot -> Custom Python Parser",
            "tool_versions": tool_versions
        },
        "physical_layout_defaults": {
            "total_pages_in_pdf": len(doc_fitz),
            "page_width_pt": page_one.rect.width if page_one else 595.0,
            "page_height_pt": page_one.rect.height if page_one else 842.0,
            "columns_per_page": CONFIG.get("physical_layout_defaults", {}).get("columns_per_page", 2),
            "estimated_header_height_pt": CONFIG.get("default_header_height_pt", 60.0),
            "estimated_footer_height_pt": CONFIG.get("default_footer_height_pt", 40.0)
        },
        "data_conventions": {
            "coordinate_system": "PDF points (origin: bottom-left for PyMuPDF bbox, top-left for Camelot bbox unless converted)",
            "empty_value_representation": empty_repr, # 스키마에 명시
            "confidence_score_scale": CONFIG["schema_details"]["confidence_score_scale"]
        }
    }

# --- 3. 페이지 단위 처리 함수 ---
def process_single_page_details(page_fitz_obj, layout_defaults, pdf_file_path_for_camelot, current_page_num):
    page_width_pt, page_height_pt = page_fitz_obj.rect.width, page_fitz_obj.rect.height
    ocr_dpi = CONFIG["ocr_dpi"]
    factor = ocr_dpi / 72.0
    matrix = fitz.Matrix(factor, factor)
    pix = page_fitz_obj.get_pixmap(matrix=matrix, alpha=False)
    full_page_pil = Image.open(io.BytesIO(pix.tobytes()))
    img_w_px, img_h_px = full_page_pil.size

    header_h_px = int(layout_defaults["estimated_header_height_pt"] * factor)
    footer_h_px = int(layout_defaults["estimated_footer_height_pt"] * factor)

    header_img = full_page_pil.crop((0, 0, img_w_px, header_h_px))
    header_text, header_conf = ocr_image_region(header_img, psm=CONFIG["ocr_engine_options"]["header_footer_psm"])

    footer_img = full_page_pil.crop((0, img_h_px - footer_h_px, img_w_px, img_h_px))
    footer_text, footer_conf = ocr_image_region(footer_img, psm=CONFIG["ocr_engine_options"]["header_footer_psm"])
    
    body_img = full_page_pil.crop((0, header_h_px, img_w_px, img_h_px - footer_h_px))
    body_w_px, body_h_px = body_img.size
    col_split_px = int(body_w_px * CONFIG.get("default_column_gap_ratio", 0.5))

    left_col_img = body_img.crop((0, 0, col_split_px, body_h_px))
    left_text, left_conf = ocr_image_region(left_col_img)

    right_col_img = body_img.crop((col_split_px, 0, body_w_px, body_h_px))
    right_text, right_conf = ocr_image_region(right_col_img)

    content_start_y = layout_defaults["estimated_header_height_pt"]
    content_end_y = page_height_pt - layout_defaults["estimated_footer_height_pt"]
    mid_x = page_width_pt * CONFIG.get("default_column_gap_ratio", 0.5)
    left_bbox = [0.0, content_start_y, mid_x, content_end_y]
    right_bbox = [mid_x, content_start_y, page_width_pt, content_end_y]

    display_label = footer_text # 기본값
    page_label_re = CONFIG["regex_patterns"]["page_label_common"]
    match_label = re.search(page_label_re, footer_text) or re.search(page_label_re, header_text)
    if match_label: display_label = match_label.group(1).replace(" ", "")

    page_entry = {
        "page_number_in_pdf": current_page_num, "display_page_label": display_label,
        "dimensions_pt": {"width": page_width_pt, "height": page_height_pt},
        "detected_header_text": header_text, "detected_footer_text": footer_text,
        "columns_content": [
            {"column_index": 0, "bbox_pt": left_bbox, "raw_ocr_text": left_text, "estimated_confidence": left_conf},
            {"column_index": 1, "bbox_pt": right_bbox, "raw_ocr_text": right_text, "estimated_confidence": right_conf}
        ],
        "identified_structural_elements_locations": []
    }

    try:
        camelot_opts = CONFIG["camelot_options"]
        tables_camelot = camelot.read_pdf(pdf_file_path_for_camelot, pages=str(current_page_num), 
                                          flavor=camelot_opts["flavor"], line_scale=camelot_opts["line_scale"],
                                          edge_tol=camelot_opts["edge_tol"])
        for tbl_idx, detected_table in enumerate(tables_camelot):
            el_id = generate_unique_id(f"TABLE_P{current_page_num}_T{tbl_idx+1}")
            cb = detected_table.bbox
            fitz_bbox = [cb[0], page_height_pt - cb[3], cb[2], page_height_pt - cb[1]]
            col_assign = 0 if (fitz_bbox[0] + fitz_bbox[2]) / 2 < mid_x else 1
            page_entry["identified_structural_elements_locations"].append({
                "element_id": el_id, "type": "data_table", "bbox_pt": fitz_bbox,
                "column_index_assignment": col_assign,
                "estimated_confidence": round(detected_table.parsing_report.get('accuracy', 0) / 100.0, 3)
            })
    except Exception as e:
        logger.warning(f"Camelot 테이블 추출 실패 (페이지 {current_page_num}): {e}", exc_info=False)

    # TODO: 양식 영역 식별 로직 (예: 키워드 기반)
    # form_keyword = CONFIG["keywords"]["form_title_keyword"]
    # for col_idx, col_data in enumerate(page_entry["columns_content"]):
    #   if form_keyword in col_data["raw_ocr_text"]:
    #       # form_bbox = estimate_form_bbox_from_text_location(...) # 매우 복잡
    #       # page_entry["identified_structural_elements_locations"].append(...)
    #       pass
    return page_entry

# --- 4. 구조화된 요소(테이블/양식) 상세 데이터 파싱 ---
def parse_structured_elements_data(page_details_list, pdf_file_path_for_camelot, doc_fitz_obj):
    all_elements = {}
    empty_repr = None if CONFIG["schema_details"]["empty_value_representation_is_null"] else ""
    camelot_opts = CONFIG["camelot_options"]

    for page_data in page_details_list:
        current_page_num = page_data["page_number_in_pdf"]
        page_fitz = doc_fitz_obj[current_page_num - 1]

        for el_loc in page_data["identified_structural_elements_locations"]:
            el_id, el_type, el_bbox = el_loc["element_id"], el_loc["type"], el_loc["bbox_pt"]
            el_col_assign = el_loc["column_index_assignment"]
            el_parsing_conf = el_loc["estimated_confidence"] # Camelot 정확도를 초기 파싱 신뢰도로 사용

            # 해당 bbox 영역 OCR (선택적, Camelot이 이미 텍스트를 제공하므로)
            # clip_rect = fitz.Rect(el_bbox)
            # pix_el = page_fitz.get_pixmap(matrix=fitz.Matrix(OCR_DPI/72, OCR_DPI/72), clip=clip_rect, alpha=False)
            # el_pil_img = Image.open(io.BytesIO(pix_el.tobytes()))
            # raw_ocr_text_for_element, _ = ocr_image_region(el_pil_img, psm=CONFIG["ocr_engine_options"]["table_psm"])
            raw_ocr_text_for_element = "RAW_OCR_TODO" # 임시

            if el_type == "data_table":
                try:
                    # bbox를 Camelot 좌표계로 변환: x1, y1(top), x2, y2(bottom)
                    camelot_bbox_str = f"{el_bbox[0]},{page_fitz.rect.height - el_bbox[3]},{el_bbox[2]},{page_fitz.rect.height - el_bbox[1]}"
                    tables = camelot.read_pdf(pdf_file_path_for_camelot, pages=str(current_page_num), flavor=camelot_opts["flavor"],
                                              table_areas=[camelot_bbox_str], line_scale=camelot_opts["line_scale"])
                    if tables:
                        df = tables[0].df
                        headers = [str(h).strip() if h is not None else "" for h in df.iloc[0].tolist()] if not df.empty and len(df.columns) > 0 else []
                        rows_data = []
                        if len(df) > (1 if headers else 0) : # 헤더가 있으면 1행부터, 없으면 0행부터
                            start_row = 1 if headers else 0
                            for _, row_series in df.iloc[start_row:].iterrows():
                                row_dict = {}
                                # 헤더가 실제 데이터보다 많거나 적을 수 있음
                                for h_idx, h_name in enumerate(headers):
                                    if h_idx < len(row_series):
                                        cell_val = row_series.iloc[h_idx]
                                        row_dict[h_name] = str(cell_val).strip() if cell_val is not None else empty_repr
                                    else: # 헤더는 있는데 데이터가 부족한 경우
                                        row_dict[h_name] = empty_repr
                                # 헤더보다 데이터 열이 더 많은 경우 (보통은 발생 안함)
                                if not headers and len(row_series) > 0: # 헤더가 없을 때
                                    row_dict = [str(cell_val).strip() if cell_val is not None else empty_repr for cell_val in row_series]

                                rows_data.append(row_dict)
                        
                        raw_ocr_text_for_element = df.to_string(index=False, header=False) # Camelot df에서 텍스트화

                        all_elements[el_id] = {
                            "type": "data_table", "source_page_number": current_page_num,
                            "primary_column_assignment": el_col_assign,
                            "caption_or_title_text": None, # TODO
                            "table_headers": headers, "table_rows_data": rows_data,
                            "parsing_details": {"parsing_confidence": el_parsing_conf, "parsing_method": f"Camelot:{camelot_opts['flavor']}"},
                            "raw_element_ocr_text": raw_ocr_text_for_element
                        }
                except Exception as e:
                    logger.error(f"테이블 파싱 실패 {el_id} (페이지 {current_page_num}): {e}", exc_info=False)
                    all_elements[el_id] = {"type": "data_table", "source_page_number": current_page_num, "raw_element_ocr_text": "PARSING_FAILED_WITH_CAMELOT", "parsing_details": {"parsing_confidence": 0.0}}
            
            elif el_type == "form_template":
                # TODO: 양식 파싱 로직 (규칙 기반, 키워드: CONFIG["keywords"]["form_title_keyword"])
                # 1. raw_ocr_text_for_element (해당 bbox OCR 결과) 사용
                # 2. 헤더 및 행 구조 파싱
                # 여기서는 기본 틀만 제공
                all_elements[el_id] = {
                    "type": "form_template", "source_page_number": current_page_num,
                    "primary_column_assignment": el_col_assign,
                    "caption_or_title_text": CONFIG["keywords"]["form_title_keyword"], # 예시
                    "form_fields_headers": [], # TODO
                    "form_rows_structure": [], # TODO
                    "parsing_details": {"parsing_confidence": 0.3, "parsing_method": "RuleBasedFormParser_TODO"},
                    "raw_element_ocr_text": raw_ocr_text_for_element
                }
    return all_elements

# --- 5. 논리적 구조 파싱 함수 ---
# TODO: 이 함수는 매우 정교한 개발이 필요합니다. 아래는 극히 일부의 데모 로직입니다.
def parse_document_logical_content(all_pages_column_texts, page_details_list, structured_elements_map):
    problems_list = []
    problem_re = re.compile(CONFIG["regex_patterns"]["problem_start"])
    subq_re = re.compile(CONFIG["regex_patterns"]["sub_question_start"])
    item_re = re.compile(CONFIG["regex_patterns"]["item_marker"], re.MULTILINE)

    full_text_for_parsing = ""
    # 페이지 및 컬럼 정보를 포함하는 텍스트 스트림 생성
    for p_idx, p_content in enumerate(all_pages_column_texts):
        # 페이지 번호 마커 추가 (파싱 시 위치 추적용)
        full_text_for_parsing += f"\n<PAGE:{p_content['page']}_COL:LEFT>\n{p_content['left_text']}\n"
        full_text_for_parsing += f"\n<PAGE:{p_content['page']}_COL:RIGHT>\n{p_content['right_text']}\n"

    # 문제 블록 찾기
    problem_matches = list(problem_re.finditer(full_text_for_parsing))
    for i, p_match in enumerate(problem_matches):
        problem_id = generate_unique_id("P" + p_match.group(2))
        problem_block_start = p_match.end()
        problem_block_end = problem_matches[i+1].start() if i + 1 < len(problem_matches) else len(full_text_for_parsing)
        problem_text_block = full_text_for_parsing[problem_block_start:problem_block_end].strip()
        
        # TODO: source_page_numbers, estimated_confidence 등 계산
        #       introductory_description_text 추출 (문제 제목 ~ 첫 물음 사이)
        
        current_problem = {
            "problem_id": problem_id, "display_number": p_match.group(2),
            "raw_title_text": p_match.group(1),
            "parsed_topic": p_match.group(4).strip() if p_match.group(4) else "주제 분석 필요",
            "points_allocated": int(p_match.group(3)),
            "introductory_description_text": "문제 설명 추출 필요", # TODO
            "source_page_numbers": [1], "estimated_confidence": 0.8, # TODO: 실제 값
            "sub_questions": []
        }

        # 물음 블록 찾기
        subq_matches = list(subq_re.finditer(problem_text_block))
        for j, sq_match in enumerate(subq_matches):
            subq_id = generate_unique_id(f"{problem_id}_Q{sq_match.group(2)}")
            subq_block_start = sq_match.end()
            subq_block_end = subq_matches[j+1].start() if j + 1 < len(subq_matches) else len(problem_text_block)
            subq_text_content_block = problem_text_block[subq_block_start:subq_block_end].strip()
            
            # 물음 프롬프트: (물음 X) 이후, 첫 항목 마커 이전까지
            first_item_in_subq = item_re.search(sq_match.group(3))
            actual_prompt = sq_match.group(3)[:first_item_in_subq.start()].strip() if first_item_in_subq else sq_match.group(3).strip()

            current_subq = {
                "sub_question_id": subq_id, "display_number": sq_match.group(2),
                "raw_prompt_text": sq_match.group(1) + " " + sq_match.group(3).strip(), # 원본 (물음X) + 내용
                "parsed_summary": "물음 요약 필요", # TODO
                "source_page_numbers": [1], "primary_column_assignment": "left", # TODO
                "estimated_confidence": 0.7, "content_elements": [],
                "referenced_structural_element_ids": [] # TODO
            }

            # 항목 파싱
            items_text_after_prompt = sq_match.group(3)[first_item_in_subq.start():].strip() if first_item_in_subq else ""
            item_matches = list(item_re.finditer(items_text_after_prompt))
            for k, item_match in enumerate(item_matches):
                item_id = generate_unique_id(f"{subq_id}_ITEM{k+1}")
                item_block_start = item_match.end()
                item_block_end = item_matches[k+1].start() if k + 1 < len(item_matches) else len(items_text_after_prompt)
                item_text = items_text_after_prompt[item_block_start:item_block_end].strip()
                
                current_subq["content_elements"].append({
                    "element_id": item_id, "type": "numbered_list_item",
                    "display_marker": item_match.group(1).strip(),
                    "text_content": item_text, "raw_ocr_text": item_match.group(0) + item_text,
                    "source_page_number": 1, "column_assignment": "left", # TODO
                    "estimated_confidence": 0.6 # TODO
                })
            current_problem["sub_questions"].append(current_subq)
        problems_list.append(current_problem)

    return {"problems": problems_list}


def extract_preamble_and_appendices(all_pages_column_texts_list):
    preamble_data, appendices_data = [], []
    preamble_keyword = CONFIG["keywords"]["preamble_start"]
    appendix_re = re.compile(CONFIG["keywords"]["appendix_start_regex"], re.IGNORECASE)

    # 서문 (보통 문서 초반)
    for p_idx, page_texts in enumerate(all_pages_column_texts_list):
        # 예시로 첫 1~2 페이지만 검색
        if page_texts["page"] > 2 and preamble_data: break # 서문은 보통 초반에
        
        combined_page_text = page_texts["left_text"] + "\n" + page_texts["right_text"]
        if preamble_keyword in combined_page_text and not preamble_data: # 한번만 찾음
            content = combined_page_text.split(preamble_keyword, 1)[1].split("【문제",1)[0].strip() # 문제 시작 전까지
            preamble_data.append({
                "block_id": generate_unique_id("PREAMBLE"), "type": "instruction_block",
                "text_content": content, "raw_ocr_text": preamble_keyword + "\n" + content,
                "source_page_numbers": [page_texts["page"]],
                "estimated_confidence": (page_texts["left_conf"] + page_texts["right_conf"])/2 # 대략적
            })
            break # 첫번째 발견된 것만 사용

    # 부록 (보통 문서 후반)
    # TODO: 부록 추출 로직 구현
    return preamble_data, appendices_data

# --- 6. 메인 실행 함수 ---
def main(pdf_file_path, output_json_path):
    logger.info(f"'{pdf_file_path}' 파일 처리 시작...")
    try:
        doc_fitz = fitz.open(pdf_file_path)
    except Exception as e:
        logger.error(f"오류: PDF 파일 열기 실패 - {pdf_file_path}. 에러: {e}", exc_info=True)
        return

    doc_info = get_pdf_document_info_from_meta(doc_fitz, pdf_file_path)
    layout_defaults = doc_info["physical_layout_defaults"]

    page_details_list_data = []
    all_column_texts_for_logic = []
    for i in range(len(doc_fitz)):
        logger.info(f"페이지 {i+1}/{len(doc_fitz)} 처리 중...")
        page_detail = process_single_page_details(doc_fitz[i], layout_defaults, pdf_file_path, i + 1)
        page_details_list_data.append(page_detail)
        all_column_texts_for_logic.append({
            "page": i + 1,
            "left_text": page_detail["columns_content"][0]["raw_ocr_text"],
            "left_conf": page_detail["columns_content"][0]["estimated_confidence"],
            "right_text": page_detail["columns_content"][1]["raw_ocr_text"],
            "right_conf": page_detail["columns_content"][1]["estimated_confidence"]
        })
    
    logger.info("구조화된 요소(테이블/양식) 데이터 파싱 중...")
    structured_elements = parse_structured_elements_data(page_details_list_data, pdf_file_path, doc_fitz)
    
    logger.info("서문 및 부록 추출 중...")
    preamble, appendices = extract_preamble_and_appendices(all_column_texts_for_logic)
    
    logger.info("논리적 콘텐츠 구조 파싱 중 (시간이 걸릴 수 있습니다)...")
    logical_structure = parse_document_logical_content(all_column_texts_for_logic, page_details_list_data, structured_elements)
    # TODO: 논리 구조 파싱 후, referenced_structural_element_ids를 structured_elements 키와 연결/검증
    # 예: for prob in logical_structure["problems"]: for sq in prob["sub_questions"]:
    #       sq["referenced_structural_element_ids"] = [id for id in sq.get("referenced_structural_element_ids", []) if id in structured_elements]

    final_output = {
        "schema_version": CONFIG["schema_details"]["version"],
        "document_info": doc_info,
        "preamble_content": preamble,
        "page_details": page_details_list_data,
        "logical_content_structure": logical_structure,
        "structured_data_elements": structured_elements,
        "appendices_content": appendices
    }
    
    doc_fitz.close()

    try:
        output_dir = CONFIG.get("output_options", {}).get("sub_directory_name", "extracted_json_results")
        if not os.path.isabs(output_json_path): # 상대경로이면
            base_output_dir = os.path.dirname(output_json_path) if os.path.dirname(output_json_path) else "."
            output_dir_path = os.path.join(base_output_dir, output_dir)
        else: # 절대경로이면
             output_dir_path = os.path.join(os.path.dirname(output_json_path), output_dir)

        os.makedirs(output_dir_path, exist_ok=True)
        final_json_file_path = os.path.join(output_dir_path, os.path.basename(output_json_path))


        with open(final_json_file_path, 'w', encoding='utf-8') as f_out:
            json.dump(final_output, f_out, ensure_ascii=False, indent=2)
        logger.info(f"추출된 데이터가 성공적으로 '{final_json_file_path}' 파일로 저장되었습니다.")
    except Exception as e:
        logger.error(f"오류: JSON 파일 저장 실패 - {final_json_file_path}. 에러: {e}", exc_info=True)

if __name__ == '__main__':
    # 스크립트 시작 시 설정 파일 로드
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_path = os.path.join(script_dir, "config.json")
    load_config(default_config_path)


    if len(sys.argv) < 2 : # 최소 1개 인자 (pdf_list.txt)
        print(f"사용법: python {os.path.basename(sys.argv[0])} <pdf_list_file.txt> [optional_output_dir]")
        print(f"예시: python {os.path.basename(sys.argv[0])} ./pdf_list.txt")
        sys.exit(1)
    
    pdf_list_file = sys.argv[1]
    # 기본 출력 디렉터리는 pdf_list.txt 파일이 있는 곳 하위의 설정된 폴더명
    custom_output_dir_base = os.path.dirname(os.path.abspath(pdf_list_file))
    if len(sys.argv) > 2:
        custom_output_dir_base = sys.argv[2] # 사용자가 출력 디렉터리 지정 시


    if not os.path.exists(pdf_list_file):
        logger.error(f"오류: PDF 목록 파일({pdf_list_file})을 찾을 수 없습니다.")
        sys.exit(1)

    with open(pdf_list_file, 'r', encoding='utf-8') as f_list:
        pdf_files = [line.strip() for line in f_list if line.strip() and not line.startswith('#')]

    if not pdf_files:
        logger.warning(f"'{pdf_list_file}'에 처리할 PDF 파일이 없습니다.")
        sys.exit(0)

    for pdf_path_in_list in pdf_files:
        # list.txt 파일 내의 경로가 상대경로일 경우, list.txt 파일 위치 기준으로 절대경로화
        if not os.path.isabs(pdf_path_in_list):
            pdf_path = os.path.join(os.path.dirname(os.path.abspath(pdf_list_file)), pdf_path_in_list)
        else:
            pdf_path = pdf_path_in_list
            
        if not os.path.exists(pdf_path):
            logger.warning(f"경고: 목록의 PDF 파일({pdf_path})을 찾을 수 없습니다. 건너뜁니다.")
            continue

        pdf_base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_json_file_name = f"{pdf_base_name}_extracted.json"
        
        # 출력 파일 경로 설정
        # 사용자가 지정한 출력 디렉터리가 있다면 그것을 사용, 없다면 list.txt와 동일한 디렉터리 사용
        final_output_path = os.path.join(custom_output_dir_base, output_json_file_name)


        main(pdf_path, final_output_path)