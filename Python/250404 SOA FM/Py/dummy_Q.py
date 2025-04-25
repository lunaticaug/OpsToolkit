import json
from pathlib import Path

def insert_dummy_nodes(json_path, output_path):
    # JSON 파일 로드
    with open(json_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    # 기존 문제번호들을 정수형 리스트로 변환 후 최대 문제번호 확인
    question_numbers = [int(k) for k in questions.keys()]
    max_question = max(question_numbers)
    
    # 1부터 최대 문제번호까지 누락된 번호 찾기
    missing_numbers = sorted(set(range(1, max_question + 1)) - set(question_numbers))
    print("누락된 문제번호:", missing_numbers)
    
    # 누락된 번호에 대해 더미 노드 생성
    for num in missing_numbers:
        questions[str(num)] = {
            "content": f"Dummy question node for question number {num}.",
            "page_number": None
        }
    
    # 문제번호 순서대로 정렬 (문자열 키를 정수 기준 정렬)
    sorted_questions = {str(k): questions[str(k)] for k in sorted([int(k) for k in questions.keys()])}
    
    # 새로운 JSON 파일로 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_questions, f, indent=2, ensure_ascii=False)
    
    print(f"더미 노드가 추가되었습니다. 결과는 {output_path}에 저장되었습니다.")

if __name__ == "__main__":
    base = Path(__file__).parent
    json_file = base / "questions_filtered_new.json"
    output_file = base / "questions_filtered_new_with_dummies.json"
    insert_dummy_nodes(json_file, output_file)