"""
프로젝트 정리 스크립트
"""
import os
import shutil
from pathlib import Path

def cleanup_project():
    """불필요한 파일들 정리"""
    
    # 현재 디렉토리
    current_dir = Path(".")
    
    # 삭제할 파일/폴더 패턴들
    files_to_delete = [
        # 테스트 파일들 (일부 유용한 것만 제외)
        "test_*.py",
        "debug_*.py",
        
        # 더미 데이터 파일들
        "simple_*.py",
        "simple_*.json",
        "*_property.json",
        "*test*.json",
        
        # Vercel 프록시 관련 (실패한 시도들)
        "vercel_proxy.js",
        "vworld-proxy-setup.js",
        
        # 중복 문서들
        "RAILWAY_NETWORK_ISSUE.md",
        "V-World_API_수정사항.md", 
        "VERCEL_PROXY_SETUP.md",
        
        # Node.js 관련 (Python 프로젝트에서 불필요)
        "package-lock.json"
    ]
    
    # 삭제할 디렉토리들
    dirs_to_delete = [
        "vworld-proxy",
        "vworld-proxy-public"
    ]
    
    print("=== 프로젝트 파일 정리 시작 ===")
    
    # 파일 삭제
    deleted_files = []
    for pattern in files_to_delete:
        for file_path in current_dir.glob(pattern):
            if file_path.is_file():
                print(f"삭제: {file_path}")
                file_path.unlink()
                deleted_files.append(str(file_path))
    
    # 디렉토리 삭제
    deleted_dirs = []
    for dir_name in dirs_to_delete:
        dir_path = current_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"디렉토리 삭제: {dir_path}")
            shutil.rmtree(dir_path)
            deleted_dirs.append(str(dir_path))
    
    # 유지할 중요한 테스트 파일들은 tests/ 디렉토리로 이동
    important_tests = [
        "test_supabase_api.py",  # Supabase 연결 테스트
    ]
    
    tests_dir = current_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    
    moved_files = []
    for test_file in important_tests:
        file_path = current_dir / test_file
        if file_path.exists():
            new_path = tests_dir / test_file
            if not new_path.exists():
                shutil.move(str(file_path), str(new_path))
                moved_files.append(f"{file_path} → {new_path}")
                print(f"이동: {file_path} → {new_path}")
    
    print(f"\n=== 정리 완료 ===")
    print(f"삭제된 파일: {len(deleted_files)}개")
    print(f"삭제된 디렉토리: {len(deleted_dirs)}개")
    print(f"이동된 파일: {len(moved_files)}개")
    
    # 정리 후 남은 중요 파일들 확인
    print(f"\n=== 남은 중요 파일들 ===")
    important_files = [
        "main.py",
        "requirements.txt", 
        "railway.toml",
        "supabase_schema.sql",
        "env.example"
    ]
    
    for file_name in important_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} (누락됨)")
    
    # API 디렉토리 구조 확인
    print(f"\n=== API 구조 ===")
    api_dir = current_dir / "api"
    if api_dir.exists():
        for item in api_dir.rglob("*.py"):
            print(f"  {item.relative_to(current_dir)}")
    
    # Services 디렉토리 구조 확인  
    print(f"\n=== Services 구조 ===")
    services_dir = current_dir / "services"
    if services_dir.exists():
        for item in services_dir.glob("*.py"):
            if item.name != "__init__.py":
                print(f"  {item.relative_to(current_dir)}")
    
    # Models 디렉토리 구조 확인
    print(f"\n=== Models 구조 ===")
    models_dir = current_dir / "models"
    if models_dir.exists():
        for item in models_dir.glob("*.py"):
            if item.name != "__init__.py":
                print(f"  {item.relative_to(current_dir)}")

if __name__ == "__main__":
    cleanup_project()