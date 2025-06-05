# 🚀 Render.com 배포 가이드

## 📋 사전 준비사항

### 1. GitHub Repository 준비
- [x] 코드가 GitHub에 push 되어 있어야 함
- [x] render.yaml 파일 생성 완료
- [x] requirements.txt 파일 확인 완료

### 2. 환경변수 값 준비
다음 환경변수들을 준비해주세요:

```env
SUPABASE_URL=https://scgeybkrraddyawwwtyn.supabase.co
SUPABASE_ANON_KEY=[Supabase Anon Key]
VWORLD_API_KEY=B84F7999-0B97-3752-AEB1-4C546F49DE84
BUILDING_API_KEY=[건축물대장 API Key]
LAND_API_KEY=[토지 API Key]  
LAND_REGULATION_API_KEY=[토지규제정보 API Key]
```

## 🛠️ Render.com 배포 단계

### Step 1: Render.com 계정 생성
1. https://render.com 접속
2. GitHub 계정으로 로그인
3. 무료 계정 생성

### Step 2: 새 웹 서비스 생성
1. Dashboard → "New +" → "Web Service"
2. GitHub Repository 연결
3. Repository 선택: `real-estate-platform`
4. Branch: `main`

### Step 3: 서비스 설정
```yaml
Name: real-estate-backend
Region: Singapore (또는 가장 가까운 지역)
Branch: main
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Step 4: 환경변수 설정
Environment Variables 섹션에서 다음 추가:

| Key | Value |
|-----|-------|
| `SUPABASE_URL` | `https://scgeybkrraddyawwwtyn.supabase.co` |
| `SUPABASE_ANON_KEY` | `[실제 값]` |
| `VWORLD_API_KEY` | `B84F7999-0B97-3752-AEB1-4C546F49DE84` |
| `BUILDING_API_KEY` | `[실제 값]` |
| `LAND_API_KEY` | `[실제 값]` |
| `LAND_REGULATION_API_KEY` | `[실제 값]` |
| `DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |
| `CORS_ORIGINS` | `*` |

### Step 5: 배포 실행
1. "Create Web Service" 클릭
2. 빌드 로그 확인
3. 배포 완료 대기 (5-10분)

## 🧪 배포 후 테스트

### 1. 기본 연결 테스트
```bash
# 배포된 URL (예시)
curl https://real-estate-backend-xxxx.onrender.com/

# 예상 응답
{
  "message": "부동산 매물 분석 시스템 API",
  "status": "running",
  "version": "1.0.0"
}
```

### 2. Health Check
```bash
curl https://real-estate-backend-xxxx.onrender.com/health

# 예상 응답
{
  "status": "healthy",
  "supabase_configured": true,
  "api_keys_configured": {...}
}
```

### 3. V-World API 테스트
```bash
# 가장 중요한 테스트!
curl "https://real-estate-backend-xxxx.onrender.com/api/v1/analysis/property" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"address": "서울특별시 중구 세종대로 110"}'

# 성공 시 V-World API 좌표 반환
{
  "success": true,
  "address_info": {
    "x": 126.978346780,
    "y": 37.566700969,
    "method": "vworld_direct"  # 🎯 이게 나오면 성공!
  }
}
```

### 4. Sections API 테스트
```bash
curl https://real-estate-backend-xxxx.onrender.com/api/v1/sections

# 예상 응답: 섹션 목록 JSON 배열
```

## 🎯 성공 지표

### ✅ 완전 성공
- [ ] 서버 정상 시작 (200 응답)
- [ ] Supabase 연결 성공
- [ ] V-World API 직접 연결 성공 (`method: vworld_direct`)
- [ ] 모든 CRUD API 정상 작동

### ⚠️ 부분 성공  
- [ ] 서버 정상 시작
- [ ] V-World API 여전히 차단 (`method: nominatim` 또는 `method: static`)
- [ ] 다른 API는 정상 작동

### ❌ 실패
- [ ] 서버 시작 실패
- [ ] 환경변수 오류
- [ ] 의존성 설치 실패

## 🔧 문제 해결

### 빌드 실패 시
1. Render 대시보드에서 "Logs" 확인
2. requirements.txt 의존성 문제 확인
3. Python 버전 호환성 확인

### 환경변수 오류 시
1. Supabase 키 재확인
2. API 키들 유효성 확인
3. 대소문자 정확히 입력

### V-World API 여전히 실패 시
- 적어도 다른 기능들은 정상 작동할 것
- V-World만 별도 해결 방안 모색

## 📞 다음 단계

배포 완료 후:
1. URL 공유
2. 전체 기능 테스트 수행  
3. V-World API 연결 여부 확인
4. 성공 시 도메인 설정 및 최종 마이그레이션

---

**🎯 목표**: Railway의 307 리다이렉트 문제를 해결하고 V-World API 정상 연결 달성!