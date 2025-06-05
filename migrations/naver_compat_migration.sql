-- 1. 기존 property 테이블 백업
CREATE TABLE IF NOT EXISTS property_backup AS TABLE property;

-- 2. property 테이블 필드명 네이버 표준으로 변경 및 신규 컬럼 추가
ALTER TABLE property RENAME COLUMN display_address TO address;
ALTER TABLE property RENAME COLUMN city_district TO city;
ALTER TABLE property ADD COLUMN district VARCHAR(100);
ALTER TABLE property RENAME COLUMN exclusive_area TO exclusiveArea;
ALTER TABLE property RENAME COLUMN total_floor_area TO totalArea;
ALTER TABLE property RENAME COLUMN land_area TO landArea;
ALTER TABLE property RENAME COLUMN building_area TO buildingArea;
ALTER TABLE property RENAME COLUMN common_area TO commonArea;
ALTER TABLE property RENAME COLUMN floor_count TO floorCount;
ALTER TABLE property RENAME COLUMN basement_count TO basementCount;
ALTER TABLE property RENAME COLUMN sale_price TO salePrice;
ALTER TABLE property RENAME COLUMN lease_deposit TO deposit;
ALTER TABLE property RENAME COLUMN monthly_rent TO monthlyRent;
ALTER TABLE property RENAME COLUMN exchange_value TO exchangeValue;
ALTER TABLE property RENAME COLUMN maintenance_fee TO maintenanceFee;
ALTER TABLE property RENAME COLUMN additional_costs TO additionalCosts;

-- owner_info 및 정보 분류 컬럼 추가
ALTER TABLE property ADD COLUMN owner_info JSONB;
ALTER TABLE property ADD COLUMN manual_data JSONB DEFAULT '{}'::jsonb;
ALTER TABLE property ADD COLUMN ocr_data JSONB DEFAULT '{}'::jsonb;
ALTER TABLE property ADD COLUMN api_data JSONB DEFAULT '{}'::jsonb;

-- 3. sections 테이블 생성
CREATE TABLE IF NOT EXISTS sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    theme_tags JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    "order" INTEGER DEFAULT 0
);

-- 4. property_sections 중간 테이블 생성
CREATE TABLE IF NOT EXISTS property_sections (
    property_id UUID REFERENCES property(id) ON DELETE CASCADE,
    section_id UUID REFERENCES sections(id) ON DELETE CASCADE,
    PRIMARY KEY (property_id, section_id)
);

-- 5. 기존 데이터 district 필드 변환 (city에서 추출)
UPDATE property SET district = city;

-- 6. 데이터 검증: 백업 테이블과 row count 비교
-- SELECT COUNT(*) FROM property_backup;
-- SELECT COUNT(*) FROM property; 

-- 네이버 호환성 및 섹션 관리 시스템 마이그레이션
-- 생성일: 2025-06-03
-- 목적: 네이버 표준 필드명 확정 및 홈페이지 섹션 관리 시스템 추가

-- 1. 백업 테이블 생성 (안전한 마이그레이션을 위해)
CREATE TABLE IF NOT EXISTS properties_backup AS 
SELECT * FROM properties;

-- 2. 섹션 관리 테이블 생성
CREATE TABLE IF NOT EXISTS sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    theme_tags JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    "order" INTEGER DEFAULT 0,
    display_title VARCHAR(200),
    display_subtitle VARCHAR(300),
    max_properties INTEGER,
    auto_update BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    property_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0
);

-- 3. 매물-섹션 관계 테이블 생성 (Many-to-Many)
CREATE TABLE IF NOT EXISTS property_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL,
    section_id UUID NOT NULL,
    is_featured BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by VARCHAR(100),
    auto_added BOOLEAN DEFAULT false,
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
    UNIQUE(property_id, section_id)
);

-- 4. Properties 테이블에 누락된 네이버 표준 필드 확인 및 추가
-- (Property 모델이 이미 네이버 표준을 사용하고 있으므로 대부분 존재할 것)

-- Address Info 필드 확인 및 추가
DO $$
BEGIN
    -- address_info 구조 확정 (네이버 표준)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'address_info') THEN
        ALTER TABLE properties ADD COLUMN address_info JSONB;
    END IF;
    
    -- area_info 구조 확정 (네이버 표준)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'area_info') THEN
        ALTER TABLE properties ADD COLUMN area_info JSONB;
    END IF;
    
    -- price_info 구조 확정 (네이버 표준)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'price_info') THEN
        ALTER TABLE properties ADD COLUMN price_info JSONB;
    END IF;
    
    -- owner_info 필드 추가 (OCR에서 추출한 소유주 정보)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'owner_info') THEN
        ALTER TABLE properties ADD COLUMN owner_info JSONB;
    END IF;
    
    -- 건축물대장 정보 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'building_register_info') THEN
        ALTER TABLE properties ADD COLUMN building_register_info JSONB;
    END IF;
    
    -- 토지대장 정보 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'land_register_info') THEN
        ALTER TABLE properties ADD COLUMN land_register_info JSONB;
    END IF;
    
    -- 데이터 분류 필드 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'manual_data') THEN
        ALTER TABLE properties ADD COLUMN manual_data JSONB DEFAULT '{}'::jsonb;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'ocr_data') THEN
        ALTER TABLE properties ADD COLUMN ocr_data JSONB DEFAULT '{}'::jsonb;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'api_data') THEN
        ALTER TABLE properties ADD COLUMN api_data JSONB DEFAULT '{}'::jsonb;
    END IF;
    
    -- 네이버 호환성 정보 필드
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'properties' AND column_name = 'naver_info') THEN
        ALTER TABLE properties ADD COLUMN naver_info JSONB;
    END IF;
