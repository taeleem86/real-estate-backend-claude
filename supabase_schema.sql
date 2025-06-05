-- 부동산 매물 분석 시스템 Supabase 테이블 생성 스크립트
-- Supabase SQL Editor에서 실행하세요

-- 1. properties 테이블 생성
CREATE TABLE IF NOT EXISTS properties (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    property_number VARCHAR(50) UNIQUE NOT NULL,
    property_type VARCHAR(20) NOT NULL CHECK (property_type IN ('토지', '건물', '사무실', '상가', '주거', '기타')),
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('매매', '교환', '임대')),
    
    -- 주소 정보 (JSONB)
    address_info JSONB NOT NULL DEFAULT '{}',
    
    -- 면적 정보 (JSONB)  
    area_info JSONB NOT NULL DEFAULT '{}',
    
    -- 가격 정보 (JSONB) - 거래형태별로 다른 필드 사용
    price_info JSONB NOT NULL DEFAULT '{}',
    
    -- 매물 설명 (JSONB)
    property_description JSONB NOT NULL DEFAULT '{}',
    
    -- 상태 및 채널 정보
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'inactive', 'sold', 'suspended')),
    channel_info JSONB DEFAULT '{}',
    
    -- 분석 결과 연결
    building_analysis_id UUID,
    land_analysis_id UUID,
    competitor_analysis_id UUID,
    marketing_content TEXT,
    
    -- 네이버 부동산 호환 정보 (JSONB)
    naver_info JSONB DEFAULT '{}' NOT NULL,
    
    -- 메타데이터
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- properties 테이블 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_properties_status ON properties(status);
CREATE INDEX IF NOT EXISTS idx_properties_type ON properties(property_type);
CREATE INDEX IF NOT EXISTS idx_properties_transaction ON properties(transaction_type);
CREATE INDEX IF NOT EXISTS idx_properties_created_at ON properties(created_at);
CREATE INDEX IF NOT EXISTS idx_properties_number ON properties(property_number);

-- 네이버 부동산 호환성 인덱스
CREATE INDEX IF NOT EXISTS idx_properties_naver_property_type 
ON properties USING GIN ((naver_info->'propertyType'));
CREATE INDEX IF NOT EXISTS idx_properties_naver_trade_type 
ON properties USING GIN ((naver_info->'tradeType'));
CREATE INDEX IF NOT EXISTS idx_properties_naver_location 
ON properties USING GIN ((naver_info->'location'));
CREATE INDEX IF NOT EXISTS idx_properties_naver_price 
ON properties USING GIN ((naver_info->'price'));

-- properties 테이블 RLS (Row Level Security) 활성화
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;

-- properties 테이블 정책 생성 (모든 사용자가 읽기 가능, 인증된 사용자만 수정 가능)
CREATE POLICY "Enable read access for all users" ON properties
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for authenticated users only" ON properties
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update for authenticated users only" ON properties
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Enable delete for authenticated users only" ON properties
    FOR DELETE USING (auth.role() = 'authenticated');

-- 2. analysis_results 테이블 생성
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    property_id UUID NOT NULL,
    analysis_type VARCHAR(50) NOT NULL CHECK (analysis_type IN ('건축물대장', '토지대장', '경쟁사분석', '시장분석')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    
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
    
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);

