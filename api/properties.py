"""
간단한 Properties CRUD API - 기존 호환성 유지
실제 배포된 API 구조와 호환되도록 수정
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends

from models.property import PropertyCreate, PropertyResponse
from services.property_service import PropertyService

# 라우터 생성
router = APIRouter(tags=["properties"])


def get_property_service() -> PropertyService:
    """Property 서비스 의존성 주입"""
    return PropertyService()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreate,
    service: PropertyService = Depends(get_property_service)
):
    """매물 생성"""
    try:
        result = await service.create_listing(property_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="매물 생성에 실패했습니다."
            )

        # 응답 형식을 기존 배포된 API와 일치시킴
        response_data = {
            "id": result.get("id"),
            "property_type": property_data.property_type,
            "transaction_type": property_data.transaction_type,
            "title": property_data.title if hasattr(
                property_data,
                'title') else property_data.property_description.title,
            "address_info": {
                "address": property_data.address_info.address,
                "city": property_data.address_info.city,
                "district": property_data.address_info.district},
            "price_info": {
                "salePrice": property_data.price_info.salePrice,
                "deposit": property_data.price_info.deposit,
                "monthlyRent": property_data.price_info.monthlyRent},
            "status": "등록대기",
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at")}

        return response_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매물 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/")
async def get_properties(
    service: PropertyService = Depends(get_property_service)
):
    """매물 목록 조회"""
    try:
        properties = await service.get_listings()

        # 응답 형식을 기존 배포된 API와 일치시킴
        formatted_properties = []
        for prop in properties:
            formatted_prop = {
                "id": prop.get("id"),
                "property_type": prop.get("property_type", "주거"),
                "transaction_type": prop.get("deal_type", "매매"),
                "title": prop.get("title"),
                "address_info": {
                    "address": prop.get("display_address", ""),
                    "city": prop.get("sido", ""),
                    "district": prop.get("sigungu", "")
                },
                "price_info": {
                    "salePrice": int(prop.get("price", 0)) if prop.get("price") else 0,
                    "deposit": int(prop.get("deposit", 0)) if prop.get("deposit") else 0,
                    "monthlyRent": int(prop.get("rent_fee", 0)) if prop.get("rent_fee") else 0
                },
                "status": "등록대기",
                "created_at": prop.get("created_at"),
                "updated_at": prop.get("updated_at")
            }
            formatted_properties.append(formatted_prop)

        return formatted_properties
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매물 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/count")
async def get_properties_count(
    service: PropertyService = Depends(get_property_service)
):
    """매물 개수 조회"""
    try:
        properties = await service.get_listings()
        return {"count": len(properties), "mode": "supabase"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매물 개수 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{property_id}")
async def get_property(
    property_id: UUID,
    service: PropertyService = Depends(get_property_service)
):
    """매물 상세 조회"""
    try:
        property_obj = await service.get_listing(property_id)
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 매물을 찾을 수 없습니다."
            )

        # 응답 형식을 기존 배포된 API와 일치시킴
        formatted_prop = {
            "id": property_obj.get("id"),
            "property_type": property_obj.get(
                "property_type",
                "주거"),
            "transaction_type": property_obj.get(
                "deal_type",
                "매매"),
            "title": property_obj.get("title"),
            "address_info": {
                "address": property_obj.get(
                    "display_address",
                    ""),
                "city": property_obj.get(
                    "sido",
                    ""),
                "district": property_obj.get(
                    "sigungu",
                    "")},
            "price_info": {
                "salePrice": int(
                    property_obj.get(
                        "price",
                        0)) if property_obj.get("price") else 0,
                "deposit": int(
                    property_obj.get(
                        "deposit",
                        0)) if property_obj.get("deposit") else 0,
                "monthlyRent": int(
                    property_obj.get(
                        "rent_fee",
                        0)) if property_obj.get("rent_fee") else 0},
            "status": "등록대기",
            "created_at": property_obj.get("created_at"),
            "updated_at": property_obj.get("updated_at")}

        return formatted_prop
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매물 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{property_id}")
async def update_property(
    property_id: UUID,
    property_data: PropertyCreate,
    service: PropertyService = Depends(get_property_service)
):
    """매물 정보 수정"""
    try:
        # 매물 존재 여부 확인
        existing_property = await service.get_listing(property_id)
        if not existing_property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 매물을 찾을 수 없습니다."
            )

        # PropertyCreate를 간단한 업데이트 데이터로 변환
        from models.property import PropertyUpdate
        update_data = PropertyUpdate()

        if hasattr(
                property_data,
                'property_description') and property_data.property_description:
            update_data.property_description = property_data.property_description
        if hasattr(property_data, 'price_info') and property_data.price_info:
            update_data.price_info = property_data.price_info
        if hasattr(
                property_data,
                'address_info') and property_data.address_info:
            update_data.address_info = property_data.address_info

        # 매물 정보 수정
        updated_property = await service.update_listing(property_id, update_data)
        if not updated_property:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="매물 수정에 실패했습니다."
            )

        # 응답 형식을 기존 배포된 API와 일치시킴
        formatted_prop = {
            "id": updated_property.get("id"),
            "property_type": property_data.property_type,
            "transaction_type": property_data.transaction_type,
            "title": property_data.title if hasattr(
                property_data,
                'title') else property_data.property_description.title,
            "address_info": {
                "address": property_data.address_info.address,
                "city": property_data.address_info.city,
                "district": property_data.address_info.district},
            "price_info": {
                "salePrice": property_data.price_info.salePrice,
                "deposit": property_data.price_info.deposit,
                "monthlyRent": property_data.price_info.monthlyRent},
            "status": "등록대기",
            "created_at": updated_property.get("created_at"),
            "updated_at": updated_property.get("updated_at")}

        return formatted_prop
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매물 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{property_id}")
async def delete_property(
    property_id: UUID,
    service: PropertyService = Depends(get_property_service)
):
    """매물 삭제"""
    try:
        # 매물 존재 여부 확인
        existing_property = await service.get_listing(property_id)
        if not existing_property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 매물을 찾을 수 없습니다."
            )

        # 매물 삭제
        success = await service.delete_listing(property_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="매물 삭제에 실패했습니다."
            )

        return {
            "message": "매물이 성공적으로 삭제되었습니다.",
            "property_id": str(property_id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매물 삭제 중 오류가 발생했습니다: {str(e)}"
        )
