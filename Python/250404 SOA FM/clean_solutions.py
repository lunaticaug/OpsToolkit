import re
import json

def clean_text(txt: str) -> str:
    # 1) 여러 줄바꿈 -> 하나로 축소
    txt = re.sub(r"\n+", "\n", txt)
    # 2) 줄바꿈 앞뒤의 불필요한 공백 제거
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    txt = re.sub(r"\n[ \t]+", "\n", txt)
    # 3) 전체 앞뒤 공백 제거
    txt = txt.strip()
    return txt

def main():
    input_json = "solutions_final.json"       # 정리 전 파일
    output_json = "solutions_final_cleaned.json"  # 정리 후 파일
    
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # data가 [ {question_num, content, ...}, {…}, … ] 형태라고 가정
    for item in data:
        if "content" in item and isinstance(item["content"], str):
            item["content"] = clean_text(item["content"])
        if "intro_text" in item and isinstance(item["intro_text"], str):
            item["intro_text"] = clean_text(item["intro_text"])
    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[완료] {len(data)}개 문제 content를 정리하여 {output_json}에 저장했습니다.")

if __name__ == "__main__":
    main()