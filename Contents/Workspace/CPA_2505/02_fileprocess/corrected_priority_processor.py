# priority_processor_corrected.py
# 현재 폴더 구조에 맞춘 우선순위별 문서 처리기

import pathlib
import json
import shutil
import datetime

def create_priority_folders():
    """우선순위별 폴더 생성 및 파일 분류"""
    script_dir = pathlib.Path(__file__).resolve().parent
    
    # 현재 폴더 구조에 맞춘 경로
    enhanced_dir = script_dir / "enhanced_markdown"
    report_path = enhanced_dir / "structure_analysis_report.json"
    
    print(f"📂 분석 결과 위치: {enhanced_dir}")
    print(f"📂 리포트 파일: {report_path}")
    
    if not report_path.exists():
        print("❌ 먼저 document_structure_analyzer_corrected.py를 실행하세요.")
        return
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # 우선순위 폴더 생성
    priority_dir = script_dir / "priority_review"
    priority_dir.mkdir(exist_ok=True)
    
    folders = {
        'high_priority': priority_dir / "1_high_priority" / "많은_구조물(5개이상)",
        'medium_priority': priority_dir / "2_medium_priority" / "중간_구조물(2-4개)",
        'low_priority': priority_dir / "3_low_priority" / "적은_구조물(1개)",
        'text_only': priority_dir / "4_text_only" / "텍스트전용"
    }
    
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
        print(f"📁 폴더 생성: {folder}")
    
    # 파일 분류
    classified = {
        'high_priority': [],
        'medium_priority': [],
        'low_priority': [],
        'text_only': []
    }
    
    for file_info in report['files']:
        filename = file_info['filename']
        element_count = file_info.get('element_count', 0)
        
        # 우선순위 결정
        if element_count >= 5:
            category = 'high_priority'
        elif element_count >= 2:
            category = 'medium_priority'
        elif element_count >= 1:
            category = 'low_priority'
        else:
            category = 'text_only'
        
        classified[category].append(file_info)
        
        # 파일 복사
        source_path = enhanced_dir / f"{filename}_enhanced.md"
        if source_path.exists():
            dest_path = folders[category] / f"{filename}_enhanced.md"
            shutil.copy2(source_path, dest_path)
            print(f"📄 복사: {filename} → {category}")
        else:
            print(f"⚠️ 파일 없음: {source_path}")
    
    # 처리 가이드 생성
    create_processing_guide(priority_dir, classified, report)
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("📁 우선순위별 폴더 생성 완료!")
    print("=" * 60)
    print(f"🔥 고우선순위 (5개+ 구조물): {len(classified['high_priority'])}개")
    print(f"⚠️ 중우선순위 (2-4개 구조물): {len(classified['medium_priority'])}개")
    print(f"📝 저우선순위 (1개 구조물): {len(classified['low_priority'])}개")
    print(f"✅ 텍스트 전용: {len(classified['text_only'])}개")
    print(f"\n📂 폴더 위치: {priority_dir}")

