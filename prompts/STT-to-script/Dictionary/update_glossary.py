#!/usr/bin/env python3
import json
from pathlib import Path

# Paths to glossary and snippet files
GLOSSARY = Path(__file__).parent / "glossary.json"
SNIPPET  = Path(__file__).parent / "snippet.json"

def load_json(path: Path) -> dict:
    """Load JSON from path or return default structure."""
    if not path.exists():
        return {"terms": [], "index": {}}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: dict) -> None:
    """Save JSON data to path with indentation."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def build_index(terms: list) -> dict:
    """Rebuild the index from the list of term entries."""
    idx = {}
    for term in terms:
        term_id = f"{term['category']}/{term['correct']}"
        # map only variants (wrong spellings) to the term ID
        for variant in term.get("variants", []):
            idx[variant] = term_id
    return idx

def merge_terms(existing_terms: list, new_entry: dict) -> None:
    """
    Merge a single term entry into existing_terms.
    If an entry with same id exists, update english/variants; otherwise append.
    """
    for term in existing_terms:
        if term["id"] == new_entry["id"]:
            if "english" in new_entry and new_entry["english"] != term.get("english"):
                term["english"] = new_entry["english"]
            old_vars = set(term.get("variants", []))
            for v in new_entry.get("variants", []):
                if v not in old_vars:
                    term.setdefault("variants", []).append(v)
            return
    existing_terms.append(new_entry)

def delete_term(existing_terms: list, deleted_id: str) -> None:
    """Remove term entries matching the deleted_id (format 'category/correct')."""
    cat, corr = deleted_id.split("/", 1)
    existing_terms[:] = [
        term for term in existing_terms
        if not (term["category"] == cat and term["correct"] == corr)
    ]

def main() -> None:
    data    = load_json(GLOSSARY)
    snippet = load_json(SNIPPET)
    data.setdefault("terms", [])

    # Handle array or single-object snippet
    snips = snippet if isinstance(snippet, list) else [snippet]

    for sn in snips:
        if "terms_entry" in sn:
            merge_terms(data["terms"], sn["terms_entry"])
        elif "terms" in sn:
            for entry in sn["terms"]:
                merge_terms(data["terms"], entry)
        if "deleted_terms_id" in sn:
            delete_term(data["terms"], sn["deleted_terms_id"])

    # Sort and rebuild
    data["terms"].sort(key=lambda t: (t["category"], t["correct"]))
    data["index"] = build_index(data["terms"])
    save_json(GLOSSARY, data)
    print(f"✔ Updated glossary.json with {len(data['terms'])} terms")

if __name__ == "__main__":
    main()