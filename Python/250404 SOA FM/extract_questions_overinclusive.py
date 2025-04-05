import re
import json
from pathlib import Path
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    return full_text

def preprocess_text(text):
    # 각 줄을 분리하고, 만약 줄 전체가 숫자만 있는 경우(예: 페이지 번호) 제거
    lines = text.splitlines()
    filtered_lines = [line for line in lines if not re.match(r"^\s*\d+\s*$", line)]
    return "\n".join(filtered_lines)

def extract_questions_by_number(text):
    """
    개선된 정규표현식:
      - (?m): 멀티라인 모드
      - ^\s*(\d{1,3})\. : 줄 맨 앞에 1~3자리 숫자와 점
      - \s+ : 한 개 이상의 공백
      - (?![A-E]\b): 바로 뒤에 단독 A~E가 나오면(답안 선택지인 경우) 매칭하지 않음
      - (.*?): 최소 반복으로 해당 문제 블록의 본문 캡처 (다음 문제 번호가 나오기 전까지)
      - (?=^\s*\d{1,3}\.\s+|$): 다음 문제 번호나 텍스트 끝까지
    """
    pattern = r"(?m)^\s*(\d{1,3})\.\s+(?![A-E]\b)(.*?)(?=^\s*\d{1,3}\.\s+|$)"
    matches = list(re.finditer(pattern, text, re.DOTALL))
    items = {}
    for match in matches:
        number = match.group(1)
        content = match.group(2).strip()
        # 선택지 (예: (A))가 포함되어 있는 경우만 정상적인 문제로 판단
        if re.search(r"\([A-E]\)", content):
            items[number] = content
    return items

def verify_sequential_numbers(questions):
    # 추출된 문제 번호를 정렬하고, 누락된 번호가 있는지 확인
    q_nums = sorted(map(int, questions.keys()))
    if not q_nums:
        print("No question numbers found.")
        return
    expected = list(range(q_nums[0], q_nums[-1] + 1))
    missing = sorted(set(expected) - set(q_nums))
    print("Extracted question numbers:", q_nums)
    print("Expected sequence:", expected)
    print("Missing numbers:", missing)

if __name__ == "__main__":
    base = Path(__file__).parent
    raw_text = extract_text_from_pdf(base / "2018-10-exam-fm-sample-questions.pdf")
    processed_text = preprocess_text(raw_text)
    questions = extract_questions_by_number(processed_text)
    
    print(f"📘 개선된 추출 방식으로 문제 수: {len(questions)}개")
    verify_sequential_numbers(questions)
    
    with open(base / "questions_filtered_improved.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)