-- analysis_results 테이블 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_analysis_property_id ON analysis_results(property_id);
CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis_results(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_status ON analysis_results(status);
CREATE INDEX IF NOT EXISTS idx_analysis_analyzed_at ON analysis_results(analyzed_at);

-- analysis_results 테이블 RLS 활성화
ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;

-- analysis_results 테이블 정책 생성
CREATE POLICY "Enable read access for all users" ON analysis_results
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for authenticated users only" ON analysis_results
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update for authenticated users only" ON analysis_results
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Enable delete for authenticated users only" ON analysis_results
    FOR DELETE USING (auth.role() = 'authenticated');

-- 3. sections 테이블 생성
CREATE TABLE IF NOT EXISTS sections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    section_type VARCHAR(50) NOT NULL CHECK (section_type IN ('추천', '오피스', '상가', '빌딩', '주거', '토지', '급매')),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    property_ids JSONB DEFAULT '[]',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- sections 테이블 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_sections_active ON sections(is_active);
CREATE INDEX IF NOT EXISTS idx_sections_sort ON sections(sort_order);
CREATE INDEX IF NOT EXISTS idx_sections_type ON sections(section_type);
CREATE INDEX IF NOT EXISTS idx_sections_name ON sections(name);

-- sections 테이블 RLS 활성화
ALTER TABLE sections ENABLE ROW LEVEL SECURITY;

-- sections 테이블 정책 생성
CREATE POLICY "Enable read access for all users" ON sections
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for authenticated users only" ON sections
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update for authenticated users only" ON sections
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Enable delete for authenticated users only" ON sections
    FOR DELETE USING (auth.role() = 'authenticated');

-- 4. 기본 섹션 데이터 삽입
INSERT INTO sections (name, section_type, description, sort_order) VALUES
    ('추천 매물', '추천', '관리자가 엄선한 프리미엄 매물', 1),
    ('오피스', '오피스', '사무용 건물 및 오피스텔', 2),
    ('상가', '상가', '상업용 건물 및 점포', 3),
    ('빌딩', '빌딩', '수익형 건물 및 대형 건축물', 4),
    ('주거', '주거', '아파트, 빌라, 단독주택', 5),
    ('토지', '토지', '개발용지 및 나대지', 6),
    ('급매', '급매', '빠른 거래 희망 매물', 7)
ON CONFLICT (name) DO NOTHING;

-- 5. 트리거 함수 생성 (updated_at 자동 업데이트)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 6. 트리거 생성
CREATE TRIGGER update_properties_updated_at 
    BEFORE UPDATE ON properties 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sections_updated_at 
    BEFORE UPDATE ON sections 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 7. 거래형태별 가격 정보 유효성 검증 함수
CREATE OR REPLACE FUNCTION validate_price_by_transaction_type()
RETURNS TRIGGER AS $$
BEGIN
    -- 매매: sale_price 필수
    IF NEW.transaction_type = '매매' AND (NEW.price_info->>'sale_price') IS NULL THEN
        RAISE EXCEPTION '매매 거래시 매매가는 필수입니다.';
    END IF;
    
    -- 임대: lease_deposit 또는 monthly_rent 중 하나는 필수
    IF NEW.transaction_type = '임대' AND 
       (NEW.price_info->>'lease_deposit') IS NULL AND 
       (NEW.price_info->>'monthly_rent') IS NULL THEN
        RAISE EXCEPTION '임대 거래시 보증금 또는 월 임대료는 필수입니다.';
    END IF;
    
    -- 교환: exchange_value 필수
    IF NEW.transaction_type = '교환' AND (NEW.price_info->>'exchange_value') IS NULL THEN
        RAISE EXCEPTION '교환 거래시 교환 평가가는 필수입니다.';
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 가격 검증 트리거 생성
CREATE TRIGGER validate_price_trigger
    BEFORE INSERT OR UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION validate_price_by_transaction_type();

-- 8. 유용한 뷰 생성
CREATE OR REPLACE VIEW property_summary AS
SELECT 
    p.id,
    p.property_number,
    p.property_type,
    p.transaction_type,
    p.address_info->>'detail_address' as address,
    p.address_info->>'city_district' as district,
    p.property_description->>'title' as title,
    p.status,
    CASE 
        WHEN p.transaction_type = '매매' THEN p.price_info->>'sale_price'
        WHEN p.transaction_type = '임대' THEN 
            COALESCE(p.price_info->>'lease_deposit', '0') || '/' || 
            COALESCE(p.price_info->>'monthly_rent', '0')
        WHEN p.transaction_type = '교환' THEN p.price_info->>'exchange_value'
        ELSE NULL
    END as price_display,
    p.created_at,
    COUNT(ar.id) as analysis_count
FROM properties p
LEFT JOIN analysis_results ar ON p.id = ar.property_id
GROUP BY p.id, p.property_number, p.property_type, p.transaction_type, 
         p.address_info, p.property_description, p.status, p.price_info, p.created_at
ORDER BY p.created_at DESC;

-- 거래형태별 통계 뷰
CREATE OR REPLACE VIEW transaction_type_stats AS
SELECT 
    transaction_type,
    COUNT(*) as total_count,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
    COUNT(CASE WHEN status = 'sold' THEN 1 END) as sold_count,
    AVG(CASE 
        WHEN transaction_type = '매매' THEN (price_info->>'sale_price')::numeric
        WHEN transaction_type = '교환' THEN (price_info->>'exchange_value')::numeric
        ELSE NULL
    END) as avg_price
FROM properties 
GROUP BY transaction_type
ORDER BY total_count DESC;

-- 성공 메시지
SELECT '거래형태 수정 완료: 매매/교환/임대 🎉' as message;
