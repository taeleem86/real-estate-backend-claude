"""
Supabase 데이터베이스 클라이언트 서비스
CRUD 연산 및 데이터베이스 상호작용 관리
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from supabase import Client
from core.database import get_database
from models.property import Property, PropertyCreate, PropertyUpdate
from models.analysis import AnalysisResult, AnalysisResultCreate, Section, SectionCreate

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase 데이터베이스 클라이언트"""

    def __init__(self):
        self.db: Optional[Client] = None

    async def get_client(self) -> Optional[Client]:
        """데이터베이스 클라이언트 가져오기"""
        if not self.db:
            self.db = get_database()
        return self.db

    # 리스팅 CRUD 연산 (매물 -> 리스팅으로 용어 변경)
    # Renamed method, param `listing_data` (type hint PropertyCreate is kept)
    async def create_listing(
            self,
            listing_data: PropertyCreate) -> Optional[Property]:
        """리스팅 생성"""
        try:
            client = await self.get_client()
            if not client:
                logger.error("데이터베이스 클라이언트를 가져올 수 없습니다.")
                return None

            # Pydantic 모델을 딕셔너리로 변환
            data = listing_data.dict()  # Use listing_data

            # 생성 시간 추가
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = datetime.now().isoformat()

            response = client.table('listings').insert(data).execute()

            if response.data:
                # Returns a Property model object
                return Property(**response.data[0])

            logger.error(f"리스팅 생성 실패: {response}")
            return None

        except Exception as e:
            logger.error(f"리스팅 생성 중 오류 발생: {e}")
            return None

    # Renamed method and param
    async def get_listing(self, listing_id: UUID) -> Optional[Property]:
        """리스팅 조회"""
        try:
            client = await self.get_client()
            if not client:
                return None

            response = client.table('listings').select(
                '*').eq('id', str(listing_id)).execute()

            if response.data:
                # Returns a Property model object
                return Property(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"리스팅 조회 중 오류 발생: {e}")
            return None

    async def get_listings(  # Renamed method
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        # This is a filter for a characteristic, name can stay
        property_type: Optional[str] = None
    ) -> List[Property]:
        """리스팅 목록 조회"""
        try:
            client = await self.get_client()
            if not client:
                return []

            query = client.table('listings').select('*')

            # 필터 적용
            if status:
                query = query.eq('status', status)
            if property_type:
                query = query.eq('property_type', property_type)

            # 페이징 적용
            query = query.range(skip, skip + limit - 1)

            response = query.execute()

            if response.data:
                # Returns a list of Property model objects
                return [Property(**item) for item in response.data]

            return []

        except Exception as e:
            logger.error(f"리스팅 목록 조회 중 오류 발생: {e}")
            return []

    # Renamed method and params
    async def update_listing(
            self,
            listing_id: UUID,
            listing_data: PropertyUpdate) -> Optional[Property]:
        """리스팅 수정"""
        try:
            client = await self.get_client()
            if not client:
                return None

            # None이 아닌 필드만 추출
            data = listing_data.dict(exclude_unset=True)  # Use listing_data
            data['updated_at'] = datetime.now().isoformat()

            response = client.table('listings').update(
                data).eq('id', str(listing_id)).execute()

            if response.data:
                # Returns a Property model object
                return Property(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"리스팅 수정 중 오류 발생: {e}")
            return None

    async def delete_listing(self, listing_id: UUID) -> bool:  # Renamed method and param
        """리스팅 삭제"""
        try:
            client = await self.get_client()
            if not client:
                return False

            response = client.table('listings').delete().eq(
                'id', str(listing_id)).execute()

            return response.data is not None

        except Exception as e:
            logger.error(f"리스팅 삭제 중 오류 발생: {e}")
            return False

    # 분석 결과 CRUD 연산
    async def create_analysis_result(
            self, analysis_data: AnalysisResultCreate) -> Optional[AnalysisResult]:
        """분석 결과 생성"""
        try:
            client = await self.get_client()
            if not client:
                return None

            data = analysis_data.dict()
            data['analyzed_at'] = datetime.now().isoformat()

            response = client.table('analysis_results').insert(data).execute()

            if response.data:
                return AnalysisResult(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"분석 결과 생성 중 오류 발생: {e}")
            return None

    # Renamed listing_id here
    async def get_analysis_results_by_property(
            self, listing_id: UUID) -> List[AnalysisResult]:
        """매물별 분석 결과 조회"""
        try:
            client = await self.get_client()
            if not client:
                return []

            response = client.table('analysis_results').select(
                '*').eq('property_id', str(listing_id)).execute()  # Used listing_id

            if response.data:
                return [AnalysisResult(**item) for item in response.data]

            return []

        except Exception as e:
            logger.error(f"분석 결과 조회 중 오류 발생: {e}")
            return []

    # 섹션 CRUD 연산
    async def create_section(
            self,
            section_data: SectionCreate) -> Optional[Section]:
        """섹션 생성"""
        try:
            client = await self.get_client()
            if not client:
                return None

            data = section_data.dict()
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = datetime.now().isoformat()

            response = client.table('sections').insert(data).execute()

            if response.data:
                return Section(**response.data[0])

            return None

        except Exception as e:
            logger.error(f"섹션 생성 중 오류 발생: {e}")
            return None

    async def get_sections(self) -> List[Section]:
        """섹션 목록 조회"""
        try:
            client = await self.get_client()
            if not client:
                return []

            response = client.table('sections').select(
                '*').eq('is_active', True).order('sort_order').execute()

            if response.data:
                return [Section(**item) for item in response.data]

            return []

        except Exception as e:
            logger.error(f"섹션 목록 조회 중 오류 발생: {e}")
            return []


# 전역 클라이언트 인스턴스
supabase_client = SupabaseClient()


def get_supabase_client() -> SupabaseClient:
    """Supabase 클라이언트 인스턴스 반환"""
    return supabase_client
