import re
import json
from pathlib import Path
from PyPDF2 import PdfReader

# 1. PDF 읽기 함수
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    return full_text

# 2. 문제 파싱 함수
def split_questions(text):
    pattern = r"(?m)^\s*(\d+)\.(?=\s+[A-Z])"
    matches = list(re.finditer(pattern, text))
    items = {}
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        number = match.group(1)
        items[number] = text[start:end].strip()
    return items

# 3. 실행
if __name__ == "__main__":
    base = Path(__file__).parent
    text = extract_text_from_pdf(base / "2018-10-exam-fm-sample-questions.pdf")
    questions = split_questions(text)

    print(f"📘 추출된 문제 수: {len(questions)}개")
    with open(base / "questions_only.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)