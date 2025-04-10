import json

def main():
    # (1) 기존 해설 파일 (리스트 형태) 읽기
    input_file = "solutions_minimal.json"
    output_file = "solutions_dict.json"

    with open(input_file, "r", encoding="utf-8") as f:
        solutions_list = json.load(f)  
        # 예) [
        #   {"question_num":"1","page_number":2,"answer":"C","intro_text":"..."},
        #   {"question_num":"2","page_number":2,"answer":"E","intro_text":"..."},
        #   ...
        # ]

    # (2) 새 딕셔너리 생성
    #     key: 문제번호 (문자열)
    #     value: { "answer":..., "intro_text":..., "page_number":... }
    solutions_dict = {}

    for item in solutions_list:
        qnum = item.get("question_num")
        if qnum is None:
            # 문제번호가 없는 경우는 스킵 (또는 처리)
            continue
        
        # page_number, answer, intro_text 추출
        page_num = item.get("page_number")
        ans = item.get("answer")
        intro = item.get("intro_text")

        # 딕셔너리 구조로 저장
        solutions_dict[qnum] = {
            "answer": ans,
            "intro_text": intro,
            "page_number": page_num
        }

    # (3) JSON 파일로 저장 (딕셔너리 구조)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(solutions_dict, f, ensure_ascii=False, indent=2)

    print(f"[완료] 해설을 딕셔너리 형태로 변환하여 '{output_file}'에 저장했습니다.")

if __name__ == "__main__":
    main()