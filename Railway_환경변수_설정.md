# Railway 환경변수 설정 가이드

## 🔑 V-World API 키 설정

Railway 대시보드에서 다음 환경변수를 추가/수정하세요:

### 1. Railway 대시보드 접속
1. https://railway.app 로그인
2. 프로젝트 선택
3. "Variables" 탭 클릭

### 2. 환경변수 추가/수정

```bash
# V-World API 키 (주소검색)
VWORLD_API_KEY=B84F7999-0B97-3752-AEB1-4C546F49DE84

# 기타 필요한 환경변수들 (이미 설정되어 있을 수 있음)
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-key
SECRET_KEY=your-secret-key
```

### 3. 배포 재시작
환경변수 추가 후 자동으로 재배포됩니다.

## 🧪 테스트 예상 결과

환경변수 설정 후 다음 API 호출이 성공해야 합니다:

```bash
curl -X POST "https://backend-production-9d6f.up.railway.app/api/v1/analysis/address" \
-H "Content-Type: application/json" \
-d '{"address": "서울특별시 강남구 테헤란로 152"}'
```

**예상 응답:**
```json
{
  "success": true,
  "data": {
    "address_info": {
      "success": true,
      "x": 127.036514469,
      "y": 37.500028534,
      "address": "서울특별시 강남구 테헤란로 152"
    },
    "building_info": { ... },
    "errors": []
  }
}
```

## ✅ 성공 지표

1. **주소 검색 성공**: `"address_found": true`
2. **실제 좌표 반환**: `"fallback": false` (fallback 아님)
3. **오류 개수 감소**: 0-1개
4. **완성도 향상**: 60% 이상

## 🔄 설정 후 확인사항

1. Railway에서 환경변수 저장
2. 자동 재배포 완료 대기 (2-3분)
3. API 테스트 실행
4. 로그에서 "V-World 좌표 획득 성공" 메시지 확인