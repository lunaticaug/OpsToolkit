
"""extract_exam_pdf.py
Usage:
    python extract_exam_pdf.py input.pdf output.md

Fully automatic pipeline to convert 2‑column Korean exam PDFs
into Markdown with tables preserved.

Dependencies:
    pip install pdfplumber camelot-py[cv] PyMuPDF pytesseract pandas
    # plus system: Ghostscript (for camelot stream) & Tesseract OCR (optional)

Author: ChatGPT draft
"""

import sys, os, re, json, argparse, textwrap
import pdfplumber, camelot, fitz, pandas as pd

def detect_header_y(page, marker_text="3교시", fallback=90.0, margin=2.0):
    words = [w for w in page.extract_words() if marker_text in w["text"]]
    if words:
        return max(w["bottom"] for w in words) + margin
    return fallback

def split_columns(page, mid_ratio=0.5):
    w, h = page.width, page.height
    mid_x = w * mid_ratio
    left = page.crop((0, 0, mid_x, h), relative=True)
    right = page.crop((mid_x, 0, w, h), relative=True)
    return [left, right]

def extract_text(col_page):
    txt = col_page.extract_text(layout=True, x_tolerance=2, y_tolerance=3) or ""
    # merge hyphenated lines
    lines = [l.rstrip() for l in txt.splitlines()]
    merged = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.endswith("-") and i + 1 < len(lines):
            merged.append(ln[:-1] + lines[i+1].lstrip())
            i += 2
        else:
            merged.append(ln)
            i += 1
    return "\n".join([l.strip() for l in merged if l.strip()])

def table_to_md(df: pd.DataFrame):
    col_count = len(df.columns)
    out = []
    out.append("| " + " | ".join(df.columns) + " |")
    out.append("| " + " | ".join(["---"]*col_count) + " |")
    for _, row in df.iterrows():
        out.append("| " + " | ".join(str(c).strip() for c in row.values) + " |")
    return "\n".join(out)

def main(input_pdf, output_md):
    md_parts = []
    with pdfplumber.open(input_pdf) as pdf:
        for pnum, page in enumerate(pdf.pages, start=1):
            header_y = detect_header_y(page)
            body = page.crop((0, header_y, page.width, page.height))
            cols = split_columns(body)
            for col in cols:
                md_parts.append(extract_text(col))
            md_parts.append("\n\n")

    # tables with camelot
    tables = camelot.read_pdf(input_pdf, pages="1-2", flavor="stream", edge_tol=200, split_text=True)
    for tbl in tables:
        md_parts.append(table_to_md(tbl.df))

    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_parts))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf", help="PDF file to convert")
    parser.add_argument("output_md", help="Output Markdown file")
    args = parser.parse_args()
    main(args.input_pdf, args.output_md)
