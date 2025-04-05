import re
import json
from pathlib import Path
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    주어진 PDF 파일에서 전체 텍스트를 추출합니다.
    """
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    return full_text

def preprocess_text(text):
    """
    텍스트를 줄 단위로 분리한 후, 
    단독으로 존재하는 페이지번호(공백 제외 숫자만 있는 줄)는 제거합니다.
    """
    lines = text.splitlines()
    filtered_lines = []
    for line in lines:
        if re.match(r"^\s*\d+\s*$", line):
            continue
        filtered_lines.append(line)
    return "\n".join(filtered_lines)

def extract_questions_and_pages(text):
    """
    전처리된 텍스트에서 문제 블록을 추출합니다.
    각 문제 블록은 “1.”, “2.” 등 1~3자리 숫자와 점으로 시작하며,
    블록 내부에 도입부에 페이지번호가 붙어 있는 경우(예: "3 3. …")에는
    첫 토큰을 페이지번호(page_number)로 분리하여 저장합니다.
    
    반환 예시:
      {
         "2": {
             "content": "Kathryn deposits 100 ... (E) 6195",
             "page_number": "3"  # (해당 블록 도입부에 페이지번호가 있다면)
         },
         ...
      }
    """
    # lookahead에 optional 페이지번호(숫자 + 공백)를 허용하도록 수정
    pattern = r"(?m)^\s*(\d{1,3})\.\s+(.*?)(?=^\s*(?:\d+\s+)?\d{1,3}\.\s+|$)"
    matches = list(re.finditer(pattern, text, re.DOTALL))
    items = {}
    for match in matches:
        prob_num = match.group(1)
        content = match.group(2).strip()
        page_number = None

        # 블록의 첫 줄에 페이지번호가 붙어 있는지 확인 (예: "3 3. …")
        lines = content.splitlines()
        if lines:
            first_line = lines[0]
            m = re.match(r"^\s*(\d+)\s+(.*)$", first_line)
            if m:
                page_number = m.group(1)
                # 첫 줄에서 페이지번호를 제거한 나머지로 대체
                lines[0] = m.group(2)
                content = "\n".join(lines).strip()
        items[prob_num] = {"content": content, "page_number": page_number}
    return items

def verify_sequential_numbers(questions):
    """
    추출된 문제번호들이 순차적으로 증가하는지 검증합니다.
    """
    q_nums = sorted(map(int, questions.keys()))
    if not q_nums:
        print("문제 번호를 찾을 수 없습니다.")
        return
    expected = list(range(q_nums[0], q_nums[-1] + 1))
    missing = sorted(set(expected) - set(q_nums))
    print("추출된 문제 번호:", q_nums)
    print("기대되는 번호:", expected)
    print("누락된 번호:", missing)

def verify_sequential_page_numbers(questions):
    """
    각 문제 블록에서 추출한 페이지번호(존재하는 경우)들이 순차적으로 증가하는지 검증합니다.
    """
    page_nums = [int(q["page_number"]) for q in questions.values() if q["page_number"] is not None]
    if not page_nums:
        print("추출된 페이지번호가 없습니다.")
        return
    page_nums_sorted = sorted(page_nums)
    expected = list(range(page_nums_sorted[0], page_nums_sorted[-1] + 1))
    missing = sorted(set(expected) - set(page_nums_sorted))
    print("추출된 페이지번호:", page_nums_sorted)
    print("기대되는 페이지번호 순서:", expected)
    print("누락된 페이지번호:", missing)

if __name__ == "__main__":
    base = Path(__file__).parent
    # 1. PDF에서 텍스트 추출
    raw_text = extract_text_from_pdf(base / "2018-10-exam-fm-sample-questions.pdf")
    # 2. 전처리: 단독 페이지번호 줄 제거
    processed_text = preprocess_text(raw_text)
    # 3. 문제와 페이지번호 추출
    questions = extract_questions_and_pages(processed_text)
    
    print(f"📘 개선된 방식으로 {len(questions)}개의 문제가 추출되었습니다.")
    verify_sequential_numbers(questions)
    verify_sequential_page_numbers(questions)
    
    # 4. 결과를 JSON 파일로 저장
    with open(base / "questions_filtered_improved.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)