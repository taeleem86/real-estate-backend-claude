"""
네이버 부동산 호환성 모듈
네이버 부동산 표준 코드 체계와 호환되는 데이터 변환 기능을 제공합니다.
"""
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel
from .property import PropertyType, TransactionType, Property


# 네이버 부동산 표준 코드 매핑
REALESTATE_TYPE_MAP = {
    # 우리 시스템 -> 네이버 코드
    "토지": "LND",  # 토지
    "건물": "APT",  # 건물 (일반적으로 아파트로 분류)
    "사무실": "OFC",  # 오피스
    "상가": "SHP",  # 상가
    "주거": "APT",  # 주거용 건물
    "기타": "ETC"   # 기타
}

# 역방향 매핑
NAVER_TO_PROPERTY_TYPE = {v: k for k, v in REALESTATE_TYPE_MAP.items()}

TRADE_TYPE_MAP = {
    # 우리 시스템 -> 네이버 코드
    "매매": "A1",    # 매매
    "교환": "A2",    # 교환
    "임대": "B1"     # 임대 (전세/월세 통합)
}

# 역방향 매핑
NAVER_TO_TRADE_TYPE = {v: k for k, v in TRADE_TYPE_MAP.items()}

# 네이버 부동산 표준 구조 템플릿 (이미 표준 필드명 사용)
NAVER_PROPERTY_SCHEMA = {
    "propertyType": "",      # 부동산 유형 코드
    "tradeType": "",         # 거래 유형 코드
    "location": {             # 위치 정보
        "address": "",
        "city": "",
        "district": "",
        "coordinates": {
            "lat": 0.0,
            "lng": 0.0
        }
    },
    "area": {                 # 면적 정보 (네이버 표준 필드명)
        "totalArea": 0.0,
        "exclusiveArea": 0.0,
        "landArea": 0.0,
        "buildingArea": 0.0,
        "commonArea": 0.0,
        "floorCount": 0,
        "basementCount": 0
    },
    "price": {                # 가격 정보 (네이버 표준 필드명)
        "salePrice": 0,
        "deposit": 0,
        "monthlyRent": 0,
        "exchangeValue": 0,
        "maintenanceFee": 0
    },
    "description": {          # 설명 정보
        "title": "",
        "features": "",
        "details": ""
    },
    "buildingInfo": {         # 건물 정보 (선택적)
        "floors": 0,
        "buildYear": 0,
        "parking": False
    }
}


