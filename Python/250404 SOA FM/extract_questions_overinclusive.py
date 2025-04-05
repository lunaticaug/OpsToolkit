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
    - 문제 내용은 그 후부터 종결코돈이 나타나기 전까지입니다.
    - 종결코돈은 "(E)"로 시작하여, 그 뒤에 어떤 문자가 있더라도 (비탐욕적으로) 줄바꿈 전까지의 부분을 포함합니다.
    
    각 문제 블록은 딕셔너리의 key(문제번호)와
    {"content": 문제내용, "page_number": 페이지번호(있을 경우)} 형태로 저장됩니다.
    """
    # 종결코돈 부분: "(E)"로 시작해서 줄바꿈 또는 문자열 끝까지 캡처 (숫자뿐 아니라 LaTeX 등 다양한 형식 대응)
    pattern = r"(?ms)^(?P<page>\d+)?\s*(?P<problem>\d{1,3})\.\s+(?P<content>.*?)(?P<term>\(E\).*?(?:\n|$))"
    matches = list(re.finditer(pattern, text))
    questions = {}
    for match in matches:
        prob_num = match.group("problem")
        # 문제 내용에서는 종결코돈 부분은 제외하도록 함.
        content = match.group("content").strip()
        page_num = match.group("page")
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
    
    # 1. PDF에서 텍스트 추출
    text = extract_text_from_pdf(pdf_file)
    
    # 2. 새 기준에 따라 문제 블록 추출
    questions = extract_questions_new(text)
    print(f"새 기준으로 추출된 문제 블록 개수: {len(questions)}개")
    
    # 3. 문제번호와 페이지번호의 순차성 검증
    verify_sequential_numbers(questions)
    verify_sequential_page_numbers(questions)
    
    # 4. 결과를 JSON 파일로 저장
    output_file = base / "questions_filtered_new.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)