import fitz
import re
import json

######################
# 사용자가 직접 수정/확인해야 할 부분
######################
pdf_path = "2018-10-exam-fm-sample-solutions.pdf"  # 실제 파일명에 맞춰 변경
output_json = "solutions_minimal.json"            # 결과 JSON 파일명
# (E) 종결코돈 기준으로 페이지를 구분
END_MARKER = "(E)"

# 문제번호 정규표현식: "12. " 형태
question_num_pattern = re.compile(r"^\s*(\d+)\.\s")

# 정답(A~E) 패턴: "Solution: A" ~ "Solution: E"
answer_pattern = re.compile(r"Solution\s*:\s*([A-E])")

# 수식 검출 키워드 (너무 광범위하면 거의 전부 true가 될 수 있음)
equation_keywords = [
    r"\^",   # x^2 등
    r"_",    # x_1 등
    r"±",    # ±
    r"Σ",    # Σ
    r"∫"     # ∫
]
equation_pattern = re.compile("|".join(equation_keywords))

# 도입부 몇 줄만 저장할지
MAX_INTRO_LINES = 2

def main():
    doc = fitz.open(pdf_path)

    # (1) PDF 모든 페이지 텍스트를 합쳐서, 각 페이지 끝에 (E) 추가
    all_text = []
    for page_index in range(len(doc)):
        text = doc[page_index].get_text("text")
        all_text.append(text)
        # 페이지 끝 표시
        all_text.append("\n" + END_MARKER + "\n")

    merged_text = "".join(all_text)

    # (2) (E) 기준으로 블록 분할
    raw_blocks = re.split(r"\(E\)\s*", merged_text)
    # 빈 블록 제거
    blocks = [b.strip() for b in raw_blocks if b.strip()]

    results = []

    def save_problem(q_num, block_lines):
        """
        문제번호(q_num), 라인 리스트(block_lines)를 받아서
        answer, intro_text, equations 여부 등을 추출.
        """
        joined_text = "\n".join(block_lines)

        # (A) 정답(A~E)
        ans_match = answer_pattern.search(joined_text)
        answer_char = ans_match.group(1) if ans_match else None

        # (B) 도입부 (최대 MAX_INTRO_LINES줄)
        intro_text_lines = block_lines[:MAX_INTRO_LINES]
        intro_text = "\n".join(intro_text_lines).strip()

        # (C) 수식 검출
        eq_found = bool(equation_pattern.search(joined_text))

        # (D) 페이지번호: 여기서는 따로 매핑하지 않으므로 None
        page_number = None

        results.append({
            "question_num": q_num,
            "page_number": page_number,
            "answer": answer_char,
            "intro_text": intro_text,
            "equations": eq_found
        })

    # (3) 각 블록에서, 문제번호 정규식으로 문제 단위 분리
    current_qnum = None
    current_lines = []

    for block in blocks:
        lines = block.splitlines()
        # 매 블록마다 line을 돌며 새로운 문제번호 만날 때마다 저장
        current_qnum = None
        current_lines = []

        for line in lines:
            q_match = question_num_pattern.match(line)
            if q_match:
                # 기존 문제 저장
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

    # (4) JSON 저장
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[완료] 총 {len(results)}개 문제 항목을 '{output_json}'에 저장했습니다.")

if __name__ == "__main__":
    main()