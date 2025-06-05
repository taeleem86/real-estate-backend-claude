"""
Supabase 데이터베이스 연결 및 초기화
"""
import logging
from typing import Optional
from supabase import create_client, Client
from core.config import settings

logger = logging.getLogger(__name__)

# Supabase 클라이언트 인스턴스
supabase: Optional[Client] = None


async def init_database() -> None:
    """데이터베이스 초기화 및 연결 테스트"""
    global supabase

    try:
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            logger.warning("Supabase 설정이 없습니다. 환경변수를 확인해주세요.")
            return

        # Supabase 클라이언트 생성
        supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        # 연결 테스트 및 테이블 확인
        # await create_tables_if_not_exists()  # 기존 테이블이 있으므로 주석처리
        logger.info("✅ Supabase 데이터베이스 연결 완료")
        logger.info("✅ 테스트 모드: 데이터베이스 초기화 완료")

    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        # 연결 실패 시에도 서버는 계속 실행
        supabase = None


async def create_tables_if_not_exists() -> None:
    """필요한 테이블들이 존재하지 않으면 생성"""
    global supabase

    if not supabase:
        return

    try:
        # 테이블 존재 확인 (실제로는 Supabase 대시보드에서 테이블을 만들고 여기서는 연결만 확인)

        # listings 테이블 존재 확인
        try:
            properties_check = supabase.table('listings').select(
                'count', count='exact').limit(1).execute()
            logger.info("✅ listings 테이블 확인됨")
        except Exception:
            logger.warning(
                "⚠️ listings 테이블이 존재하지 않습니다. Supabase 대시보드에서 생성해주세요.")

        # analysis_results 테이블 존재 확인
        try:
            analysis_check = supabase.table('analysis_results').select(
                'count', count='exact').limit(1).execute()
            logger.info("✅ analysis_results 테이블 확인됨")
        except Exception:
            logger.warning(
                "⚠️ analysis_results 테이블이 존재하지 않습니다. Supabase 대시보드에서 생성해주세요.")

        # sections 테이블 존재 확인
        try:
            sections_check = supabase.table('sections').select(
                'count', count='exact').limit(1).execute()
            logger.info("✅ sections 테이블 확인됨")
        except Exception:
            logger.warning(
                "⚠️ sections 테이블이 존재하지 않습니다. Supabase 대시보드에서 생성해주세요.")

    except Exception as e:
        logger.error(f"테이블 확인 중 오류 발생: {e}")


def get_database() -> Optional[Client]:
    """데이터베이스 클라이언트 반환"""
    return supabase


async def close_database() -> None:
    """데이터베이스 연결 종료"""
    global supabase
    if supabase:
        # Supabase는 자동으로 연결 관리하므로 특별한 종료 작업 불필요
        logger.info("✅ 데이터베이스 연결 종료")
        supabase = None


def get_table_schemas() -> dict:
    """Supabase에서 생성할 테이블 스키마 정의 반환"""
    return {
        "listings": """
        CREATE TABLE IF NOT EXISTS listings (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            property_number VARCHAR(50) UNIQUE NOT NULL,
            property_type VARCHAR(20) NOT NULL,
            transaction_type VARCHAR(20) NOT NULL,

            -- 주소 정보 (JSONB)
            address_info JSONB NOT NULL DEFAULT '{}',

            -- 면적 정보 (JSONB)
            area_info JSONB NOT NULL DEFAULT '{}',

            -- 가격 정보 (JSONB)
            price_info JSONB NOT NULL DEFAULT '{}',

            -- 매물 설명 (JSONB)
            property_description JSONB NOT NULL DEFAULT '{}',

            -- 상태 및 채널 정보
            status VARCHAR(20) DEFAULT 'pending',
            channel_info JSONB DEFAULT '{}',

            -- 분석 결과 연결
            building_analysis_id UUID,
            land_analysis_id UUID,
            competitor_analysis_id UUID,
            marketing_content TEXT,

            -- 메타데이터
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- 인덱스 생성
        CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status);
        CREATE INDEX IF NOT EXISTS idx_listings_type ON listings(property_type);
        CREATE INDEX IF NOT EXISTS idx_listings_created_at ON listings(created_at);
        """,

        "analysis_results": """
        CREATE TABLE IF NOT EXISTS analysis_results (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            property_id UUID NOT NULL,
            analysis_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',

            -- 원본 데이터
            raw_data JSONB DEFAULT '{}',

            -- 각 분석 유형별 데이터
            building_data JSONB,
            land_data JSONB,
            competitor_data JSONB,

            -- 메타데이터
            analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            analysis_duration FLOAT,
            data_source VARCHAR(100),
            api_version VARCHAR(20),
            error_message TEXT,

            FOREIGN KEY (property_id) REFERENCES listings(id) ON DELETE CASCADE
        );

        -- 인덱스 생성
        CREATE INDEX IF NOT EXISTS idx_analysis_property_id ON analysis_results(property_id);
        CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type);
        CREATE INDEX IF NOT EXISTS idx_analysis_status ON analysis_results(status);
        """,

        "sections": """
        CREATE TABLE IF NOT EXISTS sections (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            section_type VARCHAR(50) NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            sort_order INTEGER DEFAULT 0,
            property_ids JSONB DEFAULT '[]',

            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- 인덱스 생성
        CREATE INDEX IF NOT EXISTS idx_sections_active ON sections(is_active);
        CREATE INDEX IF NOT EXISTS idx_sections_sort ON sections(sort_order);
        CREATE INDEX IF NOT EXISTS idx_sections_type ON sections(section_type);
        """
    }
