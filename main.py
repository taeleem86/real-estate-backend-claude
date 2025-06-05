"""
부동산 매물 분석 시스템 FastAPI 서버 (런웨이 배포 최적화)
메인 애플리케이션 진입점 - 매물 CRUD API 라우터 등록
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

# 상대 경로로 import 변경
from core.config import settings
from core.database import init_database

# 로깅 설정 (import 이전으로 이동)
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# API 라우터 임포트 (상대 경로로 변경) - 에러 처리 추가
try:
    from api.v1.listings import router as listings_router
    logger.info("✅ listings 라우터 import 성공")
except Exception as e:
    logger.error(f"❌ listings 라우터 import 실패: {e}")
    listings_router = None

try:
    from api.v1.analysis import router as analysis_router
    logger.info("✅ analysis 라우터 import 성공")
except Exception as e:
    logger.error(f"❌ analysis 라우터 import 실패: {e}")
    analysis_router = None

try:
    from api.v1.sections import router as sections_router
    logger.info("✅ sections 라우터 import 성공")
except Exception as e:
    logger.error(f"❌ sections 라우터 import 실패: {e}")
    sections_router = None

try:
    from api.properties import router as properties_router
    logger.info("✅ properties 라우터 import 성공")
except Exception as e:
    logger.error(f"❌ properties 라우터 import 실패: {e}")
    properties_router = None

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="부동산 매물 분석 시스템 API",
    description="PyQt 데스크톱 앱을 위한 부동산 매물 분석 및 관리 API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,  # 프로덕션에서는 docs 비활성화
    redoc_url="/redoc" if settings.DEBUG else None,
    redirect_slashes=False  # 307 리다이렉트 문제 해결
)

# CORS 설정 (프로덕션 보안 강화)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    logger.info("🚀 부동산 매물 분석 시스템 API 서버 시작")
    try:
        await init_database()
        logger.info("✅ 데이터베이스 연결 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        raise


@app.get("/")
async def root():
    """루트 엔드포인트 - 서버 상태 확인"""
    return {
        "message": "부동산 매물 분석 시스템 API",
        "status": "running",
        "version": "1.0.0",
        "environment": "production" if not settings.DEBUG else "development",
        "docs": "/docs" if settings.DEBUG else "disabled",
        "features": [
            "리스팅 CRUD API (✅ 완료)",
            "섹션 관리 API (✅ 완료)",
            "주소 기반 자동 분석 (✅ 완료)",
            "네이버 호환성 시스템 (✅ 완료)",
            "건축물대장/토지대장 연동 (✅ 완료)",
            "경쟁사 분석 (🔄 2단계 예정)",
            "홍보글 생성 (🔄 2단계 예정)",
            "OCR 매물등기부 분석 (🔄 2단계 예정)"
        ],
        "phase_1_status": "완료 ✅",
        "next_phase": "2단계 PyQt 데스크톱 앱 개발"
    }


@app.get("/health")
async def health_check():
    """런웨이 배포용 강화된 헬스체크 엔드포인트"""
    try:
        # 기본 서버 상태
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "environment": "production" if not settings.DEBUG else "development"}

        # 설정 검증
        config_status = {
            "supabase_configured": bool(
                settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY), "api_keys_configured": {
                "vworld": bool(
                    settings.VWORLD_API_KEY), "building": bool(
                    settings.BUILDING_API_KEY), "land_regulation": bool(
                        settings.LAND_REGULATION_API_KEY), "land": bool(
                            settings.LAND_API_KEY)}}

        # API 엔드포인트 정보
        api_info = {
            "listings": "/api/v1/listings",
            "analysis": "/api/v1/analysis",
            "sections": "/api/v1/sections"
        }

        return {
            **health_status,
            "config": config_status,
            "api_endpoints": api_info
        }

    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/debug/routes")
async def debug_routes():
    """등록된 라우트 디버그"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', 'Unknown')
            })
    return {
        "total_routes": len(routes),
        "routes": routes
    }

@app.get("/api/v1")
async def api_info():
    """API 정보 엔드포인트"""
    return {
        "api_version": "v1",
        "environment": "production" if not settings.DEBUG else "development",
        "available_endpoints": {
            "listings": {
                "base_url": "/api/v1/listings",
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "features": [
                    "리스팅 등록 (주소 기반)",
                    "리스팅 목록 조회 (필터링, 페이징)",
                    "리스팅 상세 조회",
                    "리스팅 정보 수정",
                    "리스팅 삭제",
                    "리스팅 검색",
                    "통계 조회"
                ]
            },
            "analysis": {
                "base_url": "/api/v1/analysis",
                "status": "구현완료",
                "methods": ["GET", "POST"],
                "features": [
                    "주소 기반 자동 분석",
                    "건축물대장 정보 조회",
                    "V-World 주소 검색",
                    "토지대장 분석 (향후 구현)",
                    "경쟁사 분석 (향후 구현)",
                    "홍보글 생성 (향후 구현)"
                ]
            },
            "sections": {
                "base_url": "/api/v1/sections",
                "status": "구현완료",
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "features": [
                    "섹션 CRUD (생성/조회/수정/삭제)",
                    "섹션별 매물 분류 관리",
                    "매물 일괄 추가/이동",
                    "섹션 순서 변경",
                    "섹션별 통계 조회",
                    "홈페이지 노출 관리"
                ]
            }
        },
        "documentation": "/docs" if settings.DEBUG else "disabled"
    }

# API 라우터 등록 - import에 성공한 라우터만 등록
if listings_router:
    app.include_router(
        listings_router,
        prefix="/api/v1/listings",
        tags=["listings"]
    )
    logger.info("✅ listings 라우터 등록 완료")
else:
    logger.warning("❌ listings 라우터 등록 실패 (import 실패)")

if analysis_router:
    app.include_router(
        analysis_router,
        prefix="/api/v1/analysis",
        tags=["analysis"]
    )
    logger.info("✅ analysis 라우터 등록 완료")
else:
    logger.warning("❌ analysis 라우터 등록 실패 (import 실패)")

if sections_router:
    app.include_router(
        sections_router,
        prefix="/api/v1/sections",
        tags=["sections"]
    )
    logger.info("✅ sections 라우터 등록 완료")
else:
    logger.warning("❌ sections 라우터 등록 실패 (import 실패)")

# properties 라우터는 더 구체적인 경로로 변경하여 충돌 방지
if properties_router:
    app.include_router(
        properties_router,
        prefix="/api/properties",
        tags=["properties"]
    )
    logger.info("✅ properties 라우터 등록 완료")
else:
    logger.warning("❌ properties 라우터 등록 실패 (import 실패)")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
