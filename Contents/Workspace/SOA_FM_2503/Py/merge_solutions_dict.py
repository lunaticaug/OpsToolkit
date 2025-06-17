import json
import re

def clean_text(txt: str) -> str:
    """
    본문 내에서 앞뒤 불필요한 공백만 제거합니다.
    줄바꿈은 유지하여 문단 구분이 보존되도록 합니다.
    """
    return txt.strip()

def main():
    input_file = "solutions_minimal.json"   # 기존 리스트 형식의 파일
    output_file = "solutions_dict.json"     # 결과 딕셔너리 형식 파일

    # 리스트 형태 JSON 읽기
    with open(input_file, "r", encoding="utf-8") as f:
        solutions_list = json.load(f)
    
    solutions_dict = {}
    for item in solutions_list:
        qnum = item.get("question_num")
        if not qnum:
            continue
        
        # answer는 좌우 공백만 제거
        answer = item.get("answer")
        if answer is not None:
            answer = answer.strip()
        
        # intro_text는 앞뒤 공백만 제거(중간 줄바꿈은 유지)
        intro_text = item.get("intro_text", "")
        intro_text = clean_text(intro_text)
        
        page_number = item.get("page_number")
        
        solutions_dict[qnum] = {
            "page_number": page_number,
            "answer": answer,
            "intro_text": intro_text
        }
    
    # 딕셔너리 구조의 JSON 파일로 저장
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(solutions_dict, f, ensure_ascii=False, indent=2)
    
    print(f"[완료] '{input_file}' 파일의 데이터를 딕셔너리 형태로 변환하고 정리하여 '{output_file}'에 저장했습니다.")

if __name__ == "__main__":
    main()