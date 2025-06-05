"""
Sections API 및 Property-Sections 연결 종합 테스트
"""
import asyncio
import httpx
import json
from datetime import datetime

# Railway 배포된 API URL (실제 URL로 변경 필요)
BASE_URL = "https://real-estate-platform-backend-production.up.railway.app"
# 로컬 테스트용
# BASE_URL = "http://localhost:8000"

class SectionsAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def test_sections_crud(self):
        """섹션 CRUD 기능 테스트"""
        print("🏗️ === Sections CRUD 테스트 ===")
        
        # 1. 섹션 목록 조회
        print("\n1. 섹션 목록 조회")
        response = await self.client.get(f"{self.base_url}/api/v1/sections")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            sections = response.json()
            print(f"✅ 기존 섹션 {len(sections)}개 발견")
            for section in sections[:3]:  # 처음 3개만 출력
                print(f"  - {section['name']} (order: {section['order']}, active: {section['is_active']})")
        else:
            print(f"❌ 섹션 조회 실패: {response.text}")
            return False
            
        # 2. 새 섹션 생성
        print("\n2. 새 섹션 생성")
        new_section_data = {
            "name": "🧪 API 테스트 섹션",
            "description": "종합 API 테스트를 위한 임시 섹션",
            "theme_tags": ["테스트", "API", "자동화"],
            "display_title": "🔬 테스트 전용 섹션",
            "display_subtitle": "API 테스트 진행 중",
            "is_active": True,
            "order": 999,  # 맨 마지막에 배치
            "max_properties": 5,
            "auto_update": False
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/sections",
            json=new_section_data
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            created_section = response.json()
            print(f"✅ 섹션 생성 성공: {created_section['name']}")
            print(f"   ID: {created_section['id']}")
            test_section_id = created_section['id']
        else:
            print(f"❌ 섹션 생성 실패: {response.text}")
            return False
            
        # 3. 섹션 상세 조회
        print("\n3. 섹션 상세 조회")
        response = await self.client.get(f"{self.base_url}/api/v1/sections/{test_section_id}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            section_detail = response.json()
            print(f"✅ 섹션 상세 조회 성공")
            print(f"   이름: {section_detail['name']}")
            print(f"   설명: {section_detail['description']}")
            print(f"   테마 태그: {section_detail['theme_tags']}")
            print(f"   최대 매물 수: {section_detail['max_properties']}")
        else:
            print(f"❌ 섹션 상세 조회 실패: {response.text}")
            
        # 4. 섹션 수정
        print("\n4. 섹션 수정")
        update_data = {
            "name": "🧪 API 테스트 섹션 (수정됨)",
            "description": "수정된 설명입니다",
            "theme_tags": ["테스트", "API", "자동화", "수정완료"],
            "max_properties": 10
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
            print(f"   수정된 최대 매물 수: {updated_section['max_properties']}")
        else:
            print(f"❌ 섹션 수정 실패: {response.text}")
            
        return test_section_id

    async def test_property_sections_connection(self, section_id: str):
        """매물-섹션 연결 기능 테스트"""
        print("\n🔗 === Property-Sections 연결 테스트 ===")
        
        # 1. 기존 매물 목록 조회
        print("\n1. 기존 매물 목록 조회")
        response = await self.client.get(f"{self.base_url}/api/v1/listings?limit=3")
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ 매물 조회 실패: {response.text}")
            return False
            
        listings_data = response.json()
        listings = listings_data.get('data', [])
        
        if not listings:
            print("❌ 테스트할 매물이 없습니다")
            return False
            
        print(f"✅ 매물 {len(listings)}개 발견")
        for listing in listings:
            print(f"  - {listing['title']} (ID: {listing['id'][:8]}...)")
            
        # 2. 매물을 섹션에 추가
        print(f"\n2. 매물들을 섹션 '{section_id[:8]}...'에 추가")
        
        property_ids = [listing['id'] for listing in listings]
        add_properties_data = {
            "property_ids": property_ids,
            "is_featured": True,  # 첫 번째는 추천으로
            "priority": 8
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/sections/{section_id}/properties",
            json=add_properties_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 매물 추가 성공")
            print(f"   추가된 매물 수: {result.get('added_count', 0)}")
            print(f"   메시지: {result.get('message', 'N/A')}")
        else:
            print(f"❌ 매물 추가 실패: {response.text}")
            return False
            
        # 3. 섹션의 매물 목록 조회
        print(f"\n3. 섹션의 매물 목록 조회")
        response = await self.client.get(f"{self.base_url}/api/v1/sections/{section_id}/properties")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            section_properties = response.json()
            print(f"✅ 섹션 매물 조회 성공")
            print(f"   매물 수: {len(section_properties)}")
            for prop in section_properties:
                print(f"   - {prop['title']} (추천: {prop.get('is_featured', False)})")
        else:
            print(f"❌ 섹션 매물 조회 실패: {response.text}")
            
        # 4. 매물 순서 변경
        print(f"\n4. 매물 순서 및 우선순위 변경")
        if len(property_ids) >= 2:
            reorder_data = {
                "property_orders": [
                    {
                        "property_id": property_ids[0], 
                        "display_order": 2, 
                        "priority": 9,
                        "is_featured": True
                    },
                    {
                        "property_id": property_ids[1], 
                        "display_order": 1, 
                        "priority": 10,
                        "is_featured": False
                    }
                ]
            }
            
            response = await self.client.put(
                f"{self.base_url}/api/v1/sections/{section_id}/properties/reorder",
                json=reorder_data
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 매물 순서 변경 성공")
                print(f"   메시지: {result.get('message', 'N/A')}")
            else:
                print(f"❌ 매물 순서 변경 실패: {response.text}")
                
        # 5. 특정 매물을 섹션에서 제거
        print(f"\n5. 특정 매물을 섹션에서 제거")
        if property_ids:
            remove_property_id = property_ids[-1]  # 마지막 매물 제거
            
            response = await self.client.delete(
                f"{self.base_url}/api/v1/sections/{section_id}/properties/{remove_property_id}"
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 매물 제거 성공")
                print(f"   메시지: {result.get('message', 'N/A')}")
            else:
                print(f"❌ 매물 제거 실패: {response.text}")
                
        return True

    async def test_sections_statistics(self, section_id: str):
        """섹션 통계 및 추가 기능 테스트"""
        print("\n📊 === 섹션 통계 및 고급 기능 테스트 ===")
        
        # 1. 섹션 통계 조회
        print("\n1. 섹션 통계 조회")
        response = await self.client.get(f"{self.base_url}/api/v1/sections/{section_id}/stats")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 섹션 통계 조회 성공")
            print(f"   매물 수: {stats.get('property_count', 0)}")
            print(f"   추천 매물 수: {stats.get('featured_count', 0)}")
            print(f"   평균 가격: {stats.get('avg_price', 'N/A')}")
            print(f"   조회 수: {stats.get('view_count', 0)}")
        else:
            print(f"⚠️ 섹션 통계 조회 실패 (기능 미구현 가능성): {response.status_code}")
            
        # 2. 섹션 순서 변경
        print("\n2. 섹션 순서 변경")
        reorder_data = {
            "new_order": 1  # 맨 앞으로 이동
        }
        
        response = await self.client.put(
            f"{self.base_url}/api/v1/sections/{section_id}/order",
            json=reorder_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 섹션 순서 변경 성공")
            print(f"   새로운 순서: {result.get('new_order', 'N/A')}")
        else:
            print(f"⚠️ 섹션 순서 변경 실패 (기능 미구현 가능성): {response.status_code}")
            
        # 3. 섹션 활성화/비활성화
        print("\n3. 섹션 비활성화 테스트")
        toggle_data = {
            "is_active": False
        }
        
        response = await self.client.patch(
            f"{self.base_url}/api/v1/sections/{section_id}/toggle",
            json=toggle_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 섹션 상태 변경 성공")
            print(f"   활성화 상태: {result.get('is_active', 'N/A')}")
        else:
            print(f"⚠️ 섹션 상태 변경 실패 (기능 미구현 가능성): {response.status_code}")

    async def cleanup_test_section(self, section_id: str):
        """테스트 섹션 정리"""
        print(f"\n🗑️ === 테스트 섹션 정리 ===")
        
        response = await self.client.delete(f"{self.base_url}/api/v1/sections/{section_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 테스트 섹션 삭제 완료")
        else:
            print(f"❌ 테스트 섹션 삭제 실패: {response.text}")
            print(f"⚠️ 수동으로 섹션 ID {section_id}를 삭제해주세요")

async def main():
    """메인 테스트 실행"""
    print("🚀 === Sections & Property-Sections API 종합 테스트 시작 ===")
    print(f"테스트 대상: {BASE_URL}")
    print(f"시작 시간: {datetime.now().isoformat()}")
    
    try:
        async with SectionsAPITester(BASE_URL) as tester:
            # 1. Sections CRUD 테스트
            section_id = await tester.test_sections_crud()
            
            if section_id:
                # 2. Property-Sections 연결 테스트
                await tester.test_property_sections_connection(section_id)
                
                # 3. 섹션 통계 및 고급 기능 테스트
                await tester.test_sections_statistics(section_id)
                
                # 4. 정리
                await tester.cleanup_test_section(section_id)
            else:
                print("❌ 섹션 생성에 실패하여 후속 테스트를 건너뜁니다")
                
    except Exception as e:
        print(f"❌ 테스트 중 예외 발생: {str(e)}")
        
    print(f"\n🏁 === 테스트 완료 ===")
    print(f"종료 시간: {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())