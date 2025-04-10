import fitz
import re
import json

# ========= 파일 / 설정 =========
pdf_path = "2018-10-exam-fm-sample-solutions.pdf"  # 실제 PDF 파일명
solution_pg_map_file = "solution_page_map.json"    # 문제번호->페이지번호 매핑
output_json = "solutions_minimal.json"             # 최종 JSON 결과

END_MARKER = "(E)"  # 페이지 끝마다 추가해 블록 분할
question_num_pattern = re.compile(r"^\s*(\d+)\.\s")     # 문제번호 "12. " 형태
answer_pattern = re.compile(r"Solution\s*:\s*([A-E])")  # 정답(A~E)
MAX_INTRO_LINES = 2  # intro_text로 몇 줄을 가져올지

def main():
    # (1) solution_page_map.json 로드
    with open(solution_pg_map_file, "r", encoding="utf-8") as f:
        sol_map = json.load(f)
        # 구조 예: {"1": {"page_number":2}, "2": {"page_number":2}, ...}

    # (2) PDF 열고, 각 페이지 뒤에 (E)를 삽입
    doc = fitz.open(pdf_path)
    all_text_parts = []
    for page_index in range(len(doc)):
        text = doc[page_index].get_text("text")
        # 페이지 내용 + (E)
        all_text_parts.append(text)
        all_text_parts.append("\n" + END_MARKER + "\n")

    merged_text = "".join(all_text_parts)

    # (E) 기준으로 큰 블록 분할
    raw_blocks = re.split(r"\(E\)\s*", merged_text)
    blocks = [b.strip() for b in raw_blocks if b.strip()]

    results = []

    def save_problem(q_num, block_lines):
        """
        문제번호 q_num, 블록 라인들 block_lines를 받아
        - 정답(answer)
        - intro_text (“Solution: …” 바로 다음 줄부터)
        - page_number
        를 추출하여 results에 append.
        """
        joined_text = "\n".join(block_lines)

        # A) 정답(A~E)
        ans_match = answer_pattern.search(joined_text)
        answer_char = ans_match.group(1) if ans_match else None

        # B) page_number (solution_pg_map.json 이용)
        page_number = None
        if q_num in sol_map:
            page_number = sol_map[q_num].get("page_number")

        # C) intro_text : “문제번호 + Solution: X” 라인 찾고, 그 다음 줄부터 N줄
        sol_line_idx = None
        for i, line in enumerate(block_lines):
            if "Solution:" in line:
                # 예: "1. Solution: A"
                sol_line_idx = i
                break

        intro_text = ""
        if sol_line_idx is not None:
            # 그 다음 줄부터 MAX_INTRO_LINES줄
            start_idx = sol_line_idx + 1
            snippet = block_lines[start_idx : start_idx + MAX_INTRO_LINES]
            intro_text = "\n".join(snippet).strip()
        else:
            # 혹시 못 찾으면, block_lines[1:N]을 intro_text로
            snippet = block_lines[1 : 1 + MAX_INTRO_LINES]
            intro_text = "\n".join(snippet).strip()

        # 최종 저장 (equations 없이)
        results.append({
            "question_num": q_num,
            "page_number": page_number,
            "answer": answer_char,
            "intro_text": intro_text
        })

    # (3) 블록을 순회, 문제번호 정규식으로 세분화
    for block in blocks:
        lines = block.splitlines()
        current_qnum = None
        current_lines = []

        for line in lines:
            q_match = question_num_pattern.match(line)
            if q_match:
                # 이미 인식된 문제 있으면 저장
                if current_qnum and current_lines:
                    save_problem(current_qnum, current_lines)
                # 새 문제번호
                current_qnum = q_match.group(1)
                current_lines = [line]
            else:
                if current_qnum:
                    current_lines.append(line)

        # 마지막 문제
        if current_qnum and current_lines:
            save_problem(current_qnum, current_lines)

    # (4) JSON으로 저장
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[완료] 총 {len(results)}개 문제를 '{output_json}'에 저장했습니다.")

if __name__ == "__main__":
    main()