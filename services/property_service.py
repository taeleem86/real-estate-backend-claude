"""
Property Service - 실제 Supabase 연동 버전
기존 listings 테이블 구조에 맞게 수정
네이버 부동산 호환 기능 통합
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from supabase import create_client, Client
from core.config import settings
from models.property import PropertyCreate, PropertyUpdate

# 네이버 변환 서비스 import
try:
    from .naver_conversion_service import NaverConversionService
except ImportError:
    NaverConversionService = None

# 네이버 호환성 모듈 import
try:
    from ..models.naver_compatibility import (
        REALESTATE_TYPE_MAP, TRADE_TYPE_MAP,
        NAVER_TO_PROPERTY_TYPE, NAVER_TO_TRADE_TYPE,
        NAVER_PROPERTY_SCHEMA
    )
except ImportError:
    # import 실패 시 기본값 설정
    REALESTATE_TYPE_MAP = {}
    TRADE_TYPE_MAP = {}
    NAVER_TO_PROPERTY_TYPE = {}
    NAVER_TO_TRADE_TYPE = {}
    NAVER_PROPERTY_SCHEMA = {}

logger = logging.getLogger(__name__)


class PropertyService:
    """리스팅 관리 서비스 - Supabase 실제 연동 + 네이버 호환"""

    def __init__(self, supabase_client=None):
        if supabase_client:
            self.client = supabase_client
        else:
            if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
                logger.error(
                    "Supabase URL 또는 Anon Key가 설정되지 않았습니다. PropertyService 초기화 실패.")
                self.client = None
            else:
                # SERVICE_ROLE_KEY가 있으면 우선 사용 (RLS 우회)
                supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
                self.client = create_client(
                    settings.SUPABASE_URL,
                    supabase_key
                )
        self.naver_converter = NaverConversionService() if NaverConversionService else None

    async def create_listing(
            self,
            listing_data_in: PropertyCreate) -> Optional[Dict]:
        """새로운 리스팅 생성 - 기존 테이블 구조 사용 + 네이버 정보 자동 생성"""
        try:
            logger.info(
                f"리스팅 생성 시작: {listing_data_in.property_description.title}")
            db_listing_payload = {
                "title": listing_data_in.property_description.title,
                "deal_type": listing_data_in.transaction_type,
                "property_type": listing_data_in.property_type,
                "price": str(
                                        listing_data_in.price_info.salePrice) if listing_data_in.price_info.salePrice else None,
                "display_address": listing_data_in.address_info.address,
                "sido": listing_data_in.address_info.city,
                "sigungu": listing_data_in.address_info.district,
                "eupmyeondong": "",
                "address": listing_data_in.address_info.address,
                "land_area": listing_data_in.area_info.landArea if listing_data_in.area_info.landArea else None,
                "building_area": listing_data_in.area_info.buildingArea if listing_data_in.area_info.buildingArea else None,
                "total_floor_area": listing_data_in.area_info.totalArea if listing_data_in.area_info.totalArea else None,
                "exclusive_area": listing_data_in.area_info.exclusiveArea if listing_data_in.area_info.exclusiveArea else None,
                "deposit": listing_data_in.price_info.deposit if listing_data_in.price_info.deposit else None,
                "rent_fee": listing_data_in.price_info.monthlyRent if listing_data_in.price_info.monthlyRent else None,
                "status": "거래가능"}
            result = self.client.table("listings").insert(
                db_listing_payload).execute()
            if result.data:
                created_listing = result.data[0]
                logger.info(f"리스팅 생성 완료: {created_listing['id']}")
                try:
                    naver_data = self.convert_to_naver_format(created_listing)
                    if naver_data:
                        listing_naver_record = {
                            "id": created_listing['id'],
                            "property_number": f"P{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            "property_type": listing_data_in.property_type,
                            "transaction_type": listing_data_in.transaction_type,
                            "naver_info": naver_data,
                            "status": "pending"}
                        self.client.table("listings").insert(
                            listing_naver_record).execute()
                        logger.info(
                            f"네이버 정보 자동 생성 완료: {created_listing['id']}")
                except Exception as e:
                    logger.warning(f"네이버 정보 자동 생성 실패: {e}")
                return created_listing
            else:
                logger.error("리스팅 생성 실패: 응답 데이터 없음")
                return None
        except Exception as e:
            logger.error(f"리스팅 생성 실패: {e}")
            return None

    async def get_listing(self, listing_id: UUID) -> Optional[Dict]:
        """리스팅 상세 조회"""
        try:
            result = self.client.table("listings").select(
                "*").eq("id", str(listing_id)).execute()
            if result.data:
                listing_obj = result.data[0]
                logger.info(f"리스팅 조회 완료: {listing_obj['id']}")
                return listing_obj
            else:
                logger.warning(f"리스팅을 찾을 수 없음: {listing_id}")
                return None
        except Exception as e:
            logger.error(f"리스팅 조회 실패: {e}")
            return None

    async def get_listings(
            self,
            skip: int = 0,
            limit: int = 100,
            **filters) -> List[Dict]:
        """리스팅 목록 조회"""
        try:
            query = self.client.table("listings").select("*")
            if filters.get("status"):
                query = query.eq("status", filters["status"])
            if filters.get("property_type"):
                query = query.eq("property_type", filters["property_type"])
            if filters.get("transaction_type"):
                query = query.eq("deal_type", filters["transaction_type"])
            result = query.range(skip, skip + limit - 1).execute()
            if result.data:
                listings = result.data
                logger.info(f"리스팅 목록 조회 완료: {len(listings)}건")
                return listings
            else:
                logger.info("리스팅 목록이 비어있습니다")
                return []
        except Exception as e:
            logger.error(f"리스팅 목록 조회 실패: {e}")
            return []

    async def update_listing(
            self,
            listing_id: UUID,
            listing_data_in: PropertyUpdate) -> Optional[Dict]:
        """리스팅 정보 수정 + 네이버 정보 자동 업데이트"""
        try:
            update_data = {}

            # property_description 처리
            if hasattr(
                    listing_data_in,
                    'property_description') and listing_data_in.property_description:
                if listing_data_in.property_description.title:
                    update_data["title"] = listing_data_in.property_description.title

            # title 직접 처리
            if hasattr(listing_data_in, 'title') and listing_data_in.title:
                update_data["title"] = listing_data_in.title

            # price_info 처리
            if hasattr(
                    listing_data_in,
                    'price_info') and listing_data_in.price_info:
                if listing_data_in.price_info.salePrice:
                    update_data["price"] = str(
                        listing_data_in.price_info.salePrice)

            # address_info 처리 (추가)
            if hasattr(
                    listing_data_in,
                    'address_info') and listing_data_in.address_info:
                if listing_data_in.address_info.address:
                    update_data["address"] = listing_data_in.address_info.address
                if listing_data_in.address_info.city:
                    update_data["city"] = listing_data_in.address_info.city
                if listing_data_in.address_info.district:
                    update_data["district"] = listing_data_in.address_info.district

            # property_type 처리 (추가)
            if hasattr(
                    listing_data_in,
                    'property_type') and listing_data_in.property_type:
                update_data["property_type"] = listing_data_in.property_type

            # transaction_type 처리 (추가)
            if hasattr(
                    listing_data_in,
                    'transaction_type') and listing_data_in.transaction_type:
                update_data["deal_type"] = listing_data_in.transaction_type

            # status 처리
            if hasattr(listing_data_in, 'status') and listing_data_in.status:
                status_mapping = {
                    "active": "거래가능",
                    "pending": "거래가능",
                    "sold": "거래완료"
                }
                update_data["status"] = status_mapping.get(
                    listing_data_in.status, "거래가능")

            if not update_data:
                logger.warning("수정할 데이터가 없습니다")
                return None
            result = self.client.table("listings").update(
                update_data).eq("id", str(listing_id)).select("*").execute()
            if result.data and len(result.data) > 0:
                updated_listing = result.data[0]
                logger.info(f"리스팅 수정 완료: {updated_listing['id']}")
                try:
                    await self.sync_naver_info(listing_id)
                except Exception as e:
                    logger.warning(f"네이버 정보 동기화 실패: {e}")
                return updated_listing
            else:
                logger.error(f"리스팅 수정 실패: 응답 데이터 없음. Result: {result.data}, Count: {getattr(result, 'count', 'N/A')}")
                return None
        except Exception as e:
            logger.error(f"리스팅 수정 실패: {e}")
            return None

    async def delete_listing(self, listing_id: UUID) -> bool:
        """리스팅 삭제"""
        try:
            result = self.client.table("listings").delete().eq(
                "id", str(listing_id)).execute()
            if result.data:
                logger.info(f"리스팅 삭제 완료: {listing_id}")
                return True
            else:
                logger.error("리스팅 삭제 실패: 대상 리스팅 없음")
                return False
        except Exception as e:
            logger.error(f"리스팅 삭제 실패: {e}")
            return False

    async def search_listings(
            self,
            query: str,
            skip: int = 0,
            limit: int = 50) -> List[Dict]:
        """리스팅 검색"""
        try:
            result = self.client.table("listings").select("*").or_(
                f"title.ilike.%{query}%,display_address.ilike.%{query}%,address.ilike.%{query}%"
            ).range(skip, skip + limit - 1).execute()
            if result.data:
                listings = result.data
                logger.info(f"'{query}' 검색 결과: {len(listings)}건")
                return listings
            else:
                logger.info(f"'{query}' 검색 결과가 없습니다")
                return []
        except Exception as e:
            logger.error(f"리스팅 검색 실패: {e}")
            return []

    async def get_listing_statistics(self) -> Dict[str, Any]:
        """리스팅 통계 정보 조회"""
        try:
            total_result = self.client.table("listings").select(
                "id", count="exact").execute()
            total_count = total_result.count if total_result.count else 0
            status_result = self.client.table(
                "listings").select("status").execute()
            status_distribution = {}
            if status_result.data:
                for item in status_result.data:
                    status_val = item['status']
                    status_distribution[status_val] = status_distribution.get(
                        status_val, 0) + 1
            recent_30_days = 0
            stats = {
                "total_count": total_count,
                "status_distribution": status_distribution,
                "recent_30_days": recent_30_days,
                "last_updated": datetime.now().isoformat()
            }
            logger.info("리스팅 통계 조회 완료")
            return stats
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {
                "total_count": 0,
                "status_distribution": {},
                "recent_30_days": 0,
                "last_updated": datetime.now().isoformat()}

    def convert_to_naver_format(
            self, listing_data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        리스팅 데이터를 네이버 부동산 표준 형식으로 변환
        Args:
            listing_data_dict: 기존 리스팅 데이터 (listings 테이블 형식의 dict)
        Returns:
            Dict[str, Any]: 네이버 표준 형식의 매물 정보
        """
        try:
            if self.naver_converter:
                naver_data, validation_result = self.naver_converter.convert_property_to_naver(
                    listing_data_dict)
                logger.info(
                    f"네이버 형식 변환 완료: {listing_data_dict.get('id', 'unknown')}, 호환성: {validation_result.get('naver_compatible', False)}")
                return naver_data
            else:
                return self._fallback_naver_conversion(listing_data_dict)
        except Exception as e:
            logger.error(f"네이버 형식 변환 실패: {e}")
            return self._fallback_naver_conversion(listing_data_dict)

    def _fallback_naver_conversion(
            self, listing_data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """폴백 네이버 변환 메서드 (기본 로직)"""
        naver_data = {
            "propertyType": "ETC",
            "tradeType": "A1",
            "location": {
                "address": listing_data_dict.get("display_address", ""),
                "city": listing_data_dict.get("sido", ""),
                "district": f"{listing_data_dict.get('sido', '')} {listing_data_dict.get('sigungu', '')}".strip(),
                "coordinates": {
                    "lat": float(listing_data_dict.get("lat", 0)) if listing_data_dict.get("lat") else 0.0,
                    "lng": float(listing_data_dict.get("lng", 0)) if listing_data_dict.get("lng") else 0.0
                }
            },
            "area": {
                "totalArea": float(listing_data_dict.get("total_floor_area", 0)) if listing_data_dict.get("total_floor_area") else 0.0,
                "exclusiveArea": float(listing_data_dict.get("exclusive_area", 0)) if listing_data_dict.get("exclusive_area") else 0.0,
                "landArea": float(listing_data_dict.get("land_area", 0)) if listing_data_dict.get("land_area") else 0.0
            },
            "price": {
                "salePrice": int(listing_data_dict.get("price", 0)) if (listing_data_dict.get("price") and str(listing_data_dict.get("price")).replace(',', '').replace('만원', '').strip().isdigit()) else 0,
                "deposit": int(listing_data_dict.get("deposit", 0)) if listing_data_dict.get("deposit") else 0,
                "monthlyRent": int(listing_data_dict.get("rent_fee", 0)) if listing_data_dict.get("rent_fee") else 0
            },
            "description": {
                "title": listing_data_dict.get("title", ""),
                "features": listing_data_dict.get("description", ""),
                "details": listing_data_dict.get("memo", "")
            },
            "buildingInfo": {
                "floors": int(listing_data_dict.get("floors", 0)) if listing_data_dict.get("floors") else 0,
                "buildYear": int(listing_data_dict.get("build_year", 0)) if listing_data_dict.get("build_year") else 0,
                "parking": bool(listing_data_dict.get("parking", False))
            }
        }
        
        # 매물 유형 변환 (직접 매핑)
        property_type = listing_data_dict.get("property_type", "")
        if property_type == "토지":
            naver_data["propertyType"] = "LND"
        elif property_type in ["주거", "아파트", "건물"]:
            naver_data["propertyType"] = "APT"
        elif property_type == "사무실":
            naver_data["propertyType"] = "OFC"
        elif property_type == "상가":
            naver_data["propertyType"] = "SHP"
        
        # 거래 유형 변환 (직접 매핑)
        deal_type = listing_data_dict.get("deal_type", "")
        if deal_type == "매매":
            naver_data["tradeType"] = "A1"
        elif deal_type == "교환":
            naver_data["tradeType"] = "A2"
        elif deal_type == "임대":
            naver_data["tradeType"] = "B1"
        
        # 기존 매핑이 있는 경우 사용 (선택적)
        if REALESTATE_TYPE_MAP and listing_data_dict.get("property_type"):
            naver_data["propertyType"] = REALESTATE_TYPE_MAP.get(
                listing_data_dict.get("property_type"), naver_data["propertyType"])
        if TRADE_TYPE_MAP and listing_data_dict.get("deal_type"):
            naver_data["tradeType"] = TRADE_TYPE_MAP.get(
                listing_data_dict.get("deal_type"), naver_data["tradeType"])
        
        return naver_data

    async def sync_naver_info(self, listing_id: UUID) -> bool:
        """네이버 정보 동기화"""
        try:
            listing_data_dict = await self.get_listing(listing_id)
            if not listing_data_dict:
                return False
            naver_data = self.convert_to_naver_format(listing_data_dict)
            result = self.client.table("listings").update({
                "naver_info": naver_data,
                "updated_at": datetime.now().isoformat()
            }).eq("id", str(listing_id)).execute()
            if result.data:
                logger.info(f"네이버 정보 동기화 완료: {listing_id}")
                return True
            else:
                logger.warning(f"네이버 정보 동기화 실패: {listing_id}")
                return False
        except Exception as e:
            logger.error(f"네이버 정보 동기화 오류: {e}")
            return False

    async def get_naver_compatible_response(
            self, listing_id: UUID, include_naver: bool = False) -> Optional[Dict[str, Any]]:
        """
        네이버 호환 형식으로 리스팅 정보 조회
        Args:
            listing_id: 리스팅 ID
            include_naver: 네이버 형식 데이터 포함 여부
        Returns:
            Optional[Dict[str, Any]]: 리스팅 정보 (네이버 형식 포함)
        """
        try:
            listing_data_dict = await self.get_listing(listing_id)
            if not listing_data_dict:
                return None
            response = {
                "id": listing_data_dict.get("id"),
                "title": listing_data_dict.get("title"),
                "property_type": listing_data_dict.get("property_type"),
                "deal_type": listing_data_dict.get("deal_type"),
                "price": listing_data_dict.get("price"),
                "display_address": listing_data_dict.get("display_address"),
                "status": listing_data_dict.get("status"),
                "created_at": listing_data_dict.get("created_at"),
                "updated_at": listing_data_dict.get("updated_at")
            }
            if include_naver:
                naver_data = self.convert_to_naver_format(listing_data_dict)
                response["naver_format"] = naver_data
                response["naver_compatibility"] = self._validate_naver_data(
                    naver_data)
            logger.info(f"네이버 호환 응답 생성 완료: {listing_id}")
            return response
        except Exception as e:
            logger.error(f"네이버 호환 응답 생성 실패: {e}")
            return None

    def _validate_naver_data(
            self, naver_data: Dict[str, Any]) -> Dict[str, bool]:
        """네이버 데이터 유효성 검증"""
        validation_result = {
            "property_type_valid": False,
            "trade_type_valid": False,
            "required_fields_complete": False,
            "naver_compatible": False}
        try:
            property_type_val = naver_data.get("propertyType", "")
            validation_result["property_type_valid"] = property_type_val in [
                "LND", "APT", "OFC", "SHP", "ETC"]
            trade_type_val = naver_data.get("tradeType", "")
            validation_result["trade_type_valid"] = trade_type_val in [
                "A1", "A2", "B1"]
            description = naver_data.get("description", {})
            location = naver_data.get("location", {})
            validation_result["required_fields_complete"] = all([
                description.get("title", "").strip() != "",
                location.get("address", "").strip() != "",
                naver_data.get("price") is not None
            ])
            validation_result["naver_compatible"] = all([
                validation_result["property_type_valid"],
                validation_result["trade_type_valid"],
                validation_result["required_fields_complete"]
            ])
        except Exception as e:
            logger.error(f"네이버 데이터 검증 오류: {e}")
        return validation_result

    async def auto_convert_public_data_to_naver(self,
                                                listing_id: UUID,
                                                building_data: Optional[Dict] = None,
                                                land_data: Optional[Dict] = None,
                                                ocr_data: Optional[Dict] = None,
                                                manual_data: Optional[Dict] = None,
                                                api_data: Optional[Dict] = None) -> Dict[str,
                                                                                         Any]:
        """공공데이터(건축물대장, 토지대장) 수집 결과를 네이버 형식으로 자동 변환 및 Listing 모델 필드에 매핑/저장"""
        try:
            listing_data_internal = await self.get_listing(listing_id)
            if not listing_data_internal:
                logger.warning(f"리스팅을 찾을 수 없음: {listing_id}")
                return {}
            naver_data = self.convert_to_naver_format(listing_data_internal)
            update_fields = {}
            if building_data:
                update_fields["building_register_info"] = building_data
                if "totalFloorArea" in building_data:
                    naver_data["area"]["totalArea"] = float(
                        building_data["totalFloorArea"])
                if "buildingArea" in building_data:
                    naver_data["area"]["exclusiveArea"] = float(
                        building_data["buildingArea"])
                if "floors" in building_data:
                    naver_data["buildingInfo"]["floors"] = int(
                        building_data["floors"])
                if "buildYear" in building_data:
                    naver_data["buildingInfo"]["buildYear"] = int(
                        building_data["buildYear"])
                if "parkingSpaces" in building_data:
                    naver_data["buildingInfo"]["parking"] = int(
                        building_data["parkingSpaces"]) > 0
            if land_data:
                update_fields["land_register_info"] = land_data
                if "landArea" in land_data:
                    naver_data["area"]["landArea"] = float(
                        land_data["landArea"])
                land_use = land_data.get("landUse", "")
                if "상업" in land_use or "상가" in land_use:
                    naver_data["propertyType"] = "SHP"
                elif "주거" in land_use or "주택" in land_use:
                    naver_data["propertyType"] = "APT"
            if ocr_data:
                update_fields["ocr_data"] = ocr_data
                owner_info = {
                    k: ocr_data[k] for k in [
                        "owner_name",
                        "owner_address",
                        "ownership_changed_at"] if k in ocr_data}
                if owner_info:
                    update_fields["owner_info"] = owner_info
            if manual_data:
                update_fields["manual_data"] = manual_data
            if api_data:
                update_fields["api_data"] = api_data
            update_fields["naver_info"] = naver_data
            update_fields["updated_at"] = datetime.now().isoformat()
            result = self.client.table("listings").update(
                update_fields).eq("id", str(listing_id)).execute()
            logger.info(f"공공데이터 기반 리스팅 필드 및 네이버 변환 완료: {listing_id}")
            return naver_data
        except Exception as e:
            logger.error(f"공공데이터 네이버 변환/매핑 실패: {e}")
            return {}
