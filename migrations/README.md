# 네이버 부동산 호환성 데이터베이스 마이그레이션

## 📋 개요

이 마이그레이션은 기존 `properties` 테이블에 네이버 부동산 표준 정보를 저장할 수 있는 `naver_info` JSONB 컬럼을 추가합니다.

## 🎯 마이그레이션 목표

- ✅ **기존 데이터 보존**: 기존 매물 데이터에 영향 없음
- ✅ **네이버 호환성 추가**: 네이버 부동산 표준 형식 지원
- ✅ **성능 최적화**: JSONB 필드에 대한 GIN 인덱스 추가
- ✅ **데이터 무결성**: 검증 함수 및 트리거 추가
- ✅ **점진적 적용**: 기존 데이터 자동 변환 함수 제공

## 📁 파일 구조

```
backend/
├── api/v1/          # API 엔드포인트들
├── core/            # 설정 및 DB
├── models/          # 데이터 모델
├── services/        # 비즈니스 로직
├── migrations/      # 마이그레이션
├── tests/           # 필수 테스트만 (naver_compatibility)
├── .dockerignore    # 배포 최적화
├── Dockerfile       # 컨테이너 설정
├── railway.toml     # Railway 배포 설정
├── main.py          # 메인 서버
└── requirements-prod.txt  # 프로덕션 의존성
```

## 🔧 마이그레이션 내용

### 1. 스키마 변경사항

```sql
-- naver_info JSONB 컬럼 추가
ALTER TABLE properties 
ADD COLUMN IF NOT EXISTS naver_info JSONB DEFAULT '{}' NOT NULL;
```

### 2. 추가된 인덱스

```sql
-- 네이버 부동산 타입 코드 인덱스
CREATE INDEX idx_properties_naver_property_type 
ON properties USING GIN ((naver_info->'propertyType'));

-- 네이버 거래 타입 코드 인덱스  
CREATE INDEX idx_properties_naver_trade_type 
ON properties USING GIN ((naver_info->'tradeType'));

-- 네이버 위치 정보 인덱스
CREATE INDEX idx_properties_naver_location 
ON properties USING GIN ((naver_info->'location'));

-- 네이버 가격 정보 인덱스
CREATE INDEX idx_properties_naver_price 
ON properties USING GIN ((naver_info->'price'));
```

### 3. 네이버 데이터 구조

```json
{
  "propertyType": "OFC",           // 네이버 부동산 타입 코드
  "tradeType": "B1",               // 네이버 거래 타입 코드
  "location": {
    "address": "강남구 테헤란로 123",
    "city": "서울특별시",
    "district": "서울특별시 강남구",
    "coordinates": {
      "lat": 37.5013,
      "lng": 127.0595
    }
  },
  "area": {
    "totalArea": 100.5,
    "exclusiveArea": 85.3,
    "landArea": 50.0
  },
  "price": {
    "salePrice": 0,
    "deposit": 5000,
    "monthlyRent": 300
  },
  "description": {
    "title": "강남 프리미엄 오피스",
    "features": "지하철 2호선 역세권, 주차 가능",
    "details": "강남 핵심 상권의 프리미엄 오피스텔입니다."
  },
  "buildingInfo": {
    "floors": 10,
    "buildYear": 0,
    "parking": false
  }
}
```

## 🔄 코드 매핑

### 부동산 타입 매핑
| 한국어 | 네이버 코드 | 설명 |
|--------|-------------|------|
| 토지 | LND | 토지 |
| 건물 | APT | 아파트/건물 |
| 사무실 | OFC | 오피스 |
| 상가 | SHP | 상가/점포 |
| 주거 | APT | 주거용 건물 |
| 기타 | ETC | 기타 |

### 거래 타입 매핑
| 한국어 | 네이버 코드 | 설명 |
|--------|-------------|------|
| 매매 | A1 | 매매 |
| 교환 | A2 | 교환 |
| 임대 | B1 | 임대 (전세/월세) |

## 🚀 마이그레이션 실행 방법

