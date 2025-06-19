# table_extractor_corrected.py
# 현재 폴더 구조에 맞춘 표 추출기

import pathlib
import win32com.client as win32
import csv
import json

def extract_tables_from_docx(docx_path, output_dir):
    """DOCX에서 모든 표를 CSV로 추출"""
    word = win32.Dispatch("Word.Application")
    word.DisplayAlerts = 0
    word.Visible = False
    
    try:
        doc = word.Documents.Open(str(docx_path))
        
        tables_data = []
        
        for i, table in enumerate(doc.Tables, 1):
            try:
                # 표 데이터 추출
                table_data = []
                for row_idx in range(1, table.Rows.Count + 1):
                    row_data = []
                    for col_idx in range(1, table.Columns.Count + 1):
                        try:
                            cell = table.Cell(row_idx, col_idx)
                            cell_text = cell.Range.Text.strip().replace('\r\x07', '')
                            row_data.append(cell_text)
                        except:
                            row_data.append('[셀 읽기 실패]')
                    table_data.append(row_data)
                
                # CSV 파일로 저장
                csv_filename = f"{docx_path.stem}_table_{i}.csv"
                csv_path = output_dir / csv_filename
                
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(table_data)
                
                tables_data.append({
                    'table_index': i,
                    'csv_file': csv_filename,
                    'rows': len(table_data),
                    'columns': len(table_data[0]) if table_data else 0
                })
                
                print(f"   표 {i} → {csv_filename}")
                
            except Exception as e:
                print(f"   표 {i} 추출 실패: {e}")
        
        doc.Close()
        return tables_data
        
    except Exception as e:
        print(f"문서 열기 실패: {e}")
        return []
    
    finally:
        word.Quit()

def main():
    """표가 많은 문서들의 표를 일괄 추출"""
    script_dir = pathlib.Path(__file__).resolve().parent
    
    # 현재 폴더 구조에 맞춘 경로
    docx_dir = script_dir / "source" / "docx"
    enhanced_dir = script_dir / "enhanced_markdown"
    tables_dir = script_dir / "extracted_tables"
    
    # 경로 확인
    print(f"📂 DOCX 폴더: {docx_dir}")
    print(f"📂 분석 결과: {enhanced_dir}")
    print(f"📂 표 출력: {tables_dir}")
    
    # 분석 결과 읽기
    report_path = enhanced_dir / "structure_analysis_report.json"
    if not report_path.exists():
        print("❌ 먼저 document_structure_analyzer_corrected.py를 실행하세요.")
        return
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # 표가 있는 문서들 필터링
    files_with_tables = [
        f for f in report['files'] 
        if len(f['structures'].get('tables', [])) > 0
    ]
    
    if not files_with_tables:
        print("✅ 표가 있는 문서가 없습니다.")
        return
    
    # 출력 폴더 생성
    tables_dir.mkdir(exist_ok=True)
    
    print(f"\n📊 표 추출 시작 ({len(files_with_tables)}개 문서)")
    print("=" * 50)
    
    for file_info in files_with_tables:
        filename = file_info['filename']
        table_count = len(file_info['structures'].get('tables', []))
        
        print(f"\n▶ {filename} ({table_count}개 표)")
        
        docx_path = docx_dir / f"{filename}.docx"
        if not docx_path.exists():
            print(f"   ⚠️ DOCX 파일 없음: {docx_path}")
            continue
        
        # 표 추출
        tables_data = extract_tables_from_docx(docx_path, tables_dir)
        
        if tables_data:
            print(f"   ✔ {len(tables_data)}개 표 추출 완료")
        else:
            print(f"   ✖ 표 추출 실패")
    
    print(f"\n🎉 모든 표가 추출되었습니다!")
    print(f"📁 위치: {tables_dir}")

if __name__ == "__main__":
    main()