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

def extract_possible_questions(text):
    # 문제 번호가 1~3자리 숫자 다음에 ". Solution:"이 등장하는 패턴
    pattern = r"(?m)(\d{1,3})\s*\.\s*Solution:"
    matches = list(re.finditer(pattern, text))
    items = {}
    for i, match in enumerate(matches):
        number = match.group(1)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        items[number] = text[start:end].strip()
    return items

if __name__ == "__main__":
    base = Path(__file__).parent
    text = extract_text_from_pdf(base / "2018-10-exam-fm-sample-solutions.pdf")
    solutions = extract_possible_questions(text)

    print(f"📗 추출된 해설 수: {len(solutions)}개")
    
    # 누락된 해설 번호 확인 (예: 1부터 최대 번호까지의 범위에서 누락된 번호)
    try:
        sol_numbers = sorted(int(k) for k in solutions.keys())
        if sol_numbers:
            expected = list(range(sol_numbers[0], sol_numbers[-1] + 1))
            missing = sorted(set(expected) - set(sol_numbers))
            if missing:
                print(f"❗ 누락된 해설 번호: {missing}")
            else:
                print("✅ 모든 해설 번호가 추출되었습니다.")
    except Exception as e:
        print("해설 번호를 정수로 변환하는 도중 오류 발생:", e)
    
    with open(base / "solutions_loose.json", "w", encoding="utf-8") as f:
        json.dump(solutions, f, indent=2, ensure_ascii=False)