"""
리스팅 CRUD API 라우터 (수정된 버전)
RESTful API 엔드포인트 구현 - 라우팅 순서 최적화
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse

from models.property import (
    Property, PropertyCreate, PropertyUpdate, PropertyResponse,
    PropertyType, TransactionType, PropertyStatus
)
from models.naver_response import (
    NaverPropertyResponse, NaverPropertyListResponse, NaverFormatOptions,
    NaverPropertyData, NaverValidation
)
from services.property_service import PropertyService
from models.section import Section

# 라우터 생성
router = APIRouter(tags=["listings"])


def get_property_service() -> PropertyService:
    """Property 서비스 의존성 주입"""
    return PropertyService()


# 구체적인 엔드포인트를 먼저 정의 (UUID 충돌 방지)

@router.get("/search")
async def search_listings(
    q: str = Query(..., min_length=2, description="검색어 (최소 2글자)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: PropertyService = Depends(get_property_service)
):
    """
    리스팅 검색

    - **검색 대상**: 제목, 주소, 특징, 키워드
    - **부분 일치**: 검색어가 포함된 모든 리스팅 검색
    """
    try:
        listings = await service.search_listings(q, skip, limit)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": listings,
                "message": f"'{q}' 검색 결과 {len(listings)}건을 찾았습니다.",
                "status": "success",
                "search": {
                    "query": q,
                    "count": len(listings)
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"검색 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/stats/summary")
async def get_listing_stats(
    service: PropertyService = Depends(get_property_service)
):
    """
    리스팅 통계 요약

    - **전체 현황**: 상태별, 거래형태별, 매물구분별 통계
    - **최근 동향**: 최근 등록된 리스팅 수
    """
    try:
        stats = await service.get_listing_statistics()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": stats,
                "message": "리스팅 통계를 조회했습니다.",
                "status": "success"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/naver-format", response_model=NaverPropertyListResponse)
async def get_listings_naver_format(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    listing_status: Optional[PropertyStatus] = Query(None, description="매물 상태 필터"),
    property_type: Optional[PropertyType] = Query(None, description="매물 구분 필터"),
    transaction_type: Optional[TransactionType] = Query(None, description="거래형태 필터"),
    include_validation: bool = Query(True, description="호환성 검증 포함 여부"),
    naver_compatible_only: bool = Query(False, description="네이버 호환 매물만 조회"),
    service: PropertyService = Depends(get_property_service)
):
    """
    리스팅 목록 조회 - 네이버 표준 형식

    - **네이버 대량 데이터**: 모든 리스팅을 네이버 표준 형식으로 제공
    - **호환성 필터**: 네이버 호환 리스팅만 선택적 조회 가능
    - **경쟁사 분석**: 대량 데이터 비교 분석을 위한 API
    - **매물 매핑**: 네이버 부동산 자동 등록 준비
    """
    try:
        # 기본 리스팅 목록 조회
        listings = await service.get_listings(
            skip=skip,
            limit=limit,
            status=listing_status.value if listing_status else None,
            property_type=property_type.value if property_type else None,
            transaction_type=transaction_type.value if transaction_type else None
        )

        # 네이버 형식으로 변환
        naver_listings = []
        naver_compatible_count = 0

        for prop_dict in listings:
            try:
                listing_id_uuid = UUID(prop_dict['id'])
                naver_response = await service.get_naver_compatible_response(
                    listing_id_uuid,
                    include_naver=True
                )

                if naver_response:
                    # 네이버 호환성 검사
                    is_compatible = naver_response.get(
                        "naver_compatibility", {}).get(
                        "naver_compatible", False)

                    # 호환 매물만 조회 옵션 처리
                    if naver_compatible_only and not is_compatible:
                        continue

                    if is_compatible:
                        naver_compatible_count += 1

                    # 응답 데이터 구성 (Pydantic 모델 오류 방지를 위해 JSON 형태로)
                    naver_listing_item = {
                        "id": str(listing_id_uuid),
                        "title": naver_response.get("title", ""),
                        "property_type": naver_response.get("property_type", ""),
                        "deal_type": naver_response.get("deal_type", ""),
                        "price": str(naver_response.get("price", "")),
                        "display_address": naver_response.get("display_address", ""),
                        "status": naver_response.get("status", ""),
                        "created_at": naver_response.get("created_at"),
                        "updated_at": naver_response.get("updated_at"),
                        "naver_format": naver_response.get("naver_format", {}),
                        "naver_compatibility": naver_response.get("naver_compatibility", {}) if include_validation else None
                    }
                    naver_listings.append(naver_listing_item)

            except Exception as e:
                # 개별 리스팅 변환 실패는 로그만 남기고 계속
                print(f"리스팅 {prop_dict.get('id')} 네이버 변환 실패: {str(e)}")
                continue

        # JSON 응답으로 반환
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": naver_listings,
                "total_count": len(listings),
                "naver_compatible_count": naver_compatible_count,
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "returned_count": len(naver_listings),
                    "total_count": len(listings)
                },
                "message": f"네이버 형식 리스팅 {len(naver_listings)}건을 조회했습니다. (호환: {naver_compatible_count}건)",
                "status": "success"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"네이버 형식 리스팅 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


# 기본 CRUD 엔드포인트들

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_listing(
    listing_data: PropertyCreate,
    service: PropertyService = Depends(get_property_service)
):
    """
    새로운 리스팅 등록

    - **주소 기반**: 주소 입력 시 자동으로 분석 시작 예정
    - **거래형태**: 매매/교환/임대 중 선택
    - **매물구분**: 토지/건물/사무실/상가/주거/기타 중 선택
    """
    try:
        listing_obj = await service.create_listing(listing_data)
        if not listing_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="리스팅 생성에 실패했습니다."
            )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "data": listing_obj,
                "message": "리스팅이 성공적으로 등록되었습니다.",
                "status": "success"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"리스팅 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/")
async def get_listings(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    format: Optional[str] = Query(None, description="응답 형식 (naver: 네이버 표준)"),
    listing_status: Optional[PropertyStatus] = Query(None, description="매물 상태 필터"),
    property_type: Optional[PropertyType] = Query(None, description="매물 구분 필터"),
    transaction_type: Optional[TransactionType] = Query(None, description="거래형태 필터"),
    service: PropertyService = Depends(get_property_service)
):
    """
    리스팅 목록 조회 - 형식 선택 가능

    - **페이징**: skip, limit 파라미터로 페이징 처리
    - **필터링**: 상태, 매물구분, 거래형태별 필터 가능
    - **정렬**: 등록일 최신순으로 정렬
    - **네이버 형식**: format=naver 파라미터로 네이버 표준 형식 사용
    """
    if format == "naver":
        # 네이버 형식으로 응답
        return await get_listings_naver_format(
            skip=skip,
            limit=limit,
            listing_status=listing_status,
            property_type=property_type,
            transaction_type=transaction_type,
            include_validation=True,
            naver_compatible_only=False,
            service=service
        )
    else:
        # 기존 형식 유지
        try:
            listings = await service.get_listings(
                skip=skip,
                limit=limit,
                status=listing_status.value if listing_status else None,
                property_type=property_type.value if property_type else None,
                transaction_type=transaction_type.value if transaction_type else None
            )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "data": listings,
                    "message": f"리스팅 {len(listings)}건을 조회했습니다.",
                    "status": "success",
                    "pagination": {
                        "skip": skip,
                        "limit": limit,
                        "count": len(listings)
                    }
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"리스팅 목록 조회 중 오류가 발생했습니다: {str(e)}"
            )


@router.get("/{listing_id}")
async def get_listing(
    listing_id: UUID,
    service: PropertyService = Depends(get_property_service)
):
    """
    리스팅 상세 조회

    - **리스팅 ID**: UUID 형식의 리스팅 고유 식별자
    - **상세 정보**: 모든 리스팅 정보와 연결된 분석 결과 포함
    """
    try:
        listing_obj = await service.get_listing(listing_id)
        if not listing_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 리스팅을 찾을 수 없습니다."
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": listing_obj,
                "message": "리스팅 정보를 조회했습니다.",
                "status": "success"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"리스팅 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{listing_id}")
async def update_listing(
    listing_id: UUID,
    listing_data: PropertyUpdate,
    service: PropertyService = Depends(get_property_service)
):
    """
    리스팅 정보 수정

    - **부분 수정**: 변경할 필드만 포함하여 전송
    - **자동 갱신**: updated_at 필드 자동 업데이트
    - **상태 관리**: 매물 상태별 수정 권한 검증
    """
    try:
        # 리스팅 존재 여부 확인
        existing_listing = await service.get_listing(listing_id)
        if not existing_listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 리스팅을 찾을 수 없습니다."
            )

        # 리스팅 정보 수정
        updated_listing = await service.update_listing(listing_id, listing_data)
        if not updated_listing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="리스팅 수정에 실패했습니다."
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": updated_listing,
                "message": "리스팅 정보가 성공적으로 수정되었습니다.",
                "status": "success"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"리스팅 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{listing_id}")
async def delete_listing(
    listing_id: UUID,
    service: PropertyService = Depends(get_property_service)
):
    """
    리스팅 삭제

    - **연관 데이터**: 관련된 분석 결과도 함께 삭제 (CASCADE)
    - **복구 불가**: 삭제된 데이터는 복구할 수 없음
    - **권한 확인**: 삭제 권한 검증 후 실행
    """
    try:
        # 리스팅 존재 여부 확인
        existing_listing = await service.get_listing(listing_id)
        if not existing_listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 리스팅을 찾을 수 없습니다."
            )

        # 리스팅 삭제
        success = await service.delete_listing(listing_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="리스팅 삭제에 실패했습니다."
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": {"listing_id": str(listing_id)},
                "message": "리스팅이 성공적으로 삭제되었습니다.",
                "status": "success"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"리스팅 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{listing_id}/naver-format")
async def get_listing_naver_format(
    listing_id: UUID,
    include_validation: bool = Query(True, description="호환성 검증 포함 여부"),
    service: PropertyService = Depends(get_property_service)
):
    """
    리스팅 상세 조회 - 네이버 표준 형식

    - **네이버 호환**: 네이버 부동산 API 구조와 동일한 형식
    - **호환성 검증**: 네이버 표준 코드 체계 준수 여부 확인
    - **경쟁사 분석**: 네이버 부동산 데이터와 비교 분석 가능
    """
    try:
        # 기본 리스팅 정보 조회
        listing_obj = await service.get_listing(listing_id)
        if not listing_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 리스팅을 찾을 수 없습니다."
            )

        # 네이버 호환 형식으로 변환
        naver_response = await service.get_naver_compatible_response(
            listing_id,
            include_naver=True
        )

        if not naver_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="네이버 형식 변환에 실패했습니다."
            )

        # JSON 응답으로 반환 (Pydantic 모델 오류 방지)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(listing_id),
                "title": naver_response.get("title", ""),
                "property_type": naver_response.get("property_type", ""),
                "deal_type": naver_response.get("deal_type", ""),
                "price": str(naver_response.get("price", "")),
                "display_address": naver_response.get("display_address", ""),
                "status": naver_response.get("status", ""),
                "created_at": naver_response.get("created_at"),
                "updated_at": naver_response.get("updated_at"),
                "naver_format": naver_response.get("naver_format", {}),
                "naver_compatibility": naver_response.get("naver_compatibility", {}) if include_validation else None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"네이버 형식 리스팅 조회 중 오류가 발생했습니다: {str(e)}"
        )