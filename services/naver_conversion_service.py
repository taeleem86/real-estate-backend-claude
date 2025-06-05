"""
네이버 부동산 호환성 변환 전용 서비스
매물 데이터를 네이버 부동산 표준 형식으로 변환하는 전문 서비스
"""
import logging
from typing import Dict, Any, Tuple
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://backend-production-9d6f.up.railway.app"
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

class NaverConversionService:
    """네이버 부동산 호환성 변환 전용 서비스 클래스 (단순화 버전)"""

    def __init__(self):
        self.conversion_stats = {
            "total_conversions": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "last_conversion_time": None
        }

    def convert_property_to_naver(
            self, property_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, bool]]:
        """
        이미 네이버 표준 필드명을 사용하는 property_data를 검증 및 통계 처리만 수행
        """
        self.conversion_stats["total_conversions"] += 1
        try:
            validation_result = self.validate_naver_conversion(property_data)
            if validation_result.get("naver_compatible", False):
                self.conversion_stats["successful_conversions"] += 1
            else:
                self.conversion_stats["failed_conversions"] += 1
            self.conversion_stats["last_conversion_time"] = datetime.now(
            ).isoformat()
            logger.info(f"네이버 형식 검증 완료: {property_data.get('id', 'unknown')}")
            return property_data, validation_result
        except Exception as e:
            self.conversion_stats["failed_conversions"] += 1
            logger.error(f"네이버 형식 검증 실패: {e}")
            return {}, {"naver_compatible": False, "error": str(e)}

    def validate_naver_conversion(
            self, naver_data: Dict[str, Any]) -> Dict[str, bool]:
        """네이버 데이터 유효성 검증 (기존과 동일)"""
        validation_result = {
            "property_type_valid": False,
            "trade_type_valid": False,
            "required_fields_complete": False,
            "location_valid": False,
            "price_valid": False,
            "naver_compatible": False
        }
        try:
            property_type = naver_data.get("propertyType", "")
            validation_result["property_type_valid"] = property_type in [
                "LND", "APT", "OFC", "SHP", "ETC"]
            trade_type = naver_data.get("tradeType", "")
            validation_result["trade_type_valid"] = trade_type in [
                "A1", "A2", "B1"]
            location = naver_data.get("location", {})
            try:
                # 데이터 타입 안전 처리
                property_type = naver_data.get("propertyType", "")
                validation_result["property_type_valid"] = property_type in [
                    "LND", "APT", "OFC", "SHP", "ETC"]
                
                trade_type = naver_data.get("tradeType", "")
                validation_result["trade_type_valid"] = trade_type in [
                    "A1", "A2", "B1"]
                
                # location 필드를 안전하게 처리
                location = naver_data.get("location", {})
                if isinstance(location, dict):
                    validation_result["location_valid"] = (
                        location.get("address", "").strip() != "" or
                        location.get("city", "").strip() != ""
                    )
                else:
                    validation_result["location_valid"] = False
                
                # price 필드를 안전하게 처리  
                price = naver_data.get("price", {})
                if isinstance(price, dict):
                    validation_result["price_valid"] = (
                        price.get("salePrice", 0) > 0 or
                        price.get("deposit", 0) > 0 or
                        price.get("monthlyRent", 0) > 0
                    )
                elif isinstance(price, (int, float)):
                    # 숫자 타입의 경우 0보다 큰지만 체크
                    validation_result["price_valid"] = price > 0
                else:
                    validation_result["price_valid"] = False
                
                # description 필드를 안전하게 처리
                description = naver_data.get("description", {})
                if isinstance(description, dict):
                    validation_result["required_fields_complete"] = (
                        description.get("title", "").strip() != "" and
                        validation_result["location_valid"]
                    )
                else:
                    validation_result["required_fields_complete"] = (
                        validation_result["location_valid"]
                    )
                
                validation_result["naver_compatible"] = all([
                    validation_result["property_type_valid"],
                    validation_result["trade_type_valid"],
                    validation_result["required_fields_complete"]
                ])
            except Exception as e:
                # 내부 try 블록 예외 처리
                pass
        except Exception as e:
            # 최상위 try 블록 예외 처리
            pass
        return validation_result

    def get_conversion_statistics(self) -> Dict[str, Any]:
        stats = self.conversion_stats.copy()
        total = stats["total_conversions"]
        if total > 0:
            stats["success_rate"] = round(
                (stats["successful_conversions"] / total) * 100, 2)
            stats["failure_rate"] = round(
                (stats["failed_conversions"] / total) * 100, 2)
        else:
            stats["success_rate"] = 0.0
            stats["failure_rate"] = 0.0
        return stats

# 1. 목록 조회
res = requests.get(f"{BASE_URL}/api/v1/listings/", params={"skip": 0, "limit": 5}, headers=headers)
print(res.status_code, res.json())

# 2. 생성
listing_data = {
    "title": "테스트 리스팅",
    "description": "테스트 설명",
    "price": 1000000,
    "address": "서울시 강남구",
    "property_type": "APT",
    "transaction_type": "A1"
}
res = requests.post(f"{BASE_URL}/api/v1/listings/", json=listing_data, headers=headers)
print(res.status_code, res.json())
