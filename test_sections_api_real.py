"""
실제 구현된 Sections API 테스트
"""
import asyncio
import httpx
import json
from datetime import datetime

# Railway 배포된 실제 API URL
BASE_URL = "https://backend-production-9d6f.up.railway.app"

class SectionsAPIRealTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def test_server_health(self):
        """서버 상태 확인"""
        print("🏥 === 서버 상태 확인 ===")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ 서버 정상 작동")
                print(f"   환경: {health.get('environment', 'unknown')}")
                print(f"   Supabase 연결: {health.get('config', {}).get('supabase_configured', False)}")
                return True
            else:
                print(f"⚠️ 서버 응답 이상: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 서버 연결 실패: {str(e)}")
            return False

    async def test_sections_basic_crud(self):
        """기본 섹션 CRUD 테스트"""
        print("\n🏗️ === Sections 기본 CRUD 테스트 ===")
        
        # 1. 섹션 목록 조회
        print("\n1. 섹션 목록 조회")
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/sections")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                sections = response.json()
                print(f"✅ 섹션 {len(sections)}개 조회 성공")
                for i, section in enumerate(sections[:3]):  # 처음 3개만
                    print(f"   {i+1}. {section['name']} (ID: {section['id'][:8]}...)")
                    print(f"      순서: {section['order']}, 활성: {section['is_active']}")
                    print(f"      태그: {section.get('theme_tags', [])}")
            else:
                print(f"❌ 섹션 조회 실패: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 섹션 조회 예외: {str(e)}")
            return False
            
        # 2. 새 섹션 생성
        print("\n2. 새 섹션 생성")
        try:
            new_section = {
                "name": "🧪 실제 API 테스트 섹션",
                "description": "실제 API 엔드포인트 테스트용 섹션",
                "theme_tags": ["테스트", "실제API", "검증"],
                "display_title": "🔬 API 검증 섹션",
                "display_subtitle": "실제 구현 확인",
                "is_active": True,
                "order": 999,
                "max_properties": 10,
                "auto_update": False
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/sections",
                json=new_section
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                created_section = response.json()
                print(f"✅ 섹션 생성 성공")
                print(f"   이름: {created_section['name']}")
                print(f"   ID: {created_section['id']}")
                test_section_id = created_section['id']
            else:
                print(f"❌ 섹션 생성 실패: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 섹션 생성 예외: {str(e)}")
            return False
            
        # 3. 섹션 상세 조회
        print("\n3. 섹션 상세 조회")
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/sections/{test_section_id}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                section = response.json()
                print(f"✅ 섹션 상세 조회 성공")
                print(f"   이름: {section['name']}")
                print(f"   설명: {section['description']}")
                print(f"   최대 매물 수: {section.get('max_properties', 'unlimited')}")
                print(f"   현재 매물 수: {section.get('property_count', 0)}")
            else:
                print(f"❌ 섹션 상세 조회 실패: {response.text}")
                
        except Exception as e:
            print(f"❌ 섹션 상세 조회 예외: {str(e)}")
            
        # 4. 섹션 수정
        print("\n4. 섹션 수정")
        try:
            update_data = {
                "name": "🧪 실제 API 테스트 섹션 (수정됨)",
                "description": "수정 테스트 완료된 섹션",
                "theme_tags": ["테스트", "실제API", "검증", "수정완료"],
                "max_properties": 15
            }
            
            response = await self.client.put(
                f"{self.base_url}/api/v1/sections/{test_section_id}",
                json=update_data
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                updated_section = response.json()
                print(f"✅ 섹션 수정 성공")
                print(f"   수정된 이름: {updated_section['name']}")
                print(f"   수정된 최대 매물 수: {updated_section.get('max_properties', 'N/A')}")
            else:
                print(f"❌ 섹션 수정 실패: {response.text}")
                
        except Exception as e:
            print(f"❌ 섹션 수정 예외: {str(e)}")
            
        return test_section_id

    async def test_property_sections_real(self, section_id: str):
        """실제 구현된 매물-섹션 연결 기능 테스트"""
        print("\n🔗 === Property-Sections 연결 테스트 ===")
        
        # 1. 기존 매물 조회
        print("\n1. 기존 매물 조회")
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/listings?limit=3")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                listings_response = response.json()
                # API 응답 구조 확인
                if isinstance(listings_response, dict) and 'data' in listings_response:
                    listings = listings_response['data']
                elif isinstance(listings_response, list):
                    listings = listings_response
                else:
                    listings = []
                    
                if not listings:
                    print("❌ 테스트할 매물이 없습니다")
                    return False
                    
                print(f"✅ 매물 {len(listings)}개 발견")
                property_ids = []
                for listing in listings:
                    print(f"   - {listing.get('title', 'N/A')} (ID: {listing['id'][:8]}...)")
                    property_ids.append(listing['id'])
            else:
                print(f"❌ 매물 조회 실패: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 매물 조회 예외: {str(e)}")
            return False
            
        # 2. 매물을 섹션에 추가
        print(f"\n2. 매물들을 섹션에 추가")
        try:
            add_data = {
                "property_ids": property_ids,
                "is_featured": True,
                "priority": 8,
                "added_by": "API_TEST"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/sections/{section_id}/properties",
                json=add_data
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 매물 추가 성공")
                print(f"   메시지: {result.get('message', 'N/A')}")
                print(f"   추가된 수: {result.get('added_count', 0)}")
            else:
                print(f"❌ 매물 추가 실패: {response.text}")
                
        except Exception as e:
            print(f"❌ 매물 추가 예외: {str(e)}")
            
        # 3. 섹션의 매물 목록 조회
        print(f"\n3. 섹션의 매물 목록 조회")
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/sections/{section_id}/properties")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                section_properties = response.json()
                print(f"✅ 섹션 매물 조회 성공")
                
                # API 응답 구조에 따라 처리
                if isinstance(section_properties, dict):
                    listings = section_properties.get('listings', [])
                    print(f"   총 매물 수: {section_properties.get('total', len(listings))}")
                else:
                    listings = section_properties
                    print(f"   매물 수: {len(listings)}")
                    
                for prop in listings[:3]:  # 처음 3개만 출력
                    if 'listings' in prop:  # Join된 데이터 구조
                        listing_info = prop['listings']
                        print(f"   - {listing_info.get('title', 'N/A')} (추천: {prop.get('is_featured', False)})")
                    else:
                        print(f"   - Property ID: {prop.get('property_id', 'N/A')[:8]}...")
                        
            else:
                print(f"❌ 섹션 매물 조회 실패: {response.text}")
                
        except Exception as e:
            print(f"❌ 섹션 매물 조회 예외: {str(e)}")
            
        return True

    async def test_section_stats(self):
        """섹션 통계 기능 테스트"""
        print("\n📊 === 섹션 통계 테스트 ===")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/sections/stats")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ 섹션 통계 조회 성공")
                print(f"   통계 항목 수: {len(stats)}")
                
                for stat in stats[:3]:  # 처음 3개만 출력
                    print(f"   - {stat.get('section_name', 'N/A')}")
                    print(f"     총 매물: {stat.get('total_listings', 0)}")
                    print(f"     추천 매물: {stat.get('featured_listings', 0)}")
                    print(f"     조회수: {stat.get('view_count', 0)}")
                    
            else:
                print(f"⚠️ 섹션 통계 기능 미구현 또는 오류: {response.status_code}")
                print(f"   응답: {response.text[:200]}")
                
        except Exception as e:
            print(f"⚠️ 섹션 통계 예외: {str(e)}")

    async def cleanup_test_section(self, section_id: str):
        """테스트 섹션 정리"""
        print(f"\n🗑️ === 테스트 섹션 정리 ===")
        
        try:
            response = await self.client.delete(f"{self.base_url}/api/v1/sections/{section_id}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 테스트 섹션 삭제 완료")
                print(f"   메시지: {result.get('message', 'N/A')}")
            else:
                print(f"❌ 테스트 섹션 삭제 실패: {response.text}")
                print(f"⚠️ 수동으로 섹션 ID {section_id}를 삭제해주세요")
                
        except Exception as e:
            print(f"❌ 섹션 삭제 예외: {str(e)}")

async def main():
    """메인 테스트 실행"""
    print("🚀 === 실제 Sections API 테스트 시작 ===")
    print(f"테스트 대상: {BASE_URL}")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        async with SectionsAPIRealTester(BASE_URL) as tester:
            # 0. 서버 상태 확인
            server_ok = await tester.test_server_health()
            
            if not server_ok:
                print("❌ 서버 연결 실패로 테스트 중단")
                return
                
            # 1. 기본 CRUD 테스트
            section_id = await tester.test_sections_basic_crud()
            
            if section_id:
                # 2. 매물-섹션 연결 테스트
                await tester.test_property_sections_real(section_id)
                
                # 3. 섹션 통계 테스트
                await tester.test_section_stats()
                
                # 4. 정리
                await tester.cleanup_test_section(section_id)
            else:
                print("❌ 섹션 생성에 실패하여 후속 테스트를 건너뜁니다")
                
    except Exception as e:
        print(f"❌ 테스트 중 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
    print(f"\n🏁 === 테스트 완료 ===")
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())