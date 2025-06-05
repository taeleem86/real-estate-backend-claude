"""
1단계 마이그레이션 통합 테스트
네이버 호환성, 섹션 관리 시스템, 데이터베이스 스키마 검증
"""
import pytest
import json
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any

# 테스트용 임포트 (실제 환경에서는 경로 조정 필요)
from models.property import Property, PropertyCreate, AddressInfo, AreaInfo, PriceInfo, PropertyDescription
from models.section import Section, SectionCreate, PropertySection, PropertySectionCreate
from models.naver_compatibility import NaverCompatibilityMixin


class TestNaverCompatibility:
    """네이버 호환성 테스트"""

    def test_property_model_naver_fields(self):
        """Property 모델이 네이버 표준 필드명을 사용하는지 확인"""
        # 네이버 표준 필드명으로 매물 생성
        address_info = AddressInfo(
            address="서울특별시 강남구 역삼동 123-45",
            city="서울특별시",
            district="강남구",
            coordinate_x=127.0276,
            coordinate_y=37.4979
        )

        area_info = AreaInfo(
            landArea=100.5,
            totalArea=85.3,
            exclusiveArea=75.2,
            buildingArea=80.1,
            commonArea=10.1,
            floorCount=5,
            basementCount=1
        )

        price_info = PriceInfo(
            salePrice=50000,
            deposit=10000,
            monthlyRent=300,
            exchangeValue=48000,
            maintenanceFee=15
        )

        property_desc = PropertyDescription(
            title="강남역 인근 오피스텔",
            features="교통 편리, 주차 가능",
            description="강남역 도보 5분 거리의 신축 오피스텔입니다."
        )

        # Property 생성 테스트
        property_data = PropertyCreate(
            property_type="사무실",
            transaction_type="매매",
            address_info=address_info,
            area_info=area_info,
            price_info=price_info,
            property_description=property_desc
        )

        # 네이버 표준 필드 확인
        # exclusive_area가 아닌 exclusiveArea
        assert hasattr(area_info, 'exclusiveArea')
        # total_floor_area가 아닌 totalArea
        assert hasattr(area_info, 'totalArea')
        assert hasattr(area_info, 'landArea')       # land_area가 아닌 landArea
        assert hasattr(price_info, 'salePrice')     # sale_price가 아닌 salePrice
        # monthly_rent가 아닌 monthlyRent
        assert hasattr(price_info, 'monthlyRent')

        print("✅ Property 모델이 네이버 표준 필드명을 사용합니다")

    def test_naver_format_conversion(self):
        """네이버 형식 변환 테스트"""
        # 테스트용 Property 인스턴스 생성 (NaverCompatibilityMixin 포함)
        class TestProperty(Property, NaverCompatibilityMixin):
            pass

        property_data = TestProperty(
            property_type="사무실",
            transaction_type="매매",
            address_info=AddressInfo(
                address="서울특별시 강남구 역삼동 123-45",
                city="서울특별시",
                district="강남구"
            ),
            area_info=AreaInfo(
                exclusiveArea=75.2,
                totalArea=85.3
            ),
            price_info=PriceInfo(
                salePrice=50000
            ),
            property_description=PropertyDescription(
                title="테스트 매물"
            )
        )

        # 네이버 형식으로 변환
        naver_format = property_data.to_naver_format()

        # 변환 결과 검증
        assert naver_format["propertyType"] == "OFC"  # 사무실 -> OFC
        assert naver_format["tradeType"] == "A1"      # 매매 -> A1
        assert naver_format["location"]["address"] == "서울특별시 강남구 역삼동 123-45"
        assert naver_format["area"]["exclusiveArea"] == 75.2
        assert naver_format["price"]["salePrice"] == 50000

        print("✅ 네이버 형식 변환이 정상 작동합니다")

    def test_naver_field_mapping(self):
        """네이버 필드 매핑 테스트"""
        from models.naver_compatibility import REALESTATE_TYPE_MAP, TRADE_TYPE_MAP

        # 매물 타입 매핑 확인
        assert REALESTATE_TYPE_MAP["토지"] == "LND"
        assert REALESTATE_TYPE_MAP["사무실"] == "OFC"
        assert REALESTATE_TYPE_MAP["상가"] == "SHP"

        # 거래 타입 매핑 확인
        assert TRADE_TYPE_MAP["매매"] == "A1"
        assert TRADE_TYPE_MAP["임대"] == "B1"
        assert TRADE_TYPE_MAP["교환"] == "A2"

        print("✅ 네이버 필드 매핑이 정확합니다")


