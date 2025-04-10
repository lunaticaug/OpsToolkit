import json
import re
from pathlib import Path

def clean_solution_text(text: str) -> str:
    """
    해설 텍스트에서 불필요한 줄바꿈, 다중 공백 등을 정리해줍니다.
    필요에 따라 정규표현식을 조정하세요.
    """
    # \n 여러 개 -> 하나로 축소
    text = re.sub(r"\n+", "\n", text)
    # 탭, 여러 공백 등을 하나의 공백으로
    text = re.sub(r"[ \t]+", " ", text)
    # 줄바꿈 앞뒤의 공백 제거
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    # 앞뒤 공백 제거
    text = text.strip()
    return text

def main():
    # JSON 파일 경로 설정
    base_path = Path(__file__).parent
    input_file = base_path / "SOA_FM_Solutions_250405.json"
    output_file = base_path / "solutions_cleaned.json"
    
    # JSON 불러오기
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    cleaned_data = {}
    
    # data가 { "1": "text...", "2": "text...", ... } 형태(혹은 dict 안에 dict 형태)라고 가정
    for key, value in data.items():
        if isinstance(value, dict):
            # 혹시 content, page_number 등이 dict 형태로 있을 수도 있으므로 처리
            if "content" in value:
                cleaned_content = clean_solution_text(value["content"])
                value["content"] = cleaned_content
            cleaned_data[key] = value
        elif isinstance(value, str):
            # 문자열인 경우 그대로 정리
            cleaned_text = clean_solution_text(value)
            cleaned_data[key] = cleaned_text
        else:
            # 그 외(숫자, list 등)라면 일단 그대로 저장
            cleaned_data[key] = value
    
    # 결과 저장
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    print(f"[완료] 정리된 해설을 {output_file.name} 파일로 저장했습니다.")

if __name__ == "__main__":
    main()