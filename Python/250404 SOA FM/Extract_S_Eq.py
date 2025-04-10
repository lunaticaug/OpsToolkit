import fitz
import re
import json

pdf_path = "2018-10-exam-fm-sample-solutions.pdf"
output_json = "solutions_final.json"

# 문제번호 정규표현식 예: "123. " 형태
question_num_pattern = re.compile(r"^\s*(\d+)\.\s")

# 정답(A~E) 패턴: "Solution: A" ~ "Solution: E"
answer_pattern = re.compile(r"Solution\s*:\s*([A-E])")

# 종결코돈: 페이지 끝마다 "(E)\n" 삽입 후 re.split에 활용
END_MARKER = "(E)"

# 수식(Equations) 검출용 키워드 (예시)
equation_keywords = [
    r"\^", r"_", r"\\sqrt", r"\\sin", r"\\cos", r"\=", 
    r"∞", r"≥", r"≤", r"∑", r"±", r"∫"
]
equation_pattern = re.compile("|".join(equation_keywords))

# 도입부 텍스트 최대 줄수
MAX_INTRO_LINES = 3

def main():
    doc = fitz.open(pdf_path)

    # (1) 페이지별 텍스트 읽고, 끝에 (E) 붙여 합치기
    all_text = []
    for page_index in range(len(doc)):
        page = doc[page_index]
        text = page.get_text("text")
        # 페이지 텍스트 + (E) 구분자
        all_text.append(text)
        all_text.append("\n" + END_MARKER + "\n")

    merged_text = "".join(all_text)

    # (2) (E) 기준으로 대분할
    blocks = re.split(r"\(E\)\s*", merged_text)
    # 빈 블록 제거
    blocks = [b.strip() for b in blocks if b.strip()]

    results = []

    def save_question(q_num, content_text):
        """
        문제번호(q_num), 전체 본문(content_text)에 대해:
        - 정답 탐지
        - 도입부 텍스트
        - 수식(Equations) 여부
        - (필요하다면) 페이지번호 연동
        """
        # (A) 정답(A~E) 찾기
        ans_match = answer_pattern.search(content_text)
        answer_char = ans_match.group(1) if ans_match else None

        # (B) 도입부
        lines = content_text.splitlines()
        intro_text = "\n".join(lines[:MAX_INTRO_LINES])

        # (C) 수식 포함 여부
        eq_match = equation_pattern.search(content_text)
        has_equation = True if eq_match else False

        # (D) 페이지번호: 현재 예시에서는 별도 로직 없이 None
        #    (기존에 page_number를 잘 찾았다면, 문제번호→페이지 매핑을 여기서 활용 가능)
        page_number = None

        # (E) results에 추가
        results.append({
            "question_num": q_num,
            "page_number": page_number,
            "content": content_text,
            "answer": answer_char,
            "intro_text": intro_text,
            "equations": has_equation
        })

    # (3) 블록 안에서 문제번호별로 세분화
    for block in blocks:
        lines = block.splitlines()
        current_qnum = None
        current_lines = []

        for line in lines:
            q_match = question_num_pattern.match(line)
            if q_match:
                # 이전 문제 저장
                if current_qnum and current_lines:
                    block_text = "\n".join(current_lines).strip()
                    save_question(current_qnum, block_text)

                current_qnum = q_match.group(1)  # ex) "12"
                current_lines = [line]
            else:
                # 기존 문제 영역이면 계속 누적
                if current_qnum:
                    current_lines.append(line)

        # 마지막 문제 저장
        if current_qnum and current_lines:
            block_text = "\n".join(current_lines).strip()
            save_question(current_qnum, block_text)

    # (4) JSON 저장
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[완료] 총 {len(results)}개 문제 데이터를 '{output_json}'에 저장했습니다.")

if __name__ == "__main__":
    main()