class TestSectionManagement:
    """섹션 관리 시스템 테스트"""

    def test_section_model_creation(self):
        """섹션 모델 생성 테스트"""
        section_data = SectionCreate(
            name="추천 매물",
            description="관리자가 선별한 추천 매물",
            theme_tags=["추천", "베스트"],
            order=1,
            display_title="🏆 추천 매물",
            max_listings=10  # Renamed
        )

        section = Section(**section_data.dict())

        # 기본값 확인
        assert section.is_active
        assert section.auto_update == False
        assert section.listing_count == 0  # Renamed
        assert section.view_count == 0
        assert isinstance(section.id, type(uuid4()))

        print("✅ 섹션 모델 생성이 정상 작동합니다")

    def test_section_validation(self):
        """섹션 유효성 검증 테스트"""
        # 순서 음수 테스트
        with pytest.raises(ValueError, match="순서는 0 이상이어야 합니다"):
            Section(name="테스트", order=-1)

        # 최대 매물 수 0 테스트
        with pytest.raises(ValueError, match="최대 리스팅 수는 1 이상이어야 합니다"):  # Updated message
            Section(name="테스트", max_listings=0)  # Renamed

        # 테마 태그 개수 제한 테스트
        with pytest.raises(ValueError, match="테마 태그는 최대 10개까지"):
            Section(name="테스트", theme_tags=["tag"] * 11)

        print("✅ 섹션 유효성 검증이 정상 작동합니다")

    def test_property_section_relationship(self):
        """매물-섹션 관계 테스트"""
        property_section_data = PropertySectionCreate(
            property_id=uuid4(),
            section_id=uuid4(),
            is_featured=True,
            display_order=1,
            priority=8
        )

        property_section = PropertySection(**property_section_data.dict())

        # 기본값 확인
        assert property_section.auto_added == False
        assert isinstance(property_section.added_at, datetime)

        print("✅ 매물-섹션 관계 모델이 정상 작동합니다")

    def test_property_section_validation(self):
        """매물-섹션 관계 유효성 검증"""
        # 우선순위 범위 테스트
        with pytest.raises(ValueError, match="우선순위는 1-10 사이"):
            PropertySection(
                property_id=uuid4(),
                section_id=uuid4(),
                priority=11
            )

        # 표시 순서 음수 테스트
        with pytest.raises(ValueError, match="표시 순서는 0 이상"):
            PropertySection(
                property_id=uuid4(),
                section_id=uuid4(),
                display_order=-1
            )

        print("✅ 매물-섹션 관계 유효성 검증이 정상 작동합니다")


class TestDatabaseSchema:
    """데이터베이스 스키마 테스트 (모의 테스트)"""

    def test_schema_structure(self):
        """스키마 구조 테스트"""
        # 실제 DB 연결 없이 구조 검증
        expected_sections_fields = [
            'id', 'name', 'description', 'theme_tags', 'is_active',
            'order', 'display_title', 'display_subtitle', 'max_listings',  # Renamed
            'auto_update', 'created_at', 'updated_at', 'listing_count', 'view_count'  # Renamed
        ]

        expected_property_sections_fields = [
            'id', 'property_id', 'section_id', 'is_featured', 'display_order',
            'added_at', 'added_by', 'auto_added', 'priority'
        ]

        # Section 모델 필드 확인
        section = Section(name="테스트")
        section_fields = list(section.__fields__.keys())

        for field in expected_sections_fields:
            assert field in section_fields, f"섹션 모델에 {field} 필드가 없습니다"

        # PropertySection 모델 필드 확인
        property_section = PropertySection(
            property_id=uuid4(),
            section_id=uuid4()
        )
        ps_fields = list(property_section.__fields__.keys())

        for field in expected_property_sections_fields:
            assert field in ps_fields, f"매물-섹션 모델에 {field} 필드가 없습니다"

        print("✅ 데이터베이스 스키마 구조가 올바릅니다")

    def test_property_naver_fields(self):
        """Property 테이블 네이버 필드 확인"""
        expected_naver_fields = [
            'address_info', 'area_info', 'price_info', 'owner_info',
            'building_register_info', 'land_register_info',
            'manual_data', 'ocr_data', 'api_data', 'naver_info'
        ]

        property_instance = Property(
            property_type="토지",
            transaction_type="매매",
            address_info=AddressInfo(
                address="테스트",
                city="테스트",
                district="테스트"),
            area_info=AreaInfo(),
            price_info=PriceInfo(),
            property_description=PropertyDescription(
                title="테스트"))

        property_fields = list(property_instance.__fields__.keys())

        for field in expected_naver_fields:
            assert field in property_fields, f"Property 모델에 {field} 필드가 없습니다"

        print("✅ Property 모델에 네이버 호환 필드가 모두 있습니다")


