"""
건축물대장 API 클라이언트
PublicDataReader를 활용한 공공데이터 연동
"""
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from urllib.parse import quote

import httpx
from PublicDataReader import BuildingLedger
import PublicDataReader as pdr

from core.config import settings

logger = logging.getLogger(__name__)


class AddressSearchService:
    """V-World 주소검색 API 서비스"""

    def __init__(self):
        self.api_key = settings.VWORLD_API_KEY
        # Vercel 프록시 사용 (필요시에만 활성화)
        self.use_proxy = False  # 직접 연결 우선 시도
        self.proxy_url = "https://vworld-proxy-pi5n692oj-qfits-projects.vercel.app/api/vworld"  # 실제 배포된 URL
        self.base_url = "https://api.vworld.kr/req/address"
        self.timeout = settings.API_TIMEOUT

    async def search_address(self, query: str) -> Dict[str, Any]:
        """
        주소 검색 및 좌표 조회

        Args:
            query: 검색할 주소

        Returns:
            주소 정보 및 좌표가 포함된 딕셔너리
        """
        logger.info(f"🔍 AddressSearchService.search_address 시작: {query}")
        
        try:
            # API 키 확인
            if not self.api_key:
                logger.error("V-World API 키가 설정되지 않았습니다")
                return {'success': False, 'error': 'V-World API 키가 설정되지 않았습니다'}
            
            logger.info(f"✅ V-World API 키 확인됨: {self.api_key[:10]}...")

            # URL 인코딩 - 한글 주소 처리
            encoded_query = quote(query, safe='', encoding='utf-8')
            
            # Railway 환경에서 V-World API 연결 디버깅
            logger.info(f"🔄 V-World API 연결 시도: {query}")
            logger.info(f"API 키 존재: {'Yes' if self.api_key else 'No'}")
            
            # V-World API 봇 차단 우회를 위한 브라우저 헤더 사용
            transport = httpx.AsyncHTTPTransport(
                retries=3,
                http2=False,
                verify=False
            )
            
            # 실제 브라우저와 동일한 헤더로 V-World API 호출
            vworld_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.vworld.kr/',
                'Origin': 'https://www.vworld.kr',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            try:
                async with httpx.AsyncClient(
                    transport=transport,
                    timeout=httpx.Timeout(timeout=15.0, connect=10.0),
                    follow_redirects=True,
                    headers=vworld_headers
                ) as client:
                    params = {
                        'service': 'address',
                        'request': 'getcoord',
                        'version': '2.0',
                        'crs': 'epsg:4326',
                        'address': query,
                        'format': 'json',
                        'type': 'road',
                        'key': self.api_key
                    }
                    
                    # 1. V-World API 직접 호출 시도 (Railway에서 작동 확인됨)
                    logger.info(f"🔄 V-World API 직접 호출 시도")
                    
                    try:
                        direct_response = await client.get(self.base_url, params=params)
                        logger.info(f"직접 호출 응답 코드: {direct_response.status_code}")
                        
                        if direct_response.status_code == 200:
                            data = direct_response.json()
                            if data.get('response', {}).get('status') == 'OK':
                                result = data['response']['result']
                                if 'point' in result:
                                    point = result['point']
                                    logger.info(f"✅ V-World API 직접 호출 성공! 좌표: {point}")
                                    return {
                                        'success': True,
                                        'x': float(point['x']),
                                        'y': float(point['y']),
                                        'address': query,
                                        'method': 'vworld_direct',
                                        'raw_data': data
                                    }
                            else:
                                logger.warning(f"V-World API 오류: {data.get('response', {}).get('error', {})}")
                        elif direct_response.status_code == 502:
                            logger.warning("502 Bad Gateway - Railway에서 V-World API 차단 확인됨")
                            # 502 오류 시 대안 프록시들을 순차적으로 시도
                            proxy_result = await self._try_alternative_proxies(params, query)
                            if proxy_result:
                                return proxy_result
                    except Exception as e:
                        logger.error(f"직접 호출 실패: {str(e)}")
                    
                    # 2. V-World Search API 사용 (프록시 실패시)
                    logger.info(f"🔄 V-World Search API로 전환하여 시도")
                    
                    # Search API 엔드포인트와 파라미터
                    search_url = 'https://api.vworld.kr/req/search'
                    search_params = {
                        'key': self.api_key,
                        'service': 'search',
                        'request': 'search', 
                        'version': '2.0',
                        'crs': 'epsg:4326',
                        'size': '10',
                        'page': '1',
                        'query': query,
                        'type': 'address',  # 소문자로 변경
                        'format': 'json'
                    }
                    
                    logger.info(f"📡 V-World Search API 호출")
                    logger.info(f"URL: {search_url}")
                    logger.info(f"파라미터: {search_params}")
                    
                    # Search API 직접 호출
                    try:
                        # Search API도 동일한 브라우저 헤더 사용
                        response = await client.get(search_url, params=search_params)
                        logger.info(f"Search API 응답 코드: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            logger.info(f"Search API 응답 구조: {list(data.keys())}")
                            
                            # Search API 응답 파싱
                            response_data = data.get('response')
                            if response_data and response_data.get('status') == 'OK':
                                result = response_data.get('result')
                                if result:
                                    items = result.get('items', [])
                                    logger.info(f"검색 결과 {len(items)}건 발견")
                                    
                                    if items:
                                        # 첫 번째 결과 사용
                                        item = items[0]
                                        logger.info(f"첫 번째 결과: {item}")
                                        
                                        # 좌표 추출 (Search API는 x, y 필드를 직접 제공)
                                        x = item.get('x')
                                        y = item.get('y')
                                        
                                        if x and y:
                                            logger.info(f"✅ Search API 성공! 좌표: x={x}, y={y}")
                                            return {
                                                'success': True,
                                                'x': float(x),
                                                'y': float(y),
                                                'address': query,
                                                'method': 'vworld_search_api',
                                                'raw_data': data
                                            }
                                        else:
                                            logger.warning(f"Search API 결과에 좌표 없음: {item}")
                                else:
                                    logger.warning("Search API 결과가 비어있음")
                            else:
                                logger.error(f"Search API 상태 오류: {response_data}")
                        elif response.status_code == 502:
                            logger.warning("Search API도 502 오류 - 프록시 시도")
                            # Search API도 502 오류 시 프록시 시도
                            search_params = {
                                'key': self.api_key,
                                'service': 'search',
                                'request': 'search', 
                                'version': '2.0',
                                'crs': 'epsg:4326',
                                'size': '10',
                                'page': '1',
                                'query': query,
                                'type': 'address',
                                'format': 'json',
                                'category': 'road'  # category 파라미터 추가
                            }
                            proxy_result = await self._try_alternative_proxies(search_params, query)
                            if proxy_result:
                                return proxy_result
                        else:
                            logger.error(f"Search API HTTP 오류: {response.status_code}")
                            logger.error(f"응답 내용: {response.text[:500]}")
                            
                    except httpx.RemoteProtocolError as e:
                        logger.error(f"Search API RemoteProtocolError: {e}")
                    except Exception as e:
                        logger.error(f"Search API 예외: {type(e).__name__}: {e}")
                    
                    # Search API 실패시 Address API 시도 (프록시 없이)
                    logger.info("Search API 실패, Address API 직접 시도")
                    
                    try:
                        address_url = 'https://api.vworld.kr/req/address'
                        response = await client.get(address_url, params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('response', {}).get('status') == 'OK':
                                result = data['response']['result']
                                if 'point' in result:
                                    point = result['point']
                                    logger.info(f"✅ Address API 성공! 좌표: {point}")
                                    return {
                                        'success': True,
                                        'x': float(point['x']),
                                        'y': float(point['y']),
                                        'address': query,
                                        'method': 'address_api_direct',
                                        'raw_data': data
                                    }
                    except Exception as e:
                        logger.error(f"Address API도 실패: {e}")
                    
                    # 모든 시도 실패시 프록시 사용
                    use_proxy = False  # 프록시는 이미 실패했으므로 비활성화
                    if use_proxy:
                        for proxy in proxy_urls:
                            try:
                                # URL 인코딩
                                import urllib.parse
                                query_string = urllib.parse.urlencode(params)
                                target_url = f"{self.base_url}?{query_string}"
                                
                                if 'corsproxy.io' in proxy:
                                    proxy_url = f"{proxy}{urllib.parse.quote(target_url)}"
                                elif 'allorigins' in proxy:
                                    proxy_url = f"{proxy}{urllib.parse.quote(target_url)}"
                                else:
                                    proxy_url = f"{proxy}{target_url}"
                                
                                logger.info(f"🔄 프록시 시도: {proxy}")
                                
                                response = await client.get(proxy_url)
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    
                                    # allOrigins는 contents 안에 실제 데이터가 있을 수 있음
                                    if 'contents' in data:
                                        data = json.loads(data['contents'])
                                    
                                    if data.get('response', {}).get('status') == 'OK':
                                        result = data['response']['result']
                                        if 'point' in result:
                                            point = result['point']
                                            logger.info(f"✅ 프록시 성공! 좌표: {point}")
                                            return {
                                                'success': True,
                                                'x': float(point['x']),
                                                'y': float(point['y']),
                                                'address': query,
                                                'method': f'proxy_{proxy.split("/")[2]}',
                                                'raw_data': data
                                            }
                            except Exception as proxy_error:
                                logger.warning(f"프록시 {proxy} 실패: {proxy_error}")
                                continue
                    
                    # 프록시 실패시 직접 연결 시도
                    try:
                        response = await client.get(self.base_url, params=params)
                        logger.info(f"httpx 응답 코드: {response.status_code}")
                        logger.info(f"응답 헤더: {dict(response.headers)[:200]}")  # 헤더 일부만
                        
                        if response.status_code == 502:
                            logger.error("502 Bad Gateway - Railway 프록시 문제")
                            
                            # requests 라이브러리로 동기 호출 시도
                            import requests
                            logger.info("requests 라이브러리로 재시도")
                            
                            sync_response = await asyncio.get_event_loop().run_in_executor(
                                None,
                                lambda: requests.get(
                                    self.base_url,
                                    params=params,
                                    timeout=5,
                                    verify=False,
                                    headers={
                                        'User-Agent': 'Mozilla/5.0',
                                        'Accept': 'application/json'
                                    }
                                )
                            )
                            
                            logger.info(f"requests 응답 코드: {sync_response.status_code}")
                            
                            if sync_response.status_code == 200:
                                data = sync_response.json()
                                if data.get('response', {}).get('status') == 'OK':
                                    result = data['response']['result']
                                    if 'point' in result:
                                        point = result['point']
                                        logger.info(f"✅ requests 성공! 좌표: {point}")
                                        return {
                                            'success': True,
                                            'x': float(point['x']),
                                            'y': float(point['y']),
                                            'address': query,
                                            'method': 'requests_sync',
                                            'raw_data': data
                                        }
                        
                        elif response.status_code == 200:
                            data = response.json()
                            if data.get('response', {}).get('status') == 'OK':
                                result = data['response']['result']
                                if 'point' in result:
                                    point = result['point']
                                    logger.info(f"✅ httpx 성공! 좌표: {point}")
                                    return {
                                        'success': True,
                                        'x': float(point['x']),
                                        'y': float(point['y']),
                                        'address': query,
                                        'method': 'httpx_async',
                                        'raw_data': data
                                    }
                        else:
                            logger.error(f"V-World API 오류: {response.status_code}")
                            logger.error(f"응답 내용: {response.text[:500]}")
                            
                    except Exception as e:
                        logger.error(f"V-World API 호출 예외: {type(e).__name__}: {str(e)}")
                        
                        # 마지막 시도: urllib로 직접 호출
                        try:
                            import urllib.request
                            import urllib.parse
                            import json
                            
                            logger.info("urllib로 최종 시도")
                            query_string = urllib.parse.urlencode(params)
                            url = f"{self.base_url}?{query_string}"
                            
                            req = urllib.request.Request(url, headers={
                                'User-Agent': 'Mozilla/5.0'
                            })
                            
                            with urllib.request.urlopen(req, timeout=5) as response:
                                if response.status == 200:
                                    data = json.loads(response.read().decode('utf-8'))
                                    if data.get('response', {}).get('status') == 'OK':
                                        result = data['response']['result']
                                        if 'point' in result:
                                            point = result['point']
                                            logger.info(f"✅ urllib 성공! 좌표: {point}")
                                            return {
                                                'success': True,
                                                'x': float(point['x']),
                                                'y': float(point['y']),
                                                'address': query,
                                                'method': 'urllib_direct',
                                                'raw_data': data
                                            }
                        except Exception as urllib_error:
                            logger.error(f"urllib도 실패: {urllib_error}")
                        
            except Exception as e:
                logger.error(f"V-World API 연결 오류: {str(e)}")
            
            # 빠른 fallback
            logger.warning(f"V-World API 빠른 실패, fallback 사용: {query}")
            return await self._get_fallback_coordinates(query)

        except Exception as e:
            logger.error(f"주소 검색 중 오류 발생: {str(e)}")
            return await self._get_fallback_coordinates(query)

    async def _try_alternative_proxies(self, params: Dict[str, str], query: str) -> Dict[str, Any]:
        """대안 프록시들을 순차적으로 시도"""
        
        # 1. 공개 CORS 프록시들 우선 시도 (더 안정적)
        proxy_services = [
            "https://api.allorigins.win/raw?url=",
            "https://corsproxy.io/?"
        ]
        
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        target_url = f"{self.base_url}?{query_string}"
        
        for proxy in proxy_services:
            logger.info(f"🔄 공개 프록시 시도: {proxy}")
            try:
                proxy_url = f"{proxy}{urllib.parse.quote(target_url)}"
                
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(proxy_url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if data.get('response', {}).get('status') == 'OK':
                                result = data['response']['result']
                                if 'point' in result:
                                    point = result['point']
                                    logger.info(f"✅ 공개 프록시 성공! 좌표: {point}")
                                    return {
                                        'success': True,
                                        'x': float(point['x']),
                                        'y': float(point['y']),
                                        'address': query,
                                        'method': f'cors_proxy_{proxy.split("/")[2]}',
                                        'raw_data': data
                                    }
                        except Exception as parse_error:
                            logger.warning(f"프록시 응답 파싱 실패: {parse_error}")
                            
            except Exception as e:
                logger.warning(f"공개 프록시 {proxy} 실패: {str(e)}")
                continue
        
        # 2. 최후의 수단으로 Vercel 프록시 시도 (인증 문제가 있을 수 있음)
        if self.proxy_url:
            logger.info(f"🔄 최후 수단 Vercel 프록시 시도: {self.proxy_url}")
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    proxy_response = await client.get(self.proxy_url, params=params)
                    logger.info(f"Vercel 프록시 응답 코드: {proxy_response.status_code}")
                    
                    if proxy_response.status_code == 200:
                        data = proxy_response.json()
                        if data.get('response', {}).get('status') == 'OK':
                            result = data['response']['result']
                            if 'point' in result:
                                point = result['point']
                                logger.info(f"✅ Vercel 프록시 성공! 좌표: {point}")
                                return {
                                    'success': True,
                                    'x': float(point['x']),
                                    'y': float(point['y']),
                                    'address': query,
                                    'method': 'vercel_proxy',
                                    'raw_data': data
                                }
                    elif proxy_response.status_code == 401:
                        logger.warning("Vercel 프록시 인증 필요 - Vercel 프로젝트를 Public으로 변경하세요")
            except Exception as e:
                logger.error(f"Vercel 프록시 실패: {str(e)}")
        
        logger.warning("모든 프록시 시도 실패 - fallback으로 진행")
        return None

    async def _get_fallback_coordinates(self, address: str) -> Dict[str, Any]:
        """V-World API 실패시 Nominatim API로 시도 후 임시 좌표 제공"""
        logger.warning(f"V-World API 연결 실패, Nominatim API로 재시도: {address}")
        
        # 1. Nominatim API 시도 (OpenStreetMap - 무료) - 다양한 쿼리 패턴으로 시도
        try:
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            
            # 여러 검색 패턴 시도
            search_patterns = [
                f"{address}, South Korea",
                f"{address}, 대한민국",
                address,  # 원본 주소만
                address.replace("특별시", "").replace("광역시", ""),  # 단순화된 주소
            ]
            
            for pattern in search_patterns:
                logger.info(f"Nominatim 검색 패턴: {pattern}")
                params = {
                    'q': pattern,
                    'format': 'json',
                    'limit': 3,  # 더 많은 결과 요청
                    'addressdetails': 1,
                    'accept-language': 'ko,en'
                }
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(nominatim_url, params=params, headers={
                        'User-Agent': 'Real-Estate-Platform/1.0 (contact@example.com)'
                    })
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Nominatim API 응답 ({pattern}): {len(data) if data else 0}건")
                        
                        if data and len(data) > 0:
                            for item in data:
                                try:
                                    lat = float(item['lat'])
                                    lon = float(item['lon'])
                                    
                                    # 한국 좌표 범위 확인 (대략적인 검증)
                                    if 33.0 <= lat <= 43.0 and 124.0 <= lon <= 132.0:
                                        logger.info(f"✅ Nominatim API 성공: lat={lat}, lon={lon} (패턴: {pattern})")
                                        return {
                                            'success': True,
                                            'x': lon,  # 경도
                                            'y': lat,  # 위도
                                            'address': address,
                                            'fallback': False,  # Nominatim은 실제 좌표이므로 fallback이 아님
                                            'method': 'nominatim',
                                            'note': f'Nominatim API 사용 (검색패턴: {pattern})'
                                        }
                                    else:
                                        logger.warning(f"좌표 범위 벗어남: lat={lat}, lon={lon}")
                                except (ValueError, TypeError, KeyError) as parse_error:
                                    logger.warning(f"좌표 파싱 오류: {parse_error}")
                                    continue
                        else:
                            logger.info(f"패턴 '{pattern}' 검색 결과 없음")
                    else:
                        logger.warning(f"Nominatim HTTP 오류: {response.status_code}")
                        
        except Exception as e:
            logger.warning(f"Nominatim API 호출 오류: {str(e)}")
        
        # 2. 기존 정적 fallback 좌표 (더 많은 지역 추가)
        temp_coords = {
            '테헤란로': {'x': 127.0276, 'y': 37.4979},
            '강남구': {'x': 127.0276, 'y': 37.4979},
            '강남': {'x': 127.0276, 'y': 37.4979},
            '서초구': {'x': 127.0276, 'y': 37.4833},
            '서초': {'x': 127.0276, 'y': 37.4833},
            '서울특별시': {'x': 126.9780, 'y': 37.5665},
            '서울시': {'x': 126.9780, 'y': 37.5665},
            '서울': {'x': 126.9780, 'y': 37.5665},
            '종로구': {'x': 126.9784, 'y': 37.5703},
            '종로': {'x': 126.9784, 'y': 37.5703},
            '중구': {'x': 126.9996, 'y': 37.5640},
            '마포구': {'x': 126.9015, 'y': 37.5637},
            '영등포구': {'x': 126.8963, 'y': 37.5264},
            '부산': {'x': 129.0756, 'y': 35.1796},
            '대구': {'x': 128.6014, 'y': 35.8714},
            '인천': {'x': 126.7052, 'y': 37.4563},
            '경기도': {'x': 127.2018, 'y': 37.4138},
            '수원': {'x': 127.0286, 'y': 37.2636},
            '성남': {'x': 127.1378, 'y': 37.4449},
            '고양': {'x': 126.8577, 'y': 37.6564},
        }
        
        # 주소에서 키워드 매칭 (긴 키워드부터 매칭)
        sorted_keywords = sorted(temp_coords.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword in address:
                coords = temp_coords[keyword]
                logger.info(f"정적 fallback 좌표 매칭: {keyword} -> {coords}")
                return {
                    'success': True,
                    'x': coords['x'],
                    'y': coords['y'],
                    'address': address,
                    'fallback': True,
                    'method': 'static',
                    'note': f'V-World API 연결 문제로 임시 좌표 사용 ({keyword} 기준)'
                }
        
        # 기본값: 서울시청 좌표
        logger.info("기본 fallback 좌표 사용 (서울시청)")
        return {
            'success': True,
            'x': 126.9780,
            'y': 37.5665,
            'address': address,
            'fallback': True,
            'method': 'default',
            'note': 'V-World API 연결 문제로 기본 좌표 사용 (서울시청)'
        }


class BuildingLedgerService:
    """건축물대장 정보 조회 서비스"""

    def __init__(self):
        self.api_key = settings.BUILDING_API_KEY
        self.timeout = settings.API_TIMEOUT
        self.retry_count = settings.API_RETRY_COUNT

        # URL 디코딩된 API 키 사용
        decoded_key = self.api_key.replace(
            '%2B', '+').replace('%3D', '=') if self.api_key else None

        if decoded_key:
            self.api = BuildingLedger(decoded_key)
        else:
            logger.error("건축물대장 API 키가 설정되지 않았습니다")
            self.api = None

    def _parse_address_to_codes(self, address: str) -> Dict[str, str]:
        """
        주소에서 시군구코드와 법정동코드 추출

        Args:
            address: 주소 문자열

        Returns:
            시군구코드, 법정동코드, 번지 정보
        """
        try:
            # 기본 지역코드 데이터 로드
            code_df = pdr.code_bdong()

            # 주소 파싱 로직
            if '서울' in address:
                if '강남구' in address:
                    sigungu_code = '11680'
                    if '역삼동' in address:
                        bdong_code = '10300'
                    elif '삼성동' in address:
                        bdong_code = '10400'
                    else:
                        bdong_code = '10300'  # 기본값
                elif '서초구' in address:
                    sigungu_code = '11650'
                    bdong_code = '10600'
                else:
                    sigungu_code = '11110'  # 서울 종로구 기본값
                    bdong_code = '10100'
            elif '경기' in address:
                if '성남시' in address and '분당구' in address:
                    sigungu_code = '41135'
                    bdong_code = '11000'  # 백현동
                else:
                    sigungu_code = '41111'  # 경기 수원시 기본값
                    bdong_code = '10100'
            else:
                # 기본값 설정 (서울 강남구)
                sigungu_code = '11680'
                bdong_code = '10300'

            # 번지 추출 (간단한 정규식 패턴)
            import re
            number_pattern = r'(\d+)(?:-(\d+))?'
            match = re.search(number_pattern, address)

            if match:
                bun = match.group(1).zfill(4)  # 본번 4자리
                ji = (match.group(2) or '0').zfill(4)  # 부번 4자리
            else:
                bun = '0001'
                ji = '0000'

            return {
                'sigungu_code': sigungu_code,
                'bdong_code': bdong_code,
                'bun': bun,
                'ji': ji
            }

        except Exception as e:
            logger.error(f"주소 파싱 오류: {str(e)}")
            # 기본값 반환
            return {
                'sigungu_code': '11680',  # 서울 강남구
                'bdong_code': '10300',    # 역삼동
                'bun': '0001',
                'ji': '0000'
            }

    async def get_building_info(self, address: str) -> Dict[str, Any]:
        """
        주소 기반 건축물대장 정보 조회

        Args:
            address: 조회할 주소

        Returns:
            건축물대장 정보가 포함된 딕셔너리
        """
        if not self.api:
            return {'success': False, 'error': 'API 키가 설정되지 않았습니다'}

        try:
            # 주소에서 코드 추출
            codes = self._parse_address_to_codes(address)

            logger.info(f"건축물대장 조회 시작: {address}")
            logger.info(f"코드 정보: {codes}")

            # 비동기 실행을 위한 래퍼
            def sync_api_call():
                try:
                    # 기본개요 조회
                    basic_info = self.api.get_data(
                        ledger_type="기본개요",
                        sigungu_code=codes['sigungu_code'],
                        bdong_code=codes['bdong_code'],
                        bun=codes['bun'],
                        ji=codes['ji']
                    )

                    # 총괄표제부 조회
                    summary_info = self.api.get_data(
                        ledger_type="총괄표제부",
                        sigungu_code=codes['sigungu_code'],
                        bdong_code=codes['bdong_code'],
                        bun=codes['bun'],
                        ji=codes['ji']
                    )

                    # 표제부 조회
                    title_info = self.api.get_data(
                        ledger_type="표제부",
                        sigungu_code=codes['sigungu_code'],
                        bdong_code=codes['bdong_code'],
                        bun=codes['bun'],
                        ji=codes['ji']
                    )

                    # 전유부 조회 (집합건물의 경우)
                    exclusive_info = None
                    try:
                        exclusive_info = self.api.get_data(
                            ledger_type="전유부",
                            sigungu_code=codes['sigungu_code'],
                            bdong_code=codes['bdong_code'],
                            bun=codes['bun'],
                            ji=codes['ji']
                        )
                        logger.info("전유부 정보 조회 완료")
                    except Exception as e:
                        logger.warning(f"전유부 정보 조회 실패 (단독건물일 수 있음): {str(e)}")

                    return {
                        'basic_info': basic_info,
                        'summary_info': summary_info,
                        'title_info': title_info,
                        'exclusive_info': exclusive_info
                    }
                except Exception as e:
                    logger.error(f"PublicDataReader API 호출 오류: {str(e)}")
                    return None

            # 비동기 실행
            raw_data = await asyncio.get_event_loop().run_in_executor(
                None, sync_api_call
            )

            if raw_data is None:
                return {'success': False, 'error': '건축물대장 정보를 찾을 수 없습니다'}

            # 데이터 정규화
            processed_data = self._process_building_data(raw_data, address)

            return {
                'success': True,
                'data': processed_data,
                'address': address,
                'codes': codes
            }

        except Exception as e:
            logger.error(f"건축물대장 조회 오류: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _process_building_data(
            self, raw_data: Dict, address: str) -> Dict[str, Any]:
        """
        원시 API 데이터를 매물 정보 형태로 가공

        Args:
            raw_data: PublicDataReader에서 받은 원시 데이터
            address: 조회 주소

        Returns:
            가공된 건축물 정보
        """
        try:
            processed = {
                'address': address,
                'building_info': {},
                'area_info': {},
                'structure_info': {},
                'usage_info': {},
                'exclusive_info': {}  # 전유부 정보 추가
            }

            # 기본개요 정보 처리
            if 'basic_info' in raw_data and not raw_data['basic_info'].empty:
                basic = raw_data['basic_info'].iloc[0]
                processed['building_info'] = {
                    'building_name': basic.get('건물명', ''),
                    'building_number': basic.get('건물번호', ''),
                    'new_address': basic.get('신주소', ''),
                    'old_address': basic.get('구주소', ''),
                    'building_use': basic.get('주용도코드명', ''),
                    'structure': basic.get('구조코드명', ''),
                    'total_floor': basic.get('지상층수', 0),
                    'basement_floor': basic.get('지하층수', 0),
                    'elevator_count': basic.get('승강기수', 0)
                }

            # 총괄표제부 정보 처리
            if 'summary_info' in raw_data and not raw_data['summary_info'].empty:
                summary = raw_data['summary_info'].iloc[0]
                processed['area_info'] = {
                    'site_area': summary.get('대지면적', 0),
                    'building_area': summary.get('건축면적', 0),
                    'total_floor_area': summary.get('연면적', 0),
                    'building_coverage_ratio': summary.get('건폐율', 0),
                    'floor_area_ratio': summary.get('용적률', 0)
                }

            # 표제부 정보 처리
            if 'title_info' in raw_data and not raw_data['title_info'].empty:
                title = raw_data['title_info'].iloc[0]
                processed['structure_info'] = {
                    'main_structure': title.get('주구조', ''),
                    'roof_structure': title.get('지붕구조', ''),
                    'completion_date': title.get('사용승인일', ''),
                    'permit_date': title.get('건축허가일', '')
                }

            # 전유부 정보 처리 (집합건물의 경우)
            if 'exclusive_info' in raw_data and raw_data['exclusive_info'] is not None and not raw_data['exclusive_info'].empty:
                exclusive_df = raw_data['exclusive_info']
                exclusive_units = []
                
                for _, row in exclusive_df.iterrows():
                    unit_info = {
                        'unit_number': row.get('호수', ''),
                        'unit_area': row.get('전용면적', 0),
                        'unit_use': row.get('주용도', ''),
                        'floor_number': row.get('층수', ''),
                        'unit_structure': row.get('구조', ''),
                        'created_date': row.get('생성일자', ''),
                        'change_date': row.get('변동일자', '')
                    }
                    exclusive_units.append(unit_info)
                
                processed['exclusive_info'] = {
                    'total_units': len(exclusive_units),
                    'units': exclusive_units,
                    'has_exclusive_data': True
                }
                logger.info(f"전유부 정보 처리 완료: {len(exclusive_units)}개 호실")
            else:
                processed['exclusive_info'] = {
                    'total_units': 0,
                    'units': [],
                    'has_exclusive_data': False
                }
                logger.info("전유부 정보 없음 (단독건물 또는 데이터 없음)")

            return processed

        except Exception as e:
            logger.error(f"건축물 데이터 가공 오류: {str(e)}")
            return {
                'address': address,
                'building_info': {},
                'area_info': {},
                'structure_info': {},
                'usage_info': {},
                'error': str(e)
            }


class IntegratedPublicDataService:
    """통합 공공데이터 조회 서비스"""

    def __init__(self):
        self.address_service = AddressSearchService()
        self.building_service = BuildingLedgerService()
        # 토지 서비스는 지연 임포트로 처리
        self._land_service = None

    async def analyze_property_by_address(
            self, address: str) -> Dict[str, Any]:
        """
        주소 기반 매물 종합 분석

        Args:
            address: 분석할 주소

        Returns:
            종합 분석 결과
        """
        logger.info(f"🚀 IntegratedPublicDataService.analyze_property_by_address 시작: {address}")
        
        result = {
            'success': True,
            'address': address,
            'address_info': {},
            'building_info': {},
            'land_info': {},  # 토지 정보 추가
            'errors': []
        }

        try:
            # 1. 주소 검색 및 좌표 조회
            logger.info(f"📍 주소 검색 서비스 호출 시작: {address}")
            logger.info(f"🔑 address_service 인스턴스: {type(self.address_service)}")
            
            address_result = await self.address_service.search_address(address)
            logger.info(f"📍 주소 검색 서비스 호출 완료: {address_result}")

            if address_result['success']:
                result['address_info'] = address_result
                logger.info(f"주소 검색 완료: {address}")
            else:
                result['errors'].append(
                    f"주소 검색 실패: {address_result.get('error', '알 수 없는 오류')}")
                logger.warning(f"주소 검색 실패: {address}")

            # 2. 건축물대장 정보 조회
            logger.info(f"건축물대장 조회 시작: {address}")
            building_result = await self.building_service.get_building_info(address)

            if building_result['success']:
                result['building_info'] = building_result
                logger.info(f"건축물대장 조회 완료: {address}")
            else:
                result['errors'].append(
                    f"건축물대장 조회 실패: {building_result.get('error', '알 수 없는 오류')}")
                logger.warning(f"건축물대장 조회 실패: {address}")

            # 3. 토지 정보 조회 (개선된 주소검색 포함)
            await self._analyze_land_info(address, result)

            # 4. 전체 성공 여부 판단 (Fallback 사용 시 경고 포함)
            address_info = result.get('address_info', {})
            is_fallback = address_info.get('fallback', False)
            
            if not result['address_info'] and not result['building_info'] and not result['land_info']:
                result['success'] = False
                result['message'] = '모든 공공데이터 조회에 실패했습니다'
            elif is_fallback and result['errors']:
                result['success'] = True  # 기술적으로는 성공이지만 경고 필요
                result['message'] = f'⚠️ V-World API 연결 실패로 임시 좌표 사용 (정확도 낮음), 오류: {len(result["errors"])}건'
                result['warning'] = 'V-World API 502 오류로 인해 정확한 좌표 대신 임시 좌표를 사용했습니다'
            elif result['errors']:
                result['message'] = f'일부 데이터 조회 실패: {len(result["errors"])}건'
            else:
                result['message'] = '공공데이터 조회 완료'

            logger.info(f"매물 분석 완료: {address}, 성공: {result['success']}")
            return result

        except Exception as e:
            logger.error(f"매물 분석 오류: {str(e)}")
            result['success'] = False
            result['errors'].append(str(e))
            result['message'] = '매물 분석 중 오류가 발생했습니다'
            return result

    async def _analyze_land_info(self, address: str, result: Dict[str, Any]):
        """
        토지 정보 분석 (비동기 헬퍼 메서드)

        Args:
            address: 분석할 주소
            result: 결과 딕셔너리 (참조로 수정)
        """
        try:
            # 지연 임포트로 순환 임포트 방지
            if self._land_service is None:
                from services.land_api import IntegratedLandDataService
                self._land_service = IntegratedLandDataService()

            logger.info(f"토지 정보 조회 시작: {address}")
            land_result = await self._land_service.analyze_land_by_address(address)

            if land_result['success']:
                result['land_info'] = land_result
                logger.info(f"토지 정보 조회 완료: {address}")

                # 기존 주소 검색이 실패한 경우 토지 API에서 얻은 주소로 대체
                if not result.get(
                        'address_info',
                        {}).get('success') and land_result.get(
                        'address_search',
                        {}).get('success'):
                    result['address_info'] = land_result['address_search']
                    logger.info(f"토지 API에서 주소 정보 획득: {address}")
            else:
                result['errors'].append(
                    f"토지 정보 조회 실패: {land_result.get('message', '알 수 없는 오류')}")
                logger.warning(f"토지 정보 조회 실패: {address}")

        except Exception as e:
            logger.error(f"토지 정보 분석 오류: {str(e)}")
            result['errors'].append(f"토지 정보 분석 오류: {str(e)}")
