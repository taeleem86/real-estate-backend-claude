# 🏗️ 실거래 부동산 플랫폼 아키텍처 분석

## 📊 전체 시스템 개요

**프로젝트명**: Real Estate Platform Backend  
**배포 환경**: Railway (현재), Vercel/Render 이전 고려 중  
**데이터베이스**: Supabase PostgreSQL  
**프레임워크**: FastAPI (Python)  
**목적**: PyQt 데스크톱 앱을 위한 백엔드 API + 웹 대시보드  

## 🗂️ 정리된 프로젝트 구조

```
backend/
├── 📋 핵심 설정 파일
│   ├── main.py                 # FastAPI 메인 애플리케이션
│   ├── requirements.txt        # Python 의존성
│   ├── railway.toml           # Railway 배포 설정
│   ├── env.example           # 환경변수 템플릿
│   └── cleanup_files.py      # 프로젝트 정리 스크립트
│
├── 🏗️ 핵심 아키텍처
│   ├── core/
│   │   ├── config.py         # 환경설정 (Pydantic Settings)
│   │   └── database.py       # Supabase 연결 관리
│   │
│   ├── api/                  # API 엔드포인트
│   │   ├── v1/              # API v1
│   │   │   ├── listings.py  # 매물 CRUD (메인)
│   │   │   ├── analysis.py  # 매물 분석 API
│   │   │   └── sections.py  # 섹션 관리 API
│   │   ├── properties.py    # 매물 관리 (호환)
│   │   ├── sections.py      # 섹션 API (호환)
│   │   └── ocr.py          # OCR 매물등기부 분석
│   │
│   ├── services/            # 비즈니스 로직
│   │   ├── building_api.py  # 🔴 V-World + 건축물대장 API
│   │   ├── land_api.py      # 토지대장 API
│   │   ├── property_service.py # 매물 비즈니스 로직
│   │   ├── naver_conversion_service.py # 네이버 호환성
│   │   ├── ocr_service.py   # OCR 처리
│   │   └── supabase_client.py # Supabase 클라이언트
│   │
│   └── models/              # 데이터 모델
│       ├── property.py      # 매물 모델
│       ├── analysis.py      # 분석 결과 모델
│       ├── section.py       # 섹션 모델
│       └── naver_*.py       # 네이버 호환성 모델
│
├── 🗄️ 데이터베이스
│   ├── supabase_schema.sql  # 전체 스키마 정의
│   └── migrations/          # 마이그레이션 파일
│
├── 🧪 테스트 & 문서
│   ├── tests/               # 통합 테스트만 유지
│   └── *.md                 # 프로젝트 문서들
│
└── 🗑️ 정리 완료 (39개 파일 삭제)
    ├── test_*.py           # 중복 테스트 파일들
    ├── debug_*.py          # 디버그 스크립트들
    ├── vworld-proxy*/      # 실패한 프록시 시도들
    └── *.json              # 더미 데이터 파일들
```

## 🎯 핵심 기능 및 API 구조

### 1. **매물 관리 시스템** (`/api/v1/listings`)
```python
# 주요 엔드포인트
GET    /api/v1/listings           # 매물 목록 조회 (필터링, 페이징)
POST   /api/v1/listings           # 새 매물 등록 (주소 기반 자동 분석)
GET    /api/v1/listings/{id}      # 매물 상세 조회
PUT    /api/v1/listings/{id}      # 매물 정보 수정
DELETE /api/v1/listings/{id}      # 매물 삭제
GET    /api/v1/listings/search    # 매물 검색
GET    /api/v1/listings/stats     # 통계 조회
```

### 2. **매물 분석 시스템** (`/api/v1/analysis`)
```python
# 자동 분석 기능
POST   /api/v1/analysis/property  # 주소 기반 종합 분석
├── 🗺️ V-World 주소 검색 (좌표 변환)
├── 🏢 건축물대장 정보 조회
├── 🌿 토지대장 정보 조회  
└── 📊 분석 결과 통합
```

### 3. **섹션 관리 시스템** (`/api/v1/sections`)
```python
# 매물 분류 관리
GET    /api/v1/sections           # 섹션 목록
POST   /api/v1/sections           # 섹션 생성
PUT    /api/v1/sections/{id}      # 섹션 수정
DELETE /api/v1/sections/{id}      # 섹션 삭제
POST   /api/v1/sections/{id}/properties # 매물 일괄 추가
```

## 🗄️ Supabase 데이터베이스 스키마

### **핵심 테이블 구조**

#### 1. **listings** (메인 매물 테이블)
```sql
id UUID PRIMARY KEY                    # 매물 고유 ID
title TEXT NOT NULL                   # 매물 제목
deal_type TEXT NOT NULL               # 거래유형 (매매/전세/월세)
property_type TEXT NOT NULL           # 매물유형 (아파트/오피스텔/상가/토지)
price NUMERIC                         # 가격
display_address TEXT NOT NULL         # 표시 주소
sido TEXT NOT NULL                    # 시도
sigungu TEXT NOT NULL                 # 시군구  
eupmyeondong TEXT NOT NULL            # 읍면동
address TEXT                          # 상세 주소
land_area NUMERIC                     # 토지면적
building_area NUMERIC                 # 건물면적
lat NUMERIC, lng NUMERIC              # 🔴 좌표 (V-World API 의존)
listing_number TEXT UNIQUE            # 매물번호
status TEXT DEFAULT '거래가능'        # 매물 상태
user_id UUID                          # 사용자 ID
```

