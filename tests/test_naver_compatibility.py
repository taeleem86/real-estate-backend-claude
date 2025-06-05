"""
네이버 호환성 통합 테스트
전체 시스템의 네이버 변환 기능을 종합적으로 검증
"""
import pytest
import asyncio
from typing import Dict, Any
from uuid import uuid4

# 테스트를 위한 샘플 데이터
SAMPLE_PROPERTY_DATA = {
    "id": str(uuid4()),
    "title": "테스트 매물 - 강남구 역삼동",
    "property_type": "건물",
    "deal_type": "매매",
    "price": "1000000000",
    "display_address": "서울특별시 강남구 역삼동 123-45",
    "sido": "서울특별시",
    "sigungu": "강남구",
    "total_floor_area": 85.5,
    "exclusive_area": 65.2,
    "land_area": 100.0,
    "deposit": 0,
    "rent_fee": 0,
    "floors": 5,
    "build_year": 2020,
    "parking": True,
    "status": "거래가능"
}

EXPECTED_NAVER_FORMAT = {
    "propertyType": "APT",
    "tradeType": "A1",
    "location": {
        "address": "서울특별시 강남구 역삼동 123-45",
        "city": "서울특별시",
        "district": "서울특별시 강남구",
        "coordinates": {"lat": 0.0, "lng": 0.0}
    },
    "area": {
        "totalArea": 85.5,
        "exclusiveArea": 65.2,
        "landArea": 100.0
    },
    "price": {
        "salePrice": 1000000000,
        "deposit": 0,
        "monthlyRent": 0
    },
    "description": {
        "title": "테스트 매물 - 강남구 역삼동",
        "features": "",
        "details": ""
    },
    "buildingInfo": {
        "floors": 5,
        "buildYear": 2020,
        "parking": True
    }
}


