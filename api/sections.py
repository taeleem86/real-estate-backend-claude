from fastapi import APIRouter, HTTPException, Body, Path
from typing import List, Optional
from ..models.section import Section, PropertySection
from uuid import UUID

router = APIRouter(tags=["sections"])

# 임시 인메모리 저장소 (실제 구현시 DB로 대체)
sections_db: List[Section] = []
property_sections_db: List[PropertySection] = []


@router.get("/api/sections", response_model=List[Section])
def list_sections():
    return sections_db


@router.post("/api/sections", response_model=Section)
def create_section(section: Section):
    sections_db.append(section)
    return section


@router.put("/api/sections/{section_id}", response_model=Section)
def update_section(section_id: UUID, section: Section):
    for idx, s in enumerate(sections_db):
        if s.id == section_id:
            sections_db[idx] = section
            return section
    raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다.")


@router.delete("/api/sections/{section_id}")
def delete_section(section_id: UUID):
    global sections_db
    sections_db = [s for s in sections_db if s.id != section_id]
    return {"success": True}


@router.post("/api/listings/{listing_id}/sections")
def add_listing_sections(
        listing_id: UUID,
        section_ids: List[UUID] = Body(...)):
    for section_id in section_ids:
        # property_id in Model will be handled later if model changes
        rel = PropertySection(property_id=listing_id, section_id=section_id)
        property_sections_db.append(rel)
    return {"success": True, "count": len(section_ids)}


@router.post("/api/sections/{section_id}/order")
def update_section_order(section_id: UUID, order: int = Body(...)):
    for s in sections_db:
        if s.id == section_id:
            s.order = order
            return {"success": True, "order": order}
    raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다.")


@router.post("/api/sections/{section_id}/activate")
def activate_section(section_id: UUID, is_active: bool = Body(...)):
    for s in sections_db:
        if s.id == section_id:
            s.is_active = is_active
            return {"success": True, "is_active": is_active}
    raise HTTPException(status_code=404, detail="섹션을 찾을 수 없습니다.")
