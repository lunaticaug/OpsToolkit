# path_checker.py
# 현재 폴더 구조를 확인하고 경로를 자동 감지하는 도구

import pathlib
import os

def find_target_folders(start_dir=None):
    """docx, markdown 폴더를 자동으로 찾기"""
    if start_dir is None:
        start_dir = pathlib.Path(__file__).resolve().parent
    
    print(f"🔍 폴더 구조 확인 중...")
    print(f"📂 시작 경로: {start_dir}")
    print("=" * 60)
    
    # 현재 디렉토리부터 상위 3단계까지 검색
    search_paths = [
        start_dir,                    # 현재 폴더
        start_dir.parent,             # 상위 폴더
        start_dir.parent.parent,      # 상위의 상위 폴더
    ]
    
    found_paths = {}
    
    for search_path in search_paths:
        print(f"\n📁 검색 중: {search_path}")
        
        # 하위 폴더들 확인
        if search_path.exists():
            for item in search_path.iterdir():
                if item.is_dir():
                    folder_name = item.name.lower()
                    
                    if folder_name == "docx" and "docx" not in found_paths:
                        hwp_count = len(list(item.glob("*.docx")))
                        found_paths["docx"] = {
                            "path": item,
                            "files": hwp_count
                        }
                        print(f"   ✅ DOCX 폴더 발견: {item} ({hwp_count}개 파일)")
                    
                    elif folder_name == "markdown" and "markdown" not in found_paths:
                        md_count = len(list(item.glob("*.md")))
                        found_paths["markdown"] = {
                            "path": item,
                            "files": md_count
                        }
                        print(f"   ✅ Markdown 폴더 발견: {item} ({md_count}개 파일)")
                    
                    elif "hwp" in folder_name and "hwp_source" not in found_paths:
                        hwp_count = len(list(item.glob("*.hwp")))
                        if hwp_count > 0:
                            found_paths["hwp_source"] = {
                                "path": item,
                                "files": hwp_count
                            }
                            print(f"   ✅ HWP 원본 폴더 발견: {item} ({hwp_count}개 파일)")
    
    return found_paths

def generate_dynamic_config(found_paths):
    """동적 경로 설정 파일 생성"""
    if not found_paths:
        print("❌ 필요한 폴더들을 찾을 수 없습니다.")
        return
    
    config_content = f'''# config_paths.py
# 자동 생성된 경로 설정 파일

import pathlib

# 감지된 폴더 경로들
PATHS = {{'''
    
    for folder_type, info in found_paths.items():
        config_content += f'''
    "{folder_type}": pathlib.Path(r"{info['path']}"),'''
    
    config_content += f'''
}}

# 편의 함수들
def get_docx_dir():
    return PATHS.get("docx")

def get_markdown_dir():
    return PATHS.get("markdown")

def get_hwp_source_dir():
    return PATHS.get("hwp_source")

def get_output_dir(base_name="output"):
    """출력 폴더 생성"""
    if "docx" in PATHS:
        output_dir = PATHS["docx"].parent / base_name
    elif "markdown" in PATHS:
        output_dir = PATHS["markdown"].parent / base_name
    else:
        output_dir = pathlib.Path(__file__).parent / base_name
    
    output_dir.mkdir(exist_ok=True)
    return output_dir

# 폴더 구조 확인
def print_structure():
    print("📂 현재 설정된 경로들:")
    for folder_type, path in PATHS.items():
        if path.exists():
            file_count = len(list(path.glob("*.*")))
            print(f"   {folder_type}: {path} ({file_count}개 파일)")
        else:
            print(f"   {folder_type}: {path} (❌ 존재하지 않음)")

if __name__ == "__main__":
    print_structure()
'''
    
    # 설정 파일 저장
    config_path = pathlib.Path(__file__).parent / "config_paths.py"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"\n💾 경로 설정 파일 생성: {config_path}")
    return config_path

def main():
    """메인 실행"""
    print("🔧 폴더 구조 자동 감지 도구")
    print("=" * 60)
    
    # 1. 폴더들 찾기
    found_paths = find_target_folders()
    
    # 2. 결과 요약
    print(f"\n📋 발견된 폴더 요약:")
    print("=" * 60)
    
    if found_paths:
        for folder_type, info in found_paths.items():
            print(f"✅ {folder_type.upper()}: {info['path']} ({info['files']}개 파일)")
        
        # 3. 설정 파일 생성
        config_path = generate_dynamic_config(found_paths)
        
        print(f"\n💡 사용법:")
        print(f"   1. 다른 스크립트에서 'import config_paths' 사용")
        print(f"   2. config_paths.get_docx_dir() 등으로 경로 가져오기")
        print(f"   3. 또는 기존 스크립트 수정")
        
    else:
        print("❌ docx 또는 markdown 폴더를 찾을 수 없습니다.")
        print("💡 수동으로 폴더 경로를 확인해주세요:")
        
        current_dir = pathlib.Path(__file__).parent
        print(f"\n📂 현재 디렉토리: {current_dir}")
        print(f"📁 하위 폴더들:")
        
        try:
            for item in current_dir.iterdir():
                if item.is_dir():
                    file_count = len(list(item.glob("*.*")))
                    print(f"   - {item.name}/ ({file_count}개 파일)")
        except:
            print("   (폴더 읽기 실패)")

if __name__ == "__main__":
    main()