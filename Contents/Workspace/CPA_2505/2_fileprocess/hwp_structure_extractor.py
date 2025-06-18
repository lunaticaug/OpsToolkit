# hwp_structure_extractor.py
# HWP 원본에서 직접 구조물 정보 추출

import pathlib
import win32com.client as win32
import json

class HWPStructureExtractor:
    def __init__(self):
        self.script_dir = pathlib.Path(__file__).resolve().parent
        self.hwp_dir = self.script_dir / "source" / "hwp"
        self.markdown_dir = self.script_dir / "markdown"
        self.enhanced_dir = self.script_dir / "enhanced_markdown"
        
        self.enhanced_dir.mkdir(exist_ok=True)
        
        print(f"📂 HWP 원본: {self.hwp_dir}")
        print(f"📂 기존 Markdown: {self.markdown_dir}")
        print(f"📂 보강된 Markdown: {self.enhanced_dir}")
        
        self.word = None
    
    def start_word(self):
        """Word COM 객체 초기화"""
        self.word = win32.Dispatch("Word.Application")
        self.word.DisplayAlerts = 0
        self.word.Visible = False
    
    def quit_word(self):
        """Word COM 객체 종료"""
        if self.word:
            self.word.Quit()
    
    def find_hwp_converter(self):
        """HWP 변환기 찾기"""
        for fc in self.word.FileConverters:
            fmt = getattr(fc, "FormatName", "").upper()
            ext = getattr(fc, "Extensions", "").upper()
            if "HWP" in fmt or "HWP" in ext:
                return fc
        return None
    
    def extract_structure_from_hwp(self, hwp_path):
        """HWP에서 구조물 정보만 추출 (텍스트는 추출하지 않음)"""
        try:
            print(f"   🔍 분석 중: {hwp_path.name}")
            
            # HWP 변환기 찾기
            hwp_conv = self.find_hwp_converter()
            if hwp_conv is None:
                return {'error': 'HWP 변환기 없음'}
            
            # HWP 파일 열기 (구조 분석만 목적)
            doc = self.word.Documents.Open(
                str(hwp_path),
                ConfirmConversions=False,
                ReadOnly=True,
                Format=hwp_conv.OpenFormat
            )
            
            structures = {
                'tables': [],
                'images': [],
                'shapes': [],
                'charts': [],
                'total_elements': 0
            }
            
            # 표 정보 추출
            for i, table in enumerate(doc.Tables, 1):
                try:
                    # 표 구조 정보만 추출 (내용은 나중에 마크다운과 매칭)
                    structures['tables'].append({
                        'index': i,
                        'rows': table.Rows.Count,
                        'columns': table.Columns.Count,
                        'estimated_position': i,  # 문서 내 순서
                        'marker': f"[TABLE_{i}_{table.Rows.Count}x{table.Columns.Count}]"
                    })
                except Exception as e:
                    structures['tables'].append({
                        'index': i,
                        'rows': '?',
                        'columns': '?',
                        'estimated_position': i,
                        'marker': f"[TABLE_{i}_ERROR]",
                        'error': str(e)
                    })
            
            # 이미지/차트 정보 추출
            for i, shape in enumerate(doc.InlineShapes, 1):
                try:
                    if hasattr(shape, 'HasChart') and shape.HasChart:
                        structures['charts'].append({
                            'index': i,
                            'type': 'Chart',
                            'estimated_position': i,
                            'marker': f"[CHART_{i}]"
                        })
                    else:
                        structures['images'].append({
                            'index': i,
                            'type': 'Image',
                            'estimated_position': i,
                            'marker': f"[IMAGE_{i}]"
                        })
                except Exception as e:
                    structures['images'].append({
                        'index': i,
                        'type': 'Unknown',
                        'estimated_position': i,
                        'marker': f"[IMAGE_{i}_ERROR]",
                        'error': str(e)
                    })
            
            # 도형 정보 추출
            for i, shape in enumerate(doc.Shapes, 1):
                try:
                    structures['shapes'].append({
                        'index': i,
                        'type': shape.Type,
                        'name': getattr(shape, 'Name', 'Unknown'),
                        'estimated_position': i,
                        'marker': f"[SHAPE_{i}]"
                    })
                except Exception as e:
                    structures['shapes'].append({
                        'index': i,
                        'type': 'Unknown',
                        'name': f'분석 실패: {str(e)}',
                        'estimated_position': i,
                        'marker': f"[SHAPE_{i}_ERROR]"
                    })
            
            structures['total_elements'] = (
                len(structures['tables']) + 
                len(structures['images']) + 
                len(structures['shapes']) + 
                len(structures['charts'])
            )
            
            doc.Close()
            return structures
            
        except Exception as e:
            return {'error': str(e)}
    
    def enhance_markdown_with_hwp_structure(self, markdown_path, structures):
        """HWP 구조 정보로 마크다운 보강"""
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if structures.get('total_elements', 0) == 0:
                return content, False
            
            # 마크다운을 문단별로 나누기 (구조물 삽입 위치 추정용)
            paragraphs = content.split('\n\n')
            total_paragraphs = len(paragraphs)
            
            # 구조물 마커 생성
            markers = []
            
            # 표 마커
            for table in structures.get('tables', []):
                # 문서 내 위치 추정 (표 순서 기반)
                estimated_para = min(table['estimated_position'] * 2, total_paragraphs - 1)
                
                marker = f"\n\n> **📊 표 감지됨 (HWP 위치 {table['index']})**\n"
                marker += f"> - 크기: {table['rows']}행 x {table['columns']}열\n"
                marker += f"> - 예상 위치: 문단 {estimated_para} 근처\n"
                marker += f"> - 상태: ⚠️ HWP 원본 확인 필요\n\n"
                marker += f"<!-- {table['marker']} -->\n\n"
                markers.append(('table', estimated_para, marker))
            
            # 이미지 마커
            for image in structures.get('images', []):
                estimated_para = min(image['estimated_position'] * 2, total_paragraphs - 1)
                
                marker = f"\n\n> **🖼️ 이미지 감지됨 (HWP 위치 {image['index']})**\n"
                marker += f"> - 타입: {image['type']}\n"
                marker += f"> - 예상 위치: 문단 {estimated_para} 근처\n"
                marker += f"> - 상태: ⚠️ HWP 원본 확인 필요\n\n"
                marker += f"<!-- {image['marker']} -->\n\n"
                markers.append(('image', estimated_para, marker))
            
            # 차트 마커
            for chart in structures.get('charts', []):
                estimated_para = min(chart['estimated_position'] * 2, total_paragraphs - 1)
                
                marker = f"\n\n> **📈 차트 감지됨 (HWP 위치 {chart['index']})**\n"
                marker += f"> - 타입: {chart['type']}\n"
                marker += f"> - 예상 위치: 문단 {estimated_para} 근처\n"
                marker += f"> - 상태: ⚠️ HWP 원본 확인 필요\n\n"
                marker += f"<!-- {chart['marker']} -->\n\n"
                markers.append(('chart', estimated_para, marker))
            
            # 도형 마커
            for shape in structures.get('shapes', []):
                estimated_para = min(shape['estimated_position'] * 2, total_paragraphs - 1)
                
                marker = f"\n\n> **🔷 도형/텍스트박스 감지됨 (HWP 위치 {shape['index']})**\n"
                marker += f"> - 이름: {shape['name']}\n"
                marker += f"> - 예상 위치: 문단 {estimated_para} 근처\n"
                marker += f"> - 상태: ⚠️ HWP 원본 확인 필요\n\n"
                marker += f"<!-- {shape['marker']} -->\n\n"
                markers.append(('shape', estimated_para, marker))
            
            # 구조물을 문서 끝에 추가 (위치 추정이 부정확할 수 있으므로)
            enhanced_content = content
            if markers:
                enhanced_content += "\n\n---\n\n## 📋 HWP 구조물 분석 결과\n\n"
                enhanced_content += "> ⚠️ **주의**: 아래 구조물들은 HWP 원본에서 감지된 것입니다.\n"
                enhanced_content += "> 정확한 위치와 내용은 HWP 원본을 참조하세요.\n\n"
                
                # 타입별로 정리
                for marker_type, _, marker_text in sorted(markers, key=lambda x: x[1]):
                    enhanced_content += marker_text
                
                # 요약 추가
                enhanced_content += f"\n\n### 📊 HWP 구조물 요약\n\n"
                enhanced_content += f"- 표: {len(structures.get('tables', []))}개\n"
                enhanced_content += f"- 이미지: {len(structures.get('images', []))}개\n"
                enhanced_content += f"- 차트: {len(structures.get('charts', []))}개\n"
                enhanced_content += f"- 도형: {len(structures.get('shapes', []))}개\n"
                enhanced_content += f"- **총 구조물: {structures.get('total_elements', 0)}개**\n\n"
                enhanced_content += f"💡 **작업 방법**: HWP 원본과 이 마크다운을 동시에 열어두고 구조물 위치를 확인하여 수동으로 보완하세요.\n"
            
            return enhanced_content, len(markers) > 0
            
        except Exception as e:
            print(f"마크다운 보강 실패: {e}")
            return None, False
    
    def process_all_hwp_files(self):
        """모든 HWP 파일 처리"""
        hwp_files = list(self.hwp_dir.glob("*.hwp"))
        if not hwp_files:
            print("❌ 처리할 HWP 파일이 없습니다.")
            return
        
        print(f"\n🔍 HWP 구조물 추출 시작 ({len(hwp_files)}개 파일)")
        print("=" * 60)
        
        self.start_word()
        results = []
        
        try:
            for i, hwp_path in enumerate(hwp_files, 1):
                print(f"\n▶ [{i}/{len(hwp_files)}] {hwp_path.name}")
                
                # HWP에서 구조물 추출
                structures = self.extract_structure_from_hwp(hwp_path)
                
                if 'error' in structures:
                    print(f"   ❌ 추출 실패: {structures['error']}")
                    continue
                
                element_count = structures.get('total_elements', 0)
                print(f"   📊 구조물 발견: {element_count}개")
                
                if element_count > 0:
                    # 대응하는 마크다운 파일 찾기
                    md_path = self.markdown_dir / f"{hwp_path.stem}.md"
                    if md_path.exists():
                        enhanced_content, has_markers = self.enhance_markdown_with_hwp_structure(md_path, structures)
                        if enhanced_content:
                            enhanced_path = self.enhanced_dir / f"{hwp_path.stem}_hwp_enhanced.md"
                            with open(enhanced_path, 'w', encoding='utf-8') as f:
                                f.write(enhanced_content)
                            print(f"   ✅ 보강 완료: {enhanced_path.name}")
                    else:
                        print(f"   ⚠️ 마크다운 파일 없음: {md_path.name}")
                else:
                    print(f"   ✔ 구조물 없음")
                
                results.append({
                    'filename': hwp_path.stem,
                    'structures': structures,
                    'element_count': element_count
                })
        
        finally:
            self.quit_word()
        
        # 결과 요약
        self.generate_summary(results)
    
    def generate_summary(self, results):
        """결과 요약"""
        print("\n" + "=" * 60)
        print("📋 HWP 구조물 추출 결과")
        print("=" * 60)
        
        files_with_structures = [r for r in results if r['element_count'] > 0]
        total_structures = sum(r['element_count'] for r in results)
        
        print(f"📊 분석된 HWP: {len(results)}개")
        print(f"📈 구조물 포함: {len(files_with_structures)}개")
        print(f"🔢 총 구조물: {total_structures}개")
        
        if files_with_structures:
            print(f"\n🔝 구조물이 많은 HWP:")
            files_with_structures.sort(key=lambda x: x['element_count'], reverse=True)
            
            for i, file_info in enumerate(files_with_structures[:10], 1):
                filename = file_info['filename']
                count = file_info['element_count']
                structures = file_info['structures']
                
                print(f"   {i}. {filename} ({count}개)")
                print(f"      표:{len(structures.get('tables', []))}, "
                      f"이미지:{len(structures.get('images', []))}, "
                      f"차트:{len(structures.get('charts', []))}, "
                      f"도형:{len(structures.get('shapes', []))}")
        
        print(f"\n📁 결과 위치: {self.enhanced_dir}")
        print(f"\n💡 다음 단계:")
        print(f"   1. *_hwp_enhanced.md 파일들을 확인하세요")
        print(f"   2. HWP 원본과 마크다운을 동시에 열어두고 구조물 위치 확인")
        print(f"   3. 필요한 구조물을 마크다운에 수동으로 추가")

def main():
    """메인 실행"""
    print("🔧 HWP 구조물 추출기")
    print("=" * 60)
    
    try:
        extractor = HWPStructureExtractor()
        extractor.process_all_hwp_files()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()