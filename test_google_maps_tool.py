"""
Google Maps Tool 테스트 스크립트
Google Maps API 키가 설정되어 있는지 확인하고 Tool이 정상 작동하는지 테스트합니다.
"""

import asyncio
import os
from dotenv import load_dotenv
from tools.google_maps_tool import GoogleMapsTool

# .env 파일에서 환경 변수 로드
load_dotenv()


async def test_google_maps_tool():
    """Google Maps Tool 테스트"""
    
    print("=" * 60)
    print("Google Maps Tool 테스트 시작")
    print("=" * 60)
    
    # API 키 확인
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("\n❌ 오류: GOOGLE_MAPS_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 GOOGLE_MAPS_API_KEY를 추가하거나")
        print("   환경 변수로 설정해주세요.")
        return
    
    print(f"\n✅ API 키 확인 완료: {api_key[:10]}...")
    
    # Tool 초기화
    try:
        maps_tool = GoogleMapsTool(config={"api_key": api_key})
        print("✅ Google Maps Tool 초기화 성공")
    except Exception as e:
        print(f"❌ Tool 초기화 실패: {e}")
        return
    
    # 테스트용 장소 데이터 (서울 유명 장소들)
    test_places = [
        {
            "name": "경복궁",
            "address": "서울특별시 종로구 사직로 161",
            "coordinates": {
                "lat": 37.5796,
                "lng": 126.9770
            }
        },
        {
            "name": "남산타워",
            "address": "서울특별시 용산구 남산공원길 105",
            "coordinates": {
                "lat": 37.5512,
                "lng": 126.9882
            }
        },
        {
            "name": "명동",
            "address": "서울특별시 중구 명동",
            "coordinates": {
                "lat": 37.5636,
                "lng": 126.9826
            }
        },
        {
            "name": "인사동",
            "address": "서울특별시 종로구 인사동길",
            "coordinates": {
                "lat": 37.5735,
                "lng": 126.9868
            }
        }
    ]
    
    print("\n" + "-" * 60)
    print("테스트 1: 좌표가 있는 장소들로 경로 최적화")
    print("-" * 60)
    print(f"테스트 장소: {[place['name'] for place in test_places]}")
    
    # 테스트 1: 좌표가 있는 경우
    result1 = await maps_tool.execute(
        places=test_places,
        mode="transit",
        optimize_waypoints=True
    )
    
    if result1["success"]:
        print("\n✅ 경로 최적화 성공!")
        print(f"   최적화된 경로 순서:")
        for i, place in enumerate(result1["optimized_route"], 1):
            print(f"   {i}. {place['name']}")
        print(f"\n   총 소요 시간: {result1['total_duration']}초 ({result1['total_duration'] // 60}분)")
        print(f"   총 거리: {result1['total_distance']}m ({result1['total_distance'] / 1000:.2f}km)")
        print(f"   구간 수: {len(result1['directions'])}개")
        
        # 각 구간별 정보 출력
        if result1["directions"]:
            print("\n   구간별 상세 정보:")
            for i, direction in enumerate(result1["directions"], 1):
                print(f"\n   구간 {i}: {direction['from']} → {direction['to']}")
                if direction.get("duration_text"):
                    print(f"      소요 시간: {direction['duration_text']}")
                if direction.get("distance_text"):
                    print(f"      거리: {direction['distance_text']}")
                if direction.get("error"):
                    print(f"      ⚠️ 경고: {direction['error']}")
    else:
        print(f"\n❌ 경로 최적화 실패: {result1.get('error')}")
    
    print("\n" + "-" * 60)
    print("테스트 2: 주소만 있는 장소들로 경로 최적화")
    print("-" * 60)
    
    # 테스트 2: 주소만 있는 경우 (좌표는 자동으로 변환)
    test_places_address_only = [
        {
            "name": "롯데월드타워",
            "address": "서울특별시 송파구 올림픽로 300"
        },
        {
            "name": "한강공원",
            "address": "서울특별시 영등포구 여의도로"
        }
    ]
    
    print(f"테스트 장소: {[place['name'] for place in test_places_address_only]}")
    
    result2 = await maps_tool.execute(
        places=test_places_address_only,
        mode="driving",
        optimize_waypoints=True
    )
    
    if result2["success"]:
        print("\n✅ 경로 최적화 성공!")
        print(f"   최적화된 경로 순서:")
        for i, place in enumerate(result2["optimized_route"], 1):
            print(f"   {i}. {place['name']}")
            if place.get("coordinates"):
                print(f"      좌표: {place['coordinates']['lat']:.4f}, {place['coordinates']['lng']:.4f}")
        print(f"\n   총 소요 시간: {result2['total_duration']}초 ({result2['total_duration'] // 60}분)")
        print(f"   총 거리: {result2['total_distance']}m ({result2['total_distance'] / 1000:.2f}km)")
    else:
        print(f"\n❌ 경로 최적화 실패: {result2.get('error')}")
    
    print("\n" + "-" * 60)
    print("테스트 3: 출발지/도착지 지정 테스트")
    print("-" * 60)
    
    # 테스트 3: 출발지와 도착지 지정
    origin = {
        "name": "서울역",
        "address": "서울특별시 중구 한강대로 405",
        "coordinates": {
            "lat": 37.5559,
            "lng": 126.9723
        }
    }
    
    destination = {
        "name": "김포공항",
        "address": "인천광역시 중구 공항로 272",
        "coordinates": {
            "lat": 37.5583,
            "lng": 126.7906
        }
    }
    
    print(f"출발지: {origin['name']}")
    print(f"경유지: {[place['name'] for place in test_places[:2]]}")
    print(f"도착지: {destination['name']}")
    
    result3 = await maps_tool.execute(
        places=test_places[:2],  # 경유지 2개만
        origin=origin,
        destination=destination,
        mode="transit",
        optimize_waypoints=True
    )
    
    if result3["success"]:
        print("\n✅ 경로 최적화 성공!")
        print(f"   최적화된 경로:")
        print(f"   0. {origin['name']} (출발지)")
        for i, place in enumerate(result3["optimized_route"], 1):
            print(f"   {i}. {place['name']}")
        print(f"   {len(result3['optimized_route']) + 1}. {destination['name']} (도착지)")
        print(f"\n   총 소요 시간: {result3['total_duration']}초 ({result3['total_duration'] // 60}분)")
        print(f"   총 거리: {result3['total_distance']}m ({result3['total_distance'] / 1000:.2f}km)")
    else:
        print(f"\n❌ 경로 최적화 실패: {result3.get('error')}")
    
    print("\n" + "-" * 60)
    print("테스트 4: 최적화 없이 원본 순서 유지")
    print("-" * 60)
    
    result4 = await maps_tool.execute(
        places=test_places[:3],
        mode="walking",
        optimize_waypoints=False  # 최적화 비활성화
    )
    
    if result4["success"]:
        print("\n✅ 경로 계산 성공!")
        print(f"   경로 순서 (원본 유지):")
        for i, place in enumerate(result4["optimized_route"], 1):
            print(f"   {i}. {place['name']}")
        print(f"\n   총 소요 시간: {result4['total_duration']}초 ({result4['total_duration'] // 60}분)")
        print(f"   총 거리: {result4['total_distance']}m ({result4['total_distance'] / 1000:.2f}km)")
        print(f"   구간 수: {len(result4['directions'])}개")
        
        # 디버깅: directions 내용 확인
        if result4['directions']:
            print("\n   구간별 상세 정보:")
            for i, direction in enumerate(result4["directions"], 1):
                print(f"\n   구간 {i}: {direction['from']} → {direction['to']}")
                if direction.get("duration_text"):
                    print(f"      소요 시간: {direction['duration_text']}")
                if direction.get("distance_text"):
                    print(f"      거리: {direction['distance_text']}")
                if direction.get("error"):
                    print(f"      ⚠️ 오류: {direction['error']}")
                if direction.get("duration") == 0 and direction.get("distance") == 0:
                    print(f"      ⚠️ 경고: 시간과 거리가 0입니다")
        else:
            print("\n   ⚠️ 경고: 구간 정보가 없습니다 (directions 리스트가 비어있음)")
    else:
        print(f"\n❌ 경로 계산 실패: {result4.get('error')}")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    # 비동기 함수 실행
    asyncio.run(test_google_maps_tool())

