import json
import re

def clean_solution_text(solution_text):
    """
    솔루션 텍스트에서 불필요한 줄바꿈, 중복 공백, 이상한 기호 등을 정리합니다.
    """
    # 예시: "\\n"을 실제 줄바꿈으로 변경
    solution_text = solution_text.replace("\\n", "\n")
    # 여러 개의 공백을 하나의 공백으로 정리
    solution_text = re.sub(r'\s+', ' ', solution_text)
    return solution_text.strip()

def process_solutions(input_filename, output_filename):
    with open(input_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    processed_data = {}
    for key, value in data.items():
        # 솔루션 파일은 값이 문자열이거나 dict 형태일 수 있으므로 처리
        if isinstance(value, dict):
            text = value.get("content", "")
        else:
            text = value
        cleaned_text = clean_solution_text(text)
        processed_data[key] = cleaned_text
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    print(f"Processed solutions saved to {output_filename}")

if __name__ == '__main__':
    # 예: "SOA_FM_Solutions_250405.json" 파일을 "Processed_Solutions.json"으로 처리
    process_solutions("SOA_FM_Solutions_250405.json", "Processed_Solutions.json")