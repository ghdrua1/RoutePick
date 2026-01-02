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
        "theme": "비 오는 날 서울 실내 데이트",
        "location": "서울",
        "group_size": 2,
        "visit_date": "2024-01-20",
        "visit_time": "오후",
        "transportation": "지하철"
    }
    
    print("=" * 50)
    print("RoutePick Agent 실행 예시")
    print("=" * 50)
    
    # 1. Search Agent 실행
    print("\n[1단계] Search Agent 실행 중...")
    search_agent = SearchAgent(config=config)
    search_result = await search_agent.execute({
        "theme": user_input["theme"],
        "location": user_input["location"],
        "max_results": 20,
        "min_rating": 4.0
    })
    
    if not search_result["success"]:
        print(f"검색 실패: {search_result.get('error')}")
        return
    
    print(f"검색 완료: {search_result['total_count']}개 장소 발견")
    print(f"Agent: {search_result['agent_name']}")
    
    # 2. Planning Agent 실행
    print("\n[2단계] Planning Agent 실행 중...")
    planning_agent = PlanningAgent(config=config)
    course_result = await planning_agent.execute({
        "places": search_result["places"],
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
    print(f"Agent: {course_result['agent_name']}")
    print(f"선정 이유: {course_result.get('reasoning', 'N/A')}")
    
    course = course_result.get("course", {})
    print(f"선정된 장소 수: {len(course.get('places', []))}")
    
    # 3. Routing Agent 실행
    print("\n[3단계] Routing Agent 실행 중...")
    routing_agent = RoutingAgent(config=config)
    route_result = await routing_agent.execute({
        "places": course.get("places", []),
        "mode": user_input["transportation"],
        "optimize_waypoints": True
    })
    
    if not route_result["success"]:
        print(f"경로 최적화 실패: {route_result.get('error')}")
        return
    
    print(f"경로 최적화 완료")
    print(f"Agent: {route_result['agent_name']}")
    print(f"총 소요 시간: {route_result['total_duration']}초")
    print(f"총 거리: {route_result['total_distance']}미터")
    print(f"최적화된 경로: {len(route_result['optimized_route'])}개 장소")
    
    print("\n" + "=" * 50)
    print("실행 완료!")
    print("=" * 50)


if __name__ == "__main__":
    # 비동기 함수 실행
    asyncio.run(main())

