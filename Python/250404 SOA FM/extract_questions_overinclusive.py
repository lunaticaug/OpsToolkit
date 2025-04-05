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

def extract_questions_new(text):
    """
    새 기준에 따라 문제 블록을 추출합니다.
    
    - 문제 블록은 한 줄의 시작에서 (선택적) 페이지번호와 1~3자리 문제번호(뒤에 점이 붙음)로 시작합니다.
    - 문제 내용은 그 후부터 종결코돈인 "(E)" 뒤에 숫자가 나오고 줄바꿈이 있는 패턴이 나타나기 전까지입니다.
    - 종결코돈은 블록의 경계를 나타내므로 문제 내용에서는 제외합니다.
    
    반환 형식 (예시):
      {
         "2": {
             "content": "Kathryn deposits 100 ... (A) 4695\n(B) 5070 ... (D) 5820",
             "page_number": null   # 또는 "3" (문제 도입부에 페이지번호가 있는 경우)
         },
         "3": {
             "content": "Eric deposits 100 ...",
             "page_number": "3"
         },
         ...
      }
    """
    # 정규표현식 설명:
    # - ^(?P<page>\d+)?\s* : 선택적으로 페이지번호(숫자)와 그 후 공백.
    # - (?P<problem>\d{1,3})\.\s+ : 1~3자리 숫자 뒤에 점과 공백(문제번호).
    # - (?P<content>.*?)(?P<term>\(E\)\s*\d+\s*(?:\n|$)) :
    #     내용은 종결코돈이 나타나기 전까지(비탐욕적으로) 캡처하며, 종결코돈은 (E) 다음에 숫자와 줄바꿈.
    pattern = r"(?ms)^(?P<page>\d+)?\s*(?P<problem>\d{1,3})\.\s+(?P<content>.*?)(?P<term>\(E\)\s*\d+\s*(?:\n|$))"
    matches = list(re.finditer(pattern, text))
    questions = {}
    for match in matches:
        prob_num = match.group("problem")
        content = match.group("content").strip()
        page_num = match.group("page")
        # 저장할 때, 문제번호는 key, 그리고 내용과 페이지번호를 별도 필드로 저장
        questions[prob_num] = {"content": content, "page_number": page_num}
    return questions

def verify_sequential_numbers(questions):
    """
    추출된 문제번호들이 순차적으로 증가하는지 검증합니다.
    """
    q_nums = sorted([int(num) for num in questions.keys()])
    if not q_nums:
        print("문제 번호를 찾을 수 없습니다.")
        return
    expected = list(range(q_nums[0], q_nums[-1] + 1))
    missing = sorted(set(expected) - set(q_nums))
    print("추출된 문제 번호:", q_nums)
    print("기대 번호 순서:", expected)
    print("누락된 번호:", missing)

def verify_sequential_page_numbers(questions):
    """
    각 문제 블록에서 추출한 페이지번호(존재하는 경우)들이 순차적으로 증가하는지 검증합니다.
    """
    page_nums = []
    for q in questions.values():
        if q["page_number"]:
            try:
                page_nums.append(int(q["page_number"]))
            except ValueError:
                continue
    if not page_nums:
        print("추출된 페이지번호가 없습니다.")
        return
    page_nums_sorted = sorted(page_nums)
    expected = list(range(page_nums_sorted[0], page_nums_sorted[-1] + 1))
    missing = sorted(set(expected) - set(page_nums_sorted))
    print("추출된 페이지번호:", page_nums_sorted)
    print("기대 페이지번호 순서:", expected)
    print("누락된 페이지번호:", missing)

if __name__ == "__main__":
    base = Path(__file__).parent
    pdf_file = base / "2018-10-exam-fm-sample-questions.pdf"
    text = extract_text_from_pdf(pdf_file)
    
    # 새 기준에 따라 문제 블록 추출
    questions = extract_questions_new(text)
    print(f"새 기준으로 추출된 문제 블록 개수: {len(questions)}개")
    
    verify_sequential_numbers(questions)
    verify_sequential_page_numbers(questions)
    
    # 결과를 JSON 파일로 저장
    output_file = base / "questions_filtered_new.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)