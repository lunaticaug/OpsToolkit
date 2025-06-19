# document_structure_analyzer_corrected.py
# 현재 폴더 구조에 맞춘 문서 구조 분석기

import pathlib
import win32com.client as win32
import re
import json
from collections import defaultdict

class DocumentStructureAnalyzer:
    def __init__(self):
        # 현재 폴더 구조에 맞춘 경로 설정
        script_dir = pathlib.Path(__file__).resolve().parent
        
        self.docx_dir = script_dir / "source" / "docx"
        self.markdown_dir = script_dir / "markdown" 
        self.enhanced_dir = script_dir / "enhanced_markdown"
        
        # 출력 폴더 생성
        self.enhanced_dir.mkdir(exist_ok=True)
        
        # 경로 확인
        print(f"📂 DOCX 폴더: {self.docx_dir}")
        print(f"📂 Markdown 폴더: {self.markdown_dir}")
        print(f"📂 출력 폴더: {self.enhanced_dir}")
        
        # 폴더 존재 확인
        if not self.docx_dir.exists():
            raise FileNotFoundError(f"DOCX 폴더를 찾을 수 없습니다: {self.docx_dir}")
        if not self.markdown_dir.exists():
            raise FileNotFoundError(f"Markdown 폴더를 찾을 수 없습니다: {self.markdown_dir}")
        
        # 파일 개수 확인
        docx_count = len(list(self.docx_dir.glob("*.docx")))
        md_count = len(list(self.markdown_dir.glob("*.md")))
        print(f"📊 DOCX 파일: {docx_count}개")
        print(f"📊 Markdown 파일: {md_count}개")
        
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
            
            # 2. 인라인 이미지/차트 분석
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
            
            # 3. 도형/텍스트박스 분석
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
            
            # 총 구조물 개수
            structures['total_elements'] = (
                len(structures['tables']) + 
                len(structures['images']) + 
                len(structures['shapes']) + 
                len(structures['charts'])
            )
            
            doc.Close()
            return structures, ""
            
        except Exception as e:
            return {'error': str(e)}, ""
    
    def enhance_markdown(self, markdown_path, structures):
        """마크다운에 구조물 마커 추가"""
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 구조물이 없으면 원본 반환
            if structures.get('total_elements', 0) == 0:
                return content, False
            
            enhanced_content = content
            insertion_markers = []
            
            # 표 마커 추가
            for table in structures.get('tables', []):
                marker = f"\n\n> **📊 표 감지됨 (위치 {table['index']})**\n"
                marker += f"> - 크기: {table['rows']}행 x {table['columns']}열\n"
                marker += f"> - 미리보기: {table['preview'][:50]}...\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                marker += f"<!-- {table['marker']} -->\n\n"
                insertion_markers.append(marker)
            
            # 이미지 마커 추가
            for image in structures.get('images', []):
                marker = f"\n\n> **🖼️ 이미지 감지됨 (위치 {image['index']})**\n"
                if image.get('width') and image.get('height'):
                    marker += f"> - 크기: {image['width']:.0f} x {image['height']:.0f}\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                marker += f"<!-- {image['marker']} -->\n\n"
                insertion_markers.append(marker)
            
            # 차트 마커 추가
            for chart in structures.get('charts', []):
                marker = f"\n\n> **📈 차트 감지됨 (위치 {chart['index']})**\n"
                marker += f"> - 타입: {chart['type']}\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                marker += f"<!-- {chart['marker']} -->\n\n"
                insertion_markers.append(marker)
            
            # 도형 마커 추가
            for shape in structures.get('shapes', []):
                marker = f"\n\n> **🔷 도형/텍스트박스 감지됨 (위치 {shape['index']})**\n"
                marker += f"> - 이름: {shape['name']}\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                marker += f"<!-- {shape['marker']} -->\n\n"
                insertion_markers.append(marker)
            
            # 마커들을 문서 끝에 추가
            if insertion_markers:
                enhanced_content += "\n\n---\n\n## 📋 구조물 분석 결과\n\n"
                enhanced_content += "".join(insertion_markers)
                
                # 요약 정보 추가
                enhanced_content += f"\n\n### 📊 요약\n\n"
                enhanced_content += f"- 표: {len(structures.get('tables', []))}개\n"
                enhanced_content += f"- 이미지: {len(structures.get('images', []))}개\n"
                enhanced_content += f"- 차트: {len(structures.get('charts', []))}개\n"
                enhanced_content += f"- 도형: {len(structures.get('shapes', []))}개\n"
                enhanced_content += f"- **총 구조물: {structures.get('total_elements', 0)}개**\n\n"
                enhanced_content += "> ⚠️ **주의**: 위 구조물들은 자동 변환되지 않았을 수 있습니다. 원본 문서와 비교하여 수동으로 확인해주세요.\n"
            
            return enhanced_content, len(insertion_markers) > 0
            
        except Exception as e:
            print(f"마크다운 보강 실패: {e}")
            return None, False
    
    def analyze_all_documents(self):
        """모든 문서 분석 및 처리"""
        docx_files = list(self.docx_dir.glob("*.docx"))
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
                
                # DOCX 구조 분석
                structures, docx_text = self.analyze_docx_structure(docx_path)
                
                if 'error' in structures:
                    print(f"   ✖ 분석 실패: {structures['error']}")
                    continue
                
                # 대응하는 마크다운 파일 찾기
                md_path = self.markdown_dir / f"{docx_path.stem}.md"
                if not md_path.exists():
                    print(f"   ⚠️ 마크다운 파일 없음: {md_path.name}")
                    continue
                
                # 구조물 개수 확인
                element_count = structures.get('total_elements', 0)
                total_structures += element_count
                
                if element_count > 0:
                    files_with_structures.append({
                        'filename': docx_path.stem,
                        'structures': structures,
                        'element_count': element_count
                    })
                    
                    print(f"   📊 구조물 발견: {element_count}개")
                    print(f"      - 표: {len(structures.get('tables', []))}개")
                    print(f"      - 이미지: {len(structures.get('images', []))}개")
                    print(f"      - 차트: {len(structures.get('charts', []))}개")
                    print(f"      - 도형: {len(structures.get('shapes', []))}개")
                    
                    # 마크다운 보강
                    enhanced_content, has_markers = self.enhance_markdown(md_path, structures)
                    if enhanced_content:
                        enhanced_path = self.enhanced_dir / f"{docx_path.stem}_enhanced.md"
                        with open(enhanced_path, 'w', encoding='utf-8') as f:
                            f.write(enhanced_content)
                        print(f"   ✔ 보강된 마크다운 생성: {enhanced_path.name}")
                    
                else:
                    print(f"   ✔ 구조물 없음 (텍스트만)")
                
                # 분석 결과 저장
                self.analysis_results.append({
                    'filename': docx_path.stem,
                    'structures': structures,
                    'element_count': element_count
                })
        
        finally:
            self.quit_word()
        
        # 결과 요약
        self.generate_summary_report(files_with_structures, total_structures)
    
    def generate_summary_report(self, files_with_structures, total_structures):
        """분석 결과 요약 리포트 생성"""
        print("\n" + "=" * 60)
        print("📋 분석 결과 요약")
        print("=" * 60)
        
        if not files_with_structures:
            print("✅ 모든 문서가 텍스트 전용입니다. 추가 보완이 필요하지 않습니다.")
            return
        
        print(f"📊 구조물이 있는 문서: {len(files_with_structures)}개")
        print(f"📈 총 구조물 개수: {total_structures}개")
        
        # 구조물별 통계
        table_count = sum(len(f['structures'].get('tables', [])) for f in files_with_structures)
        image_count = sum(len(f['structures'].get('images', [])) for f in files_with_structures)
        chart_count = sum(len(f['structures'].get('charts', [])) for f in files_with_structures)
        shape_count = sum(len(f['structures'].get('shapes', [])) for f in files_with_structures)
        
        print(f"\n📊 구조물 유형별 통계:")
        print(f"   - 표: {table_count}개")
        print(f"   - 이미지: {image_count}개")
        print(f"   - 차트: {chart_count}개")
        print(f"   - 도형: {shape_count}개")
        
        # 상위 10개 문서 (구조물 많은 순)
        files_with_structures.sort(key=lambda x: x['element_count'], reverse=True)
        
        print(f"\n🔝 구조물이 많은 문서 Top 10:")
        for i, file_info in enumerate(files_with_structures[:10], 1):
            filename = file_info['filename']
            count = file_info['element_count']
            structures = file_info['structures']
            
            print(f"   {i:2d}. {filename} ({count}개)")
            print(f"       표:{len(structures.get('tables', []))}, "
                  f"이미지:{len(structures.get('images', []))}, "
                  f"차트:{len(structures.get('charts', []))}, "
                  f"도형:{len(structures.get('shapes', []))}")
        
        # 결과 파일 저장
        report_path = self.enhanced_dir / "structure_analysis_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_files_analyzed': len(self.analysis_results),
                    'files_with_structures': len(files_with_structures),
                    'total_structures': total_structures,
                    'structure_counts': {
                        'tables': table_count,
                        'images': image_count,
                        'charts': chart_count,
                        'shapes': shape_count
                    }
                },
                'files': files_with_structures,
                'paths_used': {
                    'docx_dir': str(self.docx_dir),
                    'markdown_dir': str(self.markdown_dir),
                    'enhanced_dir': str(self.enhanced_dir)
                }
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 상세 분석 결과가 저장되었습니다: {report_path}")
        print(f"📁 보강된 마크다운 파일들: {self.enhanced_dir}")
        
        print(f"\n💡 다음 단계:")
        print(f"   1. enhanced_markdown 폴더의 파일들을 확인하세요")
        print(f"   2. 각 구조물 마커(📊 📈 🖼️)를 찾아 원본과 비교하세요")
        print(f"   3. 필요한 경우 수동으로 표/이미지를 마크다운으로 변환하세요")

def main():
    """메인 실행 함수"""
    try:
        print("🔧 문서 구조 분석기 (현재 폴더 구조 버전)")
        print("=" * 60)
        
        analyzer = DocumentStructureAnalyzer()
        analyzer.analyze_all_documents()
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print(f"\n📝 현재 폴더 구조를 확인하세요:")
        script_dir = pathlib.Path(__file__).resolve().parent
        print(f"   스크립트 위치: {script_dir}")
        print(f"   필요한 폴더:")
        print(f"   - {script_dir}/source/docx/")
        print(f"   - {script_dir}/markdown/")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()