def create_processing_guide(priority_dir, classified, report):
    """처리 가이드 문서 생성"""
    
    # 통계 정보
    summary = report.get('summary', {})
    total_files = summary.get('total_files_analyzed', 0)
    total_structures = summary.get('total_structures', 0)
    structure_counts = summary.get('structure_counts', {})
    
    guide_content = f"""# 📋 HWP 변환 문서 처리 가이드

## 📊 전체 통계

- **총 분석 문서**: {total_files}개
- **구조물 포함 문서**: {len(classified['high_priority']) + len(classified['medium_priority']) + len(classified['low_priority'])}개
- **총 구조물**: {total_structures}개
  - 표: {structure_counts.get('tables', 0)}개
  - 이미지: {structure_counts.get('images', 0)}개
  - 차트: {structure_counts.get('charts', 0)}개
  - 도형: {structure_counts.get('shapes', 0)}개

## 🎯 처리 우선순위

### 1️⃣ 고우선순위 (5개 이상 구조물) - {len(classified['high_priority'])}개
이 문서들은 많은 표, 이미지, 차트를 포함하고 있어 **가장 먼저 검토**해야 합니다.

**처리 방법:**
- 원본 DOCX와 변환된 마크다운을 나란히 열어두고 비교
- 각 구조물 마커(📊 📈 🖼️)를 순서대로 확인
- 표는 markdown 표 형식 또는 CSV 링크로 변환
- 이미지는 적절한 대체 텍스트와 함께 표시

### 2️⃣ 중우선순위 (2-4개 구조물) - {len(classified['medium_priority'])}개
적당한 양의 구조물이 있는 문서들입니다.

**처리 방법:**
- 시간이 허락할 때 차례대로 검토
- 중요한 표와 이미지 위주로 처리

### 3️⃣ 저우선순위 (1개 구조물) - {len(classified['low_priority'])}개
구조물이 적어 비교적 간단한 문서들입니다.

**처리 방법:**
- 마지막에 일괄 처리
- 간단한 표나 이미지만 확인

### 4️⃣ 텍스트 전용 - {len(classified['text_only'])}개
구조물이 없는 문서들은 **추가 작업 불필요**합니다.

## 🔧 구조물별 처리 팁

### 📊 표 (Table) 처리
```markdown
| 컬럼1 | 컬럼2 | 컬럼3 |
|-------|-------|-------|
| 데이터1 | 데이터2 | 데이터3 |
```

### 🖼️ 이미지 처리
```markdown
![이미지 설명](이미지_파일명.png)

> **이미지 설명**: 원본 문서의 그림/차트 내용을 텍스트로 설명
```

### 📈 차트 처리
```markdown
> **📊 차트 데이터**
> 
> - X축: 시간 (2020-2024)
> - Y축: 매출액 (억원)
> - 트렌드: 연평균 15% 증가
```

## ⚡ 효율적인 작업 순서

1. **고우선순위 폴더**의 문서부터 시작
2. 각 문서의 구조물 마커를 찾아 원본과 비교
3. `extracted_tables/` 폴더의 CSV 파일 활용 (있는 경우)
4. 완료된 문서는 별도 폴더로 이동

## 📝 작업 기록

- [ ] 고우선순위 문서 처리 ({len(classified['high_priority'])}개)
- [ ] 중우선순위 문서 처리 ({len(classified['medium_priority'])}개)
- [ ] 저우선순위 문서 처리 ({len(classified['low_priority'])}개)
- [ ] 최종 검토 완료

---
**생성일**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
**총 문서 수**: {total_files}개
**구조물 포함**: {len(classified['high_priority']) + len(classified['medium_priority']) + len(classified['low_priority'])}개
"""
    
    # 각 우선순위별 상세 리스트 추가
    for category, files in classified.items():
        if not files:
            continue
            
        category_names = {
            'high_priority': '🔥 고우선순위',
            'medium_priority': '⚠️ 중우선순위', 
            'low_priority': '📝 저우선순위',
            'text_only': '✅ 텍스트전용'
        }
        
        guide_content += f"\n\n## 📋 {category_names[category]} 문서 목록 ({len(files)}개)\n\n"
        
        for i, file_info in enumerate(files, 1):
            filename = file_info['filename']
            structures = file_info['structures']
            element_count = file_info.get('element_count', 0)
            
            guide_content += f"{i}. **{filename}** ({element_count}개 구조물)\n"
            if element_count > 0:
                guide_content += f"   - 표: {len(structures.get('tables', []))}개"
                guide_content += f", 이미지: {len(structures.get('images', []))}개"
                guide_content += f", 차트: {len(structures.get('charts', []))}개"
                guide_content += f", 도형: {len(structures.get('shapes', []))}개\n"
            guide_content += "\n"
    
    # 가이드 파일 저장
    guide_path = priority_dir / "처리_가이드.md"
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"📖 처리 가이드 생성: {guide_path}")

def main():
    print("🔧 우선순위별 문서 분류기 (현재 폴더 구조 버전)")
    print("=" * 60)
    create_priority_folders()

if __name__ == "__main__":
    main()