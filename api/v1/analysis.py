"""
매물 분석 API 라우터
공공데이터 기반 자동 분석 기능
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 절대 경로로 import 변경
from services.building_api import IntegratedPublicDataService

# 라우터 생성
router = APIRouter(tags=["analysis"])

# 서비스 인스턴스
analysis_service = IntegratedPublicDataService()


class AddressAnalysisRequest(BaseModel):
    """주소 기반 분석 요청 모델"""
    address: str = Field(...,
                         min_length=5,
                         max_length=200,
                         description="분석할 주소")
    detailed: bool = Field(default=True, description="상세 분석 여부")


class AddressAnalysisResponse(BaseModel):
    """주소 기반 분석 응답 모델"""
    success: bool
    message: str
    address: str
    address_info: Dict[str, Any] = {}
    building_info: Dict[str, Any] = {}
    errors: list = []


@router.post("/address", response_model=AddressAnalysisResponse)
async def analyze_by_address(request: AddressAnalysisRequest):
    """
    주소 기반 매물 자동 분석

    - **주소 검색**: V-World API를 통한 좌표 및 주소 정보 조회
    - **건축물대장**: 공공데이터포털 건축물대장 정보 조회
    - **토지정보**: 토지 관련 규제 및 용도 정보 조회 (향후 구현)
    - **경쟁사 분석**: 주변 매물 시세 및 경쟁사 정보 (향후 구현)
    """
    try:
        # 주소 기반 종합 분석 실행
        result = await analysis_service.analyze_property_by_address(request.address)

        if result['success']:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": result.get('message', '분석 완료'),
                    "data": result,
                    "analysis_summary": {
                        "address_found": bool(result.get('address_info')),
                        "building_info_found": bool(result.get('building_info', {}).get('success')),
                        "error_count": len(result.get('errors', [])),
                        "completeness": _calculate_completeness(result)
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_206_PARTIAL_CONTENT,
                content={
                    "success": False,
                    "message": result.get('message', '분석 실패'),
                    "data": result,
                    "errors": result.get('errors', [])
                }
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매물 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/address/{address_query}")
async def analyze_by_address_get(
    address_query: str,
    detailed: bool = Query(default=True, description="상세 분석 여부")
):
    """
    GET 방식 주소 기반 매물 분석

    - **간편 조회**: URL 파라미터로 주소 전달
    - **캐시 활용**: 동일 주소 재조회 시 성능 향상
    """
    try:
        # 주소 디코딩 처리
        import urllib.parse
        decoded_address = urllib.parse.unquote(address_query)

        # 분석 실행
        result = await analysis_service.analyze_property_by_address(decoded_address)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": result['success'],
                "message": result.get('message', '분석 완료'),
                "data": result,
                "query_info": {
                    "original_query": address_query,
                    "decoded_address": decoded_address,
                    "detailed": detailed
                }
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매물 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/building/{sigungu_code}/{bdong_code}/{bun}")
async def get_building_ledger_direct(
    sigungu_code: str,
    bdong_code: str,
    bun: str,
    ji: str = Query(default="0000", description="부번 (4자리)")
):
    """
    건축물대장 직접 조회

    - **시군구코드**: 5자리 행정구역코드
    - **법정동코드**: 5자리 법정동코드
    - **본번**: 4자리 본번
    - **부번**: 4자리 부번 (선택사항)
    """
    try:
        from services.building_api import BuildingLedgerService

        service = BuildingLedgerService()

        # 코드 정보로 직접 조회
        fake_address = f"코드조회_{sigungu_code}_{bdong_code}_{bun}_{ji}"
        result = await service.get_building_info(fake_address)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": result['success'],
                "message": "건축물대장 직접 조회",
                "data": result,
                "query_params": {
                    "sigungu_code": sigungu_code,
                    "bdong_code": bdong_code,
                    "bun": bun,
                    "ji": ji
                }
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"건축물대장 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def analysis_health_check():
    """
    분석 서비스 상태 확인

    - **API 키 확인**: 공공데이터 API 키 설정 상태
    - **서비스 상태**: 각 서비스별 연결 상태
    """
    try:
        from core.config import settings

        health_status = {
            "service": "analysis",
            "status": "healthy",
            "api_keys": {
                "vworld": bool(settings.VWORLD_API_KEY),
                "building": bool(settings.BUILDING_API_KEY),
                "land_regulation": bool(settings.LAND_REGULATION_API_KEY),
                "land": bool(settings.LAND_API_KEY)
            },
            "features": {
                "address_search": bool(settings.VWORLD_API_KEY),
                "building_ledger": bool(settings.BUILDING_API_KEY),
                "enhanced_address_search": bool(settings.VWORLD_API_KEY and settings.LAND_API_KEY),
                "land_regulation": bool(settings.LAND_REGULATION_API_KEY),
                "land_forest_search": bool(settings.LAND_API_KEY),
                "competitor_analysis": False  # 향후 구현
            },
            "dependencies": {
                "PublicDataReader": True,
                "httpx": True,
                "asyncio": True
            }
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=health_status
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "service": "analysis",
                "status": "unhealthy",
                "error": str(e)
            }
        )


def _calculate_completeness(result: Dict[str, Any]) -> float:
    """
    분석 완성도 계산

    Args:
        result: 분석 결과

    Returns:
        완성도 백분율 (0.0 ~ 100.0)
    """
    total_score = 0
    max_score = 0

    # 주소 정보 점수
    max_score += 30
    if result.get('address_info', {}).get('success'):
        total_score += 30

    # 건축물대장 정보 점수
    max_score += 40
    if result.get('building_info', {}).get('success'):
        building_data = result['building_info'].get('data', {})
        if building_data.get('building_info'):
            total_score += 15
        if building_data.get('area_info'):
            total_score += 15
        if building_data.get('structure_info'):
            total_score += 10

    # 토지 정보 점수
    max_score += 30
    if result.get('land_info', {}).get('success'):
        land_data = result['land_info']
        if land_data.get('address_search', {}).get('success'):
            total_score += 10
        if land_data.get('land_regulation', {}).get('success'):
            total_score += 10
        if land_data.get('land_characteristics'):
            total_score += 10

    # 오류 감점
    max_score += 20
    error_count = len(result.get('errors', []))
    if error_count == 0:
        total_score += 20
    elif error_count == 1:
        total_score += 10
    # 2개 이상 오류시 0점

    return (total_score / max_score * 100) if max_score > 0 else 0.0
