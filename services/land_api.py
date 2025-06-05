"""
토지대장 및 토지이용규제 API 클라이언트
V-World 토지 관련 API 연동
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import quote
import re

import httpx
import PublicDataReader as pdr

from core.config import settings

logger = logging.getLogger(__name__)


class LandLedgerService:
    """토지임야목록 정보 조회 서비스"""

    def __init__(self):
        self.api_key = settings.LAND_API_KEY
        if self.api_key:
            # URL 디코딩된 API 키 사용
            self.api_key = self.api_key.replace('%2B', '+').replace('%3D', '=')
        
        # PublicDataReader 인스턴스는 사용 시점에 생성
        self._land_api = None
        self.timeout = settings.API_TIMEOUT

    def _get_land_api(self):
        """토지임야목록 API 인스턴스 지연 생성"""
        if self._land_api is None and self.api_key:
            try:
                # PublicDataReader의 토지임야목록 클래스 사용
                from PublicDataReader import LandLedger
                self._land_api = LandLedger(self.api_key)
                logger.info("토지임야목록 API 인스턴스 생성 완료")
            except Exception as e:
                logger.error(f"토지임야목록 API 인스턴스 생성 실패: {str(e)}")
                self._land_api = None
        return self._land_api

    def _parse_address_to_land_codes(self, address: str) -> Dict[str, str]:
        """
        주소에서 PNU 코드 생성 (간단한 버전)
        
        Args:
            address: 주소 문자열
            
        Returns:
            PNU 코드 정보
        """
        try:
            # 기본 지역코드 데이터 로드
            code_df = pdr.code_bdong()
            
            # 주소 파싱 로직 (건축물대장과 동일)
            if '서울' in address:
                if '강남구' in address:
                    sigungu_code = '11680'
                    if '역삼동' in address:
                        bdong_code = '10300'
                    elif '삼성동' in address:
                        bdong_code = '10400'
                    else:
                        bdong_code = '10300'
                else:
                    sigungu_code = '11110'
                    bdong_code = '10100'
            elif '경기' in address:
                if '성남시' in address:
                    sigungu_code = '41135'
                    bdong_code = '11000'
                else:
                    sigungu_code = '41111'
                    bdong_code = '10100'
            else:
                # 기본값 (서울 강남구)
                sigungu_code = '11680'
                bdong_code = '10300'

            # 번지 추출
            import re
            number_pattern = r'(\d+)(?:-(\d+))?'
            match = re.search(number_pattern, address)
            
            if match:
                bun = match.group(1).zfill(4)
                ji = (match.group(2) or '0').zfill(4)
            else:
                bun = '0001'
                ji = '0000'

            return {
                'sigungu_code': sigungu_code,
                'bdong_code': bdong_code,
                'bun': bun,
                'ji': ji,
                'pnu': f"{sigungu_code}{bdong_code}{bun}{ji}"  # PNU 코드 생성
            }
            
        except Exception as e:
            logger.error(f"주소 파싱 오류: {str(e)}")
            return {
                'sigungu_code': '11680',
                'bdong_code': '10300', 
                'bun': '0001',
                'ji': '0000',
                'pnu': '1168010300010000'
            }

    async def get_land_ledger_info(self, address: str) -> Dict[str, Any]:
        """
        토지임야목록 정보 조회
        
        Args:
            address: 조회할 주소
            
        Returns:
            토지임야목록 정보
        """
        if not self.api_key:
            return {'success': False, 'error': '토지임야목록 API 키가 설정되지 않았습니다'}

        try:
            api = self._get_land_api()
            if not api:
                return {'success': False, 'error': '토지임야목록 API 초기화 실패'}

            codes = self._parse_address_to_land_codes(address)
            logger.info(f"토지임야목록 조회 시작: {address}, PNU: {codes['pnu']}")

            # 비동기 실행을 위한 래퍼
            def sync_land_api_call():
                try:
                    # 토지기본정보 조회
                    land_basic = api.get_data(
                        service_type="토지기본정보",
                        pnu=codes['pnu']
                    )
                    
                    # 토지소유정보 조회  
                    land_ownership = api.get_data(
                        service_type="토지소유정보",
                        pnu=codes['pnu']
                    )
                    
                    return {
                        'land_basic': land_basic,
                        'land_ownership': land_ownership
                    }
                except Exception as e:
                    logger.error(f"토지임야목록 API 호출 오류: {str(e)}")
                    return None

            # 비동기 실행
            raw_data = await asyncio.get_event_loop().run_in_executor(
                None, sync_land_api_call
            )

            if raw_data is None:
                return {'success': False, 'error': '토지임야목록 정보를 찾을 수 없습니다'}

            # 데이터 처리
            processed_data = self._process_land_data(raw_data, address)

            return {
                'success': True,
                'data': processed_data,
                'address': address,
                'codes': codes
            }

        except Exception as e:
            logger.error(f"토지임야목록 조회 오류: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _process_land_data(self, raw_data: Dict, address: str) -> Dict[str, Any]:
        """
        토지임야목록 원시 데이터 가공
        
        Args:
            raw_data: API에서 받은 원시 데이터
            address: 조회 주소
            
        Returns:
            가공된 토지 정보
        """
        try:
            processed = {
                'address': address,
                'land_basic_info': {},
                'land_ownership_info': {},
                'land_usage_info': {}
            }

            # 토지기본정보 처리
            if 'land_basic' in raw_data and not raw_data['land_basic'].empty:
                basic = raw_data['land_basic'].iloc[0] 
                processed['land_basic_info'] = {
                    'land_category': basic.get('지목', ''),
                    'land_area': basic.get('면적', 0),
                    'official_price': basic.get('공시지가', 0),
                    'road_side': basic.get('도로측면', ''),
                    'land_use_situation': basic.get('이용상황', ''),
                    'land_characteristic': basic.get('토지특성', ''),
                    'ownership_classification': basic.get('소유구분', '')
                }

            # 토지소유정보 처리
            if 'land_ownership' in raw_data and not raw_data['land_ownership'].empty:
                ownership_df = raw_data['land_ownership']
                ownership_list = []
                
                for _, row in ownership_df.iterrows():
                    owner_info = {
                        'owner_name': row.get('소유자명', ''),
                        'owner_division': row.get('소유구분', ''),
                        'ownership_ratio': row.get('지분비율', ''),
                        'acquisition_date': row.get('취득일', ''),
                        'acquisition_reason': row.get('취득원인', ''),
                        'owner_address': row.get('소유자주소', '')
                    }
                    ownership_list.append(owner_info)
                
                processed['land_ownership_info'] = {
                    'total_owners': len(ownership_list),
                    'owners': ownership_list
                }

            return processed

        except Exception as e:
            logger.error(f"토지 데이터 가공 오류: {str(e)}")
            return {
                'address': address,
                'land_basic_info': {},
                'land_ownership_info': {},
                'land_usage_info': {},
                'error': str(e)
            }


class LandRegulationService:
    """토지이용규제정보 서비스 (V-World)"""

    def __init__(self):
        self.api_key = settings.LAND_REGULATION_API_KEY
        if self.api_key:
            # URL 디코딩된 API 키 사용
            self.api_key = self.api_key.replace('%2B', '+').replace('%3D', '=')

        self.base_url = "https://api.vworld.kr/req/data"
        self.timeout = settings.API_TIMEOUT

    async def get_land_regulation_info(
            self, x: float, y: float) -> Dict[str, Any]:
        """
        좌표 기반 토지이용규제정보 조회

        Args:
            x: 경도
            y: 위도

        Returns:
            토지이용규제 정보
        """
        if not self.api_key:
            return {'success': False, 'error': 'API 키가 설정되지 않았습니다'}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'service': 'data',
                    'request': 'getfeature',
                    'data': 'LT_C_UQ111',  # 토지이용계획도
                    'key': self.api_key,
                    'geomfilter': f'POINT({x} {y})',
                    'format': 'json',
                    'size': '10',
                    'page': '1',
                    'geometry': 'false',
                    'attribute': 'true'
                }

                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get('response', {}).get('status') == 'OK':
                    features = data.get(
                        'response',
                        {}).get(
                        'result',
                        {}).get(
                        'featureCollection',
                        {}).get(
                        'features',
                        [])

                    if features:
                        return {
                            'success': True,
                            'data': features[0].get('properties', {}),
                            'raw_data': data
                        }
                    else:
                        return {
                            'success': False,
                            'error': '토지이용규제 정보를 찾을 수 없습니다'}
                else:
                    error_msg = data.get(
                        'response', {}).get(
                        'status', '알 수 없는 오류')
                    return {
                        'success': False,
                        'error': f'토지이용규제 조회 실패: {error_msg}'}

        except Exception as e:
            logger.error(f"토지이용규제 API 호출 오류: {str(e)}")
            return {'success': False, 'error': str(e)}


class VWorldLandForestService:
    """V-World 토지임야 직접 API 서비스"""

    def __init__(self):
        self.api_key = settings.VWORLD_API_KEY  # 같은 API 키 사용
        self.base_url = "https://api.vworld.kr/ned/data/ladfrlList"  # 토지임야 전용 엔드포인트
        self.timeout = settings.API_TIMEOUT

    async def get_land_forest_info(self, pnu: str) -> Dict[str, Any]:
        """
        PNU 코드로 토지임야 정보 조회
        
        Args:
            pnu: 고유번호 (예: 1168010300010001)
            
        Returns:
            토지임야 정보
        """
        if not self.api_key:
            return {'success': False, 'error': 'V-World API 키가 설정되지 않았습니다'}

        if not pnu or len(pnu) != 19:
            return {'success': False, 'error': f'PNU 코드가 유효하지 않습니다: {pnu}'}

        try:
            # 다중 연결 방식으로 시도 (building_api.py와 동일한 방식)
            connection_attempts = [
                {
                    'name': 'HTTPS_Primary',
                    'url': self.base_url,
                    'verify': True,
                    'http2': False
                },
                {
                    'name': 'HTTP_Fallback',
                    'url': self.base_url.replace('https://', 'http://'),
                    'verify': False,
                    'http2': False
                },
                {
                    'name': 'HTTPS_NoSSL',
                    'url': self.base_url,
                    'verify': False,
                    'http2': False
                }
            ]

            for attempt in connection_attempts:
                logger.info(f"🔄 토지임야 API 연결 시도: {attempt['name']}")
                
                try:
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(timeout=30.0, connect=10.0),
                        follow_redirects=True,
                        verify=attempt['verify'],
                        headers={
                            'User-Agent': 'Railway-RealEstate-Bot/1.0',
                            'Accept': 'application/json',
                            'Accept-Encoding': 'identity',
                            'Connection': 'close'
                        },
                        http2=attempt['http2'],
                        limits=httpx.Limits(max_keepalive_connections=0, max_connections=1)
                    ) as client:
                        params = {
                            'pnu': pnu,
                            'key': self.api_key,
                            'format': 'json',
                            'numOfRows': '10',
                            'pageNo': '1'
                        }
                        
                        logger.info(f"토지임야 API 호출: {attempt['url']}")
                        logger.info(f"PNU: {pnu}")
                        
                        response = await client.get(attempt['url'], params=params)
                        logger.info(f"응답 코드: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            logger.info(f"토지임야 API 응답: {data}")
                            
                            # V-World 토지임야 API 응답 구조 처리
                            if 'ladfrlVOList' in data and 'ladfrlVO' in data['ladfrlVOList']:
                                land_list = data['ladfrlVOList']['ladfrlVO']
                                if isinstance(land_list, list) and len(land_list) > 0:
                                    land_info = land_list[0]  # 첫 번째 결과 사용
                                elif isinstance(land_list, dict):
                                    land_info = land_list
                                else:
                                    logger.warning(f"토지임야 데이터 없음: {data}")
                                    continue
                                
                                logger.info(f"✅ {attempt['name']} 성공! 토지임야 정보 획득")
                                return {
                                    'success': True,
                                    'data': self._process_vworld_land_data(land_info, pnu),
                                    'method': attempt['name'],
                                    'raw_data': data
                                }
                            else:
                                logger.warning(f"토지임야 응답 구조 문제: {list(data.keys())}")
                                continue
                                
                except httpx.RemoteProtocolError as e:
                    logger.warning(f"{attempt['name']} RemoteProtocolError: {str(e)}")
                    continue
                except httpx.ConnectError as e:
                    logger.warning(f"{attempt['name']} ConnectError: {str(e)}")
                    continue
                except httpx.TimeoutException as e:
                    logger.warning(f"{attempt['name']} TimeoutException: {str(e)}")
                    continue
                except Exception as e:
                    logger.warning(f"{attempt['name']} 기타 오류: {str(e)}")
                    continue
            
            # 모든 연결 시도 실패
            logger.error(f"모든 토지임야 API 연결 시도 실패: PNU {pnu}")
            return {'success': False, 'error': '토지임야 API 연결에 실패했습니다'}

        except Exception as e:
            logger.error(f"토지임야 API 호출 오류: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _process_vworld_land_data(self, land_data: Dict[str, Any], pnu: str) -> Dict[str, Any]:
        """V-World 토지임야 데이터 가공"""
        try:
            processed = {
                'pnu': pnu,
                'land_category_code': land_data.get('lndcgrCode', ''),
                'land_category_name': self._get_land_category_name(land_data.get('lndcgrCode', '')),
                'area_sqm': land_data.get('lndpclAr', 0),  # 면적(㎡)
                'administrative_code': land_data.get('ldCode', ''),
                'lot_number': land_data.get('mnnmSlno', ''),
                'last_update_date': land_data.get('lastUpdtDt', ''),
                'raw_data': land_data
            }
            
            # 면적을 숫자로 변환
            try:
                if isinstance(processed['area_sqm'], str):
                    processed['area_sqm'] = float(processed['area_sqm'])
                elif processed['area_sqm'] is None:
                    processed['area_sqm'] = 0
            except (ValueError, TypeError):
                processed['area_sqm'] = 0
            
            return processed
            
        except Exception as e:
            logger.error(f"토지임야 데이터 가공 오류: {str(e)}")
            return {
                'pnu': pnu,
                'error': str(e),
                'raw_data': land_data
            }

    def _get_land_category_name(self, code: str) -> str:
        """지목 코드를 이름으로 변환"""
        land_categories = {
            '01': '전', '02': '답', '03': '과수원', '04': '목장용지', '05': '임야',
            '06': '광천지', '07': '염전', '08': '대', '09': '공장용지', '10': '학교용지',
            '11': '주차장', '12': '주유소용지', '13': '창고용지', '14': '도로', '15': '철도용지',
            '16': '제방', '17': '하천', '18': '구거', '19': '유지', '20': '양어장',
            '21': '수도용지', '22': '공원', '23': '체육용지', '24': '유원지', '25': '종교용지',
            '26': '사적지', '27': '묘지', '28': '잡종지'
        }
        return land_categories.get(code, f'알 수 없음({code})')


class LandForestService:
    """토지임야목록 서비스 (V-World 기존)"""

    def __init__(self):
        self.api_key = settings.LAND_API_KEY
        self.base_url = "https://api.vworld.kr/req/data"
        self.timeout = settings.API_TIMEOUT

    async def search_land_by_address(self, address: str) -> Dict[str, Any]:
        """
        주소 기반 토지임야 정보 조회

        Args:
            address: 검색할 주소 (예: "갈운리 산 108")

        Returns:
            토지임야 정보
        """
        if not self.api_key:
            return {'success': False, 'error': 'API 키가 설정되지 않았습니다'}

        try:
            # 주소에서 검색 키워드 추출
            search_keyword = self._extract_search_keyword(address)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'service': 'data',
                    'request': 'getfeature',
                    'data': 'LT_C_ADEMD_INFO',  # 토지임야도
                    'key': self.api_key,
                    'attrfilter': search_keyword,
                    'format': 'json',
                    'size': '10',
                    'page': '1',
                    'geometry': 'false',
                    'attribute': 'true'
                }

                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get('response', {}).get('status') == 'OK':
                    features = data.get(
                        'response',
                        {}).get(
                        'result',
                        {}).get(
                        'featureCollection',
                        {}).get(
                        'features',
                        [])

                    if features:
                        # 가장 유사한 결과 찾기
                        best_match = self._find_best_match(features, address)
                        return {
                            'success': True,
                            'data': best_match,
                            'total_count': len(features),
                            'raw_data': data
                        }
                    else:
                        return {
                            'success': False,
                            'error': '토지임야 정보를 찾을 수 없습니다'}
                else:
                    error_msg = data.get(
                        'response', {}).get(
                        'status', '알 수 없는 오류')
                    return {
                        'success': False,
                        'error': f'토지임야 조회 실패: {error_msg}'}

        except Exception as e:
            logger.error(f"토지임야 API 호출 오류: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _extract_search_keyword(self, address: str) -> str:
        """
        주소에서 토지임야 검색 키워드 추출

        Args:
            address: 원본 주소

        Returns:
            API 검색용 키워드
        """
        # "갈운리 산 108" -> "갈운리"와 "108" 추출
        address = address.replace("번지", "").replace("산", "").strip()

        # 숫자와 한글 분리
        korean_part = re.sub(r'[0-9\-\s]', '', address)
        number_part = re.findall(r'\d+', address)

        # 검색 필터 구성
        filters = []

        if korean_part:
            # 리동명 또는 지명으로 검색
            filters.append(f"ri_dong_nm like '%{korean_part}%'")

        if number_part:
            # 지번으로 검색 (본번)
            main_num = number_part[0]
            filters.append(f"mnnm={main_num}")

        # 산지 여부 확인
        if "산" in address:
            filters.append("mnt_yn='1'")  # 산지

        return " AND ".join(
            filters) if filters else f"ri_dong_nm like '%{korean_part}%'"

    def _find_best_match(
            self, features: List[Dict], target_address: str) -> Dict[str, Any]:
        """
        검색 결과에서 가장 유사한 결과 선택

        Args:
            features: API 검색 결과 목록
            target_address: 대상 주소

        Returns:
            가장 유사한 결과
        """
        if not features:
            return {}

        # 첫 번째 결과를 기본값으로 사용
        best_match = features[0].get('properties', {})

        # 추후 유사도 점수 계산 로직 추가 가능
        # 현재는 단순히 첫 번째 결과 반환

        return best_match


class EnhancedAddressSearchService:
    """개선된 주소검색 서비스 - 여러 API 통합"""

    def __init__(self):
        self.vworld_api_key = settings.VWORLD_API_KEY
        self.land_service = LandForestService()
        self.base_url = "http://api.vworld.kr/req/address"
        self.timeout = settings.API_TIMEOUT

    async def comprehensive_address_search(
            self, address: str) -> Dict[str, Any]:
        """
        종합 주소 검색 - 일반 주소 + 토지임야 주소

        Args:
            address: 검색할 주소

        Returns:
            통합 검색 결과
        """
        result = {
            'success': False,
            'address': address,
            'method_used': None,
            'coordinates': None,
            'land_info': None,
            'errors': []
        }

        # 1. 일반 주소검색 시도
        logger.info(f"일반 주소검색 시도: {address}")
        general_result = await self._search_general_address(address)

        if general_result['success']:
            result.update({
                'success': True,
                'method_used': 'general_address',
                'coordinates': {'x': general_result['x'], 'y': general_result['y']},
                'raw_data': general_result.get('raw_data')
            })
            return result
        else:
            result['errors'].append(
                f"일반 주소검색 실패: {general_result.get('error')}")

        # 2. 토지임야 검색 시도 (일반 검색 실패 시)
        logger.info(f"토지임야 검색 시도: {address}")
        land_result = await self.land_service.search_land_by_address(address)

        if land_result['success']:
            land_data = land_result['data']

            # 토지임야 데이터에서 좌표 추출 (만약 있다면)
            # 일반적으로 토지임야 API는 좌표를 직접 제공하지 않을 수 있음
            # 이 경우 추가 변환 로직이 필요할 수 있음

            result.update({
                'success': True,
                'method_used': 'land_forest',
                'land_info': land_data,
                'coordinates': None,  # 토지임야에서는 좌표 정보가 제한적일 수 있음
                'raw_data': land_result.get('raw_data')
            })
            return result
        else:
            result['errors'].append(f"토지임야 검색 실패: {land_result.get('error')}")

        # 3. 모든 검색 실패
        result['success'] = False
        return result

    async def _search_general_address(self, address: str) -> Dict[str, Any]:
        """기존 V-World 주소검색"""
        if not self.vworld_api_key:
            return {'success': False, 'error': 'V-World API 키가 설정되지 않았습니다'}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'service': 'address',
                    'request': 'getcoord',
                    'version': '2.0',
                    'crs': 'epsg:4326',
                    'address': address,
                    'format': 'json',
                    'type': 'road',
                    'key': self.vworld_api_key
                }

                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get('response', {}).get('status') == 'OK':
                    result = data['response']['result']['point']
                    return {
                        'success': True,
                        'x': result.get('x'),
                        'y': result.get('y'),
                        'raw_data': data
                    }
                else:
                    return {'success': False, 'error': '주소를 찾을 수 없습니다'}

        except Exception as e:
            return {'success': False, 'error': str(e)}


class IntegratedLandDataService:
    """통합 토지 데이터 서비스"""

    def __init__(self):
        self.address_service = EnhancedAddressSearchService()
        self.regulation_service = LandRegulationService()
        self.land_ledger_service = LandLedgerService()  # PublicDataReader 기반
        self.vworld_land_service = VWorldLandForestService()  # V-World 직접 API

    async def analyze_land_by_address(self, address: str) -> Dict[str, Any]:
        """
        주소 기반 토지 종합 분석

        Args:
            address: 분석할 주소

        Returns:
            토지 종합 분석 결과
        """
        result = {
            'success': False,
            'address': address,
            'address_search': {},
            'land_regulation': {},
            'land_characteristics': {},
            'errors': []
        }

        try:
            # 1. 종합 주소 검색
            logger.info(f"토지 주소 검색 시작: {address}")
            address_result = await self.address_service.comprehensive_address_search(address)
            result['address_search'] = address_result

            if not address_result['success']:
                result['errors'].extend(address_result.get('errors', []))
                result['success'] = False
                result['message'] = '주소 검색에 실패했습니다'
                return result

            # 2. 좌표가 있는 경우 토지이용규제 조회
            if address_result.get('coordinates'):
                coords = address_result['coordinates']
                if coords.get('x') and coords.get('y'):
                    logger.info(f"토지이용규제 조회: ({coords['x']}, {coords['y']})")
                    regulation_result = await self.regulation_service.get_land_regulation_info(
                        float(coords['x']), float(coords['y'])
                    )
                    result['land_regulation'] = regulation_result

                    if not regulation_result['success']:
                        result['errors'].append(
                            f"토지이용규제 조회 실패: {regulation_result.get('error')}")

            # 3. 토지임야목록 조회 (PublicDataReader)
            logger.info(f"토지임야목록 조회 시작: {address}")
            land_ledger_result = await self.land_ledger_service.get_land_ledger_info(address)
            result['land_ledger'] = land_ledger_result
            
            if not land_ledger_result['success']:
                result['errors'].append(
                    f"토지임야목록 조회 실패: {land_ledger_result.get('error')}")
            else:
                logger.info(f"토지임야목록 조회 완료: {address}")

            # 4. V-World 토지임야 직접 API 조회 시도
            if land_ledger_result.get('codes', {}).get('pnu'):
                pnu = land_ledger_result['codes']['pnu']
                logger.info(f"V-World 토지임야 API 조회 시작: PNU {pnu}")
                
                vworld_land_result = await self.vworld_land_service.get_land_forest_info(pnu)
                result['vworld_land_forest'] = vworld_land_result
                
                if vworld_land_result['success']:
                    logger.info(f"✅ V-World 토지임야 API 성공: {address}")
                else:
                    result['errors'].append(
                        f"V-World 토지임야 조회 실패: {vworld_land_result.get('error')}")
            else:
                logger.warning(f"PNU 코드 없어서 V-World 토지임야 API 건너뜀: {address}")
                result['vworld_land_forest'] = {'success': False, 'error': 'PNU 코드 없음'}

            # 5. 토지 특성 정보 정리
            if address_result.get('land_info'):
                result['land_characteristics'] = self._process_land_characteristics(
                    address_result['land_info'])

            # 6. 전체 성공 여부 판단
            if address_result['success']:
                result['success'] = True
                result['message'] = f"토지 분석 완료 (방법: {address_result.get('method_used')})"
            else:
                result['success'] = False
                result['message'] = '토지 분석에 실패했습니다'

            return result

        except Exception as e:
            logger.error(f"토지 분석 오류: {str(e)}")
            result['success'] = False
            result['errors'].append(str(e))
            result['message'] = '토지 분석 중 오류가 발생했습니다'
            return result

    def _process_land_characteristics(
            self, land_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        토지 특성 데이터 가공

        Args:
            land_data: 원시 토지 데이터

        Returns:
            가공된 토지 특성 정보
        """
        try:
            processed = {
                'land_type': '일반',
                'area': 0,
                'use_district': '',
                'ownership_info': {},
                'location_info': {}
            }

            # 토지임야 데이터 처리
            if land_data:
                # 지목 (토지 용도)
                processed['land_type'] = land_data.get('jimok_nm', '일반')

                # 면적 정보
                area_str = land_data.get('ar', '0')
                try:
                    processed['area'] = float(area_str) if area_str else 0
                except (ValueError, TypeError):
                    processed['area'] = 0

                # 위치 정보
                processed['location_info'] = {
                    'sido_nm': land_data.get('sido_nm', ''),
                    'sgg_nm': land_data.get('sgg_nm', ''),
                    'emd_nm': land_data.get('emd_nm', ''),
                    'ri_dong_nm': land_data.get('ri_dong_nm', ''),
                    'main_num': land_data.get('mnnm', ''),
                    'sub_num': land_data.get('snnm', ''),
                    'is_mountain': land_data.get('mnt_yn') == '1'
                }

                # 소유 관련 정보 (있는 경우)
                processed['ownership_info'] = {
                    'pnu': land_data.get('pnu', ''),
                    'land_serial': land_data.get('land_serial_no', '')
                }

            return processed

        except Exception as e:
            logger.error(f"토지 특성 데이터 가공 오류: {str(e)}")
            return {
                'land_type': '알 수 없음',
                'area': 0,
                'use_district': '',
                'ownership_info': {},
                'location_info': {},
                'error': str(e)
            }
