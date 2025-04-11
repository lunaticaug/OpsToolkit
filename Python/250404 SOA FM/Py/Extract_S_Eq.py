import fitz
import re
import json

# ========= 파일 / 설정 =========
pdf_path = "2018-10-exam-fm-sample-solutions.pdf"  # 실제 PDF 파일명
solution_pg_map_file = "solution_page_map.json"    # 문제번호 -> 페이지번호 매핑 파일
output_json = "solutions_minimal.json"             # 최종 JSON 결과 파일

END_MARKER = "(E)"  # 페이지 끝마다 추가해 블록 분할
question_num_pattern = re.compile(r"^\s*(\d+)\.\s")     # 문제번호 "12. " 형태
answer_pattern = re.compile(r"Solution\s*:\s*([A-E])")  # 정답(A~E)
MAX_INTRO_LINES = 2  # intro_text로 몇 줄을 가져올지

def clean_newlines(text: str) -> str:
    """
    텍스트 내의 줄바꿈을 제거(또는 단일 공백으로 치환)
    :param text: 원본 텍스트
    :return: 불필요한 \n이 제거되어 단일 공백만 있는 텍스트
    """
    # 줄바꿈 양쪽의 공백도 제거하고, 여러 개의 줄바꿈은 하나의 공백으로 치환
    return re.sub(r"\s*\n\s*", " ", text).strip()

def main():
    # (1) solution_page_map.json 로드
    with open(solution_pg_map_file, "r", encoding="utf-8") as f:
        sol_map = json.load(f)
        # 예: {"1": {"page_number":2}, "2": {"page_number":2}, ...}

    # (2) PDF 열고, 각 페이지 뒤에 (E)를 삽입
    doc = fitz.open(pdf_path)
    all_text_parts = []
    for page_index in range(len(doc)):
        text = doc[page_index].get_text("text")
        all_text_parts.append(text)
        all_text_parts.append("\n" + END_MARKER + "\n")
    merged_text = "".join(all_text_parts)

    # (3) (E) 기준으로 큰 블록 분할
    raw_blocks = re.split(r"\(E\)\s*", merged_text)
    blocks = [b.strip() for b in raw_blocks if b.strip()]

    results = []

    def save_problem(q_num, block_lines):
        """
        문제번호 q_num와 해당 블록의 라인 리스트(block_lines)를 받아서,
        - 정답(answer): "Solution: A~E" 패턴으로부터 추출
        - intro_text: "Solution:"이 있는 줄 바로 다음부터 최대 MAX_INTRO_LINES 줄 추출 후, 
                      불필요한 줄바꿈( \n )은 clean_newlines()를 통해 정리
        - page_number: solution_page_map.json을 사용
        """
        joined_text = "\n".join(block_lines)

        # A) 정답(A~E) 추출
        ans_match = answer_pattern.search(joined_text)
        answer_char = ans_match.group(1) if ans_match else None

        # B) page_number: sol_map에서 해당 문제번호가 있으면 불러옴
        page_number = sol_map.get(q_num, {}).get("page_number", None)

        # C) intro_text: "Solution:"이 포함된 줄 이후부터 MAX_INTRO_LINES 줄 추출
        sol_line_idx = None
        for i, line in enumerate(block_lines):
            if "Solution:" in line:
                sol_line_idx = i
                break

        if sol_line_idx is not None:
            start_idx = sol_line_idx + 1
            snippet = block_lines[start_idx : start_idx + MAX_INTRO_LINES]
            intro_text = "\n".join(snippet).strip()
        else:
            snippet = block_lines[1 : 1 + MAX_INTRO_LINES]
            intro_text = "\n".join(snippet).strip()

        # D) 불필요한 줄바꿈( \n )을 정리하여 단일 공백으로 치환
        intro_text = clean_newlines(intro_text)

        results.append({
            "question_num": q_num,
            "page_number": page_number,
            "answer": answer_char,
            "intro_text": intro_text
        })

    # (4) 블록 내 문제번호별로 문제를 분할 및 저장
    for block in blocks:
        lines = block.splitlines()
        current_qnum = None
        current_lines = []

        for line in lines:
            q_match = question_num_pattern.match(line)
            if q_match:
                if current_qnum and current_lines:
                    save_problem(current_qnum, current_lines)
                current_qnum = q_match.group(1)
                current_lines = [line]
            else:
                if current_qnum:
                    current_lines.append(line)

        if current_qnum and current_lines:
            save_problem(current_qnum, current_lines)

    # (5) 결과 JSON으로 저장
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[완료] 총 {len(results)}개 문제 항목을 '{output_json}'에 저장했습니다.")

if __name__ == "__main__":
    main()