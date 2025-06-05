from fastapi import UploadFile
from typing import Dict, Optional


async def extract_owner_info_from_file(file: UploadFile) -> Optional[Dict]:
    """
    OCR 파일에서 소유주 정보(소유자명, 소유자주소, 소유권변동일)를 추출한다.
    실제 OCR 연동(Google Vision API, Naver Clova 등)은 별도 구현 필요.
    """
    # TODO: 실제 OCR 처리 로직 구현
    # 예시: OCR 결과에서 정보 파싱
    # 아래는 더미 데이터
    return {
        "owner_name": "홍길동",
        "owner_address": "서울특별시 강남구 ...",
        "ownership_changed_at": "2023-01-01"
    }
