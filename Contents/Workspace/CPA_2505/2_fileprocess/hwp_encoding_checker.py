#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HWP/DOCX 파일 인코딩 상태 일괄 체크 도구
- 200개 넘는 파일을 한 번에 분석
- 인코딩 손상 여부 예측
- CSV 결과 출력
"""

import os
import glob
import sys
from pathlib import Path
import re

def analyze_file_encoding(filepath):
    """파일 인코딩 상태 분석"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # 파일 정보
        file_size = len(data)
        filename = os.path.basename(filepath)
        
        # 샘플링 (여러 구간에서 체크)
        samples = []
        if file_size > 2000:
            samples.append(data[500:1000])  # 시작 부분
            samples.append(data[file_size//3:file_size//3+500])  # 중간
            samples.append(data[file_size*2//3:file_size*2//3+500])  # 후반
        else:
            samples.append(data[:min(500, file_size)])
        
        # 텍스트 변환 및 분석
        total_stats = {
            'cyrillic': 0,    # 키릴 문자 (깨진 한글 신호)
            'korean': 0,      # 정상 한글
            'english': 0,     # 영어
            'question': 0,    # 물음표 (깨짐 신호)
            'numbers': 0,     # 숫자
            'special': 0      # 특수문자
        }
        
        for sample in samples:
            try:
                text = sample.decode('utf-8', errors='ignore')
                
                # 패턴 카운팅
                total_stats['cyrillic'] += len(re.findall(r'[А-я]', text))
                total_stats['korean'] += len(re.findall(r'[가-힣]', text))
                total_stats['english'] += len(re.findall(r'[A-Za-z]', text))
                total_stats['question'] += text.count('?')
                total_stats['numbers'] += len(re.findall(r'\d', text))
                total_stats['special'] += len(re.findall(r'[※◎●○■□▲△]', text))
                
            except Exception:
                continue
        
        # 예측 로직 (실제 테스트 결과 기반)
        prediction = predict_encoding_status(total_stats, filename)
        
        return {
            'filename': filename,
            'filepath': filepath,
            'size_kb': file_size // 1024,
            'prediction': prediction['status'],
            'confidence': prediction['confidence'],
            'reason': prediction['reason'],
            'stats': total_stats
        }
        
    except Exception as e:
        return {
            'filename': os.path.basename(filepath),
            'filepath': filepath,
            'size_kb': 0,
            'prediction': 'ERROR',
            'confidence': 0,
            'reason': f'파일 읽기 실패: {str(e)}',
            'stats': {}
        }

def predict_encoding_status(stats, filename):
    """인코딩 상태 예측 (실제 테스트 결과 기반)"""
    
    cyrillic = stats['cyrillic']
    korean = stats['korean'] 
    english = stats['english']
    question = stats['question']
    
    # 규칙 1: 키릴 문자 다수 = 심각한 인코딩 손상
    if cyrillic > 50:
        return {
            'status': '❌ 심각한 손상',
            'confidence': 90,
            'reason': f'키릴 문자 {cyrillic}개 발견 (HWP→DOCX 변환 실패)'
        }
    
    # 규칙 2: 정상 한글 다수 = 정상 인코딩  
    if korean > 30 and cyrillic < 10:
        return {
            'status': '✅ 정상',
            'confidence': 95,
            'reason': f'정상 한글 {korean}개 발견'
        }
    
    # 규칙 3: 영어는 많지만 한글 적음 = 부분 손상
    if english > 20 and korean < 10 and cyrillic > 0:
        return {
            'status': '⚠️ 부분 손상',
            'confidence': 80,
            'reason': f'영어 {english}개, 한글 {korean}개 - 구조만 파악 가능'
        }
    
    # 규칙 4: 물음표 다수 = 인코딩 문제
    if question > 100:
        return {
            'status': '❌ 손상 의심',
            'confidence': 70,
            'reason': f'물음표 {question}개 - 깨진 문자 다수'
        }
    
    # 규칙 5: 원본 HWP 파일
    if filename.lower().endswith('.hwp'):
        return {
            'status': '🔄 원본 HWP',
            'confidence': 100,
            'reason': 'HWP 원본 파일 - 변환 필요'
        }
    
    # 기타 경우
    if korean > 5:
        return {
            'status': '❓ 재검토 필요',
            'confidence': 60,
            'reason': f'한글 {korean}개 - 수동 확인 권장'
        }
    
    return {
        'status': '❓ 불명',
        'confidence': 30,
        'reason': '명확한 패턴 없음'
    }

def scan_directory(directory_path, extensions=['*.docx', '*.hwp', '*.doc']):
    """디렉토리에서 파일 스캔"""
    files = []
    for ext in extensions:
        pattern = os.path.join(directory_path, '**', ext)
        files.extend(glob.glob(pattern, recursive=True))
    return files

def save_results_csv(results, output_file='encoding_check_results.csv'):
    """결과를 CSV로 저장"""
    import csv
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # 헤더
        writer.writerow([
            '파일명', '경로', '크기(KB)', '예측결과', '신뢰도%', '이유', 
            '키릴문자', '한글', '영어', '물음표'
        ])
        
        # 데이터
        for result in results:
            stats = result['stats']
            writer.writerow([
                result['filename'],
                result['filepath'], 
                result['size_kb'],
                result['prediction'],
                result['confidence'],
                result['reason'],
                stats.get('cyrillic', 0),
                stats.get('korean', 0), 
                stats.get('english', 0),
                stats.get('question', 0)
            ])
    
    print(f"📊 결과가 {output_file}에 저장되었습니다.")

def main():
    """메인 실행 함수"""
    print("🔍 HWP/DOCX 파일 인코딩 상태 일괄 체크 도구")
    print("=" * 50)
    
    # 디렉토리 입력받기
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = input("📁 체크할 디렉토리 경로를 입력하세요: ").strip()
        if not directory:
            directory = "."  # 현재 디렉토리
    
    if not os.path.exists(directory):
        print(f"❌ 디렉토리를 찾을 수 없습니다: {directory}")
        return
    
    # 파일 스캔
    print(f"📂 디렉토리 스캔 중: {directory}")
    files = scan_directory(directory)
    
    if not files:
        print("❌ HWP/DOCX 파일을 찾을 수 없습니다.")
        return
    
    print(f"📄 발견된 파일: {len(files)}개")
    
    # 파일별 분석
    results = []
    good_files = []
    bad_files = []
    partial_files = []
    
    for i, filepath in enumerate(files, 1):
        print(f"🔍 분석 중... ({i}/{len(files)}) {os.path.basename(filepath)}")
        
        result = analyze_file_encoding(filepath)
        results.append(result)
        
        # 카테고리별 분류
        status = result['prediction']
        if '정상' in status:
            good_files.append(result)
        elif '심각한 손상' in status or '손상 의심' in status:
            bad_files.append(result)
        elif '부분 손상' in status:
            partial_files.append(result)
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 분석 결과 요약")
    print("=" * 50)
    print(f"✅ 정상 파일: {len(good_files)}개")
    print(f"⚠️ 부분 손상: {len(partial_files)}개") 
    print(f"❌ 심각한 손상: {len(bad_files)}개")
    print(f"📄 전체 파일: {len(files)}개")
    
    # 상세 결과 출력
    if good_files:
        print(f"\n✅ 정상 처리 가능한 파일 ({len(good_files)}개):")
        for f in good_files[:10]:  # 최대 10개만 표시
            print(f"   📄 {f['filename']}")
        if len(good_files) > 10:
            print(f"   ... 외 {len(good_files) - 10}개")
    
    if bad_files:
        print(f"\n❌ 인코딩 손상 파일 ({len(bad_files)}개):")
        for f in bad_files[:10]:
            print(f"   🚫 {f['filename']} - {f['reason']}")
        if len(bad_files) > 10:
            print(f"   ... 외 {len(bad_files) - 10}개")
    
    # CSV 저장
    save_results_csv(results)
    
    # 권장사항
    print(f"\n💡 권장사항:")
    print(f"   ✅ 정상 파일들은 Claude에 바로 업로드 가능")
    print(f"   ⚠️ 부분 손상 파일들은 구조 파악만 가능") 
    print(f"   ❌ 심각한 손상 파일들은 HWP 원본을 텍스트로 변환 필요")

if __name__ == "__main__":
    main()
