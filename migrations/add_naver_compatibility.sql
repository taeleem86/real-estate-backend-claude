-- 네이버 부동산 호환성 확장 마이그레이션
-- 실행 날짜: 2025-06-03
-- 목적: 기존 properties 테이블에 네이버 부동산 표준 정보를 저장할 수 있는 컬럼 추가

-- 1. 네이버 호환성 JSONB 컬럼 추가 (기존 데이터에 영향 없음)
ALTER TABLE properties 
ADD COLUMN IF NOT EXISTS naver_info JSONB DEFAULT '{}' NOT NULL;

-- 2. 네이버 정보 관련 인덱스 생성 (검색 성능 향상)
-- 네이버 부동산 타입 코드 인덱스
CREATE INDEX IF NOT EXISTS idx_properties_naver_property_type 
ON properties USING GIN ((naver_info->'propertyType'));

-- 네이버 거래 타입 코드 인덱스  
CREATE INDEX IF NOT EXISTS idx_properties_naver_trade_type 
ON properties USING GIN ((naver_info->'tradeType'));

-- 네이버 위치 정보 인덱스
CREATE INDEX IF NOT EXISTS idx_properties_naver_location 
ON properties USING GIN ((naver_info->'location'));

-- 네이버 가격 정보 인덱스
CREATE INDEX IF NOT EXISTS idx_properties_naver_price 
ON properties USING GIN ((naver_info->'price'));

-- 3. 네이버 호환성 검증 함수 생성
CREATE OR REPLACE FUNCTION validate_naver_info_structure()
RETURNS TRIGGER AS $$
BEGIN
    -- naver_info가 null이 아닌 경우에만 검증
    IF NEW.naver_info IS NOT NULL AND NEW.naver_info != '{}' THEN
        -- 필수 필드 검증
        IF NOT (NEW.naver_info ? 'propertyType') THEN
            RAISE EXCEPTION 'naver_info에 propertyType 필드가 필요합니다.';
        END IF;
        
        IF NOT (NEW.naver_info ? 'tradeType') THEN
            RAISE EXCEPTION 'naver_info에 tradeType 필드가 필요합니다.';
        END IF;
        
        -- 유효한 네이버 코드 검증
        IF NEW.naver_info->>'propertyType' NOT IN ('LND', 'APT', 'OFC', 'SHP', 'ETC') THEN
            RAISE EXCEPTION '유효하지 않은 네이버 부동산 타입 코드입니다: %', NEW.naver_info->>'propertyType';
        END IF;
        
        IF NEW.naver_info->>'tradeType' NOT IN ('A1', 'A2', 'B1') THEN
            RAISE EXCEPTION '유효하지 않은 네이버 거래 타입 코드입니다: %', NEW.naver_info->>'tradeType';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 4. 네이버 정보 검증 트리거 생성
CREATE TRIGGER validate_naver_info_trigger
    BEFORE INSERT OR UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION validate_naver_info_structure();

-- 5. 기존 데이터를 네이버 형식으로 변환하는 함수
CREATE OR REPLACE FUNCTION convert_existing_data_to_naver_format()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER := 0;
    property_record RECORD;
    naver_property_type TEXT;
    naver_trade_type TEXT;
    naver_data JSONB;
