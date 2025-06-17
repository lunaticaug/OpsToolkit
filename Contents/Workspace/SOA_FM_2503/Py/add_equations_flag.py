import re
import json
from pathlib import Path

# 예시: 미리 정의한 "수학/특수 기호" 패턴들.
# 필요한 기호나 라텍 문법 등을 늘릴 수 있음.
MATH_KEYWORDS = [
    r"\^",        # x^2 등
    r"_",         # x_1 등
    r"\\sqrt",    # \sqrt{}
    r"\\int",     # \int
    r"\\frac",    # \frac
    r"\\sum",     # \sum
    r"\\sin",     # \sin
    r"\\cos",     # \cos
    r"\\log",     # \log
    r"\\ln",      # \ln
    r"∞",         # 무한대
    r"≥",         # 크거나 같다
    r"≤",         # 작거나 같다
    r"±",         # ±
    r"∆",         # 델타
    r"δ",         # δ
    r"\%",        # 백분율 기호
    # ... 필요에 따라 추가
]

# 위 키워드들을 하나의 정규표현식으로 묶어서, 한 번에 매칭 가능하도록 컴파일
# (?: ... )는 캡처 그룹이 아닌 "그룹화만" 하도록 하는 문법.
pattern_str = r"(?:{})".format("|".join(MATH_KEYWORDS))
equation_pattern = re.compile(pattern_str)

def has_equations(text: str) -> bool:
    """
    question_text 안에 사전에 정의된 수학/특수기호가 있는지 검사해 True/False 반환.
    """
    if equation_pattern.search(text):
        return True
    return False

def main():
    # 처리할 JSON 파일 (문제/페이지번호 정보가 있는 파일)을 지정
    base_dir = Path(__file__).parent
    input_file = base_dir / "Processed_Questions.json"
    output_file = base_dir / "Processed_Questions_with_eq.json"

    # JSON 로드
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # data가 다음과 같은 구조라고 가정:
    # {
    #   "1": { "question_text": "...", "page_number": "2" },
    #   "2": { "question_text": "...", "page_number": null },
    #   ...
    # }
    # 각 key(문제번호)에 대해 equations 필드를 추가.
    for key, obj in data.items():
        if not isinstance(obj, dict):
            # 혹시 모를 구조를 대비해 dict 이 아닐 경우 continue
            continue

        question_text = obj.get("question_text", "")
        # 수식 포함 여부 탐지
        eq_flag = has_equations(question_text)
        # JSON 필드 추가
        obj["equations"] = eq_flag

    # 결과 저장
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[완료] {len(data)}개 문제 노드에 equations 필드를 추가했습니다.")
    print(f"→ 결과 JSON: {output_file.name}")

if __name__ == "__main__":
    main()