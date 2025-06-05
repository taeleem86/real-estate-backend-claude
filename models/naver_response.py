"""
네이버 부동산 API 호환 응답 모델
네이버 부동산 표준 구조와 일치하는 응답 형식 정의
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class NaverCoordinates(BaseModel):
    """네이버 좌표 정보"""
    lat: float = Field(0.0, description="위도")
    lng: float = Field(0.0, description="경도")


class NaverLocation(BaseModel):
    """네이버 위치 정보"""
    address: str = Field("", description="주소")
    city: str = Field("", description="시/도")
    district: str = Field("", description="시군구")
    coordinates: NaverCoordinates = Field(
        default_factory=NaverCoordinates, description="좌표")


class NaverArea(BaseModel):
    """네이버 면적 정보"""
    totalArea: float = Field(0.0, description="총 면적")
    exclusiveArea: float = Field(0.0, description="전용면적")
    landArea: float = Field(0.0, description="토지면적")


class NaverPrice(BaseModel):
    """네이버 가격 정보"""
    salePrice: int = Field(0, description="매매가")
    deposit: int = Field(0, description="보증금")
    monthlyRent: int = Field(0, description="월세")


class NaverDescription(BaseModel):
    """네이버 설명 정보"""
    title: str = Field("", description="제목")
    features: str = Field("", description="특징")
    details: str = Field("", description="상세설명")


class NaverBuildingInfo(BaseModel):
    """네이버 건물 정보"""
    floors: int = Field(0, description="층수")
    buildYear: int = Field(0, description="건축년도")
    parking: bool = Field(False, description="주차가능여부")


class NaverPropertyData(BaseModel):
    """네이버 매물 데이터"""
    propertyType: str = Field("ETC", description="매물유형 (LND,APT,OFC,SHP,ETC)")
    tradeType: str = Field("A1", description="거래유형 (A1:매매,A2:교환,B1:임대)")
    location: NaverLocation = Field(
        default_factory=NaverLocation,
        description="위치정보")
    area: NaverArea = Field(default_factory=NaverArea, description="면적정보")
    price: NaverPrice = Field(default_factory=NaverPrice, description="가격정보")
    description: NaverDescription = Field(
        default_factory=NaverDescription, description="설명정보")
    buildingInfo: NaverBuildingInfo = Field(
        default_factory=NaverBuildingInfo, description="건물정보")


class NaverValidation(BaseModel):
    """네이버 호환성 검증 결과"""
    property_type_valid: bool = Field(False, description="매물유형 유효성")
    trade_type_valid: bool = Field(False, description="거래유형 유효성")
    required_fields_complete: bool = Field(False, description="필수필드 완성도")
    location_valid: bool = Field(False, description="위치정보 유효성")
    price_valid: bool = Field(False, description="가격정보 유효성")
    naver_compatible: bool = Field(False, description="네이버 호환성")


class NaverPropertyResponse(BaseModel):
    """네이버 호환 매물 응답"""
    id: str = Field(..., description="매물 ID")
    title: str = Field("", description="매물 제목")
    property_type: str = Field("", description="원본 매물 유형")
    deal_type: str = Field("", description="원본 거래 유형")
    price: str = Field("", description="원본 가격")
    display_address: str = Field("", description="원본 주소")
    status: str = Field("", description="매물 상태")
    created_at: Optional[str] = Field(None, description="등록일")
    updated_at: Optional[str] = Field(None, description="수정일")
    naver_format: NaverPropertyData = Field(
        default_factory=NaverPropertyData,
        description="네이버 표준 형식")
    naver_compatibility: Optional[NaverValidation] = Field(
        None, description="네이버 호환성 검증")


class NaverPropertyListResponse(BaseModel):
    """네이버 호환 매물 목록 응답"""
    data: List[NaverPropertyResponse] = Field(
        default_factory=list, description="매물 목록")
    total_count: int = Field(0, description="전체 매물 수")
    naver_compatible_count: int = Field(0, description="네이버 호환 매물 수")
    pagination: Dict[str, Any] = Field(
        default_factory=dict, description="페이징 정보")
    message: str = Field("", description="응답 메시지")
    status: str = Field("success", description="응답 상태")


class NaverFormatOptions(BaseModel):
    """네이버 형식 옵션"""
    include_validation: bool = Field(True, description="유효성 검증 포함")
    include_raw_data: bool = Field(False, description="원본 데이터 포함")
    validation_level: str = Field("standard",
                                  description="검증 수준 (basic,standard,strict)")


# 네이버 표준 코드 매핑
NAVER_PROPERTY_TYPE_CODES = {
    "LND": "토지",
    "APT": "아파트",
    "OFC": "오피스/사무실",
    "SHP": "상가/상업시설",
    "ETC": "기타"
}

NAVER_TRADE_TYPE_CODES = {
    "A1": "매매",
    "A2": "교환",
    "B1": "임대"
}
