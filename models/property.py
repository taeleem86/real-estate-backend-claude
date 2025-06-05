"""
부동산 매물 데이터 모델
Notion 요구사항을 반영한 Pydantic 모델 정의
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class PropertyType(str, Enum):
    """매물 구분"""
    LAND = "토지"
    BUILDING = "건물"
    OFFICE = "사무실"
    RETAIL = "상가"
    RESIDENTIAL = "주거"
    OTHER = "기타"


class TransactionType(str, Enum):
    """거래 형태"""
    SALE = "매매"
    EXCHANGE = "교환"
    LEASE = "임대"


class PropertyStatus(str, Enum):
    """매물 상태"""
    PENDING = "등록대기"
    ACTIVE = "활성"
    INACTIVE = "비활성"
    SOLD = "거래완료"
    SUSPENDED = "일시중단"


class ChannelStatus(str, Enum):
    """송출 현황"""
    NOT_SENT = "미송출"
    SENT = "송출완료"
    FAILED = "송출실패"
    STOPPED = "송출중단"


class AddressInfo(BaseModel):
    """주소 정보 (네이버 표준)"""
    address: str = Field(..., description="주소")  # display_address → address
    city: str = Field(..., description="시/도")   # city_district → city
    district: str = Field(..., description="시군구")  # city_district → district
    other_addresses: Optional[List[str]] = Field(
        default=[], description="기타 관련 주소")
    postal_code: Optional[str] = Field(None, description="우편번호")
    coordinate_x: Optional[float] = Field(None, description="X 좌표")
    coordinate_y: Optional[float] = Field(None, description="Y 좌표")


class AreaInfo(BaseModel):
    """면적 정보 (네이버 표준)"""
    landArea: Optional[float] = Field(
        None, description="토지면적 (㎡)")  # land_area → landArea
    totalArea: Optional[float] = Field(
        None, description="연면적 (㎡)")    # total_floor_area → totalArea
    exclusiveArea: Optional[float] = Field(
        None, description="전용면적 (㎡)")  # exclusive_area → exclusiveArea
    buildingArea: Optional[float] = Field(
        None, description="건축면적 (㎡)")  # building_area → buildingArea
    commonArea: Optional[float] = Field(
        None, description="공용면적 (㎡)")    # common_area → commonArea
    floorCount: Optional[int] = Field(
        None, description="층수")              # floor_count → floorCount
    basementCount: Optional[int] = Field(
        None, description="지하층수")        # basement_count → basementCount


class PriceInfo(BaseModel):
    """가격 정보 (네이버 표준)"""
    salePrice: Optional[int] = Field(
        None, description="매매가 (만원)")      # sale_price → salePrice
    deposit: Optional[int] = Field(
        None, description="임대 보증금 (만원)")   # lease_deposit → deposit
    monthlyRent: Optional[int] = Field(
        None, description="월 임대료 (만원)")  # monthly_rent → monthlyRent
    exchangeValue: Optional[int] = Field(
        None, description="교환 평가가 (만원)")  # exchange_value → exchangeValue
    maintenanceFee: Optional[int] = Field(
        None, description="관리비 (만원)")   # maintenance_fee → maintenanceFee
    # additional_costs → additionalCosts
    additionalCosts: Optional[str] = Field(None, description="기타 비용")


class PropertyDescription(BaseModel):
    """매물 설명"""
    title: str = Field(..., description="매물 제목")
    features: Optional[str] = Field(None, description="매물 특징")
    description: Optional[str] = Field(None, description="상세 설명")
    keywords: Optional[List[str]] = Field(default=[], description="검색 키워드")


class ChannelInfo(BaseModel):
    """채널별 송출 정보"""
    naver: ChannelStatus = Field(
        default=ChannelStatus.NOT_SENT,
        description="네이버 송출")
    zigbang: ChannelStatus = Field(
        default=ChannelStatus.NOT_SENT,
        description="직방 송출")
    dabang: ChannelStatus = Field(
        default=ChannelStatus.NOT_SENT,
        description="다방 송출")
    peterpan: ChannelStatus = Field(
        default=ChannelStatus.NOT_SENT,
        description="피터팬 송출")


class OwnerInfo(BaseModel):
    """소유주 정보 (OCR/토지대장/건축물대장 등)"""
    owner_name: Optional[str] = Field(None, description="소유자명")
    owner_address: Optional[str] = Field(None, description="소유자 주소")
    ownership_changed_at: Optional[str] = Field(None, description="소유권 변동일")


class BuildingRegisterInfo(BaseModel):
    """건축물대장 기반 건물 정보"""
    building_name: Optional[str] = Field(None, description="건물명")
    main_purpose: Optional[str] = Field(None, description="주용도")
    structure: Optional[str] = Field(None, description="구조")
    scale: Optional[str] = Field(None, description="규모(지상/지하 층수)")
    build_year: Optional[str] = Field(None, description="건축년도")
    building_area: Optional[float] = Field(None, description="건축면적(㎡)")
    total_floor_area: Optional[float] = Field(None, description="연면적(㎡)")
    approval_date: Optional[str] = Field(None, description="사용승인일")
    building_status: Optional[str] = Field(None, description="건축물 상태")
    parking_count: Optional[int] = Field(None, description="주차대수")


class LandRegisterInfo(BaseModel):
    """토지대장 기반 토지 정보"""
    land_location: Optional[str] = Field(None, description="소재지(지번주소)")
    land_category: Optional[str] = Field(None, description="지목(용도)")
    land_area: Optional[float] = Field(None, description="면적(㎡)")
    land_use: Optional[str] = Field(None, description="용도지역/지구")
    land_ownership: Optional[str] = Field(None, description="소유구분")
    owner_name: Optional[str] = Field(None, description="소유자명")
    owner_address: Optional[str] = Field(None, description="소유자 주소")
    ownership_changed_at: Optional[str] = Field(None, description="소유권 변동일")
    land_rights: Optional[str] = Field(None, description="기타 권리(저당 등)")
    land_status: Optional[str] = Field(None, description="토지 상태")
    official_land_price: Optional[int] = Field(None, description="공시지가")


# 기본 매물 모델
class PropertyBase(BaseModel):
    """매물 기본 정보 (네이버 표준)"""
    property_type: PropertyType = Field(..., description="매물 구분")
    transaction_type: TransactionType = Field(..., description="거래 형태")
    address_info: AddressInfo = Field(..., description="주소 정보")
    area_info: AreaInfo = Field(..., description="면적 정보")
    price_info: PriceInfo = Field(..., description="가격 정보")
    property_description: PropertyDescription = Field(..., description="매물 설명")
    owner_info: Optional[OwnerInfo] = Field(None, description="소유주 정보")
    building_register_info: Optional[BuildingRegisterInfo] = Field(
        None, description="건축물대장 정보")
    land_register_info: Optional[LandRegisterInfo] = Field(
        None, description="토지대장 정보")
    manual_data: Optional[dict] = Field(
        default_factory=dict, description="수동 입력 데이터")
    ocr_data: Optional[dict] = Field(
        default_factory=dict,
        description="OCR 추출 데이터")
    api_data: Optional[dict] = Field(
        default_factory=dict,
        description="API 연동 데이터")


class PropertyCreate(PropertyBase):
    """매물 생성 모델"""
    pass


class PropertyUpdate(BaseModel):
    """매물 수정 모델"""
    property_type: Optional[PropertyType] = None
    transaction_type: Optional[TransactionType] = None
    address_info: Optional[AddressInfo] = None
    area_info: Optional[AreaInfo] = None
    price_info: Optional[PriceInfo] = None
    property_description: Optional[PropertyDescription] = None
    status: Optional[PropertyStatus] = None
    channel_info: Optional[ChannelInfo] = None


class Property(PropertyBase):
    """완전한 매물 모델"""
    id: UUID = Field(default_factory=uuid4, description="매물 ID")
    property_number: str = Field(..., description="매물 번호")
    status: PropertyStatus = Field(
        default=PropertyStatus.PENDING,
        description="매물 상태")
    channel_info: ChannelInfo = Field(
        default_factory=ChannelInfo,
        description="채널별 송출 정보")

    # 자동 생성 필드
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="등록일자")
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="수정일자")

    # 분석 결과 연결
    building_analysis_id: Optional[UUID] = Field(
        None, description="건축물 분석 결과 ID")
    land_analysis_id: Optional[UUID] = Field(None, description="토지 분석 결과 ID")
    competitor_analysis_id: Optional[UUID] = Field(
        None, description="경쟁사 분석 결과 ID")
    marketing_content: Optional[str] = Field(None, description="생성된 홍보글")

    # 네이버 호환성 필드
    naver_info: Optional[Dict[str, Any]] = Field(
        None, description="네이버 부동산 표준 정보")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

    @validator('property_number', pre=True, always=True)
    def generate_property_number(cls, v):
        """매물 번호 자동 생성"""
        if not v:
            from datetime import datetime
            now = datetime.now()
            return f"P{now.strftime('%Y%m%d')}{now.strftime('%H%M%S')}"
        return v

    def to_naver_format(self) -> Dict[str, Any]:
        """네이버 부동산 표준 형식으로 변환"""
        # 네이버 호환성 모듈을 동적으로 임포트하여 순환참조 방지
        from .naver_compatibility import NAVER_PROPERTY_SCHEMA, REALESTATE_TYPE_MAP, TRADE_TYPE_MAP

        naver_data = NAVER_PROPERTY_SCHEMA.copy()

        try:
            # 1. 기본 매물 정보 변환
            naver_data["propertyType"] = REALESTATE_TYPE_MAP.get(
                self.property_type.value, "ETC"
            )
            naver_data["tradeType"] = TRADE_TYPE_MAP.get(
                self.transaction_type.value, "A1"
            )

            # 2. 위치 정보 변환
            if self.address_info:
                naver_data["location"].update({
                    "address": self.address_info.address,
                    "city": self.address_info.city,
                    "district": self.address_info.district,
                    "coordinates": {
                        "lat": self.address_info.coordinate_y or 0.0,
                        "lng": self.address_info.coordinate_x or 0.0
                    }
                })

            # 3. 면적 정보 변환
            if self.area_info:
                naver_data["area"].update({
                    "totalArea": self.area_info.totalArea or 0.0,
                    "exclusiveArea": self.area_info.exclusiveArea or 0.0,
                    "landArea": self.area_info.landArea or 0.0
                })

            # 4. 가격 정보 변환
            if self.price_info:
                naver_data["price"].update({
                    "salePrice": self.price_info.salePrice or 0,
                    "deposit": self.price_info.deposit or 0,
                    "monthlyRent": self.price_info.monthlyRent or 0
                })

            # 5. 설명 정보 변환
            if self.property_description:
                naver_data["description"].update({
                    "title": self.property_description.title,
                    "features": self.property_description.features or "",
                    "details": self.property_description.description or ""
                })

            # 6. 건물 정보 변환
            if self.area_info:
                naver_data["buildingInfo"].update({
                    "floors": self.area_info.floorCount or 0,
                    "buildYear": 0,
                    "parking": False
                })

        except Exception as e:
            print(f"네이버 형식 변환 중 오류 발생: {e}")

        # 변환된 데이터를 naver_info 필드에 저장
        self.naver_info = naver_data
        return naver_data

    def validate_naver_compatibility(self) -> Dict[str, bool]:
        """네이버 호환성 검증"""
        from .naver_compatibility import REALESTATE_TYPE_MAP, TRADE_TYPE_MAP

        validation_result = {
            "property_type_valid": False,
            "transaction_type_valid": False,
            "required_fields_complete": False,
            "naver_compatible": False
        }

        try:
            # 1. 매물 타입 검증
            if self.property_type:
                validation_result["property_type_valid"] = (
                    self.property_type.value in REALESTATE_TYPE_MAP
                )

            # 2. 거래 타입 검증
            if self.transaction_type:
                validation_result["transaction_type_valid"] = (
                    self.transaction_type.value in TRADE_TYPE_MAP
                )

            # 3. 필수 필드 완성도 검증
            required_fields_check = all([
                self.property_description and self.property_description.title,
                self.address_info and self.address_info.address,
                self.price_info
            ])
            validation_result["required_fields_complete"] = required_fields_check

            # 4. 전체 호환성 판단
            validation_result["naver_compatible"] = all([
                validation_result["property_type_valid"],
                validation_result["transaction_type_valid"],
                validation_result["required_fields_complete"]
            ])

        except Exception as e:
            print(f"네이버 호환성 검증 중 오류 발생: {e}")

        return validation_result


class PropertyInDB(Property):
    """데이터베이스용 매물 모델"""
    pass


class PropertyResponse(Property):
    """API 응답용 매물 모델"""
    pass
