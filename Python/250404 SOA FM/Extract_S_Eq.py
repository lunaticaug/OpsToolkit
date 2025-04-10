import fitz
import re
import json

pdf_path = "2018-10-exam-fm-sample-solutions.pdf"  # PDF 경로
output_json = "solutions_minimal.json"            # 결과 JSON

END_MARKER = "(E)"

# 문제번호 정규식: "12. "
question_num_pattern = re.compile(r"^\s*(\d+)\.\s")

# 정답(A~E) 패턴: "Solution: A" ~ "Solution: E"
answer_pattern = re.compile(r"Solution\s*:\s*([A-E])")

# 조금 더 좁은 범위의 수식 키워드 예시
equation_keywords = [r"\^", r"_", r"±", r"Σ", r"∫"]
equation_pattern = re.compile("|".join(equation_keywords))

# 도입부 줄(해설) 최대 2줄
MAX_INTRO_LINES = 2

def main():
    doc = fitz.open(pdf_path)

    # 모든 페이지 텍스트에 (E) 삽입
    all_text = []
    for page_index in range(len(doc)):
        text = doc[page_index].get_text("text")
        all_text.append(text)
        all_text.append("\n" + END_MARKER + "\n")
    merged_text = "".join(all_text)

    # (E)로 블록 분할
    raw_blocks = re.split(r"\(E\)\s*", merged_text)
    blocks = [b.strip() for b in raw_blocks if b.strip()]

    results = []

    def save_problem(q_num, block_lines):
        """
        q_num (str), block_lines (list of str)
        1) 정답 찾기
        2) intro_text는 "Solution: X" 다음 줄부터
        """
        joined_text = "\n".join(block_lines)

        # A) 정답(A~E)
        ans_match = answer_pattern.search(joined_text)
        answer_char = ans_match.group(1) if ans_match else None

        # B) “문제번호 + Solution” 라인이 어디 있나 찾고, 그 다음 줄부터 intro_text
        intro_text = ""
        # line index
        sol_line_idx = None
        # 문제번호 라인 = block_lines[0] 가정할 수도 있으나, 혹시 중간에 있는 경우도 감안
        # "n. Solution: X" 구문을 찾으면 그 line index+1부터 intro_text
        for i, line in enumerate(block_lines):
            # 문제번호와 "Solution:"이 함께 있는지 확인
            if question_num_pattern.search(line) and "Solution:" in line:
                sol_line_idx = i
                break

        # sol_line_idx가 None이 아니면, 그 다음 줄부터 intro_text
        # 최대 MAX_INTRO_LINES 줄
        if sol_line_idx is not None:
            start_intro = sol_line_idx + 1
            end_intro = start_intro + MAX_INTRO_LINES
            snippet_lines = block_lines[start_intro:end_intro]
            intro_text = "\n".join(snippet_lines).strip()
        else:
            # "Solution:" 라인을 못 찾으면, 그냥 block_lines[1:] 몇 줄만 intro
            # (혹은 empty)
            snippet_lines = block_lines[1:1+MAX_INTRO_LINES]
            intro_text = "\n".join(snippet_lines).strip()

        # C) 수식 포함 여부
        eq_found = bool(equation_pattern.search(joined_text))

        # D) page_number는 None
        page_number = None

        results.append({
            "question_num": q_num,
            "page_number": page_number,
            "answer": answer_char,
            "intro_text": intro_text,
            "equations": eq_found
        })

    # 블록별로 문제번호 감지
    for block in blocks:
        lines = block.splitlines()
        current_qnum = None
        current_lines = []

        for line in lines:
            q_match = question_num_pattern.match(line)
            if q_match:
                # 이전 문제 저장
                if current_qnum and current_lines:
                    save_problem(current_qnum, current_lines)
                # 새 문제 시작
                current_qnum = q_match.group(1)
                current_lines = [line]
            else:
                if current_qnum:
                    current_lines.append(line)

        # 마지막 문제
        if current_qnum and current_lines:
            save_problem(current_qnum, current_lines)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[완료] 총 {len(results)}개 문제 항목을 '{output_json}'에 저장했습니다.")


if __name__ == "__main__":
    main()