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

def extract_questions_by_number(text):
    # 줄의 시작에서 공백 후 1~3자리 숫자와 점, 그 뒤에 한 개 이상의 공백이 오고, 바로 A~E가 나오지 않는 경우만 매칭
    pattern = r"(?m)^\s*(\d{1,3})\.\s+(?![A-E]\b)"
    matches = list(re.finditer(pattern, text))
    items = {}
    for i, match in enumerate(matches):
        number = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        items[number] = text[start:end].strip()
    return items

if __name__ == "__main__":
    base = Path(__file__).parent
    text = extract_text_from_pdf(base / "2018-10-exam-fm-sample-questions.pdf")
    questions = extract_questions_by_number(text)

    print(f"📘 번호 기반 안정 추출된 문제 수: {len(questions)}개")
    with open(base / "questions_filtered.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)