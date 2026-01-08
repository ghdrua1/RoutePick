"""
RoutePick Agent 인터랙티브 테스트 스크립트
사용자 입력을 받아 Agent를 테스트합니다.
"""

import asyncio
import os
from dotenv import load_dotenv
from agents.search_agent import SearchAgent
from agents.planning_agent import PlanningAgent
from config.config import Config

# .env 파일에서 환경 변수 로드
load_dotenv()


def get_user_input(prompt: str, required: bool = False, default: str = None) -> str:
    """
    사용자 입력을 받는 함수
    
    Args:
        prompt: 입력 프롬프트
        required: 필수 입력 여부
        default: 기본값
    
    Returns:
        사용자 입력값
    """
    while True:
        if default:
            full_prompt = f"{prompt} (기본값: {default})"
        else:
            full_prompt = f"{prompt}" if not required else f"{prompt} (필수) *"
        
        value = input(f"{full_prompt}: ").strip()
        
        if value:
            return value
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("⚠️  이 항목은 필수입니다. 다시 입력해주세요.")


def validate_and_collect_input() -> dict:
    """
    사용자 입력을 수집하고 검증하는 함수
    누락된 필수 정보가 있으면 재질문
    
    Returns:
        수집된 입력 데이터
    """
    print("=" * 70)
    print("🚀 RoutePick Agent 테스트")
    print("=" * 70)
    print()
    print("여행 코스를 설계하기 위해 다음 정보를 입력해주세요.")
    print()
    
    # 필수 정보 수집
    theme = get_user_input("📌 여행 테마", required=True)
    location = get_user_input("📍 지역 (예: 서울, 부산)", required=True)
    
    # 선택 정보 수집
    print()
    print("다음 정보는 선택사항입니다. Enter를 누르면 건너뛸 수 있습니다.")
    print()
    
    group_size_str = get_user_input("👥 여행 인원 (숫자)", required=False, default="2")
    visit_date = get_user_input("📅 방문 일자 (예: 2024-12-25)", required=False, default="")
    visit_time = get_user_input("⏰ 방문 시간 (예: 오후, 저녁)", required=False, default="오후")
    transportation = get_user_input("🚶 이동 수단 (도보, 지하철, 버스, 자동차)", required=False, default="도보")
    
    # 인원을 숫자로 변환
    try:
        group_size = int(group_size_str) if group_size_str else 2
    except ValueError:
        print("⚠️  인원은 숫자여야 합니다. 기본값 2명으로 설정합니다.")
        group_size = 2
    
    # 입력 데이터 구성
    input_data = {
        "theme": theme,
        "location": location,
        "group_size": group_size,
        "visit_date": visit_date,
        "visit_time": visit_time,
        "transportation": transportation
    }
    
    return input_data


def print_collected_info(data: dict):
    """수집된 정보를 출력하는 함수"""
    print()
    print("=" * 70)
    print("📋 수집된 정보 확인")
    print("=" * 70)
    print(f"  테마: {data['theme']}")
    print(f"  지역: {data['location']}")
    print(f"  인원: {data['group_size']}명")
    print(f"  방문 일자: {data['visit_date'] or '(미지정)'}")
    print(f"  방문 시간: {data['visit_time'] or '(미지정)'}")
    print(f"  이동 수단: {data['transportation'] or '(미지정)'}")
    print("=" * 70)
    print()