BEGIN
    -- 모든 기존 매물에 대해 네이버 형식 변환
    FOR property_record IN 
        SELECT id, property_type, transaction_type, address_info, area_info, price_info, property_description
        FROM properties 
        WHERE naver_info = '{}'
    LOOP
        -- 부동산 타입 변환
        CASE property_record.property_type
            WHEN '토지' THEN naver_property_type := 'LND';
            WHEN '건물' THEN naver_property_type := 'APT';
            WHEN '사무실' THEN naver_property_type := 'OFC';
            WHEN '상가' THEN naver_property_type := 'SHP';
            WHEN '주거' THEN naver_property_type := 'APT';
            ELSE naver_property_type := 'ETC';
        END CASE;
        
        -- 거래 타입 변환
        CASE property_record.transaction_type
            WHEN '매매' THEN naver_trade_type := 'A1';
            WHEN '교환' THEN naver_trade_type := 'A2';
            WHEN '임대' THEN naver_trade_type := 'B1';
            ELSE naver_trade_type := 'A1';
        END CASE;
        
        -- 네이버 형식 JSON 생성
        naver_data := jsonb_build_object(
            'propertyType', naver_property_type,
            'tradeType', naver_trade_type,
            'location', jsonb_build_object(
                'address', COALESCE(property_record.address_info->>'display_address', ''),
                'city', COALESCE(split_part(property_record.address_info->>'city_district', ' ', 1), ''),
                'district', COALESCE(property_record.address_info->>'city_district', ''),
                'coordinates', jsonb_build_object(
                    'lat', COALESCE((property_record.address_info->>'coordinate_y')::float, 0.0),
                    'lng', COALESCE((property_record.address_info->>'coordinate_x')::float, 0.0)
                )
            ),
            'area', jsonb_build_object(
                'totalArea', COALESCE((property_record.area_info->>'total_floor_area')::float, 0.0),
                'exclusiveArea', COALESCE((property_record.area_info->>'exclusive_area')::float, 0.0),
                'landArea', COALESCE((property_record.area_info->>'land_area')::float, 0.0)
            ),
            'price', jsonb_build_object(
                'salePrice', COALESCE((property_record.price_info->>'sale_price')::int, 0),
                'deposit', COALESCE((property_record.price_info->>'lease_deposit')::int, 0),
                'monthlyRent', COALESCE((property_record.price_info->>'monthly_rent')::int, 0)
            ),
            'description', jsonb_build_object(
                'title', COALESCE(property_record.property_description->>'title', ''),
                'features', COALESCE(property_record.property_description->>'features', ''),
                'details', COALESCE(property_record.property_description->>'description', '')
            ),
            'buildingInfo', jsonb_build_object(
                'floors', COALESCE((property_record.area_info->>'floor_count')::int, 0),
                'buildYear', 0,
                'parking', false
            )
        );
        
        -- 네이버 정보 업데이트
        UPDATE properties 
        SET naver_info = naver_data,
            updated_at = NOW()
        WHERE id = property_record.id;
        
        updated_count := updated_count + 1;
    END LOOP;
    
    RETURN updated_count;
END;
$$ language 'plpgsql';

-- 6. 네이버 호환성 확장 완료를 위한 뷰 생성
CREATE OR REPLACE VIEW naver_compatible_properties AS
SELECT 
    p.id,
    p.property_number,
    p.property_type as original_type,
    p.transaction_type as original_transaction,
    p.naver_info->>'propertyType' as naver_property_type,
    p.naver_info->>'tradeType' as naver_trade_type,
    p.naver_info->'location'->>'address' as naver_address,
    p.naver_info->'price' as naver_price,
    p.status,
    p.created_at,
    CASE 
        WHEN p.naver_info != '{}' AND 
             p.naver_info ? 'propertyType' AND 
             p.naver_info ? 'tradeType' 
        THEN true 
        ELSE false 
    END as is_naver_compatible
FROM properties p
ORDER BY p.created_at DESC;

-- 7. 네이버 호환성 통계 뷰
CREATE OR REPLACE VIEW naver_compatibility_stats AS
SELECT 
    COUNT(*) as total_properties,
    COUNT(CASE WHEN naver_info != '{}' THEN 1 END) as naver_compatible_count,
    COUNT(CASE WHEN naver_info = '{}' THEN 1 END) as needs_conversion_count,
    ROUND(
        COUNT(CASE WHEN naver_info != '{}' THEN 1 END) * 100.0 / COUNT(*), 2
    ) as compatibility_percentage
FROM properties;

-- 8. 마이그레이션 완료 메시지
SELECT 
    '네이버 부동산 호환성 스키마 확장 완료! ✅' as status,
    'naver_info JSONB 컬럼 추가됨' as schema_change,
    '인덱스 및 검증 함수 생성됨' as performance_enhancement,
    '기존 데이터 변환 함수 준비됨' as data_migration;