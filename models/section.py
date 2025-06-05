from pydantic import validator

"""
홈페이지 섹션 관리 모델
매물을 홈페이지 섹션별로 분류하기 위한 모델 정의
"""
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4


class SectionStatus(str, Enum):
    """섹션 상태"""
    ACTIVE = "활성"
    INACTIVE = "비활성"
    MAINTENANCE = "점검중"


class Section(BaseModel):
    """홈페이지 섹션 모델"""
    id: UUID = Field(default_factory=uuid4, description="섹션 ID")
    name: str = Field(..., description="섹션 이름", min_length=1, max_length=100)
    description: Optional[str] = Field(
        None, description="섹션 설명", max_length=500)
    theme_tags: List[str] = Field(default=[], description="섹션 테마 태그")
    is_active: bool = Field(default=True, description="섹션 활성화 여부")
    order: int = Field(default=0, description="메인페이지 정렬 순서")
    display_title: Optional[str] = Field(None, description="화면 표시 제목")
    display_subtitle: Optional[str] = Field(None, description="화면 표시 부제목")
    max_listings: Optional[int] = Field(
        None, description="최대 리스팅 수 (제한 없으면 None)")  # Renamed
    auto_update: bool = Field(default=False, description="자동 업데이트 여부")

    # 자동 생성 필드
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="생성일자")
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="수정일자")

    # 통계 필드
    listing_count: int = Field(default=0, description="현재 리스팅 수")  # Renamed
    view_count: int = Field(default=0, description="조회수")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

    @validator('order')
    def validate_order(cls, v):
        """순서는 0 이상이어야 함"""
        if v < 0:
            raise ValueError('순서는 0 이상이어야 합니다')
        return v

    @validator('max_listings')  # Renamed validator
    def validate_max_listings(cls, v):  # Renamed validator method
        """최대 리스팅 수는 1 이상이어야 함"""  # Updated message
        if v is not None and v < 1:
            raise ValueError('최대 리스팅 수는 1 이상이어야 합니다')  # Updated message
        return v

    @validator('theme_tags')
    def validate_theme_tags(cls, v):
        """테마 태그는 최대 10개까지"""
        if len(v) > 10:
            raise ValueError('테마 태그는 최대 10개까지 설정할 수 있습니다')
        return v


class PropertySection(BaseModel):
    """매물-섹션 관계 테이블 (Many-to-Many)"""
    id: UUID = Field(default_factory=uuid4, description="관계 ID")
    property_id: UUID = Field(..., description="매물 ID")
    section_id: UUID = Field(..., description="섹션 ID")
    is_featured: bool = Field(default=False, description="추천 매물 여부")
    display_order: int = Field(default=0, description="섹션 내 표시 순서")
    added_at: datetime = Field(
        default_factory=datetime.now,
        description="추가일자")

    # 추가 메타데이터
    added_by: Optional[str] = Field(None, description="추가한 사용자")
    auto_added: bool = Field(default=False, description="자동 추가 여부")
    priority: int = Field(default=5, description="우선순위 (1-10, 높을수록 우선)")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

    @validator('priority')
    def validate_priority(cls, v):
        """우선순위는 1-10 사이"""
        if not 1 <= v <= 10:
            raise ValueError('우선순위는 1-10 사이의 값이어야 합니다')
        return v

    @validator('display_order')
    def validate_display_order(cls, v):
        """표시 순서는 0 이상"""
        if v < 0:
            raise ValueError('표시 순서는 0 이상이어야 합니다')
        return v


# 섹션 CRUD 모델들
class SectionCreate(BaseModel):
    """섹션 생성 모델"""
    name: str = Field(..., description="섹션 이름", min_length=1, max_length=100)
    description: Optional[str] = Field(
        None, description="섹션 설명", max_length=500)
    theme_tags: List[str] = Field(default=[], description="섹션 테마 태그")
    is_active: bool = Field(default=True, description="섹션 활성화 여부")
    order: int = Field(default=0, description="메인페이지 정렬 순서")
    display_title: Optional[str] = Field(None, description="화면 표시 제목")
    display_subtitle: Optional[str] = Field(None, description="화면 표시 부제목")
    max_listings: Optional[int] = Field(
        None, description="최대 리스팅 수")  # Renamed
    auto_update: bool = Field(default=False, description="자동 업데이트 여부")


