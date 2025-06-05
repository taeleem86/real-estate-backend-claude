"""
환경변수 및 애플리케이션 설정 관리 (런웨이 배포 최적화)
"""
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000  # Render.com에서 $PORT 환경변수로 자동 설정됨
    DEBUG: bool = False  # 프로덕션 기본값: False

    # CORS 설정 (프로덕션 보안 강화)
    CORS_ORIGINS: str = "*"  # 프로덕션에서는 실제 도메인으로 변경

    # Supabase 설정 (필수)
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # 공공데이터포털 API 키
    VWORLD_API_KEY: Optional[str] = None  # 주소검색 API
    BUILDING_API_KEY: Optional[str] = None  # 건축물대장정보
    LAND_REGULATION_API_KEY: Optional[str] = None  # 토지이용규제정보
    LAND_API_KEY: Optional[str] = None  # 토지임야목록

    # 로깅 설정
    LOG_LEVEL: str = "INFO"

    # 보안 설정 (프로덕션 필수)
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"

    # 외부 API 설정
    API_TIMEOUT: int = 15
    API_RETRY_COUNT: int = 3

    # 스크래핑 설정
    SCRAPING_DELAY: int = 2
    USER_AGENT: str = "RealEstateAnalysisBot/1.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS origins를 리스트로 반환"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# 설정 인스턴스 생성
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스 반환"""
    return settings
