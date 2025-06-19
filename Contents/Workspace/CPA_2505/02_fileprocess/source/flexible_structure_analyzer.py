# flexible_document_analyzer.py
# 경로를 자동으로 찾는 문서 구조 분석기

import pathlib
import win32com.client as win32
import re
import json
from collections import defaultdict

def find_project_folders():
    """프로젝트 폴더들을 자동으로 찾기"""
    start_dir = pathlib.Path(__file__).resolve().parent
    
    # 최대 3단계 상위까지 검색
    search_dirs = [start_dir]
    current = start_dir
    for _ in range(3):
        current = current.parent
        search_dirs.append(current)
    
    found = {}
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        # 재귀적으로 하위 폴더들 검색
        for path in search_dir.rglob("*"):
            if not path.is_dir():
                continue
                
            folder_name = path.name.lower()
            
            # DOCX 폴더 찾기
            if folder_name == "docx" and "docx" not in found:
                docx_files = list(path.glob("*.docx"))
                if docx_files:
                    found["docx"] = path
                    print(f"✅ DOCX 폴더 발견: {path} ({len(docx_files)}개 파일)")
            
            # Markdown 폴더 찾기
            elif folder_name == "markdown" and "markdown" not in found:
                md_files = list(path.glob("*.md"))
                if md_files:
                    found["markdown"] = path
                    print(f"✅ Markdown 폴더 발견: {path} ({len(md_files)}개 파일)")
            
            # HWP 폴더 찾기
            elif "hwp" in folder_name and "hwp" not in found:
                hwp_files = list(path.glob("*.hwp"))
                if hwp_files:
                    found["hwp"] = path
                    print(f"✅ HWP 폴더 발견: {path} ({len(hwp_files)}개 파일)")
        
        # 필요한 폴더들을 모두 찾았으면 중단
        if "docx" in found and "markdown" in found:
            break
    
    return found

