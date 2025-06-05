"""
Supabase MCP를 사용한 통합 테스트
Row Level Security(RLS) 문제를 해결하고 직접 DB 테스트를 수행
"""

import os
import sys
import logging
from datetime import datetime
from uuid import uuid4
import asyncio

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from supabase import create_client
from core.config import settings
from models.property import PropertyCreate, PropertyUpdate
from services.property_service import PropertyService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupabaseMCPTest:
    """Supabase MCP를 사용한 테스트 클래스"""
    
    def __init__(self):
        """테스트 환경 초기화"""
        # SERVICE_ROLE_KEY를 사용하여 RLS 우회
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY
        if not self.service_key:
            logger.warning("SERVICE_ROLE_KEY가 설정되지 않았습니다. ANON_KEY를 사용합니다.")
            self.service_key = settings.SUPABASE_ANON_KEY
            
        # 서비스 롤 클라이언트 생성 (RLS 우회)
        self.client = create_client(
            settings.SUPABASE_URL,
            self.service_key
        )
        
        # PropertyService 인스턴스 생성
        self.property_service = PropertyService(supabase_client=self.client)
        
    async def test_create_listing_with_service_role(self):
        """서비스 롤을 사용한 리스팅 생성 테스트"""
        logger.info("=== 서비스 롤을 사용한 리스팅 생성 테스트 시작 ===")
        
        # 테스트 데이터 준비
        test_data = PropertyCreate(
            property_type="사무실",
            transaction_type="매매",
            property_description={
                "title": f"[MCP 테스트] 강남 테헤란로 프리미엄 사무실 - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "서비스 롤을 사용한 MCP 테스트입니다."
            },
            address_info={
                "address": "서울특별시 강남구 테헤란로 123",
                "city": "서울특별시",
                "district": "강남구",
                "dong": "역삼동"
            },
            area_info={
                "totalArea": 150.5,
                "exclusiveArea": 120.0,
                "landArea": 200.0,
                "buildingArea": 150.5
            },
            price_info={
                "salePrice": 5000000000,
                "deposit": None,
                "monthlyRent": None
            }
        )
        
        try:
            # 리스팅 생성
            result = await self.property_service.create_listing(test_data)
            
            if result:
                logger.info(f"✅ 리스팅 생성 성공: ID={result['id']}")
                logger.info(f"   - 제목: {result['title']}")
                logger.info(f"   - 주소: {result['display_address']}")
                logger.info(f"   - 상태: {result['status']}")
                return result['id']
            else:
                logger.error("❌ 리스팅 생성 실패: 결과가 없습니다.")
                return None
                
        except Exception as e:
            logger.error(f"❌ 리스팅 생성 중 오류 발생: {e}")
            return None
    
    async def test_direct_db_operations(self):
        """직접 DB 작업 테스트 (RLS 우회)"""
        logger.info("\n=== 직접 DB 작업 테스트 시작 ===")
        
        try:
            # 1. 직접 INSERT
            logger.info("1. 직접 INSERT 테스트")
            test_id = str(uuid4())
            insert_data = {
                "id": test_id,
                "title": f"[직접 DB 테스트] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "deal_type": "매매",
                "property_type": "토지",
                "price": "1000000",
                "display_address": "서울시 서초구 서초동",
                "sido": "서울특별시",
                "sigungu": "서초구",
                "eupmyeondong": "서초동",
                "address": "서울시 서초구 서초동 123-45",
                "status": "거래가능"
            }
            
            result = self.client.table("listings").insert(insert_data).execute()
            if result.data:
                logger.info(f"✅ 직접 INSERT 성공: {result.data[0]['id']}")
            else:
                logger.error("❌ 직접 INSERT 실패")
                
            # 2. 조회 테스트
            logger.info("\n2. 조회 테스트")
            select_result = self.client.table("listings").select("*").eq("id", test_id).execute()
            if select_result.data:
                logger.info(f"✅ 조회 성공: {select_result.data[0]['title']}")
            
            # 3. 업데이트 테스트
            logger.info("\n3. 업데이트 테스트")
            update_result = self.client.table("listings").update({
                "title": f"[업데이트됨] {datetime.now().strftime('%H:%M:%S')}"
            }).eq("id", test_id).execute()
            if update_result.data:
                logger.info(f"✅ 업데이트 성공")
            
            # 4. 삭제 테스트
            logger.info("\n4. 삭제 테스트")
            delete_result = self.client.table("listings").delete().eq("id", test_id).execute()
            logger.info("✅ 삭제 완료")
            
        except Exception as e:
            logger.error(f"❌ 직접 DB 작업 중 오류: {e}")
    
    async def test_property_service_operations(self):
        """PropertyService를 통한 전체 CRUD 테스트"""
        logger.info("\n=== PropertyService CRUD 테스트 시작 ===")
        
        created_id = None
        
        try:
            # 1. 생성
            created_id = await self.test_create_listing_with_service_role()
            
            if created_id:
                # 2. 조회
                logger.info("\n--- 리스팅 조회 테스트 ---")
                listing = await self.property_service.get_listing(created_id)
                if listing:
                    logger.info(f"✅ 조회 성공: {listing['title']}")
                
                # 3. 수정
                logger.info("\n--- 리스팅 수정 테스트 ---")
                update_data = PropertyUpdate(
                    title=f"[수정됨] {datetime.now().strftime('%H:%M:%S')}",
                    status="pending"
                )
                updated = await self.property_service.update_listing(created_id, update_data)
                if updated:
                    logger.info(f"✅ 수정 성공: {updated['title']}")
                
                # 4. 검색
                logger.info("\n--- 리스팅 검색 테스트 ---")
                search_results = await self.property_service.search_listings("테헤란로")
                logger.info(f"✅ 검색 결과: {len(search_results)}건")
                
                # 5. 통계
                logger.info("\n--- 통계 조회 테스트 ---")
                stats = await self.property_service.get_listing_statistics()
                logger.info(f"✅ 전체 리스팅 수: {stats['total_count']}")
                logger.info(f"   상태별 분포: {stats['status_distribution']}")
                
                # 6. 삭제
                logger.info("\n--- 리스팅 삭제 테스트 ---")
                deleted = await self.property_service.delete_listing(created_id)
                if deleted:
                    logger.info("✅ 삭제 성공")
                    
        except Exception as e:
            logger.error(f"❌ PropertyService 테스트 중 오류: {e}")
            
            # 오류 발생 시 생성된 데이터 정리
            if created_id:
                try:
                    await self.property_service.delete_listing(created_id)
                    logger.info("테스트 데이터 정리 완료")
                except:
                    pass


async def main():
    """메인 테스트 실행"""
    logger.info("Supabase MCP 통합 테스트 시작")
    logger.info(f"프로젝트 ID: scgeybkrraddyawwwtyn")
    logger.info(f"URL: {settings.SUPABASE_URL}")
    
    tester = SupabaseMCPTest()
    
    # 직접 DB 작업 테스트
    await tester.test_direct_db_operations()
    
    # PropertyService 테스트
    await tester.test_property_service_operations()
    
    logger.info("\n=== 모든 테스트 완료 ===")


if __name__ == "__main__":
    asyncio.run(main())
