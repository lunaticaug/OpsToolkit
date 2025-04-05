import re
import json
from pathlib import Path
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    Extract all text from the given PDF file.
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
    Preprocess text by splitting it into lines and removing any lines that consist solely of numbers 
    (which are likely page numbers or footer numbers).
    """
    lines = text.splitlines()
    # Remove lines that are only whitespace and digits
    filtered_lines = [line for line in lines if not re.match(r"^\s*\d+\s*$", line)]
    return "\n".join(filtered_lines)

def extract_questions_by_number(text):
    """
    Extract problem blocks from preprocessed text.
    
    The regex pattern explained:
      - (?m): Enable multiline mode.
      - ^\s*(\d{1,3})\. : At the start of a line, match 1-3 digit number followed by a dot.
      - \s+ : At least one space after the dot.
      - (?![A-E]\b) : Negative lookahead to ensure that the following text is NOT a standalone letter A–E 
                      (which would likely be an answer choice rather than problem text).
      - (.*?) : Non-greedy capture of the problem block.
      - (?=^\s*\d{1,3}\.\s+|$) : Stop at the next occurrence of a similar problem header or at the end of text.
    """
    pattern = r"(?m)^\s*(\d{1,3})\.\s+(?![A-E]\b)(.*?)(?=^\s*\d{1,3}\.\s+|$)"
    matches = list(re.finditer(pattern, text, re.DOTALL))
    items = {}
    for match in matches:
        number = match.group(1)
        content = match.group(2).strip()
        # 정상 문제라면 보통 "(A)" 등의 선택지가 포함됨
        if re.search(r"\([A-E]\)", content):
            items[number] = content
    return items

def verify_sequential_numbers(questions):
    """
    Verify if the extracted problem numbers are sequential.
    """
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
    # 1. PDF에서 텍스트 추출
    raw_text = extract_text_from_pdf(base / "2018-10-exam-fm-sample-questions.pdf")
    # 2. 전처리: 페이지 번호와 같이 숫자만 있는 줄을 제거
    processed_text = preprocess_text(raw_text)
    # 3. 문제 번호 기반으로 문제 블록 추출
    questions = extract_questions_by_number(processed_text)
    
    print(f"📘 개선된 추출 방식으로 문제 수: {len(questions)}개")
    verify_sequential_numbers(questions)
    
    # 4. 결과를 JSON 파일로 저장
    with open(base / "questions_filtered_improved.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)