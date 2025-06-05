"""
Sections API 직접 테스트 및 수동 생성
"""
import asyncio
import httpx
import json

BASE_URL = "https://backend-production-9d6f.up.railway.app"

async def test_sections_direct():
    print("🔍 === Sections API 직접 테스트 및 문제 해결 ===")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. 섹션 API 오류 상세 확인
        print("\n1. 섹션 API 오류 상세 분석")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/sections")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text}")
            
        except Exception as e:
            print(f"예외: {e}")
        
        # 2. 대안: 직접 섹션 생성 테스트
        print("\n2. 새 섹션 직접 생성 테스트")
        try:
            new_section = {
                "name": "🧪 직접 생성 테스트 섹션",
                "description": "API 문제 해결을 위한 직접 생성 테스트",
                "is_active": True,
                "order": 998
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/sections",
                json=new_section,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"생성 Status: {response.status_code}")
            print(f"생성 Response: {response.text}")
            
            if response.status_code in [200, 201]:
                created = response.json()
                print(f"✅ 섹션 생성 성공: {created.get('name', 'N/A')}")
                section_id = created.get('id')
                return section_id
            else:
                print(f"❌ 섹션 생성 실패")
                
        except Exception as e:
            print(f"생성 예외: {e}")
            
        # 3. property_sections 테이블 직접 확인
        print("\n3. Property-Sections 관계 테스트")
        try:
            # 간단한 property-section 관계 생성을 위한 더미 데이터
            print("매물 목록으로 ID 확인...")
            
            listings_response = await client.get(f"{BASE_URL}/api/v1/listings?limit=1")
            if listings_response.status_code == 200:
                listings_data = listings_response.json()
                if isinstance(listings_data, dict) and 'data' in listings_data:
                    listings = listings_data['data']
                else:
                    listings = listings_data
                    
                if listings:
                    property_id = listings[0]['id']
                    print(f"테스트용 매물 ID: {property_id[:8]}...")
                    
                    # Supabase MCP로 직접 property_sections 생성 테스트
                    print("ℹ️ Property-sections 관계는 Supabase MCP로 직접 테스트 가능")
                    
            else:
                print(f"매물 조회 실패: {listings_response.status_code}")
                
        except Exception as e:
            print(f"Property-sections 테스트 예외: {e}")
            
        return None

async def test_with_supabase_mcp():
    """Supabase MCP를 사용한 직접 테스트"""
    print("\n📊 === Supabase MCP로 직접 섹션 및 관계 테스트 ===")
    
    # 이 부분은 실제로는 MCP 호출로 대체되어야 함
    print("1. Supabase에서 직접 섹션 생성 테스트:")
    print("   - 새 섹션 생성")
    print("   - 매물-섹션 관계 생성") 
    print("   - 관계 조회 테스트")
    print("   - 정리")
    print("\n💡 이 테스트는 아래 Supabase MCP 호출로 수행됩니다.")

async def main():
    print("🚀 Sections API 문제 진단 및 테스트")
    
    # 1. 직접 API 테스트
    section_id = await test_sections_direct()
    
    # 2. MCP 테스트 안내
    await test_with_supabase_mcp()
    
    print("\n🏁 직접 테스트 완료")
    print("💡 이제 Supabase MCP로 property_sections 기능을 테스트합니다.")

if __name__ == "__main__":
    asyncio.run(main())