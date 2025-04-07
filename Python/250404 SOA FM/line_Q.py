import json
import re

def parse_question(content):
    """
    문제 텍스트에서 문제 본문과 옵션(A~E)을 분리합니다.
    """
    # 불필요한 줄바꿈 및 공백 정리
    content = re.sub(r'\s+', ' ', content).strip()
    
    # (A) 옵션이 시작되는 부분을 찾습니다.
    match = re.search(r'\(A\)', content)
    if not match:
        return content, {}
    
    # 문제 본문: (A)가 나오기 전까지의 텍스트
    question_text = content[:match.start()].strip()
    
    # 옵션 부분: (A)부터 시작하는 텍스트
    options_str = content[match.start():].strip()
    
    # 정규표현식을 사용해 옵션을 추출 (예: (A) ~ (B) ~ ...)
    parts = re.split(r'\(([A-E])\)\s*', options_str)
    if parts[0] == '':
        parts = parts[1:]
    
    options = {}
    for i in range(0, len(parts) - 1, 2):
        label = parts[i].strip()
        text = parts[i+1].strip()
        options[label] = text
    
    return question_text, options

def process_questions(input_filename, output_filename):
    with open(input_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    processed_data = {}
    for key, value in data.items():
        content = value.get("content", "")
        question_text, options = parse_question(content)
        processed_data[key] = {
            "question_text": question_text,
            "options": options,
            "page_number": value.get("page_number")
        }
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    print(f"Processed questions saved to {output_filename}")

if __name__ == '__main__':
    # 예: "SOA_FM_Questions_250405.json" 파일을 "Processed_Questions.json"으로 처리
    process_questions("SOA_FM_Questions_250405.json", "Processed_Questions.json")