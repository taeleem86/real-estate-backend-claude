"""
분석 결과 데이터 모델
건축물대장, 토지대장, 경쟁사 분석 등의 결과를 저장하는 모델
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class AnalysisType(str, Enum):
    """분석 유형"""
    BUILDING_REGISTRY = "건축물대장"
    LAND_REGISTRY = "토지대장"
    COMPETITOR_ANALYSIS = "경쟁사분석"
    MARKET_ANALYSIS = "시장분석"


class AnalysisStatus(str, Enum):
    """분석 상태"""
    PENDING = "대기중"
    IN_PROGRESS = "분석중"
    COMPLETED = "완료"
    FAILED = "실패"


class BuildingRegistryData(BaseModel):
    """건축물대장 정보"""
    building_name: Optional[str] = Field(None, description="건물명")
    building_use: Optional[str] = Field(None, description="건물용도")
    construction_year: Optional[int] = Field(None, description="건축년도")
    structure_type: Optional[str] = Field(None, description="구조")
    roof_type: Optional[str] = Field(None, description="지붕")
    total_floors: Optional[int] = Field(None, description="총 층수")
    basement_floors: Optional[int] = Field(None, description="지하층수")
    total_area: Optional[float] = Field(None, description="총 면적")
    building_coverage_ratio: Optional[float] = Field(None, description="건폐율")
    floor_area_ratio: Optional[float] = Field(None, description="용적률")
    parking_spaces: Optional[int] = Field(None, description="주차대수")


class LandRegistryData(BaseModel):
    """토지대장 정보"""
    land_classification: Optional[str] = Field(None, description="지목")
    land_area: Optional[float] = Field(None, description="면적")
    land_use_zone: Optional[str] = Field(None, description="용도지역")
    land_use_district: Optional[str] = Field(None, description="용도지구")
    land_price_per_sqm: Optional[int] = Field(None, description="공시지가 (원/㎡)")
    ownership_type: Optional[str] = Field(None, description="소유구분")
    special_conditions: Optional[List[str]] = Field(
        default=[], description="특수조건")


class CompetitorProperty(BaseModel):
    """경쟁 매물 정보"""
    source: str = Field(..., description="출처 (네이버, 직방 등)")
    property_id: Optional[str] = Field(None, description="매물 ID")
    title: str = Field(..., description="매물 제목")
    price: Optional[int] = Field(None, description="가격")
    area: Optional[float] = Field(None, description="면적")
    location: str = Field(..., description="위치")
    distance_km: Optional[float] = Field(None, description="거리 (km)")
    price_per_sqm: Optional[int] = Field(None, description="㎡당 가격")
    url: Optional[str] = Field(None, description="매물 URL")
    scraped_at: datetime = Field(
        default_factory=datetime.now,
        description="수집 시간")


class CompetitorAnalysisData(BaseModel):
    """경쟁사 분석 데이터"""
    total_competitors: int = Field(0, description="총 경쟁 매물 수")
    avg_price: Optional[float] = Field(None, description="평균 가격")
    min_price: Optional[float] = Field(None, description="최저 가격")
    max_price: Optional[float] = Field(None, description="최고 가격")
    avg_price_per_sqm: Optional[float] = Field(None, description="평균 ㎡당 가격")
    competitors: List[CompetitorProperty] = Field(
        default=[], description="경쟁 매물 목록")
    market_positioning: Optional[str] = Field(None, description="시장 포지셔닝")
    price_competitiveness: Optional[str] = Field(None, description="가격 경쟁력")


class AnalysisResultBase(BaseModel):
    """분석 결과 기본 모델"""
    property_id: UUID = Field(..., description="매물 ID")
    analysis_type: AnalysisType = Field(..., description="분석 유형")
    status: AnalysisStatus = Field(
        default=AnalysisStatus.PENDING,
        description="분석 상태")
    raw_data: Optional[Dict[str, Any]] = Field(
        default={}, description="원본 데이터")
    error_message: Optional[str] = Field(None, description="에러 메시지")


class AnalysisResultCreate(AnalysisResultBase):
    """분석 결과 생성 모델"""
    pass


class AnalysisResult(AnalysisResultBase):
    """완전한 분석 결과 모델"""
    id: UUID = Field(default_factory=uuid4, description="분석 결과 ID")

    # 각 분석 유형별 데이터
    building_data: Optional[BuildingRegistryData] = Field(
        None, description="건축물대장 데이터")
    land_data: Optional[LandRegistryData] = Field(None, description="토지대장 데이터")
    competitor_data: Optional[CompetitorAnalysisData] = Field(
        None, description="경쟁사 분석 데이터")

    # 메타데이터
    analyzed_at: datetime = Field(
        default_factory=datetime.now,
        description="분석 완료 시간")
    analysis_duration: Optional[float] = Field(
        None, description="분석 소요 시간 (초)")
    data_source: Optional[str] = Field(None, description="데이터 출처")
    api_version: Optional[str] = Field(None, description="API 버전")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class AnalysisResultInDB(AnalysisResult):
    """데이터베이스용 분석 결과 모델"""
    pass


class AnalysisResultResponse(AnalysisResult):
    """API 응답용 분석 결과 모델"""
    pass


# 섹션 관리 모델
class SectionType(str, Enum):
    """섹션 유형"""
    FEATURED = "추천"
    OFFICE = "오피스"
    RETAIL = "상가"
    BUILDING = "빌딩"
    RESIDENTIAL = "주거"
    LAND = "토지"
    URGENT = "급매"


class SectionBase(BaseModel):
    """섹션 기본 모델"""
    name: str = Field(..., description="섹션명")
    section_type: SectionType = Field(..., description="섹션 유형")
    description: Optional[str] = Field(None, description="섹션 설명")
    is_active: bool = Field(default=True, description="활성 여부")
    sort_order: int = Field(default=0, description="정렬 순서")


class SectionCreate(SectionBase):
    """섹션 생성 모델"""
    pass


class Section(SectionBase):
    """완전한 섹션 모델"""
    id: UUID = Field(default_factory=uuid4, description="섹션 ID")
    property_ids: List[UUID] = Field(default=[], description="매물 ID 목록")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="생성일시")
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="수정일시")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class SectionInDB(Section):
    """데이터베이스용 섹션 모델"""
    pass


class SectionResponse(Section):
    """API 응답용 섹션 모델"""
    property_count: int = Field(0, description="매물 수")