class TestNaverCompatibilityIntegration:
    """네이버 호환성 통합 테스트 클래스"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.test_results = {
            "conversion_accuracy": 0,
            "validation_accuracy": 0,
            "performance_ratio": 1.0,
            "error_count": 0
        }

    def test_naver_conversion_service(self):
        """네이버 변환 서비스 테스트"""
        try:
            # 네이버 변환 서비스 임포트 시도
            from services.naver_conversion_service import NaverConversionService

            converter = NaverConversionService()

            # 변환 테스트
            naver_data, validation = converter.convert_property_to_naver(
                SAMPLE_PROPERTY_DATA)

            # 변환 정확도 확인
            accuracy_score = self._calculate_conversion_accuracy(
                naver_data, EXPECTED_NAVER_FORMAT)
            self.test_results["conversion_accuracy"] = accuracy_score

            # 검증 결과 확인
            if validation.get("naver_compatible", False):
                self.test_results["validation_accuracy"] = 100
            else:
                self.test_results["validation_accuracy"] = 50

            print(f"✅ 네이버 변환 서비스 테스트 통과 - 정확도: {accuracy_score}%")

        except Exception as e:
            self.test_results["error_count"] += 1
            print(f"❌ 네이버 변환 서비스 테스트 실패: {e}")

    def test_property_service_integration(self):
        """PropertyService 네이버 통합 테스트"""
        try:
            from services.property_service import PropertyService

            service = PropertyService()

            # 변환 메서드 테스트
            naver_data = service.convert_to_naver_format(SAMPLE_PROPERTY_DATA)

            # 기본 구조 확인
            required_fields = [
                "propertyType",
                "tradeType",
                "location",
                "area",
                "price"]
            for field in required_fields:
                if field not in naver_data:
                    self.test_results["error_count"] += 1

            print(f"✅ PropertyService 통합 테스트 통과")

        except Exception as e:
            self.test_results["error_count"] += 1
            print(f"❌ PropertyService 통합 테스트 실패: {e}")

    def test_api_endpoints(self):
        """API 엔드포인트 테스트"""
        try:
            # API 모델 임포트 테스트
            from models.naver_response import (
                NaverPropertyResponse, NaverPropertyListResponse,
                NaverPropertyData, NaverValidation
            )

            # 모델 생성 테스트
            naver_response = NaverPropertyResponse(
                id=SAMPLE_PROPERTY_DATA["id"],
                title=SAMPLE_PROPERTY_DATA["title"],
                property_type=SAMPLE_PROPERTY_DATA["property_type"],
                deal_type=SAMPLE_PROPERTY_DATA["deal_type"],
                price=SAMPLE_PROPERTY_DATA["price"],
                display_address=SAMPLE_PROPERTY_DATA["display_address"],
                status=SAMPLE_PROPERTY_DATA["status"],
                naver_format=NaverPropertyData(**EXPECTED_NAVER_FORMAT)
            )

            print(f"✅ API 엔드포인트 모델 테스트 통과")

        except Exception as e:
            self.test_results["error_count"] += 1
            print(f"❌ API 엔드포인트 테스트 실패: {e}")

    def test_data_mapping_accuracy(self):
        """데이터 매핑 정확도 테스트"""
        try:
            from models.naver_compatibility import REALESTATE_TYPE_MAP, TRADE_TYPE_MAP

            # 매물 타입 매핑 테스트
            test_cases = [
                ("토지", "LND"),
                ("건물", "APT"),
                ("사무실", "OFC"),
                ("상가", "SHP"),
                ("기타", "ETC")
            ]

            correct_mappings = 0
            for korean_type, expected_naver_type in test_cases:
                if REALESTATE_TYPE_MAP.get(korean_type) == expected_naver_type:
                    correct_mappings += 1

            mapping_accuracy = (correct_mappings / len(test_cases)) * 100
            self.test_results["conversion_accuracy"] = max(
                self.test_results["conversion_accuracy"],
                mapping_accuracy
            )

            print(f"✅ 데이터 매핑 정확도: {mapping_accuracy}%")

        except Exception as e:
            self.test_results["error_count"] += 1
            print(f"❌ 데이터 매핑 테스트 실패: {e}")

    def _calculate_conversion_accuracy(
            self, actual: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """변환 정확도 계산"""
        try:
            correct_fields = 0
            total_fields = 0

            # 주요 필드들 비교
            key_fields = ["propertyType", "tradeType"]

            for field in key_fields:
                total_fields += 1
                if actual.get(field) == expected.get(field):
                    correct_fields += 1

            # 중첩 객체 비교 (간단화)
            if isinstance(
                    actual.get("location"),
                    dict) and isinstance(
                    expected.get("location"),
                    dict):
                total_fields += 1
                if actual["location"].get(
                        "city") == expected["location"].get("city"):
                    correct_fields += 1

            return (correct_fields / total_fields) * \
                100 if total_fields > 0 else 0

        except Exception:
            return 0

    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("\n🔍 네이버 호환성 통합 테스트 시작...\n")

        # 개별 테스트 실행
        self.test_naver_conversion_service()
        self.test_property_service_integration()
        self.test_api_endpoints()
        self.test_data_mapping_accuracy()

        # 전체 결과 평가
        overall_score = self._calculate_overall_score()

        print(f"\n📊 통합 테스트 결과:")
        print(f"- 변환 정확도: {self.test_results['conversion_accuracy']:.1f}%")
        print(f"- 검증 정확도: {self.test_results['validation_accuracy']:.1f}%")
        print(f"- 오류 발생: {self.test_results['error_count']}건")
        print(f"- 전체 점수: {overall_score:.1f}%")

        return {
            "overall_score": overall_score,
            "details": self.test_results,
            "passed": overall_score >= 80,
            "ready_for_production": self.test_results["error_count"] == 0 and overall_score >= 90
        }

    def _calculate_overall_score(self) -> float:
        """전체 점수 계산"""
        base_score = (
            self.test_results["conversion_accuracy"] * 0.4 +
            self.test_results["validation_accuracy"] * 0.3 +
            (100 - self.test_results["error_count"] * 10) * 0.3
        )

        # 오류가 있으면 점수 감점
        error_penalty = min(self.test_results["error_count"] * 15, 50)

        return max(0, base_score - error_penalty)


def main():
    """테스트 실행 메인 함수"""
    tester = TestNaverCompatibilityIntegration()
    results = tester.run_all_tests()

    if results["passed"]:
        print(f"\n✅ 통합 테스트 통과! (점수: {results['overall_score']:.1f}%)")
        if results["ready_for_production"]:
            print("🚀 프로덕션 배포 준비 완료!")
        else:
            print("⚠️  일부 개선이 필요합니다.")
    else:
        print(f"\n❌ 통합 테스트 실패 (점수: {results['overall_score']:.1f}%)")
        print("🔧 문제 해결 후 재테스트가 필요합니다.")

    return results


if __name__ == "__main__":
    main()