async def main():
    """메인 실행 함수"""
    
    # 설정 검증
    print("🔍 설정 확인 중...")
    if not Config.validate():
        print("\n❌ 필수 API 키가 설정되지 않았습니다.")
        print("📝 .env 파일을 확인하고 다음 키를 설정해주세요:")
        print("   - TAVILY_API_KEY")
        print("   - GOOGLE_MAPS_API_KEY")
        print("   - OPENAI_API_KEY")
        return
    
    print("✅ 설정 확인 완료\n")
    
    # 사용자 입력 수집
    user_data = validate_and_collect_input()
    
    # 입력 확인
    print_collected_info(user_data)
    
    confirm = input("위 정보로 진행하시겠습니까? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', '예', 'ㅇ']:
        print("❌ 취소되었습니다.")
        return
    
    print()
    print("=" * 70)
    print("🔄 Agent 실행 시작")
    print("=" * 70)
    print()
    
    # Agent 설정
    config = Config.get_agent_config()
    
    try:
        # ============================================================
        # Step 1: SearchAgent 실행 (Tavily 검색)
        # ============================================================
        print("📡 [Step 1] SearchAgent: 장소 검색 중...")
        print()
        
        search_agent = SearchAgent(config=config)
        search_input = {
            "theme": user_data["theme"],
            "location": user_data["location"]
        }
        
        # SearchAgent 입력 검증 및 누락 정보 확인
        if not search_agent.validate_input(search_input):
            print("❌ 필수 정보가 누락되었습니다.")
            missing_info = []
            
            if not search_input.get("theme"):
                missing_info.append("테마")
            if not search_input.get("location"):
                missing_info.append("지역")
            
            if missing_info:
                print(f"⚠️  다음 정보를 입력해주세요: {', '.join(missing_info)}")
                print()
                
                # 누락된 정보 재입력 받기
                if not search_input.get("theme"):
                    search_input["theme"] = get_user_input("📌 여행 테마", required=True)
                if not search_input.get("location"):
                    search_input["location"] = get_user_input("📍 지역", required=True)
                
                # 재검증
                if not search_agent.validate_input(search_input):
                    print("❌ 검증 실패: 필수 정보가 여전히 누락되었습니다.")
                    return
        
        search_result = await search_agent.execute(search_input)
        
        if not search_result.get("success"):
            print(f"❌ 장소 검색 실패: {search_result.get('error', '알 수 없는 오류')}")
            return
        
        places = search_result.get("candidate_pool", [])
        print(f"\n✅ 검색 완료: {len(places)}개의 장소를 찾았습니다.")
        print()
        
        if not places:
            print("⚠️  검색된 장소가 없습니다. 다른 테마나 지역으로 시도해주세요.")
            return
        
        # 검색된 장소 미리보기
        print("📍 검색된 장소 미리보기 (상위 5개):")
        for i, place in enumerate(places[:5], 1):
            print(f"  {i}. {place.get('name')} ({place.get('category')}) - 평점: {place.get('rating', 'N/A')}")
        print()
        
        # ============================================================
        # Step 2: PlanningAgent 실행 (코스 제작)
        # ============================================================
        print("🧠 [Step 2] PlanningAgent: 코스 제작 중...")
        print()
        
        planning_agent = PlanningAgent(config=config)
        
        # 사용자 선호도 구성
        user_preferences = {
            "theme": user_data["theme"],
            "group_size": user_data["group_size"],
            "visit_date": user_data["visit_date"] or "2024-12-25",
            "visit_time": user_data["visit_time"] or "오후",
            "transportation": user_data["transportation"] or "도보"
        }
        
        # 시간 제약 (선택사항)
        time_constraints = None
        if user_data.get("visit_time"):
            time_constraints = {
                "start_time": "14:00" if "오후" in user_data["visit_time"] else "10:00",
                "end_time": "20:00",
                "total_duration": 360  # 6시간
            }
        
        planning_input = {
            "places": places,
            "user_preferences": user_preferences,
            "time_constraints": time_constraints
        }
        
        # PlanningAgent 입력 검증 및 누락 정보 확인
        if not planning_agent.validate_input(planning_input):
            print("❌ 필수 정보가 누락되었습니다.")
            missing_info = []
            
            if not planning_input.get("places"):
                missing_info.append("장소 리스트")
            if not planning_input.get("user_preferences", {}).get("theme"):
                missing_info.append("테마")
            
            if missing_info:
                print(f"⚠️  다음 정보가 누락되었습니다: {', '.join(missing_info)}")
                
                # 장소가 없으면 검색 단계로 돌아가기
                if not planning_input.get("places"):
                    print("❌ 장소 검색 결과가 없습니다. 코스를 제작할 수 없습니다.")
                    return
                
                # 테마가 없으면 재입력
                if not planning_input.get("user_preferences", {}).get("theme"):
                    print()
                    theme = get_user_input("📌 여행 테마 (필수)", required=True)
                    planning_input["user_preferences"]["theme"] = theme
                
                # 재검증
                if not planning_agent.validate_input(planning_input):
                    print("❌ 검증 실패: 필수 정보가 여전히 누락되었습니다.")
                    return
        
        course_result = await planning_agent.execute(planning_input)
        
        if not course_result.get("success"):
            print(f"❌ 코스 제작 실패: {course_result.get('error', '알 수 없는 오류')}")
            return
        
        # ============================================================
        # 결과 출력
        # ============================================================
        print()
        print("=" * 70)
        print("✨ 코스 제작 완료!")
        print("=" * 70)
        print()
        
        course = course_result.get("course", {})
        
        # 코스 설명
        if course.get("course_description"):
            print("📝 코스 설명")
            print("-" * 70)
            print(course["course_description"])
            print()
        
        # 방문 순서
        sequence = course.get("sequence", [])
        places_list = course.get("places", [])
        estimated_duration = course.get("estimated_duration", {})
        
        if sequence and places_list:
            print("📍 방문 순서")
            print("-" * 70)
            
            for idx, place_idx in enumerate(sequence, 1):
                if place_idx < len(places_list):
                    place = places_list[place_idx]
                    duration = estimated_duration.get(str(place_idx), "정보 없음")
                    
                    print(f"\n{idx}. {place.get('name', '알 수 없음')}")
                    print(f"   📌 카테고리: {place.get('category', 'N/A')}")
                    print(f"   ⏱  체류 시간: {duration}분")
                    print(f"   ⭐ 평점: {place.get('rating', 'N/A')}")
                    print(f"   📍 주소: {place.get('address', '주소 정보 없음')}")
                    
                    if place.get('map_url'):
                        print(f"   🔗 지도: {place['map_url']}")
            
            print()
        
        # 선정 이유
        reasoning = course_result.get("reasoning")
        if reasoning:
            print("💡 선정 이유")
            print("-" * 70)
            print(reasoning)
            print()
        
        print("=" * 70)
        print("✅ 테스트 완료!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

