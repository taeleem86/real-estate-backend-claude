"""
간단한 Sections API 테스트
"""
import asyncio
import httpx

BASE_URL = "https://backend-production-9d6f.up.railway.app"

async def quick_test():
    print(f"🚀 빠른 Sections API 테스트")
    print(f"URL: {BASE_URL}")
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        
        # 1. 서버 상태 확인
        print("\n1. 서버 상태 확인")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"루트 Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 서버 작동: {data.get('message', 'N/A')}")
        except Exception as e:
            print(f"❌ 서버 오류: {e}")
            return
            
        # 2. API v1 정보 확인
        print("\n2. API v1 정보 확인")
        try:
            response = await client.get(f"{BASE_URL}/api/v1")
            print(f"API v1 Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API v1 정보:")
                endpoints = data.get('available_endpoints', {})
                for endpoint, info in endpoints.items():
                    print(f"   - {endpoint}: {info.get('status', 'N/A')}")
        except Exception as e:
            print(f"❌ API v1 오류: {e}")
            
        # 3. 섹션 목록 조회 (다양한 URL 시도)
        print("\n3. 섹션 목록 조회 테스트")
        
        section_urls = [
            f"{BASE_URL}/api/v1/sections",
            f"{BASE_URL}/api/v1/sections/",
        ]
        
        for url in section_urls:
            try:
                print(f"   시도 URL: {url}")
                response = await client.get(url)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    sections = response.json()
                    print(f"   ✅ 성공! 섹션 {len(sections)}개")
                    for section in sections[:2]:  # 처음 2개만
                        print(f"      - {section['name']} (order: {section['order']})")
                    break
                elif response.status_code == 307:
                    print(f"   ⚠️ 리다이렉트: {response.headers.get('location', 'N/A')}")
                else:
                    print(f"   ❌ 실패: {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ 예외: {e}")
                
        # 4. 매물 목록 확인
        print("\n4. 매물 목록 확인")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/listings")
            print(f"매물 Status: {response.status_code}")
            
            if response.status_code == 200:
                listings_data = response.json()
                if isinstance(listings_data, dict) and 'data' in listings_data:
                    listings = listings_data['data']
                else:
                    listings = listings_data
                    
                print(f"✅ 매물 {len(listings)}개 확인")
                for listing in listings[:2]:  # 처음 2개만
                    print(f"   - {listing.get('title', 'N/A')}")
            else:
                print(f"❌ 매물 조회 실패: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 매물 조회 예외: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())