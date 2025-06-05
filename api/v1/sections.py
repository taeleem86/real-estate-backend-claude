"""
섹션 관리 API v1
홈페이지 섹션별 매물 분류 및 관리 기능
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
import logging

from models.section import (
    Section, SectionCreate, SectionUpdate, SectionResponse,
    PropertySection, PropertySectionCreate, PropertySectionUpdate,
    BulkPropertySectionCreate, SectionStats
)
from services.supabase_client import get_supabase_client

router = APIRouter(tags=["sections"])
logger = logging.getLogger(__name__)

# Supabase 클라이언트 의존성


def get_db():
    return get_supabase_client()


@router.get("/", response_model=List[SectionResponse])
async def list_sections(
    active_only: bool = Query(False, description="활성 섹션만 조회"),
    db=Depends(get_db)
):
    """섹션 목록 조회"""
    try:
        query = db.table("sections").select("*").order("order")

        if active_only:
            query = query.eq("is_active", True)

        result = query.execute()
        return result.data
    except Exception as e:
        logger.error(f"섹션 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="섹션 목록 조회에 실패했습니다")


@router.get("/{section_id}", response_model=SectionResponse)
async def get_section(section_id: UUID, db=Depends(get_db)):
    """특정 섹션 조회"""
    try:
        result = db.table("sections").select(
            "*").eq("id", str(section_id)).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다")

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"섹션 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="섹션 조회에 실패했습니다")


@router.post("/", response_model=SectionResponse)
async def create_section(section_data: SectionCreate, db=Depends(get_db)):
    """새 섹션 생성"""
    try:
        # 중복 이름 확인
        existing = db.table("sections").select("id").eq(
            "name", section_data.name).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="이미 존재하는 섹션 이름입니다")

        # 섹션 생성
        result = db.table("sections").insert(section_data.dict()).execute()
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"섹션 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="섹션 생성에 실패했습니다")


@router.put("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: UUID,
    section_data: SectionUpdate,
    db=Depends(get_db)
):
    """섹션 정보 수정"""
    try:
        # 섹션 존재 확인
        existing = db.table("sections").select(
            "id").eq("id", str(section_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다")

        # 업데이트할 데이터만 추출 (None이 아닌 필드만)
        update_data = {k: v for k, v in section_data.dict(
            exclude_unset=True).items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 내용이 없습니다")

        # 섹션 업데이트
        result = db.table("sections").update(
            update_data).eq("id", str(section_id)).execute()
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"섹션 수정 실패: {e}")
        raise HTTPException(status_code=500, detail="섹션 수정에 실패했습니다")


@router.delete("/{section_id}")
async def delete_section(section_id: UUID, db=Depends(get_db)):
    """섹션 삭제"""
    try:
        # 섹션에 연결된 리스팅 관계 확인
        listing_relations = db.table("property_sections").select(
            "id").eq("section_id", str(section_id)).execute()

        if listing_relations.data:
            raise HTTPException(
                status_code=400,
                detail=f"섹션에 {len(listing_relations.data)}개의 리스팅이 연결되어 있습니다. 먼저 리스팅을 다른 섹션으로 이동하세요."
            )

        # 섹션 삭제
        result = db.table("sections").delete().eq(
            "id", str(section_id)).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다")

        return {"success": True, "message": "섹션이 삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"섹션 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="섹션 삭제에 실패했습니다")


@router.post("/{section_id}/properties")
async def add_properties_to_section(
    section_id: UUID,
    property_data: BulkPropertySectionCreate,
    db=Depends(get_db)
):
    """섹션에 매물 일괄 추가"""
    try:
        # 섹션 존재 확인
        section = db.table("sections").select(
            "id").eq("id", str(section_id)).execute()
        if not section.data:
            raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다")

        # 매물-섹션 관계 생성
        relations = []
        for i, property_id in enumerate(property_data.property_ids):
            relation = {
                "property_id": str(property_id),
                "section_id": str(section_id),
                "is_featured": property_data.is_featured,
                "priority": property_data.priority,
                "display_order": i,
                "added_by": property_data.added_by
            }
            relations.append(relation)

        # 일괄 삽입
        result = db.table("property_sections").insert(relations).execute()

        return {
            "success": True,
            "message": f"{len(relations)}개 매물이 섹션에 추가되었습니다",
            "added_count": len(result.data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"매물 섹션 추가 실패: {e}")
        raise HTTPException(status_code=500, detail="매물 섹션 추가에 실패했습니다")


@router.get("/{section_id}/properties")
async def get_section_properties(
    section_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    featured_only: bool = Query(False),
    db=Depends(get_db)
):
    """섹션별 매물 목록 조회"""
    try:
        query = db.table("property_sections").select(
            "*, listings(id, title, price, display_address, thumbnail_url)"
        ).eq("section_id", str(section_id))

        if featured_only:
            query = query.eq("is_featured", True)

        result = query.order(
            "priority", desc=True).order("display_order").range(
            offset, offset + limit - 1).execute()

        return {
            "section_id": section_id,
            "listings": result.data,  # Renamed key
            "total": len(result.data),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"섹션 매물 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="섹션 매물 조회에 실패했습니다")


@router.post("/reorder")
async def reorder_sections(
    section_orders: List[dict],
    db=Depends(get_db)
):
    """섹션 순서 재정렬"""
    try:
        for order_data in section_orders:
            section_id = order_data.get("section_id")
            new_order = order_data.get("order")

            if not section_id or new_order is None:
                continue

            db.table("sections").update({"order": new_order}).eq(
                "id", str(section_id)).execute()

        return {"success": True, "message": "섹션 순서가 변경되었습니다"}
    except Exception as e:
        logger.error(f"섹션 순서 변경 실패: {e}")
        raise HTTPException(status_code=500, detail="섹션 순서 변경에 실패했습니다")


@router.get("/stats", response_model=List[SectionStats])
async def get_sections_stats(db=Depends(get_db)):
    """모든 섹션의 통계 조회"""
    try:
        # 섹션별 매물 수 통계 조회
        result = db.rpc("get_section_stats").execute()
        return result.data
    except Exception as e:
        logger.error(f"섹션 통계 조회 실패: {e}")
        # RPC 함수가 없으면 수동 계산
        try:
            sections = db.table("sections").select("*").execute()
            stats = []

            for section in sections.data:
                listing_count_result = db.table("property_sections").select(
                    "id", count="exact").eq("section_id", section["id"]).execute()  # Renamed var
                featured_count_result = db.table("property_sections").select(
                    "id", count="exact").eq(
                    "section_id", section["id"]).eq(
                    "is_featured", True).execute()  # Renamed var

                stats.append({
                    "section_id": section["id"],
                    "section_name": section["name"],
                    "total_listings": listing_count_result.count or 0,  # Renamed key
                    "featured_listings": featured_count_result.count or 0,  # Renamed key
                    "view_count": section.get("view_count", 0),
                    "last_updated": section.get("updated_at")
                })

            return stats
        except Exception as e2:
            logger.error(f"수동 통계 계산 실패: {e2}")
            raise HTTPException(status_code=500, detail="섹션 통계 조회에 실패했습니다")
