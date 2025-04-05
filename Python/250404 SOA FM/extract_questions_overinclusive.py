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
    텍스트를 줄 단위로 분리한 후, 페이지번호처럼 
    공백을 제외하고 숫자만 있는 줄을 제거합니다.
    """
    lines = text.splitlines()
    filtered_lines = []
    # 만약 줄 전체가 공백과 숫자로만 구성되어 있다면 (예: 페이지 번호) 제거
    for line in lines:
        if re.match(r"^\s*\d+\s*$", line):
            continue
        filtered_lines.append(line)
    return "\n".join(filtered_lines)

def extract_questions_by_number(text):
    """
    전처리된 텍스트에서 문제 번호(1~3자리 숫자 뒤에 점)로 시작하는 문제 블록을 추출합니다.
    각 문제 블록은 다음 문제 번호가 나타나기 전까지의 텍스트를 포함합니다.
    """
    pattern = r"(?m)^\s*(\d{1,3})\.\s+(.*?)(?=^\s*\d{1,3}\.\s+|$)"
    matches = list(re.finditer(pattern, text, re.DOTALL))
    items = {}
    for match in matches:
        number = match.group(1)
        content = match.group(2).strip()
        items[number] = content
    return items

def verify_sequential_numbers(questions):
    """
    추출된 문제 번호들이 순차적인지 확인합니다.
    """
    q_nums = sorted(map(int, questions.keys()))
    if not q_nums:
        print("문제 번호를 찾을 수 없습니다.")
        return
    expected = list(range(q_nums[0], q_nums[-1] + 1))
    missing = sorted(set(expected) - set(q_nums))
    print("추출된 문제 번호:", q_nums)
    print("기대하는 순서:", expected)
    print("누락된 번호:", missing)

if __name__ == "__main__":
    base = Path(__file__).parent
    # 1. PDF에서 텍스트 추출
    raw_text = extract_text_from_pdf(base / "2018-10-exam-fm-sample-questions.pdf")
    # 2. 전처리: 페이지번호(숫자만 있는 줄) 제거
    processed_text = preprocess_text(raw_text)
    # 3. 문제 번호를 기준으로 문제 블록 추출
    questions = extract_questions_by_number(processed_text)
    
    print(f"📘 개선된 추출 방식으로 추출된 문제 개수: {len(questions)}개")
    verify_sequential_numbers(questions)
    
    # 4. 결과를 JSON 파일로 저장
    with open(base / "questions_filtered_improved.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)