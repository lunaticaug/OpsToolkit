# docx_encoding_fixer.py
# 인코딩이 망가진 DOCX 파일들을 재변환하여 수정

import pathlib
import win32com.client as win32
import time

class DocxEncodingFixer:
    def __init__(self):
        self.script_dir = pathlib.Path(__file__).resolve().parent
        self.broken_docx_dir = self.script_dir / "source" / "docx"
        self.fixed_docx_dir = self.script_dir / "fixed_docx"
        self.markdown_dir = self.script_dir / "markdown"
        
        # 출력 폴더 생성
        self.fixed_docx_dir.mkdir(exist_ok=True)
        
        print(f"📂 문제있는 DOCX: {self.broken_docx_dir}")
        print(f"📂 수정된 DOCX: {self.fixed_docx_dir}")
        print(f"📂 기존 Markdown: {self.markdown_dir}")
        
        self.word = None
    
    def start_word(self):
        """Word COM 객체 초기화"""
        self.word = win32.Dispatch("Word.Application")
        self.word.DisplayAlerts = 0
        self.word.Visible = False
        
        # 자동 복구 기능 활성화
        self.word.Options.DoNotPromptForConvert = True
        self.word.Options.ConfirmConversions = False
    
    def quit_word(self):
        """Word COM 객체 종료"""
        if self.word:
            self.word.Quit()
    
    def fix_docx_encoding(self, broken_docx_path):
        """DOCX 파일 인코딩 문제 수정"""
        try:
            print(f"   🔧 수정 중: {broken_docx_path.name}")
            
            # 강제로 열기 (인코딩 문제 무시)
            doc = self.word.Documents.Open(
                str(broken_docx_path),
                ConfirmConversions=False,  # 변환 확인 안함
                ReadOnly=False,
                AddToRecentFiles=False,
                Revert=False
            )
            
            # 잠시 대기 (문서 완전 로딩)
            time.sleep(0.5)
            
            # 새 경로에 다시 저장 (UTF-8로 강제 변환됨)
            fixed_path = self.fixed_docx_dir / broken_docx_path.name
            doc.SaveAs2(
                str(fixed_path),
                FileFormat=16,  # wdFormatXMLDocument (DOCX)
                EmbedTrueTypeFonts=False,
                SaveNativePictureFormat=False,
                SaveFormsData=True,
                CompressLevel=0
            )
            
            doc.Close(SaveChanges=False)
            
            print(f"   ✅ 수정 완료: {fixed_path.name}")
            return True
            
        except Exception as e:
            print(f"   ❌ 수정 실패: {e}")
            # 문서가 열려있을 수 있으니 강제 닫기 시도
            try:
                if hasattr(self, 'word') and self.word:
                    for doc in self.word.Documents:
                        if doc.Name == broken_docx_path.name:
                            doc.Close(SaveChanges=False)
                            break
            except:
                pass
            return False
    
    def analyze_fixed_structure(self, fixed_docx_path):
        """수정된 DOCX에서 구조물 분석"""
        try:
            doc = self.word.Documents.Open(str(fixed_docx_path))
            
            structures = {
                'tables': [],
                'images': [],
                'shapes': [],
                'charts': [],
                'total_elements': 0
            }
            
            # 표 분석
            for i, table in enumerate(doc.Tables, 1):
                try:
                    structures['tables'].append({
                        'index': i,
                        'rows': table.Rows.Count,
                        'columns': table.Columns.Count,
                        'preview': table.Range.Text[:100].replace('\r', ' ').replace('\n', ' ').strip(),
                        'marker': f"[TABLE_{i}_{table.Rows.Count}x{table.Columns.Count}]"
                    })
                except Exception as e:
                    structures['tables'].append({
                        'index': i,
                        'rows': '?',
                        'columns': '?',
                        'preview': f'표 분석 실패: {str(e)}',
                        'marker': f"[TABLE_{i}_ERROR]"
                    })
            
            # 이미지/차트 분석
            for i, shape in enumerate(doc.InlineShapes, 1):
                try:
                    if hasattr(shape, 'HasChart') and shape.HasChart:
                        structures['charts'].append({
                            'index': i,
                            'type': 'Chart',
                            'marker': f"[CHART_{i}]"
                        })
                    else:
                        structures['images'].append({
                            'index': i,
                            'type': 'Image',
                            'width': getattr(shape, 'Width', 0),
                            'height': getattr(shape, 'Height', 0),
                            'marker': f"[IMAGE_{i}]"
                        })
                except Exception as e:
                    structures['images'].append({
                        'index': i,
                        'type': 'Unknown',
                        'marker': f"[IMAGE_{i}_ERROR]"
                    })
            
            # 도형 분석
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
            return structures
            
        except Exception as e:
            print(f"   구조 분석 실패: {e}")
            return {'error': str(e)}
    
    def enhance_existing_markdown(self, markdown_path, structures):
        """기존 마크다운에 구조물 정보 추가"""
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if structures.get('total_elements', 0) == 0:
                return content, False
            
            # 구조물 마커 생성
            markers = []
            
            for table in structures.get('tables', []):
                marker = f"\n\n> **📊 표 감지됨 (위치 {table['index']})**\n"
                marker += f"> - 크기: {table['rows']}행 x {table['columns']}열\n"
                marker += f"> - 미리보기: {table['preview'][:50]}...\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                markers.append(marker)
            
            for image in structures.get('images', []):
                marker = f"\n\n> **🖼️ 이미지 감지됨 (위치 {image['index']})**\n"
                if image.get('width') and image.get('height'):
                    marker += f"> - 크기: {image['width']:.0f} x {image['height']:.0f}\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                markers.append(marker)
            
            for chart in structures.get('charts', []):
                marker = f"\n\n> **📈 차트 감지됨 (위치 {chart['index']})**\n"
                marker += f"> - 타입: {chart['type']}\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                markers.append(marker)
            
            for shape in structures.get('shapes', []):
                marker = f"\n\n> **🔷 도형/텍스트박스 감지됨 (위치 {shape['index']})**\n"
                marker += f"> - 이름: {shape['name']}\n"
                marker += f"> - 상태: ⚠️ 수동 확인 필요\n\n"
                markers.append(marker)
            
            # 마커 추가
            enhanced_content = content
            if markers:
                enhanced_content += "\n\n---\n\n## 📋 구조물 분석 결과\n\n"
                enhanced_content += "".join(markers)
                
                enhanced_content += f"\n\n### 📊 요약\n\n"
                enhanced_content += f"- 표: {len(structures.get('tables', []))}개\n"
                enhanced_content += f"- 이미지: {len(structures.get('images', []))}개\n"
                enhanced_content += f"- 차트: {len(structures.get('charts', []))}개\n"
                enhanced_content += f"- 도형: {len(structures.get('shapes', []))}개\n"
                enhanced_content += f"- **총 구조물: {structures.get('total_elements', 0)}개**\n\n"
            
            return enhanced_content, len(markers) > 0
            
        except Exception as e:
            print(f"마크다운 보강 실패: {e}")
            return None, False
    
    def process_all_files(self):
        """모든 파일 처리"""
        # DOCX 파일 찾기
        broken_docx_files = list(self.broken_docx_dir.glob("*.docx"))
        if not broken_docx_files:
            print("❌ 처리할 DOCX 파일이 없습니다.")
            return
        
        print(f"\n🔧 DOCX 인코딩 수정 시작 ({len(broken_docx_files)}개 파일)")
        print("=" * 60)
        
        self.start_word()
        
        enhanced_dir = self.script_dir / "enhanced_markdown"
        enhanced_dir.mkdir(exist_ok=True)
        
        results = []
        
        try:
            for i, broken_docx in enumerate(broken_docx_files, 1):
                print(f"\n▶ [{i}/{len(broken_docx_files)}] {broken_docx.name}")
                
                # 1. DOCX 인코딩 수정
                if self.fix_docx_encoding(broken_docx):
                    
                    # 2. 수정된 DOCX에서 구조물 분석
                    fixed_docx = self.fixed_docx_dir / broken_docx.name
                    structures = self.analyze_fixed_structure(fixed_docx)
                    
                    if 'error' not in structures:
                        element_count = structures.get('total_elements', 0)
                        print(f"   📊 구조물 발견: {element_count}개")
                        
                        # 3. 기존 마크다운에 구조물 정보 추가
                        md_path = self.markdown_dir / f"{broken_docx.stem}.md"
                        if md_path.exists():
                            enhanced_content, has_markers = self.enhance_existing_markdown(md_path, structures)
                            if enhanced_content:
                                enhanced_path = enhanced_dir / f"{broken_docx.stem}_enhanced.md"
                                with open(enhanced_path, 'w', encoding='utf-8') as f:
                                    f.write(enhanced_content)
                                print(f"   ✅ 마크다운 보강 완료: {enhanced_path.name}")
                        else:
                            print(f"   ⚠️ 마크다운 파일 없음: {md_path.name}")
                        
                        results.append({
                            'filename': broken_docx.stem,
                            'structures': structures,
                            'element_count': element_count
                        })
                    else:
                        print(f"   ❌ 구조 분석 실패: {structures['error']}")
                else:
                    print(f"   ❌ DOCX 수정 실패")
        
        finally:
            self.quit_word()
        
        # 결과 요약
        self.generate_summary(results)
    
    def generate_summary(self, results):
        """결과 요약"""
        print("\n" + "=" * 60)
        print("📋 DOCX 수정 및 분석 결과")
        print("=" * 60)
        
        files_with_structures = [r for r in results if r['element_count'] > 0]
        total_structures = sum(r['element_count'] for r in results)
        
        print(f"✅ 수정된 DOCX: {len(results)}개")
        print(f"📊 구조물 포함: {len(files_with_structures)}개")
        print(f"📈 총 구조물: {total_structures}개")
        
        if files_with_structures:
            print(f"\n🔝 구조물이 많은 문서:")
            files_with_structures.sort(key=lambda x: x['element_count'], reverse=True)
            
            for i, file_info in enumerate(files_with_structures[:10], 1):
                print(f"   {i}. {file_info['filename']} ({file_info['element_count']}개)")
        
        print(f"\n📁 결과 위치:")
        print(f"   - 수정된 DOCX: {self.fixed_docx_dir}")
        print(f"   - 보강된 마크다운: {self.script_dir / 'enhanced_markdown'}")

def main():
    """메인 실행"""
    print("🔧 DOCX 인코딩 수정 및 구조물 분석기")
    print("=" * 60)
    
    try:
        fixer = DocxEncodingFixer()
        fixer.process_all_files()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()