class SectionUpdate(BaseModel):
    """섹션 수정 모델"""
    name: Optional[str] = Field(
        None,
        description="섹션 이름",
        min_length=1,
        max_length=100)
    description: Optional[str] = Field(
        None, description="섹션 설명", max_length=500)
    theme_tags: Optional[List[str]] = Field(None, description="섹션 테마 태그")
    is_active: Optional[bool] = Field(None, description="섹션 활성화 여부")
    order: Optional[int] = Field(None, description="메인페이지 정렬 순서")
    display_title: Optional[str] = Field(None, description="화면 표시 제목")
    display_subtitle: Optional[str] = Field(None, description="화면 표시 부제목")
    max_listings: Optional[int] = Field(
        None, description="최대 리스팅 수")  # Renamed
    auto_update: Optional[bool] = Field(None, description="자동 업데이트 여부")


class PropertySectionCreate(BaseModel):
    """매물-섹션 관계 생성 모델"""
    property_id: UUID = Field(..., description="매물 ID")
    section_id: UUID = Field(..., description="섹션 ID")
    is_featured: bool = Field(default=False, description="추천 매물 여부")
    display_order: int = Field(default=0, description="섹션 내 표시 순서")
    priority: int = Field(default=5, description="우선순위 (1-10)")
    added_by: Optional[str] = Field(None, description="추가한 사용자")


class PropertySectionUpdate(BaseModel):
    """매물-섹션 관계 수정 모델"""
    is_featured: Optional[bool] = Field(None, description="추천 매물 여부")
    display_order: Optional[int] = Field(None, description="섹션 내 표시 순서")
    priority: Optional[int] = Field(None, description="우선순위 (1-10)")


# 응답 모델들
class SectionResponse(Section):
    """섹션 응답 모델"""
    pass


class PropertySectionResponse(PropertySection):
    """매물-섹션 관계 응답 모델"""
    pass


class SectionWithListings(Section):  # Renamed class
    """리스팅 목록을 포함한 섹션 응답 모델"""  # Updated description
    listings: List[dict] = Field(
        default=[],
        description="섹션에 속한 리스팅 목록")  # Renamed field and updated description

    class Config:
        from_attributes = True


class SectionStats(BaseModel):
    """섹션 통계 모델"""
    section_id: UUID = Field(..., description="섹션 ID")
    section_name: str = Field(..., description="섹션 이름")
    total_listings: int = Field(default=0, description="총 리스팅 수")  # Renamed
    featured_listings: int = Field(
        default=0, description="추천 리스팅 수")  # Renamed
    view_count: int = Field(default=0, description="조회수")
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="마지막 업데이트")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


# 벌크 작업 모델들
class BulkPropertySectionCreate(BaseModel):
    """매물-섹션 관계 벌크 생성 모델"""
    section_id: UUID = Field(..., description="섹션 ID")
    property_ids: List[UUID] = Field(..., description="매물 ID 목록")
    is_featured: bool = Field(default=False, description="추천 매물 여부")
    priority: int = Field(default=5, description="우선순위")
    added_by: Optional[str] = Field(None, description="추가한 사용자")

    @validator('property_ids')
    def validate_property_ids(cls, v):
        """매물 ID 목록은 1개 이상 100개 이하"""
        if not v:
            raise ValueError('매물 ID 목록이 비어있습니다')
        if len(v) > 100:
            raise ValueError('한 번에 처리할 수 있는 매물은 최대 100개입니다')
        return v


class SectionOrderUpdate(BaseModel):
    """섹션 순서 변경 모델"""
    section_orders: List[dict] = Field(..., description="섹션 ID와 순서 목록")

    @validator('section_orders')
    def validate_section_orders(cls, v):
        """섹션 순서 목록 검증"""
        if not v:
            raise ValueError('섹션 순서 목록이 비어있습니다')

        required_keys = {'section_id', 'order'}
        for item in v:
            if not isinstance(item, dict):
                raise ValueError('섹션 순서 항목은 딕셔너리여야 합니다')
            if not required_keys.issubset(item.keys()):
                raise ValueError('section_id와 order 필드가 필요합니다')

        return v
