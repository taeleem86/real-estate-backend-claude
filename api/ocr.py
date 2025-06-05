from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Any
from ..services.ocr_service import extract_owner_info_from_file
from ..models.property import Property, OwnerInfo

router = APIRouter(tags=["ocr"])


@router.post("/api/ocr/upload")
async def upload_ocr_file(file: UploadFile = File(...)) -> Any:
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")
    try:
        # OCR 처리 및 소유주 정보 추출
        owner_info_data = await extract_owner_info_from_file(file)
        if not owner_info_data:
            raise HTTPException(status_code=422, detail="소유주 정보를 추출할 수 없습니다.")
        # Property.owner_info 업데이트 (예시: property_id를 쿼리 파라미터로 받는 경우)
        # property = ... (DB에서 property 조회)
        # property.owner_info = OwnerInfo(**owner_info_data)
        # ... (DB 저장)
        return {"success": True, "owner_info": owner_info_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 처리 중 오류: {e}")