#### 2. **sections** (섹션 관리)
```sql
id UUID PRIMARY KEY                   # 섹션 ID
name VARCHAR(100) NOT NULL            # 섹션명
description VARCHAR                   # 설명
theme_tags JSONB                      # 테마 태그
is_active BOOLEAN DEFAULT true        # 활성화 여부
order INTEGER DEFAULT 0              # 정렬 순서
max_properties INTEGER               # 최대 매물 수
property_count INTEGER DEFAULT 0      # 현재 매물 수
```

#### 3. **property_sections** (다대다 관계)
```sql
id UUID PRIMARY KEY                   # 관계 ID
property_id UUID → listings(id)       # 매물 ID
section_id UUID → sections(id)        # 섹션 ID
is_featured BOOLEAN DEFAULT false     # 추천 매물 여부
display_order INTEGER DEFAULT 0      # 섹션 내 순서
priority INTEGER DEFAULT 5           # 우선순위 (1-10)
```

#### 4. **기타 테이블**
- **profiles**: 사용자 프로필
- **user_roles**: 사용자 권한 (admin/realtor/assistant)  
- **listings_sends**: 매물 발송 이력
- **properties_backup**: 매물 백업

## ⚡ 핵심 서비스 구조

### 1. **🔴 AddressSearchService** (`building_api.py`)
```python
# V-World API 연결 (현재 문제!)
class AddressSearchService:
    def __init__(self):
        self.api_key = settings.VWORLD_API_KEY
        self.use_proxy = False  # Railway에서 차단됨
        self.proxy_url = "https://vworld-proxy-*.vercel.app"
        
    async def search_address(self, query: str):
        # 1. V-World API 직접 호출 시도 → 502 오류
        # 2. 다양한 프록시 시도 → 실패  
        # 3. Nominatim API 대안 사용
        # 4. 정적 좌표 fallback
```

### 2. **IntegratedPublicDataService** (`building_api.py`)
```python
# 통합 매물 분석
async def analyze_property_by_address(self, address: str):
    # 1. 주소 검색 → V-World (문제!) 또는 fallback
    # 2. 건축물대장 조회 → PublicDataReader
    # 3. 토지정보 조회 → land_api
    # 4. 결과 통합 반환
```

### 3. **PropertyService** (`property_service.py`)
```python
# 매물 비즈니스 로직
class PropertyService:
    async def create_property(self, data):
        # 1. 주소 분석 호출
        # 2. 네이버 호환성 변환
        # 3. Supabase 저장
        # 4. 결과 반환
```

## 🔴 현재 주요 문제점

### **V-World API 연결 차단 (Railway)**
```python
# 문제 상황
Railway 환경에서 V-World API 호출 → 502 Bad Gateway
- 직접 연결: ❌ 502 오류
- Vercel 프록시: ❌ 500/401 오류  
- 공개 CORS 프록시: ❌ 403/400 오류
- 로컬 환경: ✅ 정상 작동

# 현재 대안
1. Nominatim API (OpenStreetMap)
2. 정적 좌표 fallback
3. ⚠️ 정확도 낮음 → 사용자 불만족
```

## 💡 해결 방안 우선순위

### **1. 즉시 해결 (추천) 🌟**
**Render.com으로 플랫폼 이전**
```bash
# 장점
✅ Python FastAPI 완전 지원 (코드 변경 최소)
✅ V-World API 연결 가능성 높음
✅ 무료 tier 제공
✅ Railway와 유사한 Git 배포

# 이전 절차
1. Render.com 프로젝트 생성
2. GitHub 연결
3. 환경변수 설정
4. render.yaml 추가
5. 배포 테스트
```

### **2. 중장기 해결**
**마이크로서비스 분리**
```
Frontend/PyQt ←→ Railway FastAPI (주요 로직)
                     ↓
               AWS Lambda (V-World API만)
```

### **3. 최후 수단**
**Vercel로 완전 이전 (Node.js 재작성)**

## 🎯 향후 개발 계획

### **Phase 1 (완료) ✅**
- [x] 매물 CRUD API
- [x] 섹션 관리 시스템  
- [x] 주소 기반 자동 분석
- [x] 네이버 호환성
- [x] Supabase 연동

### **Phase 2 (진행 중) 🔄**
- [ ] **V-World API 연결 문제 해결** (최우선)
- [ ] PyQt 데스크톱 앱 개발
- [ ] 경쟁사 분석 기능
- [ ] 홍보글 자동 생성
- [ ] OCR 매물등기부 분석

## 📈 시스템 성능 지표

### **현재 상태**
```
API 응답 속도: ~200-500ms (Railway)
데이터베이스: Supabase (안정적)
V-World API: ❌ 차단됨 (가장 큰 문제)
Fallback 정확도: ~60-70% (불충분)
사용자 만족도: ⚠️ 낮음 (정확한 좌표 필요)
```

### **목표 상태**
```
API 응답 속도: ~100-300ms  
V-World API: ✅ 정상 연결
좌표 정확도: >95%
사용자 만족도: ✅ 높음
```

## 🔧 권장 조치사항

1. **즉시**: Render.com 이전 테스트
2. **단기**: V-World API 연결 확인
3. **중기**: PyQt 앱 개발 시작
4. **장기**: 성능 최적화 및 기능 확장

---

> **결론**: 현재 시스템은 잘 설계되어 있으나 Railway의 V-World API 차단 문제로 인해 핵심 기능(정확한 좌표)에 제약이 있음. Render.com 이전을 통해 문제 해결 추진 필요.