class TestIntegrationFlow:
    """통합 플로우 테스트"""

    def test_end_to_end_flow(self):
        """End-to-End 플로우 테스트"""
        # 1. 매물 생성 (네이버 표준 필드 사용)
        property_data = Property(
            property_type="사무실",
            transaction_type="매매",
            address_info=AddressInfo(
                address="서울특별시 강남구 역삼동 123-45",
                city="서울특별시",
                district="강남구"
            ),
            area_info=AreaInfo(exclusiveArea=75.2),
            price_info=PriceInfo(salePrice=50000),
            property_description=PropertyDescription(title="테스트 매물")
        )

        # 2. 섹션 생성
        section = Section(
            name="추천 매물",
            description="관리자 추천",
            order=1
        )

        # 3. 매물-섹션 관계 생성
        property_section = PropertySection(
            property_id=property_data.id,
            section_id=section.id,
            is_featured=True,
            priority=9
        )

        # 4. 네이버 형식 변환 테스트
        class TestPropertyWithMixin(Property, NaverCompatibilityMixin):
            pass

        test_property = TestPropertyWithMixin(**property_data.dict())
        naver_format = test_property.to_naver_format()

        # 5. 검증
        assert naver_format["propertyType"] == "OFC"
        assert naver_format["location"]["address"] == "서울특별시 강남구 역삼동 123-45"
        assert property_section.is_featured
        assert section.name == "추천 매물"

        print("✅ End-to-End 플로우가 정상 작동합니다")

    def test_data_flow_integrity(self):
        """데이터 플로우 무결성 테스트"""
        # 매물 ID 생성
        property_id = uuid4()
        section_id = uuid4()

        # Property 생성
        property_data = Property(
            id=property_id,
            property_type="상가",
            transaction_type="임대",
            address_info=AddressInfo(
                address="테스트",
                city="테스트",
                district="테스트"),
            area_info=AreaInfo(),
            price_info=PriceInfo(),
            property_description=PropertyDescription(
                title="테스트"))

        # Section 생성
        section = Section(
            id=section_id,
            name="신규 매물"
        )

        # PropertySection 관계 생성
        relationship = PropertySection(
            property_id=property_id,
            section_id=section_id
        )

        # ID 일관성 확인
        assert relationship.property_id == property_data.id
        assert relationship.section_id == section.id

        print("✅ 데이터 플로우 무결성이 보장됩니다")


def run_all_tests():
    """모든 테스트 실행"""
    print("🧪 1단계 마이그레이션 통합 테스트 시작")
    print("=" * 50)

    # 네이버 호환성 테스트
    naver_tests = TestNaverCompatibility()
    naver_tests.test_property_model_naver_fields()
    naver_tests.test_naver_format_conversion()
    naver_tests.test_naver_field_mapping()

    # 섹션 관리 테스트
    section_tests = TestSectionManagement()
    section_tests.test_section_model_creation()
    section_tests.test_section_validation()
    section_tests.test_property_section_relationship()
    section_tests.test_property_section_validation()

    # 데이터베이스 스키마 테스트
    db_tests = TestDatabaseSchema()
    db_tests.test_schema_structure()
    db_tests.test_property_naver_fields()

    # 통합 플로우 테스트
    integration_tests = TestIntegrationFlow()
    integration_tests.test_end_to_end_flow()
    integration_tests.test_data_flow_integrity()

    print("=" * 50)
    print("🎉 모든 테스트 통과! 1단계 마이그레이션 완료")

    # 테스트 결과 요약
    test_summary = {
        "migration_status": "COMPLETED",
        "naver_compatibility": "PASSED",
        "section_management": "PASSED",
        "database_schema": "PASSED",
        "integration_flow": "PASSED",
        "completion_time": datetime.now().isoformat(),
        "next_step": "2단계 PyQt 데스크톱 앱 개발 시작"
    }

    return test_summary


if __name__ == "__main__":
    # 실제 테스트 실행 시 사용
    # pytest.main([__file__, "-v"])

    # 간단한 테스트 실행
    try:
        result = run_all_tests()
        print(
            f"\n📊 테스트 결과: {
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        print("🔧 모델 import 경로를 실제 환경에 맞게 조정하세요")