END $$;

-- 5. 인덱스 생성 (성능 최적화)

-- 섹션 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_sections_active ON sections(is_active);
CREATE INDEX IF NOT EXISTS idx_sections_order ON sections("order");
CREATE INDEX IF NOT EXISTS idx_sections_name ON sections(name);

-- 매물-섹션 관계 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_property_sections_property_id ON property_sections(property_id);
CREATE INDEX IF NOT EXISTS idx_property_sections_section_id ON property_sections(section_id);
CREATE INDEX IF NOT EXISTS idx_property_sections_featured ON property_sections(is_featured);
CREATE INDEX IF NOT EXISTS idx_property_sections_order ON property_sections(display_order);
CREATE INDEX IF NOT EXISTS idx_property_sections_priority ON property_sections(priority);

-- Properties 테이블 JSONB 필드 인덱스 (네이버 표준 필드 검색용)
CREATE INDEX IF NOT EXISTS idx_properties_address_info ON properties USING GIN (address_info);
CREATE INDEX IF NOT EXISTS idx_properties_area_info ON properties USING GIN (area_info);
CREATE INDEX IF NOT EXISTS idx_properties_price_info ON properties USING GIN (price_info);
CREATE INDEX IF NOT EXISTS idx_properties_naver_info ON properties USING GIN (naver_info);

-- 6. 트리거 함수 생성 (자동 업데이트 용)

-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- sections 테이블에 updated_at 트리거 적용
CREATE TRIGGER update_sections_updated_at 
    BEFORE UPDATE ON sections 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- properties 테이블에 updated_at 트리거 적용 (이미 있을 수 있음)
CREATE TRIGGER update_properties_updated_at 
    BEFORE UPDATE ON properties 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 7. 섹션 통계 업데이트 함수
CREATE OR REPLACE FUNCTION update_section_property_count()
RETURNS TRIGGER AS $$
BEGIN
    -- 섹션의 매물 수 업데이트
    IF TG_OP = 'INSERT' THEN
        UPDATE sections 
        SET property_count = (
            SELECT COUNT(*) 
            FROM property_sections 
            WHERE section_id = NEW.section_id
        )
        WHERE id = NEW.section_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE sections 
        SET property_count = (
            SELECT COUNT(*) 
            FROM property_sections 
            WHERE section_id = OLD.section_id
        )
        WHERE id = OLD.section_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- 섹션 통계 업데이트 트리거
CREATE TRIGGER update_section_stats_trigger
    AFTER INSERT OR DELETE ON property_sections
    FOR EACH ROW
    EXECUTE FUNCTION update_section_property_count();

-- 8. 기본 섹션 데이터 생성 (샘플)
INSERT INTO sections (name, description, theme_tags, "order", display_title) 
VALUES 
    ('추천 매물', '관리자가 선별한 추천 매물', '["추천", "베스트"]', 1, '🏆 추천 매물'),
    ('신규 매물', '최근 등록된 신규 매물', '["신규", "최신"]', 2, '🆕 신규 매물'),
    ('프리미엄', '프리미엄 매물 모음', '["프리미엄", "고급"]', 3, '⭐ 프리미엄'),
    ('특가 매물', '특가 할인 매물', '["특가", "할인"]', 4, '💰 특가 매물')
ON CONFLICT DO NOTHING;

-- 9. 데이터 검증 함수 (네이버 호환성 체크)
CREATE OR REPLACE FUNCTION validate_naver_compatibility(property_data JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- 필수 필드 체크
    IF NOT (property_data ? 'address_info' AND 
            property_data ? 'area_info' AND 
            property_data ? 'price_info') THEN
        RETURN FALSE;
    END IF;
    
    -- 네이버 표준 필드명 체크 (address_info 예시)
    IF property_data->'address_info' ? 'address' AND
       property_data->'address_info' ? 'city' AND
       property_data->'address_info' ? 'district' THEN
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ language 'plpgsql';

-- 10. RLS (Row Level Security) 설정 (필요시)
-- ALTER TABLE sections ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE property_sections ENABLE ROW LEVEL SECURITY;

-- 11. 권한 설정
GRANT SELECT, INSERT, UPDATE, DELETE ON sections TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON property_sections TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- 12. 마이그레이션 완료 로그
INSERT INTO migrations_log (name, executed_at, description) 
VALUES (
    'naver_compat_migration', 
    CURRENT_TIMESTAMP, 
    '네이버 호환성 확정 및 섹션 관리 시스템 추가'
) ON CONFLICT DO NOTHING;

-- 마이그레이션 검증 쿼리
SELECT 
    'Migration Completed' as status,
    (SELECT COUNT(*) FROM sections) as sections_count,
    (SELECT COUNT(*) FROM property_sections) as property_sections_count,
    (SELECT COUNT(*) FROM properties WHERE naver_info IS NOT NULL) as naver_compatible_properties
; 