# 🚀 레일웨이(Railway) 배포 가이드

## 📋 배포 준비 완료 상태

### ✅ 준비된 파일들
- **Dockerfile**: 최적화된 Python 3.11 컨테이너 이미지
- **railway.toml**: 레일웨이 배포 설정 (헬스체크 포함)
- **requirements-prod.txt**: 프로덕션 의존성 (pandas, pydantic-settings 포함)
- **.dockerignore**: 도커 빌드 최적화 (수정됨)
- **config.py**: Pydantic v1/v2 호환성 처리
- **main.py**: 강화된 헬스체크 및 보안
- **.env.production**: 프로덕션 환경변수 템플릿

## 🛠️ 레일웨이 배포 단계

### 1단계: 레일웨이 프로젝트 생성
1. [Railway](https://railway.app)에 로그인
2. "New Project" → "Deploy from GitHub repo"
3. `real-estate-platform/backend` 폴더 선택
4. 또는 GitHub 저장소 연동 후 자동 감지

### 2단계: 환경변수 설정 (중요!)
Railway 대시보드에서 다음 환경변수를 **반드시** 설정:
SECRET_KEY=your-super-secret-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
CORS_ORIGINS=https://yourdomain.com

# 선택적 API 키들
VWORLD_API_KEY=your-vworld-api-key
BUILDING_API_KEY=your-building-api-key
LAND_REGULATION_API_KEY=your-land-regulation-api-key
LAND_API_KEY=your-land-api-key
```

### 3단계: 배포 실행
1. Railway가 자동으로 Dockerfile을 감지
2. 빌드 및 배포 진행 상황 모니터링
3. 배포 완료 후 제공된 URL 확인

### 4단계: 배포 검증
```bash
# 헬스체크
curl https://your-app.railway.app/health

# API 문서 (개발 모드에서만)
https://your-app.railway.app/docs
```

## 🔧 트러블슈팅

### 빌드 실패
- requirements-prod.txt 의존성 확인
- Python 버전 호환성 확인

### 시작 실패
- 환경변수 설정 확인 (특히 SUPABASE_URL)
- 로그에서 오류 메시지 확인

### 데이터베이스 연결 실패
- Supabase 프로젝트 상태 확인
- 네트워크 연결 및 API 키 유효성 확인

## 📊 모니터링

### 헬스체크 엔드포인트
```bash
GET /health
{
  "status": "healthy",
  "timestamp": "2025-06-04T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "config": {
    "supabase_configured": true,
    "api_keys_configured": {...}
  }
}
```

### 주요 API 엔드포인트
- `/api/v1/properties` - 매물 관리
- `/api/v1/sections` - 섹션 관리  
- `/api/v1/analysis` - 분석 기능

## 🎯 배포 후 확인사항

1. **기본 기능**: `/health` 엔드포인트 응답 확인
2. **데이터베이스**: Supabase 연결 상태 확인
3. **API 기능**: 주요 엔드포인트 동작 확인
4. **보안**: CORS 설정 및 환경변수 보안 확인

## 📈 성능 최적화

### 서버 설정
- Worker 수: 2개 (기본)
- 메모리: 512MB 권장
- CPU: 0.5 vCPU 권장

### 확장성
- Railway Pro 플랜으로 업그레이드 시 자동 스케일링
- 데이터베이스 연결 풀링 활용
- 캐싱 전략 적용 가능

---
**✅ 배포 준비 완료!** 
런웨이에서 GitHub 연동하여 자동 배포를 시작하세요. 