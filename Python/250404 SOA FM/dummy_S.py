import json
from pathlib import Path

def insert_dummy_solutions(json_path, output_path):
    # JSON 파일에서 해설 데이터 로드
    with open(json_path, 'r', encoding='utf-8') as f:
        solutions = json.load(f)
    
    # 현재 존재하는 해설 번호들을 정수 리스트로 변환
    solution_numbers = [int(k) for k in solutions.keys()]
    if not solution_numbers:
        print("해설 번호를 찾을 수 없습니다.")
        return
    
    max_solution = max(solution_numbers)
    
    # 1부터 최대 번호까지 누락된 번호 찾기
    missing_numbers = sorted(set(range(1, max_solution + 1)) - set(solution_numbers))
    print("누락된 해설 번호:", missing_numbers)
    
    # 누락된 번호에 대해 더미 노드 생성
    for num in missing_numbers:
        solutions[str(num)] = {
            "content": f"Dummy solution node for solution number {num}.",
            "page_number": None
        }
    
    # 해설 번호 순서대로 정렬하여 새 딕셔너리 생성
    sorted_solutions = {str(num): solutions[str(num)] for num in sorted([int(k) for k in solutions.keys()])}
    
    # 새 JSON 파일로 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_solutions, f, indent=2, ensure_ascii=False)
    
    print(f"더미 노드가 추가되었습니다. 결과는 {output_path}에 저장되었습니다.")

if __name__ == "__main__":
    base = Path(__file__).parent
    json_path = base / "solutions_loose.json"  # 추출된 해설 JSON 파일 경로
    output_path = base / "solutions_with_dummies.json"  # 더미 노드가 추가된 새 JSON 파일 경로
    insert_dummy_solutions(json_path, output_path)