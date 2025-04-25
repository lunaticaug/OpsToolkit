#!/usr/bin/env python3
"""새 JSON 조각(snippet.json)을 glossary.json에 병합한다."""
from __future__ import annotations
import json, sys, pathlib
from collections import defaultdict

# ---------- 설정 ----------
BASE = pathlib.Path(__file__).parent
GLOSSARY = BASE / "glossary.json"
SNIPPET  = BASE / "snippet.json"
# --------------------------

def load_json(path):            # 파일이 없으면 빈 구조 생성
    if not path.exists():
        return {"terms": [], "index": {}}
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def build_index(terms):
    idx = {}
    for t in terms:
        term_id = f"{t['category']}/{t['correct']}"
        for v in [t["correct"], *t["variants"]]:
            idx[v] = term_id
    return idx

def merge_terms(terms, new):
    key = (new["category"], new["correct"])
    for t in terms:
        if (t["category"], t["correct"]) == key:
            # 중복 variant 제거 후 병합
            t["variants"] = sorted(set(t["variants"] + new["variants"]))
            return
    terms.append(new)

def main():
    data     = load_json(GLOSSARY)
    snippet  = load_json(SNIPPET)

    if "terms_entry" in snippet:       # 추가/수정
        merge_terms(data["terms"], snippet["terms_entry"])
    if "deleted_terms_id" in snippet:  # 삭제
        cat, corr = snippet["deleted_terms_id"].split("/", 1)
        data["terms"] = [t for t in data["terms"]
                         if not (t["category"] == cat and
                                 t["correct"] == corr)]

    # 정렬
    data["terms"].sort(key=lambda x: (x["category"], x["correct"]))

    # index 재생성
    data["index"] = build_index(data["terms"])

    with GLOSSARY.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ glossary.json 갱신 완료")

if __name__ == "__main__":
    sys.exit(main())