### 1. Supabase SQL Editor에서 실행

```sql
-- 1단계: 마이그레이션 스크립트 실행
-- backend/migrations/add_naver_compatibility.sql 내용을 복사하여 실행

-- 2단계: 기존 데이터 변환 (선택사항)
SELECT convert_existing_data_to_naver_format();
```

### 2. 마이그레이션 결과 확인

```sql
-- 호환성 통계 확인
SELECT * FROM naver_compatibility_stats;

-- 변환된 매물 확인
SELECT * FROM naver_compatible_properties LIMIT 5;
```

## 🔍 검증 및 테스트

### 테스트 실행
```bash
# 마이그레이션 구조 테스트
python test_db_migration.py

# 네이버 호환성 기능 테스트
python test_naver_compatibility.py
```

### 수동 검증
```sql
-- 1. naver_info 컬럼 존재 확인
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'properties' AND column_name = 'naver_info';

-- 2. 인덱스 생성 확인
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'properties' AND indexname LIKE '%naver%';

-- 3. 트리거 함수 확인
SELECT routine_name, routine_type
FROM information_schema.routines 
WHERE routine_name LIKE '%naver%';
```

## 🔒 데이터 무결성

### 자동 검증
- **네이버 코드 유효성**: 유효한 네이버 표준 코드만 허용
- **필수 필드 존재**: propertyType, tradeType 필수
- **JSON 구조 검증**: 올바른 네이버 데이터 구조 강제

### 트리거 기능
```sql
-- 잘못된 네이버 코드 입력 시 오류 발생
INSERT INTO properties (..., naver_info) 
VALUES (..., '{"propertyType": "INVALID"}');
-- 오류: 유효하지 않은 네이버 부동산 타입 코드입니다: INVALID
```

## 📊 모니터링

### 호환성 통계 모니터링
```sql
SELECT 
    total_properties,
    naver_compatible_count,
    compatibility_percentage
FROM naver_compatibility_stats;
```

### 성능 모니터링
```sql
-- 네이버 정보 검색 성능 테스트
EXPLAIN ANALYZE 
SELECT * FROM properties 
WHERE naver_info->>'propertyType' = 'OFC';
```

## 🔄 롤백 절차 (필요시)

```sql
-- 주의: 이 작업은 네이버 호환성 데이터를 모두 삭제합니다
-- 1. 트리거 제거
DROP TRIGGER IF EXISTS validate_naver_info_trigger ON properties;

-- 2. 함수 제거
DROP FUNCTION IF EXISTS validate_naver_info_structure();
DROP FUNCTION IF EXISTS convert_existing_data_to_naver_format();

-- 3. 인덱스 제거
DROP INDEX IF EXISTS idx_properties_naver_property_type;
DROP INDEX IF EXISTS idx_properties_naver_trade_type;
DROP INDEX IF EXISTS idx_properties_naver_location;
DROP INDEX IF EXISTS idx_properties_naver_price;

-- 4. 뷰 제거
DROP VIEW IF EXISTS naver_compatible_properties;
DROP VIEW IF EXISTS naver_compatibility_stats;

-- 5. 컬럼 제거 (선택사항 - 데이터 손실 주의!)
-- ALTER TABLE properties DROP COLUMN naver_info;
```

## 📝 마이그레이션 체크리스트

- [ ] 기존 데이터 백업 완료
- [ ] 마이그레이션 스크립트 검토
- [ ] 테스트 환경에서 마이그레이션 검증
- [ ] Supabase에서 마이그레이션 실행
- [ ] 인덱스 생성 확인
- [ ] 트리거 및 함수 동작 테스트
- [ ] 기존 데이터 변환 실행 (선택)
- [ ] 애플리케이션 연동 테스트
- [ ] 성능 영향 모니터링

---

**⚠️ 주의사항**
- 마이그레이션 실행 전 반드시 데이터베이스 백업 수행
- 운영 환경에서는 트래픽이 적은 시간대에 실행 권장
- 마이그레이션 후 애플리케이션 정상 동작 확인 필수