class FlexibleDocumentAnalyzer:
    def __init__(self):
        self.paths = find_project_folders()
        
        if "docx" not in self.paths:
            raise FileNotFoundError("DOCX 폴더를 찾을 수 없습니다.")
        if "markdown" not in self.paths:
            raise FileNotFoundError("Markdown 폴더를 찾을 수 없습니다.")
        
        # 출력 폴더 설정
        base_dir = self.paths["docx"].parent
        self.enhanced_dir = base_dir / "enhanced_markdown"
        self.enhanced_dir.mkdir(exist_ok=True)
        
        print(f"📂 DOCX: {self.paths['docx']}")
        print(f"📂 Markdown: {self.paths['markdown']}")
        print(f"📂 출력: {self.enhanced_dir}")
        
        self.word = None
        self.analysis_results = []
    
    def start_word(self):
        """Word COM 객체 초기화"""
        self.word = win32.Dispatch("Word.Application")
        self.word.DisplayAlerts = 0
        self.word.Visible = False
    
    def quit_word(self):
        """Word COM 객체 종료"""
        if self.word:
            self.word.Quit()
    
    def analyze_docx_structure(self, docx_path):
        """DOCX 파일의 구조 분석"""
        try:
            doc = self.word.Documents.Open(str(docx_path))
            
            structures = {
                'tables': [],
                'images': [],
                'shapes': [],
                'charts': [],
                'total_elements': 0
            }
            
            # 1. 표 분석
            for i, table in enumerate(doc.Tables, 1):
                try:
                    table_range = table.Range
                    table_start = table_range.Start
                    table_text = table_range.Text[:100].replace('\r', ' ').replace('\n', ' ')
                    
                    structures['tables'].append({
                        'index': i,
                        'rows': table.Rows.Count,
                        'columns': table.Columns.Count,
                        'position': table_start,
                        'preview': table_text.strip(),
                        'marker': f"[TABLE_{i}_{table.Rows.Count}x{table.Columns.Count}]"
                    })
                except Exception as e:
                    structures['tables'].append({
                        'index': i,
                        'rows': '?',
                        'columns': '?',
                        'position': 0,
                        'preview': f'표 분석 실패: {str(e)}',
                        'marker': f"[TABLE_{i}_ERROR]"
                    })
            
            # 2. 이미지/차트 분석
            for i, shape in enumerate(doc.InlineShapes, 1):
                try:
                    shape_range = shape.Range
                    shape_start = shape_range.Start
                    
                    if hasattr(shape, 'HasChart') and shape.HasChart:
                        structures['charts'].append({
                            'index': i,
                            'position': shape_start,
                            'type': 'Chart',
                            'marker': f"[CHART_{i}]"
                        })
                    else:
                        structures['images'].append({
                            'index': i,
                            'position': shape_start,
                            'type': 'Image',
                            'width': getattr(shape, 'Width', 0),
                            'height': getattr(shape, 'Height', 0),
                            'marker': f"[IMAGE_{i}]"
                        })
                        
                except Exception as e:
                    structures['images'].append({
                        'index': i,
                        'position': 0,
                        'type': 'Unknown',
                        'marker': f"[IMAGE_{i}_ERROR]"
                    })
            
            # 3. 도형 분석
            for i, shape in enumerate(doc.Shapes, 1):
                try:
                    structures['shapes'].append({
                        'index': i,
                        'type': shape.Type,
                        'name': getattr(shape, 'Name', 'Unknown'),
                        'marker': f"[SHAPE_{i}]"
                    })
                except Exception as e:
                    structures['shapes'].append({
                        'index': i,
                        'type': 'Unknown',
                        'name': f'분석 실패: {str(e)}',
                        'marker': f"[SHAPE_{i}_ERROR]"
                    })
            
            structures['total_elements'] = (
                len(structures['tables']) + 
                len(structures['images']) + 
                len(structures['shapes']) + 
                len(structures['charts'])
            )
            
            doc.Close()
            return structures, doc.Content.Text if 'doc' in locals() else ""
            
        except Exception as e:
            return {'error': str(e)}, ""
    
    def enhance_markdown(self, markdown_path, structures):
        """마크다운에 구조물 마커 추가"""
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if structures.get('total_elements', 0) == 0:
                return content, False
            
            enhanced_content = content
            insertion_markers = []
            
            # 구조물별 마커 생성
            for table in structures.get('tables', []):
                marker = f"\n\n> **📊 표 감지됨 (위치 {table['index']})**\n"
                marker += f"> - 크기: {table['rows']}행 x {table['columns']}열\n"
                marker += f"> - 미리보기: {table['preview'][:50]}...\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                insertion_markers.append(marker)
            
            for image in structures.get('images', []):
                marker = f"\n\n> **🖼️ 이미지 감지됨 (위치 {image['index']})**\n"
                if image.get('width') and image.get('height'):
                    marker += f"> - 크기: {image['width']:.0f} x {image['height']:.0f}\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                insertion_markers.append(marker)
            
            for chart in structures.get('charts', []):
                marker = f"\n\n> **📈 차트 감지됨 (위치 {chart['index']})**\n"
                marker += f"> - 타입: {chart['type']}\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                insertion_markers.append(marker)
            
            for shape in structures.get('shapes', []):
                marker = f"\n\n> **🔷 도형/텍스트박스 감지됨 (위치 {shape['index']})**\n"
                marker += f"> - 이름: {shape['name']}\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                insertion_markers.append(marker)
            
            if insertion_markers:
                enhanced_content += "\n\n---\n\n## 📋 구조물 분석 결과\n\n"
                enhanced_content += "".join(insertion_markers)
                
                enhanced_content += f"\n\n### 📊 요약\n\n"
                enhanced_content += f"- 표: {len(structures.get('tables', []))}개\n"
                enhanced_content += f"- 이미지: {len(structures.get('images', []))}개\n"
                enhanced_content += f"- 차트: {len(structures.get('charts', []))}개\n"
                enhanced_content += f"- 도형: {len(structures.get('shapes', []))}개\n"
                enhanced_content += f"- **총 구조물: {structures.get('total_elements', 0)}개**\n\n"
            
            return enhanced_content, len(insertion_markers) > 0
            
        except Exception as e:
            print(f"마크다운 처리 실패: {e}")
            return None, False
    
    def analyze_all_documents(self):
        """모든 문서 분석"""
        docx_files = list(self.paths["docx"].glob("*.docx"))
        if not docx_files:
            print("⚠️ 분석할 DOCX 파일이 없습니다.")
            return
        
        print(f"\n🔍 문서 구조 분석 시작 ({len(docx_files)}개 파일)")
        print("=" * 60)
        
        self.start_word()
        
        files_with_structures = []
        total_structures = 0
        
        try:
            for i, docx_path in enumerate(docx_files, 1):
                print(f"\n▶ [{i}/{len(docx_files)}] {docx_path.name}")
                
                structures, docx_text = self.analyze_docx_structure(docx_path)
                
                if 'error' in structures:
                    print(f"   ✖ 분석 실패: {structures['error']}")
                    continue
                
                # 마크다운 파일 찾기
                md_path = self.paths["markdown"] / f"{docx_path.stem}.md"
                if not md_path.exists():
                    print(f"   ⚠️ 마크다운 파일 없음: {md_path.name}")
                    continue
                
                element_count = structures.get('total_elements', 0)
                total_structures += element_count
                
                if element_count > 0:
                    files_with_structures.append({
                        'filename': docx_path.stem,
                        'structures': structures,
                        'element_count': element_count
                    })
                    
                    print(f"   📊 구조물 발견: {element_count}개")
                    
                    # 마크다운 보강
                    enhanced_content, has_markers = self.enhance_markdown(md_path, structures)
                    if enhanced_content:
                        enhanced_path = self.enhanced_dir / f"{docx_path.stem}_enhanced.md"
                        with open(enhanced_path, 'w', encoding='utf-8') as f:
                            f.write(enhanced_content)
                        print(f"   ✔ 보강 완료: {enhanced_path.name}")
                
                else:
                    print(f"   ✔ 텍스트 전용")
                
                self.analysis_results.append({
                    'filename': docx_path.stem,
                    'structures': structures,
                    'element_count': element_count
                })
        
        finally:
            self.quit_word()
        
        self.generate_summary_report(files_with_structures, total_structures)
    
    def generate_summary_report(self, files_with_structures, total_structures):
        """분석 결과 요약"""
        print("\n" + "=" * 60)
        print("📋 분석 결과 요약")
        print("=" * 60)
        
        if not files_with_structures:
            print("✅ 모든 문서가 텍스트 전용입니다.")
            return
        
        print(f"📊 구조물이 있는 문서: {len(files_with_structures)}개")
        print(f"📈 총 구조물 개수: {total_structures}개")
        
        # 결과 저장
        report_path = self.enhanced_dir / "structure_analysis_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_files_analyzed': len(self.analysis_results),
                    'files_with_structures': len(files_with_structures),
                    'total_structures': total_structures
                },
                'files': files_with_structures,
                'paths_used': {
                    'docx_dir': str(self.paths['docx']),
                    'markdown_dir': str(self.paths['markdown']),
                    'enhanced_dir': str(self.enhanced_dir)
                }
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 상세 결과: {report_path}")
        print(f"📁 보강된 마크다운: {self.enhanced_dir}")

def main():
    """메인 실행"""
    try:
        print("🔧 자동 경로 탐지 문서 구조 분석기")
        print("=" * 60)
        
        analyzer = FlexibleDocumentAnalyzer()
        analyzer.analyze_all_documents()
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\n📝 해결 방법:")
        print("1. path_checker.py를 먼저 실행해서 폴더 구조 확인")
        print("2. 또는 docx, markdown 폴더가 있는 디렉토리에서 실행")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()