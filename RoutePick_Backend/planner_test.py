"""
RoutePick Agent 사용 예시
이 파일은 Agent와 Tool을 사용하는 방법을 보여줍니다.
"""

import asyncio
from agents import SearchAgent, PlanningAgent, RoutingAgent
from config.config import Config


async def main():
    """메인 실행 함수"""
    
    # 설정 로드
    config = Config.get_agent_config()
    
    # 사용자 입력 (실제 구현에서는 프론트엔드에서 받음)
    user_input = {
        "theme": "여자친구와의 연극 관람이 포함된 혜화 저녁 데이트",
        "location": "서울",
        "group_size": 2,
        "visit_date": "2024-01-20",
        "visit_time": "저녁",
        "transportation": "지하철"
    }
    
    print("=" * 50)
    print("Planning Agent 실행 예시")
    print("=" * 50)    
    # 2. Planning Agent 실행
    print("\nPlanning Agent 실행 중...")
    planning_agent = PlanningAgent(config=config)

    places = [
    {
        "name": "Pizzeria O",
        "category": "식당",
        "rating": 4.8,
        "trust_score": 5.0,
        "address": "86 Dongsung-gil, Jongno District, Seoul, South Korea",
        "source_url": "https://www.diningcode.com/list.dc?query=%ED%98%9C%ED%99%94",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Pizzeria+O+서울+혜화"
    },
    {
        "name": "REAL SHOT",
        "category": "활동",
        "rating": 4.3,
        "trust_score": 4.4,
        "address": "10 Jong-ro 12-gil, Jongno District, Seoul, South Korea",
        "source_url": "https://www.instagram.com/p/C53ALY9hIyl/",
        "map_url": "https://www.google.com/maps/search/?api=1&query=REAL+SHOT+서울+혜화"
    },
    {
        "name": "크레마노 경복궁점",
        "category": "카페",
        "rating": 5.0,
        "trust_score": 5.0,
        "address": "6 Tongui-dong, Jongno District, Seoul, South Korea",
        "source_url": "https://www.instagram.com/reel/DSMrfxkDz9i/",
        "map_url": "https://www.google.com/maps/search/?api=1&query=크레마노+경복궁점+서울+혜화"
    },
    {
        "name": "혜화시장",
        "category": "기타",
        "rating": 4.2,
        "trust_score": 4.4,
        "address": "27-1 Myeongnyun 2(i)-ga, Jongno District, Seoul, South Korea",
        "source_url": "https://www.diningcode.com/list.dc?query=%ED%98%9C%ED%99%94+%EB%B6%84%EC%9C%84%EA%B8%B0%EC%A2%8B%EC%9D%80%EC%B9%B4%ED%8E%98",
        "map_url": "https://www.google.com/maps/search/?api=1&query=혜화시장+서울+혜화"
    },
    {
        "name": "Hyehwa Art Center",
        "category": "관광지",
        "rating": 4.5,
        "trust_score": 4.7,
        "address": "156 Daehak-ro, Jongno District, Seoul, South Korea",
        "source_url": "https://www.instagram.com/p/ChtBhPiuDfM/",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Hyehwa+Art+Center+서울+혜화"
    },
    {
        "name": "메종아카이",
        "category": "식당",
        "rating": 5.0,
        "trust_score": 5.0,
        "address": "South Korea, Seoul, Jongno District, Daemyeong-gil, 34 2층",
        "source_url": "https://www.diningcode.com/list.dc?query=%ED%98%9C%ED%99%94",
        "map_url": "https://www.google.com/maps/search/?api=1&query=메종아카이+서울+혜화"
    },
    {
        "name": "세우아트센터",
        "category": "활동",
        "rating": 4.3,
        "trust_score": 4.3,
        "address": "49 Daehak-ro 12-gil, Jongno District, Seoul, South Korea",
        "source_url": "https://blog.naver.com/kshjbe/223873927572",
        "map_url": "https://www.google.com/maps/search/?api=1&query=세우아트센터+서울+혜화"
    },
    {
        "name": "Cafe Chieut",
        "category": "카페",
        "rating": 4.8,
        "trust_score": 4.9,
        "address": "18 Dongsung 4na-gil, Jongno District, Seoul, South Korea",
        "source_url": "https://kr.trip.com/moments/detail/seoul-234-132096855/",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Cafe+Chieut+서울+혜화"
    },
    {
        "name": "Yurae",
        "category": "식당",
        "rating": 5.0,
        "trust_score": 5.0,
        "address": "266 Jong-ro, Jongno District, Seoul, South Korea",
        "source_url": "https://meanmin.tistory.com/97",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Yurae+서울+혜화"
    },
    {
        "name": "Meerkat Park",
        "category": "활동",
        "rating": 3.7,
        "trust_score": 3.85,
        "address": "1-113 6층, Dongsung-dong, Jongno District, Seoul, South Korea",
        "source_url": "https://m.blog.naver.com/tiffany0711/222703684516",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Meerkat+Park+서울+혜화"
    },
    {
        "name": "Coffee Hanyakbang Hyehwa Branch",
        "category": "카페",
        "rating": 4.6,
        "trust_score": 4.7,
        "address": "9 Dongsung 2-gil, Jongno District, Seoul, South Korea",
        "source_url": "https://www.diningcode.com/list.dc?query=%ED%98%9C%ED%99%94",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Coffee+Hanyakbang+Hyehwa+Branch+서울+혜화"
    },
    {
        "name": "Sundae Silrok",
        "category": "식당",
        "rating": 4.5,
        "trust_score": 4.75,
        "address": "South Korea, Seoul, Jongno District, Dongsung-gil, 113 1층",
        "source_url": "https://m.blog.naver.com/seulpaces/222762217258",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Sundae+Silrok+서울+혜화"
    },
    {
        "name": "Seohwa Coffee",
        "category": "카페",
        "rating": 4.5,
        "trust_score": 4.6,
        "address": "8 Daehak-ro 9ga-gil, Jongno District, Seoul, South Korea",
        "source_url": "https://www.diningcode.com/list.dc?query=%ED%98%9C%ED%99%94",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Seohwa+Coffee+서울+혜화"
    },
    {
        "name": "Hidden Sushi",
        "category": "식당",
        "rating": 4.6,
        "trust_score": 4.7,
        "address": "27 Daemyeong-gil, Myeongnyun 4(sa)-ga, Jongno District, Seoul, South Korea",
        "source_url": "https://www.diningcode.com/list.dc?query=%ED%98%9C%ED%99%94+%EB%B6%84%EC%9C%84%EA%B8%B0%EC%A2%8B%EC%9D%80%EC%B9%B4%ED%8E%98",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Hidden+Sushi+서울+혜화"
    },
    {
        "name": "Chillin",
        "category": "카페",
        "rating": 4.5,
        "trust_score": 4.6,
        "address": "South Korea, Seoul, Jongno District, 혜화동 Daehak-ro 11-gil, 41-8 1층",
        "source_url": "https://www.instagram.com/p/C53ALY9hIyl/",
        "map_url": "https://www.google.com/maps/search/?api=1&query=Chillin+서울+혜화"
    }
    ]
    course_result = await planning_agent.execute({
        "places": places,
        "user_preferences": {
            "theme": user_input["theme"],
            "group_size": user_input["group_size"],
            "visit_date": user_input["visit_date"],
            "visit_time": user_input["visit_time"],
            "transportation": user_input["transportation"]
        }
    })
    
    if not course_result["success"]:
        print(f"코스 생성 실패: {course_result.get('error')}")
        return
    
    print(f"코스 생성 완료")
    print(f"Agent: {course_result['agent_name']}\n")
    print(f"선정 이유: {course_result.get('reasoning', 'N/A')}\n")
    course_info = course_result.get('course')
    print(f"간단 설명: {course_info.get('course_description')}\n")
    print(f"선정한 장소들: {', '.join(plc['name'] for plc in course_info.get('places'))}\n")
    print(f"순서 인덱스: {course_info.get('sequence')}\n")
    
    course = course_result.get("course", {})
    print(f"선정된 장소 수: {len(course.get('places', []))}")
    
    print("\n" + "=" * 50)
    print("실행 완료!")
    print("=" * 50)


if __name__ == "__main__":
    # 비동기 함수 실행
    asyncio.run(main())