class NaverCompatibilityMixin:
    """네이버 부동산 호환성을 위한 믹스인 클래스"""

    def to_naver_format(self) -> Dict[str, Any]:
        """현재 매물 정보를 네이버 부동산 표준 형식으로 변환
        Property 모델이 이미 네이버 표준 필드명을 사용하므로 단순 매핑

        Returns:
            Dict[str, Any]: 네이버 표준 형식의 매물 정보
        """
        naver_data = NAVER_PROPERTY_SCHEMA.copy()

        try:
            # 1. 기본 매물 정보 변환
            naver_data["propertyType"] = REALESTATE_TYPE_MAP.get(
                self.property_type.value, "ETC"
            )
            naver_data["tradeType"] = TRADE_TYPE_MAP.get(
                self.transaction_type.value, "A1"
            )

            # 2. 위치 정보 변환 (이미 네이버 표준 필드명 사용)
            if hasattr(self, 'address_info') and self.address_info:
                naver_data["location"].update({
                    "address": self.address_info.address,  # 이미 표준 필드명
                    "city": self.address_info.city,        # 이미 표준 필드명
                    "district": self.address_info.district,  # 이미 표준 필드명
                    "coordinates": {
                        "lat": self.address_info.coordinate_y or 0.0,
                        "lng": self.address_info.coordinate_x or 0.0
                    }
                })

            # 3. 면적 정보 변환 (이미 네이버 표준 필드명 사용)
            if hasattr(self, 'area_info') and self.area_info:
                naver_data["area"].update({
                    "totalArea": self.area_info.totalArea or 0.0,          # 이미 표준 필드명
                    "exclusiveArea": self.area_info.exclusiveArea or 0.0,  # 이미 표준 필드명
                    "landArea": self.area_info.landArea or 0.0,            # 이미 표준 필드명
                    "buildingArea": self.area_info.buildingArea or 0.0,    # 이미 표준 필드명
                    "commonArea": self.area_info.commonArea or 0.0,        # 이미 표준 필드명
                    "floorCount": self.area_info.floorCount or 0,          # 이미 표준 필드명
                    "basementCount": self.area_info.basementCount or 0     # 이미 표준 필드명
                })

            # 4. 가격 정보 변환 (이미 네이버 표준 필드명 사용)
            if hasattr(self, 'price_info') and self.price_info:
                naver_data["price"].update({
                    "salePrice": self.price_info.salePrice or 0,            # 이미 표준 필드명
                    "deposit": self.price_info.deposit or 0,                # 이미 표준 필드명
                    "monthlyRent": self.price_info.monthlyRent or 0,        # 이미 표준 필드명
                    "exchangeValue": self.price_info.exchangeValue or 0,    # 이미 표준 필드명
                    "maintenanceFee": self.price_info.maintenanceFee or 0   # 이미 표준 필드명
                })

            # 5. 설명 정보 변환
            if hasattr(
                    self,
                    'property_description') and self.property_description:
                naver_data["description"].update({
                    "title": self.property_description.title,
                    "features": self.property_description.features or "",
                    "details": self.property_description.description or ""
                })

            # 6. 건물 정보 변환 (선택적)
            if hasattr(self, 'area_info') and self.area_info:
                naver_data["buildingInfo"].update({
                    "floors": self.area_info.floorCount or 0,   # 이미 표준 필드명
                    "buildYear": 0,  # 건축물대장에서 가져올 수 있음
                    "parking": False  # 건축물대장에서 가져올 수 있음
                })

            # 7. 건축물대장 정보가 있다면 추가 정보 활용
            if hasattr(
                    self,
                    'building_register_info') and self.building_register_info:
                if self.building_register_info.build_year:
                    try:
                        naver_data["buildingInfo"]["buildYear"] = int(
                            self.building_register_info.build_year)
                    except BaseException:
                        pass

                if self.building_register_info.parking_count:
                    naver_data["buildingInfo"]["parking"] = self.building_register_info.parking_count > 0

        except Exception as e:
            # 변환 실패시 기본 구조 반환
            print(f"네이버 형식 변환 중 오류 발생: {e}")

        return naver_data

    @classmethod
    def from_naver_format(cls, naver_data: Dict[str, Any]) -> Dict[str, Any]:
        """네이버 부동산 형식의 데이터를 우리 시스템 형식으로 변환
        Property 모델이 이미 네이버 표준 필드명을 사용하므로 단순 매핑

        Args:
            naver_data: 네이버 표준 형식의 매물 정보

        Returns:
            Dict[str, Any]: 우리 시스템 형식의 매물 정보
        """
        property_data = {}

        try:
            # 1. 매물 타입 변환
            property_data["property_type"] = NAVER_TO_PROPERTY_TYPE.get(
                naver_data.get("propertyType", "ETC"), "기타"
            )

            # 2. 거래 타입 변환
            property_data["transaction_type"] = NAVER_TO_TRADE_TYPE.get(
                naver_data.get("tradeType", "A1"), "매매"
            )

            # 3. 주소 정보 변환 (이미 네이버 표준 필드명 사용)
            location = naver_data.get("location", {})
            property_data["address_info"] = {
                "address": location.get("address", ""),           # 이미 표준 필드명
                "city": location.get("city", ""),                 # 이미 표준 필드명
                "district": location.get("district", ""),         # 이미 표준 필드명
                "coordinate_x": location.get("coordinates", {}).get("lng", None),
                "coordinate_y": location.get("coordinates", {}).get("lat", None)
            }

            # 4. 면적 정보 변환 (이미 네이버 표준 필드명 사용)
            area = naver_data.get("area", {})
            property_data["area_info"] = {
                "totalArea": area.get("totalArea"),           # 이미 표준 필드명
                "exclusiveArea": area.get("exclusiveArea"),   # 이미 표준 필드명
                "landArea": area.get("landArea"),             # 이미 표준 필드명
                "buildingArea": area.get("buildingArea"),     # 이미 표준 필드명
                "commonArea": area.get("commonArea"),         # 이미 표준 필드명
                "floorCount": area.get("floorCount"),         # 이미 표준 필드명
                "basementCount": area.get("basementCount")    # 이미 표준 필드명
            }

            # 5. 가격 정보 변환 (이미 네이버 표준 필드명 사용)
            price = naver_data.get("price", {})
            property_data["price_info"] = {
                "salePrice": price.get("salePrice"),           # 이미 표준 필드명
                "deposit": price.get("deposit"),               # 이미 표준 필드명
                "monthlyRent": price.get("monthlyRent"),       # 이미 표준 필드명
                "exchangeValue": price.get("exchangeValue"),   # 이미 표준 필드명
                "maintenanceFee": price.get("maintenanceFee")  # 이미 표준 필드명
            }

            # 6. 설명 정보 변환
            description = naver_data.get("description", {})
            property_data["property_description"] = {
                "title": description.get("title", ""),
                "features": description.get("features"),
                "description": description.get("details")
            }

        except Exception as e:
            print(f"네이버 형식에서 변환 중 오류 발생: {e}")

        return property_data

    def validate_naver_codes(self) -> Dict[str, bool]:
        """네이버 코드 체계로 변환 가능한지 검증

        Returns:
            Dict[str, bool]: 각 필드별 변환 가능 여부
        """
        validation_result = {
            "property_type_valid": False,
            "transaction_type_valid": False,
            "required_fields_complete": False,
            "naver_compatible": False
        }

        try:
            # 1. 매물 타입 검증
            if hasattr(self, 'property_type') and self.property_type:
                validation_result["property_type_valid"] = (
                    self.property_type.value in REALESTATE_TYPE_MAP
                )

            # 2. 거래 타입 검증
            if hasattr(self, 'transaction_type') and self.transaction_type:
                validation_result["transaction_type_valid"] = (
                    self.transaction_type.value in TRADE_TYPE_MAP
                )

            # 3. 필수 필드 완성도 검증
            required_fields_check = all([
                hasattr(self, 'property_description') and self.property_description and self.property_description.title,
                hasattr(self, 'address_info') and self.address_info and self.address_info.address,
                hasattr(self, 'price_info') and self.price_info
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


class NaverPropertyResponse(BaseModel):
    """네이버 호환 API 응답 모델"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, bool]] = None
    message: str = "OK"

    class Config:
        json_encoders = {
            dict: lambda v: v
        }
